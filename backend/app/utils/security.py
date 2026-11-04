"""Password hashing, token generation and password policy."""
import hashlib
import secrets

import bcrypt
from flask import current_app, has_app_context

BCRYPT_MAX_BYTES = 72


def hash_password(raw: str) -> str:
    rounds = current_app.config.get("BCRYPT_ROUNDS", 12) if has_app_context() else 12
    return bcrypt.hashpw(raw.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(raw: str, hashed: str) -> bool:
    if not raw or not hashed:
        return False
    try:
        return bcrypt.checkpw(raw.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False


def password_policy_errors(raw: str) -> list[str]:
    problems = []
    if len(raw) < 8:
        problems.append("Password must be at least 8 characters long.")
    if len(raw.encode("utf-8")) > BCRYPT_MAX_BYTES:
        problems.append("Password must be at most 72 bytes long.")
    if not any(c.islower() for c in raw):
        problems.append("Password must contain a lowercase letter.")
    if not any(c.isupper() for c in raw):
        problems.append("Password must contain an uppercase letter.")
    if not any(c.isdigit() for c in raw):
        problems.append("Password must contain a digit.")
    return problems


def generate_token(nbytes: int = 48) -> str:
    """URL-safe random token sent to the user (only its hash is stored)."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_public_slug() -> str:
    return secrets.token_urlsafe(9).replace("_", "").replace("-", "").lower()[:12]
