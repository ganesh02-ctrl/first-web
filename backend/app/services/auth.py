"""Registration, login, logout, password reset and email verification."""
from datetime import datetime, timedelta, timezone

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt

from app.extensions import db
from app.models import (EmailVerificationToken, NotificationPreference, PasswordResetToken,
                        StudentProfile, TokenBlocklist, User)
from app.services.email import send_email
from app.utils.errors import BadRequest, Conflict, Forbidden, Unauthorized
from app.utils.security import generate_token, hash_token
from app.utils.timeutils import utcnow

MAX_FAILED_LOGINS = 5
LOCKOUT_MINUTES = 15


def _normalize(email: str) -> str:
    return email.strip().lower()


def register_user(data: dict) -> User:
    email = _normalize(data["email"])
    if User.query.filter_by(email=email).first():
        raise Conflict("An account with this email already exists")
    user = User(email=email, role="student")
    user.set_password(data["password"])
    user.profile = StudentProfile(full_name=data["full_name"].strip(), phone=data.get("phone"))
    user.notification_preference = NotificationPreference()
    db.session.add(user)
    db.session.commit()
    send_verification_email(user)
    return user


def authenticate(email: str, password: str) -> User:
    user = User.query.filter_by(email=_normalize(email)).first()
    now = utcnow()
    if user and user.locked_until and user.locked_until > now:
        raise Forbidden("Too many failed attempts. Try again later.", code="account_locked")
    if not user or not user.check_password(password):
        if user:
            user.failed_login_count += 1
            if user.failed_login_count >= MAX_FAILED_LOGINS:
                user.locked_until = now + timedelta(minutes=LOCKOUT_MINUTES)
                user.failed_login_count = 0
            db.session.commit()
        raise Unauthorized("Invalid email or password", code="invalid_credentials")
    if not user.is_active:
        raise Forbidden("This account has been disabled", code="account_disabled")
    user.failed_login_count, user.locked_until, user.last_login_at = 0, None, now
    db.session.commit()
    return user


def issue_tokens(user: User) -> dict:
    return {"access_token": create_access_token(identity=user),
            "refresh_token": create_refresh_token(identity=user),
            "user": user.to_dict()}


def revoke_current_token(user_id: int | None) -> None:
    claims = get_jwt()
    exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc).replace(tzinfo=None)
    if not TokenBlocklist.query.filter_by(jti=claims["jti"]).first():
        db.session.add(TokenBlocklist(jti=claims["jti"], token_type=claims.get("type", "access"),
                                      user_id=user_id, expires_at=exp))
        db.session.commit()


def revoke_token_by_payload(payload: dict, user_id: int) -> None:
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).replace(tzinfo=None)
    if not TokenBlocklist.query.filter_by(jti=payload["jti"]).first():
        db.session.add(TokenBlocklist(jti=payload["jti"], token_type=payload.get("type", "refresh"),
                                      user_id=user_id, expires_at=exp))
        db.session.commit()


def _link(path: str, token: str) -> str:
    return f"{current_app.config['FRONTEND_URL']}{path}?token={token}"


def send_verification_email(user: User) -> bool:
    raw = generate_token()
    hours = current_app.config["EMAIL_VERIFICATION_TOKEN_HOURS"]
    db.session.add(EmailVerificationToken(user_id=user.id, token_hash=hash_token(raw),
                                          expires_at=utcnow() + timedelta(hours=hours)))
    db.session.commit()
    result = send_email(user.email, "Verify your SSS account",
                        f"Verify your email within {hours} hours:\n{_link('/verify-email', raw)}")
    return result.ok


def verify_email(raw: str) -> User:
    record = EmailVerificationToken.query.filter_by(token_hash=hash_token(raw)).first()
    if not record or not record.is_valid:
        raise BadRequest("This verification link is invalid or has expired", code="invalid_token")
    record.used_at = utcnow()
    record.user.email_verified_at = record.user.email_verified_at or utcnow()
    db.session.commit()
    return record.user


def request_password_reset(email: str) -> None:
    """Always behaves the same whether or not the account exists (no user enumeration)."""
    user = User.query.filter_by(email=_normalize(email)).first()
    if not user or not user.is_active:
        return
    raw = generate_token()
    minutes = current_app.config["PASSWORD_RESET_TOKEN_MINUTES"]
    PasswordResetToken.query.filter_by(user_id=user.id, used_at=None).update({"used_at": utcnow()})
    db.session.add(PasswordResetToken(user_id=user.id, token_hash=hash_token(raw),
                                      expires_at=utcnow() + timedelta(minutes=minutes)))
    db.session.commit()
    send_email(user.email, "Reset your SSS password",
               f"Reset your password within {minutes} minutes:\n{_link('/reset-password', raw)}\n\n"
               "If you did not request this, ignore this email.")


def reset_password(raw: str, new_password: str) -> None:
    record = PasswordResetToken.query.filter_by(token_hash=hash_token(raw)).first()
    if not record or not record.is_valid:
        raise BadRequest("This reset link is invalid or has expired", code="invalid_token")
    record.used_at = utcnow()
    record.user.set_password(new_password)  # also invalidates every existing JWT
    record.user.failed_login_count, record.user.locked_until = 0, None
    db.session.commit()


def change_password(user: User, current: str, new: str) -> None:
    if not user.check_password(current):
        raise BadRequest("Current password is incorrect", code="invalid_password")
    user.set_password(new)
    db.session.commit()


def purge_expired_tokens() -> int:
    now = utcnow()
    count = TokenBlocklist.query.filter(TokenBlocklist.expires_at < now).delete()
    count += PasswordResetToken.query.filter(PasswordResetToken.expires_at < now).delete()
    count += EmailVerificationToken.query.filter(EmailVerificationToken.expires_at < now).delete()
    db.session.commit()
    return count
