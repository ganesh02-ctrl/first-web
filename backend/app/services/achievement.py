"""Achievement locker and public portfolio."""
from app.extensions import db
from app.models import Achievement, StudentProfile
from app.services.document import get_owned
from app.utils.errors import NotFound
from app.utils.security import generate_public_slug


def list_for_user(user, category: str | None = None):
    query = Achievement.query.filter_by(user_id=user.id)
    if category:
        query = query.filter_by(category=category)
    return query.order_by(Achievement.achieved_on.desc()).all()


def get_owned_achievement(user, ach_id: int) -> Achievement:
    ach = Achievement.query.filter_by(id=ach_id, user_id=user.id).first()
    if not ach:
        raise NotFound("Achievement not found")
    return ach


def save(user, data: dict, ach_id: int | None = None) -> Achievement:
    ach = get_owned_achievement(user, ach_id) if ach_id else Achievement(user_id=user.id)
    if data.get("certificate_document_id"):
        get_owned(user, data["certificate_document_id"])  # must belong to this user
    for key, value in data.items():
        setattr(ach, key, value)
    db.session.add(ach)
    db.session.commit()
    return ach


def delete(user, ach_id: int) -> None:
    db.session.delete(get_owned_achievement(user, ach_id))
    db.session.commit()


def set_portfolio_enabled(user, enabled: bool) -> StudentProfile:
    profile = user.profile
    profile.public_portfolio_enabled = enabled
    if enabled and not profile.public_slug:
        while True:
            slug = generate_public_slug()
            if not StudentProfile.query.filter_by(public_slug=slug).first():
                profile.public_slug = slug
                break
    db.session.commit()
    return profile


def public_portfolio(slug: str) -> dict:
    profile = StudentProfile.query.filter_by(public_slug=slug, public_portfolio_enabled=True).first()
    if not profile or not profile.user.is_active:
        raise NotFound("Portfolio not found")
    items = (Achievement.query.filter_by(user_id=profile.user_id, is_public=True)
             .order_by(Achievement.achieved_on.desc()).all())
    return {"full_name": profile.full_name, "college": profile.college, "degree": profile.degree,
            "branch": profile.branch, "achievements": [a.to_dict(public=True) for a in items]}
