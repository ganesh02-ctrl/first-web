from marshmallow import fields, validate

from app.schemas.common import BaseSchema


class PreferenceSchema(BaseSchema):
    in_app_enabled = fields.Boolean()
    email_enabled = fields.Boolean()
    sms_enabled = fields.Boolean()
    deadline_reminders = fields.Boolean()
    application_updates = fields.Boolean()
    reminder_days = fields.List(fields.Integer(validate=validate.OneOf([30, 15, 7, 3, 1])),
                                validate=validate.Length(max=5))
