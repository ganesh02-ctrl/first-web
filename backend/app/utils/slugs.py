"""URL slug helpers."""
import re
import unicodedata

from app.extensions import db


def slugify(text: str, max_length: int = 250) -> str:
    value = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return (value or "item")[:max_length].strip("-")


def unique_slug(model, text: str, exclude_id: int | None = None) -> str:
    base = slugify(text)
    candidate, n = base, 2
    while True:
        query = db.session.query(model.id).filter(model.slug == candidate)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)
        if query.first() is None:
            return candidate
        candidate = f"{base}-{n}"
        n += 1
