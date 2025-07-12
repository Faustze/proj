from typing import Any, Optional, Tuple

from flask import jsonify


class ResponseFormatter:
    @staticmethod
    def success_response(
        data: Any, message: str = "", status_code: int = 200
    ) -> Tuple[Any, int]:
        response = {"success": True, "data": data}
        if message:
            response["message"] = message
        return jsonify(response), status_code

    @staticmethod
    def error_response(message: str, status_code: int = 400) -> Tuple[Any, int]:
        return jsonify({"success": False, "error": message}), status_code

    @staticmethod
    def paginated_response(
        items: list, skip: int, limit: int, total_count: Optional[int] = None
    ) -> dict:
        response = {
            "items": items,
            "count": len(items),
            "skip": skip,
            "limit": limit,
        }
        if total_count is not None:
            response["total_count"] = total_count
        return response
