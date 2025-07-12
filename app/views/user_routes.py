from typing import Any, Tuple

from flask import Blueprint, Response, g

from app.exceptions import DeleteError, handle_exceptions
from app.schemas import UserReadSchema, UserUpdateSchema
from app.services import get_user_service
from app.utils import (
    RequestValidator,
    ResponseFormatter,
    jwt_required,
    with_current_user,
)

user_bp = Blueprint("user", __name__, url_prefix="/user")


@user_bp.route("/", methods=["GET"])
@handle_exceptions()
@jwt_required
@with_current_user
def get_me() -> Tuple[Any, int]:
    with get_user_service() as service:
        user = service.get_by_id(g.current_user.id)
        user_data = UserReadSchema().dump(user)
        return ResponseFormatter.success_response({"user": user_data})


@user_bp.route("/", methods=["PUT"])
@handle_exceptions()
@jwt_required
@with_current_user
def update_my_user() -> Tuple[Any, int]:
    data = RequestValidator.validate_json(UserUpdateSchema)

    with get_user_service() as service:
        user = service.get_by_id(g.current_user.id)
        updated_user = service.update_profile(user, data)
        service.logger.info(f"User updated successfully: {updated_user.username}")
        return ResponseFormatter.success_response(
            {"user": updated_user.to_dict()}, message="User updated successfully"
        )


@user_bp.route("/", methods=["DELETE"])
@handle_exceptions()
@jwt_required
@with_current_user
def delete_my_user() -> Tuple[Any, int]:
    with get_user_service() as service:
        success = service.delete_by_id(g.current_user.id)
        if success:
            service.logger.info(
                f"User with ID {g.current_user.id} deleted successfully"
            )
            return ResponseFormatter.success_response(
                {}, message="User deleted successfully"
            )
        raise DeleteError("Failed to delete user")


@user_bp.errorhandler(404)
def not_found(error: Exception) -> Tuple[Response, int]:
    return ResponseFormatter.error_response("Endpoint not found", status_code=404)


@user_bp.errorhandler(405)
def method_not_allowed(error: Exception) -> Tuple[Response, int]:
    return ResponseFormatter.error_response("Method not allowed", status_code=405)
