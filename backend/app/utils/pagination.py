"""Query pagination driven by ?page=&per_page= query parameters."""
from flask import request

MAX_PER_PAGE = 100


def page_params(default_per_page: int = 20) -> tuple[int, int]:
    try:
        page = max(1, int(request.args.get("page", 1)))
    except (TypeError, ValueError):
        page = 1
    try:
        per_page = int(request.args.get("per_page", default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page
    return page, min(max(1, per_page), MAX_PER_PAGE)


def paginate(query, serializer, default_per_page: int = 20) -> tuple[list, dict]:
    page, per_page = page_params(default_per_page)
    total = query.order_by(None).count()
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    pages = (total + per_page - 1) // per_page if total else 0
    meta = {"page": page, "per_page": per_page, "total": total, "pages": pages}
    return [serializer(item) for item in items], meta
