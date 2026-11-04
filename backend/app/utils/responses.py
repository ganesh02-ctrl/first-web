"""Consistent JSON response envelope: {success, data, message, meta} or {success, error}."""
from typing import Any

from flask import jsonify


def success(data: Any = None, message: str | None = None, status: int = 200, meta: dict | None = None):
    body: dict[str, Any] = {"success": True, "data": data}
    if message:
        body["message"] = message
    if meta is not None:
        body["meta"] = meta
    return jsonify(body), status


def error(message: str, status: int = 400, code: str | None = None, details: Any = None):
    body: dict[str, Any] = {
        "success": False,
        "error": {"message": message, "code": code or _default_code(status)},
    }
    if details is not None:
        body["error"]["details"] = details
    return jsonify(body), status


def _default_code(status: int) -> str:
    return {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        409: "conflict",
        413: "payload_too_large",
        415: "unsupported_media_type",
        422: "validation_error",
        429: "rate_limited",
        500: "server_error",
        503: "service_unavailable",
    }.get(status, "error")
