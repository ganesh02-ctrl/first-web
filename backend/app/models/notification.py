from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.constants import DELIVERY_CHANNELS, DELIVERY_STATUSES, NOTIFICATION_KINDS
from app.utils.timeutils import isoformat, utcnow

DEFAULT_REMINDER_DAYS = [30, 15, 7, 3, 1]


class Notification(db.Model):
    """In-app notification record. dedupe_key prevents duplicate reminders."""
    __tablename__ = "notifications"
    __table_args__ = (db.Index("ix_notifications_user_read", "user_id", "is_read", "created_at"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey("scholarships.id", ondelete="SET NULL"),
                               nullable=True, index=True)
    kind = db.Column(db.Enum(*NOTIFICATION_KINDS, name="notification_kind"), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(500), nullable=True)
    reminder_days = db.Column(db.SmallInteger, nullable=True)
    dedupe_key = db.Column(db.String(191), nullable=True, unique=True)
    is_read = db.Column(db.Boolean, nullable=False, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="notifications")
    scholarship = db.relationship("Scholarship")
    deliveries = db.relationship("NotificationDelivery", back_populates="notification",
                                 cascade="all, delete-orphan", order_by="NotificationDelivery.id")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "title": self.title,
            "message": self.message,
            "link": self.link,
            "scholarship_id": self.scholarship_id,
            "reminder_days": self.reminder_days,
            "is_read": self.is_read,
            "read_at": isoformat(self.read_at),
            "created_at": isoformat(self.created_at),
            "deliveries": [d.to_dict() for d in self.deliveries],
        }


class NotificationDelivery(TimestampMixin, db.Model):
    """Delivery attempt state per channel. 'sent' is only set after provider confirmation."""
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        db.UniqueConstraint("notification_id", "channel", name="uq_delivery_notification_channel"),
        db.Index("ix_deliveries_status_next", "status", "next_attempt_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey("notifications.id", ondelete="CASCADE"),
                                nullable=False)
    channel = db.Column(db.Enum(*DELIVERY_CHANNELS, name="delivery_channel"), nullable=False)
    status = db.Column(db.Enum(*DELIVERY_STATUSES, name="delivery_status"), nullable=False, default="pending")
    recipient = db.Column(db.String(255), nullable=True)
    attempts = db.Column(db.SmallInteger, nullable=False, default=0)
    max_attempts = db.Column(db.SmallInteger, nullable=False, default=3)
    last_error = db.Column(db.Text, nullable=True)
    next_attempt_at = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)
    provider_message_id = db.Column(db.String(255), nullable=True)

    notification = db.relationship("Notification", back_populates="deliveries")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "status": self.status,
            "attempts": self.attempts,
            "last_error": self.last_error,
            "sent_at": isoformat(self.sent_at),
            "next_attempt_at": isoformat(self.next_attempt_at),
        }


class NotificationPreference(TimestampMixin, db.Model):
    __tablename__ = "notification_preferences"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    in_app_enabled = db.Column(db.Boolean, nullable=False, default=True)
    email_enabled = db.Column(db.Boolean, nullable=False, default=True)
    sms_enabled = db.Column(db.Boolean, nullable=False, default=False)
    deadline_reminders = db.Column(db.Boolean, nullable=False, default=True)
    application_updates = db.Column(db.Boolean, nullable=False, default=True)
    reminder_days = db.Column(db.JSON, nullable=False, default=lambda: list(DEFAULT_REMINDER_DAYS))

    user = db.relationship("User", back_populates="notification_preference")

    def to_dict(self) -> dict:
        return {
            "in_app_enabled": self.in_app_enabled,
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "deadline_reminders": self.deadline_reminders,
            "application_updates": self.application_updates,
            "reminder_days": sorted(self.reminder_days or DEFAULT_REMINDER_DAYS, reverse=True),
        }
