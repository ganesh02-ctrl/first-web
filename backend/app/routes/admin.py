from flask import Blueprint, request
from flask_jwt_extended import current_user, verify_jwt_in_request

from app.models import AdminLog, Notification, NotificationDelivery, Scholarship, ScholarshipReport, User
from app.routes.helpers import flag, json_body
from app.schemas import load
from app.schemas.admin import AdminUserUpdateSchema, ReportUpdateSchema
from app.schemas.scholarship import CategorySchema, FilterSchema, ScholarshipSchema, VerifySchema
from app.services import admin_users, dashboard
from app.services import scholarship as sch_svc
from app.services.audit import log_action
from app.services.notification import process_pending_deliveries
from app.services.reminder import run_deadline_reminders
from app.services.scholarship_import import import_csv
from app.extensions import db
from app.utils.constants import DELIVERY_CHANNELS, DELIVERY_STATUSES, REPORT_STATUSES
from app.utils.errors import BadRequest, Forbidden, Unauthorized
from app.utils.pagination import paginate
from app.utils.responses import success
from app.utils.timeutils import isoformat

bp = Blueprint("admin", __name__, url_prefix="/api/admin")
MAX_CSV_BYTES = 5 * 1024 * 1024


@bp.before_request
def _require_admin():
    if request.method == "OPTIONS":  # let CORS preflight through
        return None
    verify_jwt_in_request()
    if current_user is None:
        raise Unauthorized("Authentication required")
    if not current_user.is_admin:
        raise Forbidden("Administrator access required")
    return None


@bp.get("/dashboard")
def admin_dashboard():
    return success(dashboard.admin_dashboard())


# ---- Students ----------------------------------------------------------
@bp.get("/users")
def users():
    query = admin_users.search_users(request.args.get("q"), request.args.get("role") or None,
                                     request.args.get("active"))
    items, meta = paginate(query, lambda u: u.to_dict())
    return success(items, meta=meta)


@bp.get("/users/<int:user_id>")
def user_detail(user_id):
    user = admin_users.get_user(user_id)
    data = user.to_dict()
    data["profile"] = user.profile.to_dict() if user.profile else None
    data["stats"] = {"tracked": user.tracked_scholarships.count(), "applications": user.applications.count(),
                     "achievements": user.achievements.count(), "documents": user.documents.count(),
                     "semesters": len(user.semesters)}
    return success(data)


@bp.patch("/users/<int:user_id>")
def update_user(user_id):
    user = admin_users.update_user(current_user, user_id, load(AdminUserUpdateSchema(), json_body()))
    return success(user.to_dict(), "User updated")


@bp.delete("/users/<int:user_id>")
def delete_user(user_id):
    admin_users.delete_user(current_user, user_id)
    return success(None, "User deleted")


# ---- Scholarships -------------------------------------------------------
@bp.get("/scholarships")
def list_scholarships():
    args = request.args.to_dict()
    args.setdefault("include_expired", "true")
    query = sch_svc.search_query(load(FilterSchema(), args), admin=True)
    published = request.args.get("published")
    if published in ("true", "false"):
        query = query.filter(Scholarship.is_published.is_(published == "true"))
    items, meta = paginate(query, lambda s: s.to_summary())
    return success(items, meta=meta)


@bp.post("/scholarships")
def create_scholarship():
    sch = sch_svc.create(current_user, load(ScholarshipSchema(), json_body()))
    return success(sch.to_detail(), "Scholarship created as unverified", 201)


@bp.get("/scholarships/<int:sch_id>")
def get_scholarship(sch_id):
    sch = sch_svc.get_any(sch_id)
    data = sch.to_detail()
    data["publish_problems"] = sch_svc.publish_problems(sch)
    data["verified_by"] = sch.verified_by.email if sch.verified_by else None
    return success(data)


@bp.patch("/scholarships/<int:sch_id>")
def update_scholarship(sch_id):
    sch = sch_svc.update(current_user, sch_id, load(ScholarshipSchema(), json_body(), partial=True))
    return success(sch.to_detail(), "Scholarship updated")


@bp.delete("/scholarships/<int:sch_id>")
def delete_scholarship(sch_id):
    sch_svc.delete(current_user, sch_id)
    return success(None, "Scholarship deleted")


