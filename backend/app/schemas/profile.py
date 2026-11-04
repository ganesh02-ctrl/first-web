from marshmallow import fields, validate, validates

from app.schemas.common import BaseSchema, trimmed, validate_phone
from app.utils.constants import EDUCATION_LEVELS, INDIAN_STATES_AND_UTS, SCHOLARSHIP_TYPES


class ProfileUpdateSchema(BaseSchema):
    full_name = fields.String(validate=validate.Length(min=2, max=150))
    phone = trimmed(20)
    date_of_birth = fields.Date(allow_none=True)
    gender = trimmed(30)
    state = fields.String(allow_none=True, validate=validate.OneOf(INDIAN_STATES_AND_UTS))
    district = trimmed(80)
    college = trimmed(200)
    university = trimmed(200)
    degree = trimmed(120)
    branch = trimmed(120)
    education_level = fields.String(allow_none=True, validate=validate.OneOf(EDUCATION_LEVELS))
    current_semester = fields.Integer(allow_none=True, validate=validate.Range(1, 20))
    graduation_year = fields.Integer(allow_none=True, validate=validate.Range(1950, 2100))
    social_category = trimmed(30)
    annual_family_income = fields.Decimal(allow_none=True, places=2, validate=validate.Range(0, 10**10))
    academic_summary = fields.String(allow_none=True, validate=validate.Length(max=5000))
    preferred_scholarship_types = fields.List(fields.String(validate=validate.OneOf(SCHOLARSHIP_TYPES)))
    preferred_states = fields.List(fields.String(validate=validate.OneOf(INDIAN_STATES_AND_UTS)))
    public_portfolio_enabled = fields.Boolean()

    @validates("phone")
    def _phone(self, value, **_):
        validate_phone(value)
