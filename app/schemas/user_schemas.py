from marshmallow import Schema
from marshmallow import ValidationError as MarshmallowValidationError
from marshmallow import fields, validate, validates_schema

from .base_schema import BaseSchema


class UserBaseSchema(BaseSchema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    is_active = fields.Bool(dump_only=True)


class UserCreateSchema(Schema):
    username = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = fields.Email(required=True)
    password = fields.Str(
        required=True, load_only=True, validate=validate.Length(min=6)
    )


class UserReadSchema(UserBaseSchema):
    pass


class UserUpdateSchema(Schema):
    username = fields.Str(validate=validate.Length(min=3, max=50))
    email = fields.Email()
    old_password = fields.Str(load_only=True)
    new_password = fields.Str(load_only=True, validate=validate.Length(min=6))
    new_password2 = fields.Str(load_only=True)

    @validates_schema
    def validate_password_change(self, data, **kwargs):
        if any(
            field in data for field in ("old_password", "new_password", "new_password2")
        ):
            missing = [
                f
                for f in ("old_password", "new_password", "new_password2")
                if f not in data
            ]
            if missing:
                raise MarshmallowValidationError(
                    f"Missing required fields for password change: {', '.join(missing)}"
                )
            if data["new_password"] != data["new_password2"]:
                raise MarshmallowValidationError("New passwords do not match")
