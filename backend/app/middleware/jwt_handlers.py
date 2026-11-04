"""JWT callbacks: user lookup, revocation (logout + password change) and JSON error responses."""
from datetime import timezone

from flask_jwt_extended import JWTManager

from app.extensions import db
from app.utils.responses import error


def register_jwt_handlers(jwt: JWTManager) -> None:
    from app.models import TokenBlocklist, User

    @jwt.user_identity_loader
    def user_identity(user):
        return str(user.id) if isinstance(user, User) else str(user)

    @jwt.user_lookup_loader
    def lookup_user(_header, payload):
        user = db.session.get(User, int(payload["sub"]))
        if user is None or not user.is_active:
            return None
        return user

    @jwt.additional_claims_loader
    def add_claims(identity):
        user = identity if isinstance(identity, User) else db.session.get(User, int(identity))
        return {"role": user.role if user else "student"}

    @jwt.token_in_blocklist_loader
    def is_revoked(_header, payload):
        if db.session.query(TokenBlocklist.id).filter_by(jti=payload["jti"]).first() is not None:
            return True
        user = db.session.get(User, int(payload["sub"]))
        if user is not None and user.password_changed_at is not None:
            changed = int(user.password_changed_at.replace(tzinfo=timezone.utc).timestamp())
            if int(payload.get("iat", 0)) < changed:
                return True
        return False

    @jwt.user_lookup_error_loader
    def user_not_found(_header, _payload):
        return error("Account not found or disabled", status=401, code="account_unavailable")

    @jwt.expired_token_loader
    def expired(_header, _payload):
        return error("Session expired. Please sign in again.", status=401, code="token_expired")

    @jwt.invalid_token_loader
    def invalid(reason):
        return error(f"Invalid token: {reason}", status=401, code="token_invalid")

    @jwt.unauthorized_loader
    def missing(reason):
        return error("Authentication required", status=401, code="auth_required", details=reason)

    @jwt.revoked_token_loader
    def revoked(_header, _payload):
        return error("Session has been signed out", status=401, code="token_revoked")
