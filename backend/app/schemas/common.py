"""Shared validation helpers."""
import re
from urllib.parse import urlparse

from marshmallow import Schema, ValidationError, EXCLUDE, fields, validate

from app.utils.errors import ValidationFailed

PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


def load(schema: Schema, data, partial: bool = False) -> dict:
    if data is None:
        raise ValidationFailed("Request body must be JSON")
    try:
        return schema.load(data, partial=partial)
    except ValidationError as exc:
        raise ValidationFailed("Validation failed", details=exc.messages)


def validate_http_url(value: str) -> None:
    parsed = urlparse(value or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationError("Must be a valid http(s) URL.")


def validate_phone(value: str) -> None:
    if value and not PHONE_RE.match(value.replace(" ", "").replace("-", "")):
        raise ValidationError("Enter a valid phone number (10–15 digits, optional +).")


class BaseSchema(Schema):
    class Meta:
        unknown = EXCLUDE


def trimmed(max_len: int, required: bool = False, allow_none: bool = True, **kw):
    return fields.String(required=required, allow_none=allow_none and not required,
                         validate=validate.Length(max=max_len), **kw)
