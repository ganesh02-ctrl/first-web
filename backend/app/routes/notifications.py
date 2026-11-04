from flask import Blueprint
from flask_jwt_extended import current_user

from app.middleware.auth import login_required
from app.routes.helpers import flag, json_body
from app.schemas import load
from app.schemas.notification import PreferenceSchema
from app.services import notification as svc
from app.utils.pagination import paginate
from app.utils.responses import success

bp = Blueprint("notifications", __name__, url_prefix="/api/notifications")


@bp.get("")
@login_required
def list_notifications():
    items, meta = paginate(svc.list_for_user(current_user, flag("unread")), lambda n: n.to_dict())
    return success(items, meta=meta)


@bp.get("/unread-count")
@login_required
def unread_count():
    return success({"count": svc.unread_count(current_user)})


@bp.post("/<int:notification_id>/read")
@login_required
def mark_read(notification_id):
    svc.mark_read(current_user, notification_id)
    return success(None, "Marked as read")


@bp.post("/read-all")
@login_required
def mark_all_read():
    return success({"updated": svc.mark_read(current_user)}, "All notifications marked as read")


@bp.delete("/<int:notification_id>")
@login_required
def delete(notification_id):
    svc.delete(current_user, notification_id)
    return success(None, "Notification deleted")


@bp.get("/preferences")
@login_required
def get_preferences():
    return success(svc.get_preferences(current_user).to_dict())


@bp.put("/preferences")
@login_required
def update_preferences():
    pref = svc.update_preferences(current_user, load(PreferenceSchema(), json_body()))
    return success(pref.to_dict(), "Preferences saved")
