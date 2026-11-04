"""Small request helpers shared by route modules."""
from flask import request


def json_body():
    return request.get_json(silent=True)


def form_data() -> dict:
    """Multipart form fields without empty strings (so optional dates/ints validate)."""
    return {k: v for k, v in request.form.items() if v != ""}


def flag(name: str, default: bool = False) -> bool:
    value = request.args.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def int_arg(name: str):
    value = request.args.get(name)
    try:
        return int(value) if value not in (None, "") else None
    except ValueError:
        return None
