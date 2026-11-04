from flask import Blueprint
from flask_jwt_extended import current_user

from app.extensions import db
from app.middleware.auth import login_required
from app.models import StudentProfile
from app.routes.helpers import json_body
from app.schemas import load
from app.schemas.profile import ProfileUpdateSchema
from app.services import achievement as achievement_service
from app.services.dashboard import student_dashboard
from app.utils.responses import success

bp = Blueprint("students", __name__, url_prefix="/api/students")


def _profile() -> StudentProfile:
    if current_user.profile is None:
        current_user.profile = StudentProfile(full_name=current_user.email.split("@")[0])
        db.session.commit()
    return current_user.profile


@bp.get("/me/profile")
@login_required
def get_profile():
    return success(_profile().to_dict())


@bp.patch("/me/profile")
@login_required
def update_profile():
    data = load(ProfileUpdateSchema(), json_body(), partial=True)
    portfolio = data.pop("public_portfolio_enabled", None)
    profile = _profile()
    for key, value in data.items():
        setattr(profile, key, value.strip() if isinstance(value, str) else value)
    db.session.commit()
    if portfolio is not None:
        achievement_service.set_portfolio_enabled(current_user, portfolio)
    return success(profile.to_dict(), "Profile saved")


@bp.get("/me/dashboard")
@login_required
def dashboard():
    return success(student_dashboard(current_user))
