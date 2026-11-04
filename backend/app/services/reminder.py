"""Daily deadline reminder job. Idempotent: dedupe_key = user:scholarship:days:deadline."""
import logging
from datetime import date

from flask import current_app

from app.extensions import db
from app.models import Scholarship, ScholarshipApplication, TrackedScholarship
from app.services.notification import create_notification, get_preferences
from app.utils.timeutils import today_local

logger = logging.getLogger(__name__)
CLOSED_STATUSES = {"applied", "approved", "rejected"}


def mark_expired_scholarships(today: date) -> int:
    count = (Scholarship.query
             .filter(Scholarship.application_close_date < today,
                     Scholarship.verification_status.in_(["verified", "needs_review", "unverified"]))
             .update({"verification_status": "expired"}, synchronize_session=False))
    db.session.commit()
    return count


def run_deadline_reminders(today: date | None = None) -> dict:
    today = today or today_local()
    allowed_days = set(current_app.config["REMINDER_DAYS"])
    stats = {"date": today.isoformat(), "created": 0, "duplicates": 0, "expired_marked": 0}
    rows = (TrackedScholarship.query.join(Scholarship)
            .filter(TrackedScholarship.reminders_enabled.is_(True), Scholarship.is_published.is_(True),
                    Scholarship.application_close_date.isnot(None),
                    Scholarship.application_close_date >= today).all())
    for tracked in rows:
        user, sch = tracked.user, tracked.scholarship
        if not user.is_active:
            continue
        pref = get_preferences(user)
        days_left = (sch.application_close_date - today).days
        if not pref.deadline_reminders or days_left not in allowed_days or \
                days_left not in set(pref.reminder_days or []):
            continue
        app_ = ScholarshipApplication.query.filter_by(user_id=user.id, scholarship_id=sch.id).first()
        if app_ and app_.status in CLOSED_STATUSES:
            continue
        key = f"deadline:{user.id}:{sch.id}:{days_left}:{sch.application_close_date.isoformat()}"
        word = "day" if days_left == 1 else "days"
        note = create_notification(
            user, "deadline_reminder", f"{days_left} {word} left: {sch.title}",
            f"The application for '{sch.title}' closes on {sch.application_close_date:%d %b %Y}. "
            f"Confirm details on the official site before applying: {sch.application_url}",
            link=f"/scholarships/{sch.id}", scholarship_id=sch.id, reminder_days=days_left, dedupe_key=key)
        stats["created" if note else "duplicates"] += 1
        db.session.commit()
    stats["expired_marked"] = mark_expired_scholarships(today)
    logger.info("Reminder run: %s", stats)
    return stats
