"""Dashboard statistics — every number comes from live queries."""
from sqlalchemy import func

from app.extensions import db
from app.models import (Achievement, Notification, NotificationDelivery, Scholarship, ScholarshipApplication,
                        ScholarshipReport, TrackedScholarship, UploadedDocument, User)
from app.services.academic import summary
from app.utils.timeutils import today_local


def student_dashboard(user) -> dict:
    today = today_local()
    upcoming = (TrackedScholarship.query.join(Scholarship)
                .filter(TrackedScholarship.user_id == user.id, Scholarship.is_published.is_(True),
                        Scholarship.application_close_date >= today)
                .order_by(Scholarship.application_close_date).limit(5).all())
    academic = summary(user)
    return {
        "tracked_count": TrackedScholarship.query.filter_by(user_id=user.id).count(),
        "applications_submitted": ScholarshipApplication.query.filter(
            ScholarshipApplication.user_id == user.id,
            ScholarshipApplication.status.in_(["applied", "approved", "rejected"])).count(),
        "application_status_counts": dict(db.session.query(ScholarshipApplication.status, func.count())
                                          .filter_by(user_id=user.id).group_by(ScholarshipApplication.status).all()),
        "upcoming_deadlines": [t.scholarship.to_summary() for t in upcoming],
        "cgpa": academic["cgpa"],
        "sgpa_trend": [{"semester": s["number"], "sgpa": s["sgpa"]} for s in academic["semesters"]],
        "achievement_count": Achievement.query.filter_by(user_id=user.id).count(),
        "document_count": UploadedDocument.query.filter_by(user_id=user.id).count(),
        "unread_notifications": Notification.query.filter_by(user_id=user.id, is_read=False).count(),
        "recent_notifications": [n.to_dict() for n in Notification.query.filter_by(user_id=user.id)
                                 .order_by(Notification.created_at.desc()).limit(5)],
    }


def admin_dashboard() -> dict:
    today = today_local()
    by_status = dict(db.session.query(Scholarship.verification_status, func.count())
                     .group_by(Scholarship.verification_status).all())
    by_type = dict(db.session.query(Scholarship.scholarship_type, func.count())
                   .group_by(Scholarship.scholarship_type).all())
    deliveries = db.session.query(NotificationDelivery.channel, NotificationDelivery.status, func.count()) \
        .group_by(NotificationDelivery.channel, NotificationDelivery.status).all()
    most_tracked = (db.session.query(Scholarship.id, Scholarship.title, func.count(TrackedScholarship.id))
                    .join(TrackedScholarship).group_by(Scholarship.id, Scholarship.title)
                    .order_by(func.count(TrackedScholarship.id).desc()).limit(5).all())
    return {
        "students": User.query.filter_by(role="student").count(),
        "active_students": User.query.filter_by(role="student", is_active=True).count(),
        "scholarships_total": Scholarship.query.count(),
        "scholarships_published": Scholarship.query.filter_by(is_published=True).count(),
        "scholarships_open": Scholarship.query.filter(Scholarship.is_published.is_(True),
                                                      Scholarship.application_close_date >= today).count(),
        "by_verification_status": by_status,
        "by_type": by_type,
        "open_reports": ScholarshipReport.query.filter(ScholarshipReport.status.in_(["open", "reviewing"])).count(),
        "applications_total": ScholarshipApplication.query.count(),
        "deliveries": [{"channel": c, "status": s, "count": n} for c, s, n in deliveries],
        "most_tracked": [{"id": i, "title": t, "count": n} for i, t, n in most_tracked],
    }
