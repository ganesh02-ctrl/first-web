"""Notifications + per-channel delivery with retries. 'sent' only after provider confirmation."""
import logging
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

from flask import current_app

from app.extensions import db
from app.models import Notification, NotificationDelivery, NotificationPreference
from app.services import email as email_service
from app.services import sms as sms_service
from app.utils.errors import NotFound
from app.utils.timeutils import utcnow

logger = logging.getLogger(__name__)


def get_preferences(user) -> NotificationPreference:
    if user.notification_preference is None:
        user.notification_preference = NotificationPreference()
        db.session.commit()
    return user.notification_preference


def update_preferences(user, data: dict) -> NotificationPreference:
    pref = get_preferences(user)
    for key, value in data.items():
        setattr(pref, key, sorted(set(value), reverse=True) if key == "reminder_days" else value)
    db.session.commit()
    return pref


def create_notification(user, kind: str, title: str, message: str, link: str | None = None,
                        scholarship_id: int | None = None, reminder_days: int | None = None,
                        dedupe_key: str | None = None) -> Notification | None:
    """Returns None if a notification with the same dedupe_key already exists."""
    if dedupe_key and Notification.query.filter_by(dedupe_key=dedupe_key).first():
        return None
    pref = get_preferences(user)
    note = Notification(user_id=user.id, kind=kind, title=title[:255], message=message, link=link,
                        scholarship_id=scholarship_id, reminder_days=reminder_days, dedupe_key=dedupe_key,
                        is_read=not pref.in_app_enabled)
    now = utcnow()
    retries = current_app.config["EMAIL_MAX_RETRIES"]
    note.deliveries.append(NotificationDelivery(channel="in_app", status="sent", sent_at=now, attempts=1))
    if pref.email_enabled:
        if email_service.is_configured():
            note.deliveries.append(NotificationDelivery(channel="email", status="pending", recipient=user.email,
                                                        max_attempts=retries, next_attempt_at=now))
        else:
            note.deliveries.append(NotificationDelivery(channel="email", status="skipped", recipient=user.email,
                                                        last_error="SMTP not configured"))
    if pref.sms_enabled:
        phone = user.profile.phone if user.profile else None
        if sms_service.is_configured() and phone:
            note.deliveries.append(NotificationDelivery(channel="sms", status="pending", recipient=phone,
                                                        max_attempts=retries, next_attempt_at=now))
        else:
            reason = "SMS provider not configured" if not sms_service.is_configured() else "No phone number"
            note.deliveries.append(NotificationDelivery(channel="sms", status="skipped", recipient=phone,
                                                        last_error=reason))
    try:
        with db.session.begin_nested():
            db.session.add(note)
    except IntegrityError:  # concurrent run inserted the same dedupe_key
        return None
    return note


def _attempt(delivery: NotificationDelivery) -> None:
    note = delivery.notification
    delivery.attempts += 1
    if delivery.channel == "email":
        link = f"\n\nOpen: {current_app.config['FRONTEND_URL']}{note.link}" if note.link else ""
        result = email_service.send_email(delivery.recipient, note.title, note.message + link)
    else:
        result = sms_service.send_sms(delivery.recipient, f"{note.title}: {note.message}")
    if result.ok:
        delivery.status, delivery.sent_at = "sent", utcnow()
        delivery.provider_message_id, delivery.last_error, delivery.next_attempt_at = result.provider_id, None, None
    elif result.skipped:
        delivery.status, delivery.last_error, delivery.next_attempt_at = "skipped", result.error, None
    elif delivery.attempts >= delivery.max_attempts:
        delivery.status, delivery.last_error, delivery.next_attempt_at = "failed", result.error, None
    else:
        base = current_app.config["EMAIL_RETRY_BASE_MINUTES"]
        delivery.last_error = result.error
        delivery.next_attempt_at = utcnow() + timedelta(minutes=base * (2 ** (delivery.attempts - 1)))


def process_pending_deliveries(limit: int = 200) -> dict:
    due = (NotificationDelivery.query
           .filter(NotificationDelivery.status == "pending",
                   NotificationDelivery.channel.in_(["email", "sms"]),
                   NotificationDelivery.next_attempt_at <= utcnow())
           .order_by(NotificationDelivery.next_attempt_at).limit(limit).all())
    stats = {"processed": 0, "sent": 0, "failed": 0, "retrying": 0, "skipped": 0}
    for delivery in due:
        try:
            _attempt(delivery)
        except Exception as exc:  # noqa: BLE001 - one bad delivery must not stop the batch
            logger.exception("Delivery %s crashed", delivery.id)
            delivery.last_error = str(exc)[:1000]
            delivery.status = "failed" if delivery.attempts >= delivery.max_attempts else "pending"
        stats["processed"] += 1
        key = "retrying" if delivery.status == "pending" else delivery.status
        stats[key] = stats.get(key, 0) + 1
        db.session.commit()
    return stats


def list_for_user(user, unread_only: bool = False):
    query = Notification.query.filter_by(user_id=user.id)
    if unread_only:
        query = query.filter_by(is_read=False)
    return query.order_by(Notification.created_at.desc())


def unread_count(user) -> int:
    return Notification.query.filter_by(user_id=user.id, is_read=False).count()


def mark_read(user, notification_id: int | None = None) -> int:
    query = Notification.query.filter_by(user_id=user.id, is_read=False)
    if notification_id is not None:
        if not Notification.query.filter_by(id=notification_id, user_id=user.id).first():
            raise NotFound("Notification not found")
        query = query.filter_by(id=notification_id)
    count = query.update({"is_read": True, "read_at": utcnow()}, synchronize_session=False)
    db.session.commit()
    return count


def delete(user, notification_id: int) -> None:
    note = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if not note:
        raise NotFound("Notification not found")
    db.session.delete(note)
    db.session.commit()
