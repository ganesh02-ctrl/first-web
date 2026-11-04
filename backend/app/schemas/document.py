from marshmallow import fields, validate

from app.schemas.common import BaseSchema, trimmed
from app.utils.constants import STANDARD_DOCUMENT_TYPES


class DocumentMetaSchema(BaseSchema):
    display_name = fields.String(validate=validate.Length(min=1, max=200))
    document_type = fields.String(load_default="other", validate=validate.OneOf(list(STANDARD_DOCUMENT_TYPES)))
    folder_id = fields.Integer(allow_none=True)
    issued_on = fields.Date(allow_none=True)
    expires_on = fields.Date(allow_none=True)


class FolderSchema(BaseSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))


__all__ = ["DocumentMetaSchema", "FolderSchema", "trimmed"]
