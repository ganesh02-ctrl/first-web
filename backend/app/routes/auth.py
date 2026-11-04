from flask import Blueprint
from flask_jwt_extended import create_access_token, current_user, decode_token, jwt_required

from app.extensions import limiter
from app.middleware.auth import login_required
from app.routes.helpers import json_body
from app.schemas import load
from app.schemas.auth import (ChangePasswordSchema, EmailOnlySchema, LoginSchema, RegisterSchema,
                              ResetPasswordSchema, TokenSchema)
from app.services import auth as svc
from app.utils.responses import success

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.post("/register")
@limiter.limit("10 per hour")
def register():
    user = svc.register_user(load(RegisterSchema(), json_body()))
    return success(svc.issue_tokens(user), "Account created. Check your email for a verification link.", 201)


@bp.post("/login")
@limiter.limit("10 per minute")
def login():
    data = load(LoginSchema(), json_body())
    return success(svc.issue_tokens(svc.authenticate(data["email"], data["password"])), "Signed in")


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    return success({"access_token": create_access_token(identity=current_user), "user": current_user.to_dict()})


@bp.post("/logout")
@jwt_required()
def logout():
    svc.revoke_current_token(current_user.id)
    refresh_token = (json_body() or {}).get("refresh_token")
    if refresh_token:
        try:
            payload = decode_token(refresh_token)
            if payload.get("sub") == str(current_user.id):
                svc.revoke_token_by_payload(payload, current_user.id)
        except Exception:  # noqa: BLE001 - an invalid refresh token is already unusable
            pass
    return success(None, "Signed out")


@bp.get("/me")
@login_required
def me():
    return success({"user": current_user.to_dict(),
                    "profile": current_user.profile.to_dict() if current_user.profile else None})


@bp.post("/verify-email")
@limiter.limit("20 per hour")
def verify_email():
    user = svc.verify_email(load(TokenSchema(), json_body())["token"])
    return success({"email": user.email}, "Email verified")


@bp.post("/resend-verification")
@login_required
@limiter.limit("3 per hour")
def resend_verification():
    if current_user.email_verified:
        return success(None, "Email is already verified")
    sent = svc.send_verification_email(current_user)
    message = "Verification email sent" if sent else \
        "Email delivery is not configured on this server; ask an administrator."
    return success({"sent": sent}, message)


@bp.post("/forgot-password")
@limiter.limit("5 per hour")
def forgot_password():
    svc.request_password_reset(load(EmailOnlySchema(), json_body())["email"])
    return success(None, "If an account exists for that email, a reset link has been sent.")


@bp.post("/reset-password")
@limiter.limit("10 per hour")
def reset_password():
    data = load(ResetPasswordSchema(), json_body())
    svc.reset_password(data["token"], data["password"])
    return success(None, "Password updated. Please sign in.")


@bp.post("/change-password")
@login_required
@limiter.limit("10 per hour")
def change_password():
    data = load(ChangePasswordSchema(), json_body())
    svc.change_password(current_user, data["current_password"], data["new_password"])
    return success(svc.issue_tokens(current_user), "Password changed. Other sessions were signed out.")
