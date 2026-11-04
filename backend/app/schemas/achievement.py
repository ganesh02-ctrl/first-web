from marshmallow import ValidationError, fields, validate, validates_schema

from app.schemas.common import BaseSchema, trimmed
from app.utils.constants import ACHIEVEMENT_CATEGORIES


class AchievementSchema(BaseSchema):
    title = fields.String(required=True, validate=validate.Length(min=2, max=200))
    description = fields.String(allow_none=True, validate=validate.Length(max=5000))
    organization = trimmed(200)
    category = fields.String(required=True, validate=validate.OneOf(ACHIEVEMENT_CATEGORIES))
    achieved_on = fields.Date(required=True)
    rank_position = trimmed(100)
    location_name = trimmed(255)
    latitude = fields.Decimal(allow_none=True, places=6, validate=validate.Range(-90, 90))
    longitude = fields.Decimal(allow_none=True, places=6, validate=validate.Range(-180, 180))
    certificate_document_id = fields.Integer(allow_none=True)
    is_public = fields.Boolean(load_default=False)

    @validates_schema
    def _coords(self, data, **_):
        if ("latitude" in data) != ("longitude" in data) or \
                ((data.get("latitude") is None) != (data.get("longitude") is None)):
            raise ValidationError({"latitude": ["Provide both latitude and longitude, or neither."]})