@bp.post("/scholarships/<int:sch_id>/verify")
def verify_scholarship(sch_id):
    data = load(VerifySchema(), json_body())
    sch = sch_svc.verify(current_user, sch_id, data["verification_status"], data.get("verification_notes"))
    return success(sch.to_detail(), "Verification status updated")


@bp.post("/scholarships/import")
def import_scholarships():
    file = request.files.get("file")
    if file is None or not file.filename.lower().endswith(".csv"):
        raise BadRequest("Upload a .csv file")
    raw = file.read(MAX_CSV_BYTES + 1)
    if len(raw) > MAX_CSV_BYTES:
        raise BadRequest("CSV is larger than 5 MB", status=413, code="payload_too_large")
    dry_run = request.form.get("dry_run", "false").lower() in ("1", "true", "yes")
    return success(import_csv(current_user, raw, dry_run=dry_run),
                   "Dry run complete" if dry_run else "Import complete")


# ---- Categories ---------------------------------------------------------
@bp.get("/categories")
def categories():
    return success([{**c.to_dict(), "scholarship_count": len(c.scholarships)} for c in sch_svc.list_categories()])


@bp.post("/categories")
def create_category():
    return success(sch_svc.save_category(current_user, load(CategorySchema(), json_body())).to_dict(),
                   "Category created", 201)


@bp.put("/categories/<int:cat_id>")
def update_category(cat_id):
    return success(sch_svc.save_category(current_user, load(CategorySchema(), json_body()), cat_id).to_dict(),
                   "Category updated")


@bp.delete("/categories/<int:cat_id>")
def delete_category(cat_id):
    sch_svc.delete_category(current_user, cat_id)
    return success(None, "Category deleted")


# ---- Reports ------------------------------------------------------------
@bp.get("/reports")
def reports():
    query = ScholarshipReport.query
    status = request.args.get("status")
    if status in REPORT_STATUSES:
        query = query.filter_by(status=status)
    items, meta = paginate(query.order_by(ScholarshipReport.created_at.desc()), lambda r: r.to_dict())
    return success(items, meta=meta)


@bp.patch("/reports/<int:report_id>")
def update_report(report_id):
    report = sch_svc.update_report(current_user, report_id, load(ReportUpdateSchema(), json_body()))
    return success(report.to_dict(), "Report updated")


# ---- Logs ---------------------------------------------------------------
def _delivery_row(d: NotificationDelivery) -> dict:
    data = d.to_dict()
    data.update({"recipient": d.recipient, "notification_title": d.notification.title,
                 "kind": d.notification.kind, "user_email": d.notification.user.email,
                 "created_at": isoformat(d.created_at)})
    return data


@bp.get("/notifications/deliveries")
def delivery_logs():
    query = NotificationDelivery.query.join(Notification).join(User, Notification.user_id == User.id)
    if request.args.get("channel") in DELIVERY_CHANNELS:
        query = query.filter(NotificationDelivery.channel == request.args["channel"])
    if request.args.get("status") in DELIVERY_STATUSES:
        query = query.filter(NotificationDelivery.status == request.args["status"])
    if q := request.args.get("q"):
        query = query.filter(User.email.ilike(f"%{q.strip()}%"))
    items, meta = paginate(query.order_by(NotificationDelivery.id.desc()), _delivery_row, default_per_page=50)
    return success(items, meta=meta)


@bp.get("/logs")
def admin_logs():
    query = AdminLog.query
    if action := request.args.get("action"):
        query = query.filter(AdminLog.action.ilike(f"%{action.strip()}%"))
    items, meta = paginate(query.order_by(AdminLog.created_at.desc()), lambda e: e.to_dict(), default_per_page=50)
    return success(items, meta=meta)


# ---- Manual job triggers ------------------------------------------------
@bp.post("/jobs/reminders")
def run_reminders_now():
    stats = run_deadline_reminders()
    log_action(current_user, "job.run_reminders", "job", None, stats)
    db.session.commit()
    return success(stats, "Reminder job finished")


@bp.post("/jobs/deliveries")
def run_deliveries_now():
    stats = process_pending_deliveries()
    log_action(current_user, "job.process_deliveries", "job", None, stats)
    db.session.commit()
    return success(stats, "Delivery job finished")


@bp.get("/flags")
def flags():
    return success({"include_inactive": flag("include_inactive")})
