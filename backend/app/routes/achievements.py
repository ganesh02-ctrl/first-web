import io

from flask import Blueprint, request, send_file
from flask_jwt_extended import current_user

from app.middleware.auth import login_required
from app.routes.helpers import json_body
from app.schemas import load
from app.schemas.achievement import AchievementSchema
from app.services import achievement as svc
from app.services.report_pdf import portfolio
from app.utils.constants import ACHIEVEMENT_CATEGORIES
from app.utils.responses import success

bp = Blueprint("achievements", __name__, url_prefix="/api/achievements")


@bp.get("")
@login_required
def list_achievements():
    category = request.args.get("category")
    category = category if category in ACHIEVEMENT_CATEGORIES else None
    return success([a.to_dict() for a in svc.list_for_user(current_user, category)])


@bp.post("")
@login_required
def create():
    ach = svc.save(current_user, load(AchievementSchema(), json_body()))
    return success(ach.to_dict(), "Achievement added", 201)


@bp.get("/<int:ach_id>")
@login_required
def get_one(ach_id):
    return success(svc.get_owned_achievement(current_user, ach_id).to_dict())


@bp.put("/<int:ach_id>")
@login_required
def update(ach_id):
    ach = svc.save(current_user, load(AchievementSchema(), json_body(), partial=True), ach_id)
    return success(ach.to_dict(), "Achievement updated")


@bp.delete("/<int:ach_id>")
@login_required
def delete(ach_id):
    svc.delete(current_user, ach_id)
    return success(None, "Achievement deleted")


@bp.get("/portfolio.pdf")
@login_required
def portfolio_pdf():
    return send_file(io.BytesIO(portfolio(current_user)), mimetype="application/pdf",
                     as_attachment=True, download_name="achievement-portfolio.pdf")
