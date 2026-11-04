from flask import Blueprint, request
from flask_jwt_extended import current_user

from app.middleware.auth import login_required
from app.routes.helpers import flag, json_body
from app.schemas import load
from app.schemas.scholarship import ApplicationSchema, TrackSchema
from app.services import tracking as svc
from app.utils.constants import APPLICATION_STATUSES
from app.utils.responses import success

bp = Blueprint("tracking", __name__, url_prefix="/api")


@bp.get("/tracking")
@login_required
def list_tracked():
    return success(svc.list_tracked(current_user, bookmarked_only=flag("bookmarked")))


@bp.put("/tracking/<int:sch_id>")
@login_required
def track(sch_id):
    tracked = svc.track(current_user, sch_id, load(TrackSchema(), json_body() or {}))
    return success(tracked.to_dict(), "Scholarship tracked")


@bp.delete("/tracking/<int:sch_id>")
@login_required
def untrack(sch_id):
    svc.untrack(current_user, sch_id)
    return success(None, "Scholarship removed from tracking")


@bp.get("/applications")
@login_required
def list_applications():
    status = request.args.get("status")
    status = status if status in APPLICATION_STATUSES else None
    return success([a.to_dict() for a in svc.list_applications(current_user, status)])


@bp.put("/applications/<int:sch_id>")
@login_required
def upsert_application(sch_id):
    app_ = svc.upsert_application(current_user, sch_id, load(ApplicationSchema(), json_body() or {}))
    return success(app_.to_dict(), "Application updated")


@bp.delete("/applications/<int:sch_id>")
@login_required
def delete_application(sch_id):
    svc.delete_application(current_user, sch_id)
    return success(None, "Application record deleted")
