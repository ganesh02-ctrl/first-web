"""Time helpers. Database stores naive UTC datetimes; deadlines are calendar dates in APP_TIMEZONE."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

from flask import current_app, has_app_context


def utcnow() -> datetime:
    """Naive UTC datetime suitable for MySQL DATETIME columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def app_timezone() -> ZoneInfo:
    name = current_app.config.get("APP_TIMEZONE", "Asia/Kolkata") if has_app_context() else "Asia/Kolkata"
    return ZoneInfo(name)


def today_local() -> date:
    """Today's date in the application timezone (used for deadline comparisons)."""
    return datetime.now(app_timezone()).date()


def days_until(target: date | None) -> int | None:
    if target is None:
        return None
    return (target - today_local()).days


def isoformat(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat() + ("Z" if value.tzinfo is None else "")
    return value.isoformat()
