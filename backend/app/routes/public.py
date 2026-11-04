from flask import Blueprint

from app.services.achievement import public_portfolio
from app.utils.constants import (ACHIEVEMENT_CATEGORIES, APPLICATION_STATUS_LABELS, EDUCATION_LEVELS,
                                 ELIGIBILITY_CRITERIA, INDIAN_STATES_AND_UTS, PROVIDER_TYPES, REPORT_REASONS,
                                 REPORT_STATUSES, SCHOLARSHIP_TYPES, STANDARD_DOCUMENT_TYPES,
                                 VERIFICATION_STATUSES)
from app.utils.responses import success

bp = Blueprint("public", __name__, url_prefix="/api/public")


@bp.get("/portfolio/<slug>")
def portfolio(slug):
    return success(public_portfolio(slug))


@bp.get("/meta")
def meta():
    """Vocabulary lists for frontend dropdowns (no user data)."""
    return success({
        "states": list(INDIAN_STATES_AND_UTS),
        "education_levels": list(EDUCATION_LEVELS),
        "scholarship_types": list(SCHOLARSHIP_TYPES),
        "provider_types": list(PROVIDER_TYPES),
        "eligibility_criteria": list(ELIGIBILITY_CRITERIA),
        "achievement_categories": list(ACHIEVEMENT_CATEGORIES),
        "application_statuses": [{"value": k, "label": v} for k, v in APPLICATION_STATUS_LABELS.items()],
        "document_types": STANDARD_DOCUMENT_TYPES,
        "verification_statuses": list(VERIFICATION_STATUSES),
        "report_reasons": list(REPORT_REASONS),
        "report_statuses": list(REPORT_STATUSES),
        "reminder_days": [30, 15, 7, 3, 1],
    })
