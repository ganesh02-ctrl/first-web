"""Admin action audit log."""
from flask import has_request_context, request

from app.extensions import db
from app.models import AdminLog


def log_action(admin, action: str, entity_type: str, entity_id: int | None = None,
               details: dict | None = None) -> AdminLog:
    entry = AdminLog(
        admin_id=getattr(admin, "id", None), action=action, entity_type=entity_type,
        entity_id=entity_id, details=details,
        ip_address=(request.headers.get("X-Forwarded-For", request.remote_addr) or "")[:45]
        if has_request_context() else None,
    )
    db.session.add(entry)
    return entry
