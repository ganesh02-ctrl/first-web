from marshmallow import fields, validate

from app.schemas.common import BaseSchema
from app.utils.constants import REPORT_STATUSES, ROLES


class AdminUserUpdateSchema(BaseSchema):
    is_active = fields.Boolean()
    role = fields.String(validate=validate.OneOf(ROLES))


class ReportUpdateSchema(BaseSchema):
    status = fields.String(required=True, validate=validate.OneOf(REPORT_STATUSES))
    admin_notes = fields.String(allow_none=True, validate=validate.Length(max=5000))

