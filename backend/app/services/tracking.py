"""Tracking, bookmarks and application status."""
from app.extensions import db
from app.models import ScholarshipApplication, TrackedScholarship
from app.services.notification import create_notification, get_preferences
from app.services.scholarship import get_public
from app.utils.constants import APPLICATION_STATUS_LABELS
from app.utils.errors import NotFound


def list_tracked(user, bookmarked_only: bool = False):
    query = TrackedScholarship.query.filter_by(user_id=user.id)
    if bookmarked_only:
        query = query.filter_by(is_bookmarked=True)
    items = query.order_by(TrackedScholarship.created_at.desc()).all()
    apps = {a.scholarship_id: a for a in ScholarshipApplication.query.filter_by(user_id=user.id)}
    return [t.to_dict(apps.get(t.scholarship_id)) for t in items if t.scholarship and t.scholarship.is_published]


def track(user, sch_id: int, data: dict) -> TrackedScholarship:
    get_public(sch_id)
    tracked = TrackedScholarship.query.filter_by(user_id=user.id, scholarship_id=sch_id).first()
    if not tracked:
        tracked = TrackedScholarship(user_id=user.id, scholarship_id=sch_id)
        db.session.add(tracked)
    for key in ("is_bookmarked", "reminders_enabled"):
        if key in data:
            setattr(tracked, key, data[key])
    db.session.commit()
    return tracked


def untrack(user, sch_id: int) -> None:
    tracked = TrackedScholarship.query.filter_by(user_id=user.id, scholarship_id=sch_id).first()
    if not tracked:
        raise NotFound("Scholarship is not tracked")
    db.session.delete(tracked)
    db.session.commit()


def list_applications(user, status: str | None = None):
    query = ScholarshipApplication.query.filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(ScholarshipApplication.updated_at.desc()).all()


def upsert_application(user, sch_id: int, data: dict) -> ScholarshipApplication:
    sch = get_public(sch_id)
    app_ = ScholarshipApplication.query.filter_by(user_id=user.id, scholarship_id=sch_id).first()
    old_status = app_.status if app_ else None
    if not app_:
        app_ = ScholarshipApplication(user_id=user.id, scholarship_id=sch_id, status="interested")
        app_.change_status(data.get("status", "interested"), data.get("status_note"))
        db.session.add(app_)
    elif "status" in data:
        app_.change_status(data["status"], data.get("status_note"))
    for key in ("applied_on", "application_reference", "notes"):
        if key in data:
            setattr(app_, key, data[key])
    if not TrackedScholarship.query.filter_by(user_id=user.id, scholarship_id=sch_id).first():
        db.session.add(TrackedScholarship(user_id=user.id, scholarship_id=sch_id))
    if old_status and old_status != app_.status and get_preferences(user).application_updates:
        label = APPLICATION_STATUS_LABELS[app_.status]
        create_notification(user, "application_update", f"Status updated: {sch.title}",
                            f"You marked your application as '{label}'.", link="/applications",
                            scholarship_id=sch.id)
    db.session.commit()
    return app_


def delete_application(user, sch_id: int) -> None:
    app_ = ScholarshipApplication.query.filter_by(user_id=user.id, scholarship_id=sch_id).first()
    if not app_:
        raise NotFound("Application not found")
    db.session.delete(app_)
    db.session.commit()
