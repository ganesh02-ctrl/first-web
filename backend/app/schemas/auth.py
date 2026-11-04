from marshmallow import ValidationError, fields, validate, validates

from app.schemas.common import BaseSchema, trimmed, validate_phone
from app.utils.security import password_policy_errors


class PasswordField(fields.String):
    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        problems = password_policy_errors(value)
        if problems:
            raise ValidationError(problems)
        return value


class RegisterSchema(BaseSchema):
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = PasswordField(required=True)
    full_name = fields.String(required=True, validate=validate.Length(min=2, max=150))
    phone = trimmed(20)

    @validates("phone")
    def _phone(self, value, **_):
        validate_phone(value)


class LoginSchema(BaseSchema):
    email = fields.Email(required=True)
    password = fields.String(required=True, validate=validate.Length(min=1, max=200))


class EmailOnlySchema(BaseSchema):
    email = fields.Email(required=True)


class TokenSchema(BaseSchema):
    token = fields.String(required=True, validate=validate.Length(min=10, max=200))


class ResetPasswordSchema(TokenSchema):
    password = PasswordField(required=True)


class ChangePasswordSchema(BaseSchema):
    current_password = fields.String(required=True)
    new_password = PasswordField(required=True)
