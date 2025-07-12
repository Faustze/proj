from typing import Any, Dict, Type, cast

from flask import request
from marshmallow import Schema
from marshmallow import ValidationError as MarshmallowValidationError

from app.exceptions import ValidationError


class RequestValidator:
    @staticmethod
    def validate_json(schema_cls: Type[Schema]) -> Dict[str, Any]:
        if not request.is_json:
            raise ValidationError("Request must be JSON")

        json_data = request.get_json()
        if not isinstance(json_data, dict):
            raise ValidationError("Invalid JSON format: expected a JSON object")

        try:
            result = schema_cls().load(json_data)
            return cast(Dict[str, Any], result)
        except MarshmallowValidationError as e:
            raise MarshmallowValidationError(e.messages)

    @staticmethod
    def validate_pagination() -> tuple[int, int]:
        skip = request.args.get("skip", 0, type=int)
        limit = request.args.get("limit", 100, type=int)

        if skip < 0:
            raise ValidationError("Skip parameter must be non-negative")
        if limit <= 0 or limit > 1000:
            raise ValidationError("Limit parameter must be between 1 and 1000")

        return skip, limit
