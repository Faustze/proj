from marshmallow import Schema, fields


class LoginSchema(Schema):
    username = fields.Str(required=True)
    password = fields.Str(required=True)


class RefreshTokenSchema(Schema):
    refresh_token = fields.Str(required=True)
