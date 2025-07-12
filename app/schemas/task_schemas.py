from marshmallow import Schema, fields, pre_load, validate

from .base_schema import BaseSchema


class TaskBaseSchema(BaseSchema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(allow_none=True)
    is_completed = fields.Bool(load_default=False)


class TaskCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False, allow_none=True)

    @pre_load
    def strip_strings(self, data, **kwargs):
        for key in ("title", "description"):
            if isinstance(data.get(key), str):
                data[key] = data[key].strip()
        return data


class TaskUpdateSchema(Schema):
    title = fields.Str(required=False, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=False, allow_none=True)
    is_completed = fields.Bool(required=False)
