"""Restore scholarship editing using existing validation and service logic."""
from flask import Blueprint, request
from flask_jwt_extended import current_user

from app.middleware.auth import admin_required
from app.schemas import load
from app.schemas.scholarship import ScholarshipSchema
from app.services import scholarship
from app.utils.responses import success

bp = Blueprint(
    "admin_scholarship_edit",
    __name__,
    url_prefix="/api/admin",
)


@bp.route(
    "/scholarships/<int:sch_id>",
    methods=["PUT", "PATCH"],
)
@admin_required
def update_scholarship(sch_id):
    data = load(
        ScholarshipSchema(),
        request.get_json(silent=True),
        partial=True,
    )
    return success(
        scholarship.update(
            current_user, sch_id, data
        ).to_detail(),
        "Scholarship updated",
    )
