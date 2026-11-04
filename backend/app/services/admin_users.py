"""Admin student management."""
from sqlalchemy import or_

from app.extensions import db
from app.models import StudentProfile, User
from app.services.audit import log_action
from app.utils.errors import BadRequest, NotFound


def search_users(q: str | None, role: str | None = None, active: str | None = None):
    query = User.query.outerjoin(StudentProfile)
    if q:
        like = f"%{q.strip()}%"
        query = query.filter(or_(User.email.ilike(like), StudentProfile.full_name.ilike(like),
                                 StudentProfile.college.ilike(like)))
    if role:
        query = query.filter(User.role == role)
    if active in ("true", "false"):
        query = query.filter(User.is_active.is_(active == "true"))
    return query.order_by(User.created_at.desc())


def get_user(user_id: int) -> User:
    user = db.session.get(User, user_id)
    if not user:
        raise NotFound("User not found")
    return user


def update_user(admin, user_id: int, data: dict) -> User:
    user = get_user(user_id)
    if user.id == admin.id and (data.get("is_active") is False or data.get("role") == "student"):
        raise BadRequest("You cannot disable or demote your own account")
    changes = {k: v for k, v in data.items() if getattr(user, k) != v}
    for key, value in changes.items():
        setattr(user, key, value)
    if changes:
        log_action(admin, "user.update", "user", user.id, changes)
    db.session.commit()
    return user


def delete_user(admin, user_id: int) -> None:
    from app.services.storage import delete_file
    user = get_user(user_id)
    if user.id == admin.id:
        raise BadRequest("You cannot delete your own account")
    files = [d.stored_filename for d in user.documents]
    log_action(admin, "user.delete", "user", user.id, {"email": user.email})
    db.session.delete(user)
    db.session.commit()
    for name in files:
        delete_file(user_id, name)
