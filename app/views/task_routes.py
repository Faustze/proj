from typing import Any, Tuple

from flask import Blueprint, g

from app.exceptions import handle_exceptions
from app.schemas import TaskCreateSchema, TaskUpdateSchema
from app.services import get_task_service
from app.utils import (
    RequestValidator,
    ResponseFormatter,
    jwt_required,
    with_current_user,
)

task_bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@task_bp.route("/", methods=["GET"])
@handle_exceptions()
@jwt_required
@with_current_user
def get_user_tasks() -> Tuple[Any, int]:
    skip, limit = RequestValidator.validate_pagination()
    with get_task_service() as service:
        tasks = service.get_all_with_pagination(
            limit=limit, 
            offset=skip
        )

        response_data = ResponseFormatter.paginated_response(
            items=[task.to_dict() for task in tasks], skip=skip, limit=limit
        )
        return ResponseFormatter.success_response(response_data)


@task_bp.route("/", methods=["POST"])
@handle_exceptions()
@jwt_required
@with_current_user
def create_new_task() -> Tuple[Any, int]:
    data = RequestValidator.validate_json(TaskCreateSchema)

    with get_task_service() as service:
        task = service.create_task(
            user_id=g.current_user.id,
            title=data["title"],
            description=data.get("description", ""),
        )
        service.logger.info(f"Task created successfully: {task.title}")

        return ResponseFormatter.success_response(
            {"task": task.to_dict()}, "Task created successfully", 201
        )


@task_bp.route("/<int:task_id>", methods=["GET"])
@handle_exceptions()
@jwt_required
@with_current_user
def get_task_by_id(task_id: int) -> Tuple[Any, int]:
    with get_task_service() as service:
        task = service.get_task_by_user_and_id(
            user_id=g.current_user.id, task_id=task_id
        )
        service.logger.info(f"Get task successfully: '{task.to_dict()}'")
        return ResponseFormatter.success_response(
            {"task": task.to_dict()}, f"Get Task {task_id} successfully", 200
        )


@task_bp.route("/<int:task_id>", methods=["PUT"])
@handle_exceptions()
@jwt_required
@with_current_user
def update_task_by_id(task_id: int) -> Tuple[Any, int]:
    data = RequestValidator.validate_json(TaskUpdateSchema)

    with get_task_service() as service:
        task = service.update_task_by_user_and_id(
            user_id=g.current_user.id, task_id=task_id, **data
        )
        service.logger.info(f"Task updated successfully: '{task.to_dict()}'")

        return ResponseFormatter.success_response(
            {"task": task.to_dict()}, f"Task {task_id} updated successfully", 200
        )


@task_bp.route("/<int:task_id>", methods=["DELETE"])
@handle_exceptions()
@jwt_required
@with_current_user
def delete_task_by_id(task_id: int) -> Tuple[Any, int]:
    with get_task_service() as service:
        service.delete_task_by_user_and_id(user_id=g.current_user.id, task_id=task_id)
        service.logger.info(f"Task {task_id} deleted successfully")
        return ResponseFormatter.success_response(
            {"task_id": task_id}, f"Task {task_id} deleted successfully", 200
        )
