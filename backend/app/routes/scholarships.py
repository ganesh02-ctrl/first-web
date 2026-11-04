from flask import Blueprint, request
from flask_jwt_extended import current_user, get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.middleware.auth import login_required
from app.models import ScholarshipApplication, TrackedScholarship, User
from app.routes.helpers import json_body
from app.schemas import load
from app.schemas.scholarship import FilterSchema, ReportSchema
from app.services import scholarship as svc
from app.utils.pagination import paginate
from app.utils.responses import success

bp = Blueprint("scholarships", __name__, url_prefix="/api/scholarships")


@bp.get("")
def list_scholarships():
    filters = load(FilterSchema(), request.args.to_dict())
    items, meta = paginate(svc.search_query(filters), lambda s: s.to_summary())
    return success(items, meta=meta)


@bp.get("/categories")
def categories():
    return success([c.to_dict() for c in svc.list_categories()])


@bp.get("/<id_or_slug>")
def detail(id_or_slug):
    sch = svc.get_public(id_or_slug)
    data = sch.to_detail()
    data["tracking"] = data["application"] = None
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity)) if identity else None
    if user:
        tracked = TrackedScholarship.query.filter_by(user_id=user.id, scholarship_id=sch.id).first()
        application = ScholarshipApplication.query.filter_by(user_id=user.id, scholarship_id=sch.id).first()
        data["tracking"] = {"is_bookmarked": tracked.is_bookmarked,
                            "reminders_enabled": tracked.reminders_enabled} if tracked else None
        data["application"] = application.to_dict() if application else None
    return success(data)


@bp.post("/<int:sch_id>/report")
@login_required
def report(sch_id):
    item = svc.submit_report(current_user, sch_id, load(ReportSchema(), json_body()))
    return success(item.to_dict(), "Thank you. An administrator will review this report.", 201)
