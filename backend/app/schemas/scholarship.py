from marshmallow import fields, validate

from app.schemas.common import BaseSchema, trimmed, validate_http_url
from app.utils.constants import (APPLICATION_STATUSES, EDUCATION_LEVELS, ELIGIBILITY_CRITERIA,
                                 PROVIDER_TYPES, REPORT_REASONS, SCHOLARSHIP_TYPES, VERIFICATION_STATUSES)


class EligibilityInSchema(BaseSchema):
    criterion_type = fields.String(required=True, validate=validate.OneOf(ELIGIBILITY_CRITERIA))
    value = trimmed(120)
    numeric_value = fields.Decimal(allow_none=True, places=2)
    description = fields.String(required=True, validate=validate.Length(min=3, max=1000))


class RequiredDocInSchema(BaseSchema):
    document_type = fields.String(load_default="other", validate=validate.Length(max=50))
    name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    is_mandatory = fields.Boolean(load_default=True)
    notes = trimmed(500)


class ScholarshipSchema(BaseSchema):
    title = fields.String(required=True, validate=validate.Length(min=3, max=255))
    provider_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    provider_type = fields.String(required=True, validate=validate.OneOf(PROVIDER_TYPES))
    scholarship_type = fields.String(required=True, validate=validate.OneOf(SCHOLARSHIP_TYPES))
    category_id = fields.Integer(allow_none=True)
    state = trimmed(80)
    academic_year = trimmed(20)
    description = fields.String(allow_none=True)
    benefits = fields.String(allow_none=True)
    amount_text = trimmed(255)
    amount_max = fields.Decimal(allow_none=True, places=2, validate=validate.Range(0))
    application_open_date = fields.Date(allow_none=True)
    application_close_date = fields.Date(allow_none=True)
    official_source_name = fields.String(required=True, validate=validate.Length(min=2, max=255))
    source_url = fields.String(required=True, validate=[validate.Length(max=1000), validate_http_url])
    application_url = fields.String(required=True, validate=[validate.Length(max=1000), validate_http_url])
    verification_notes = fields.String(allow_none=True)
    is_published = fields.Boolean(load_default=False)
    eligibility = fields.List(fields.Nested(EligibilityInSchema), load_default=list)
    required_documents = fields.List(fields.Nested(RequiredDocInSchema), load_default=list)


class VerifySchema(BaseSchema):
    verification_status = fields.String(required=True, validate=validate.OneOf(VERIFICATION_STATUSES))
    verification_notes = fields.String(allow_none=True, validate=validate.Length(max=5000))


class CategorySchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    description = trimmed(500)


class ReportSchema(BaseSchema):
    reason = fields.String(required=True, validate=validate.OneOf(REPORT_REASONS))
    details = fields.String(required=True, validate=validate.Length(min=10, max=3000))


class FilterSchema(BaseSchema):
    q = fields.String(validate=validate.Length(max=200))
    state = fields.String(validate=validate.Length(max=80))
    category_id = fields.Integer()
    education_level = fields.String(validate=validate.OneOf(EDUCATION_LEVELS))
    scholarship_type = fields.String(validate=validate.OneOf(SCHOLARSHIP_TYPES))
    income = fields.Decimal(validate=validate.Range(0))
    deadline_before = fields.Date()
    deadline_after = fields.Date()
    status = fields.String(validate=validate.OneOf(VERIFICATION_STATUSES))
    include_expired = fields.Boolean(load_default=False)
    sort = fields.String(load_default="deadline", validate=validate.OneOf(["deadline", "newest", "title"]))


class TrackSchema(BaseSchema):
    is_bookmarked = fields.Boolean()
    reminders_enabled = fields.Boolean()


class ApplicationSchema(BaseSchema):
    status = fields.String(validate=validate.OneOf(APPLICATION_STATUSES))
    applied_on = fields.Date(allow_none=True)
    application_reference = trimmed(120)
    notes = fields.String(allow_none=True, validate=validate.Length(max=5000))
    status_note = trimmed(500)
