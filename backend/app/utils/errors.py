"""Typed API exceptions and global error handlers."""
import logging

from flask import Flask
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from app.extensions import db
from app.utils.responses import error

logger = logging.getLogger(__name__)


class APIError(Exception):
    status = 400
    code = "bad_request"

    def __init__(self, message: str, status: int | None = None, code: str | None = None, details=None):
        super().__init__(message)
        self.message = message
        if status is not None:
            self.status = status
        if code is not None:
            self.code = code
        self.details = details


class BadRequest(APIError):
    status, code = 400, "bad_request"


class Unauthorized(APIError):
    status, code = 401, "unauthorized"


class Forbidden(APIError):
    status, code = 403, "forbidden"


class NotFound(APIError):
    status, code = 404, "not_found"


class Conflict(APIError):
    status, code = 409, "conflict"


class ValidationFailed(APIError):
    status, code = 422, "validation_error"


class UnsupportedMedia(APIError):
    status, code = 415, "unsupported_media_type"


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(APIError)
    def handle_api_error(exc: APIError):
        return error(exc.message, status=exc.status, code=exc.code, details=exc.details)

    @app.errorhandler(ValidationError)
    def handle_validation(exc: ValidationError):
        return error("Validation failed", status=422, code="validation_error", details=exc.messages)

    @app.errorhandler(IntegrityError)
    def handle_integrity(exc: IntegrityError):
        db.session.rollback()
        logger.warning("Integrity error: %s", exc.orig)
        return error("The request conflicts with existing data", status=409, code="conflict")

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_exc):
        limit = app.config.get("MAX_UPLOAD_MB", 10)
        return error(f"File too large. Maximum size is {limit} MB.", status=413)

    @app.errorhandler(429)
    def handle_rate_limit(exc):
        return error(f"Too many requests: {getattr(exc, 'description', '')}", status=429)

    @app.errorhandler(HTTPException)
    def handle_http(exc: HTTPException):
        return error(exc.description or exc.name, status=exc.code or 500)

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        db.session.rollback()
        logger.exception("Unhandled error: %s", exc)
        return error("An unexpected error occurred", status=500)
