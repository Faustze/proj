import logging
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type, TypeVar, cast

from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=Callable[..., Tuple[Any, int]])


class ErrorCode(Enum):
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    DATABASE_ERROR = "DATABASE_ERROR"
    INTEGRITY_ERROR = "INTEGRITY_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"

    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"


class BaseServiceException(Exception):
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        details: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.original_exception = original_exception

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "error": self.message,
            "error_code": self.error_code.value,
        }
        if self.details:
            result["details"] = self.details
        return result


class ValidationError(BaseServiceException):
    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.VALIDATION_ERROR, **kwargs)
        if field_errors:
            self.details["field_errors"] = field_errors


class NotFoundError(BaseServiceException):
    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.NOT_FOUND, **kwargs)
        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id:
            self.details["resource_id"] = str(resource_id)


class AlreadyExistsError(BaseServiceException):
    def __init__(
        self,
        message: str = "Resource already exists",
        resource_type: Optional[str] = None,
        conflicting_field: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.ALREADY_EXISTS, **kwargs)
        if resource_type:
            self.details["resource_type"] = resource_type
        if conflicting_field:
            self.details["conflicting_field"] = conflicting_field


class PermissionDeniedError(BaseServiceException):
    def __init__(
        self,
        message: str = "Permission denied",
        required_permission: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.PERMISSION_DENIED, **kwargs)
        if required_permission:
            self.details["required_permission"] = required_permission


class DatabaseError(BaseServiceException):
    def __init__(
        self,
        message: str = "Database error occurred",
        operation: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.DATABASE_ERROR, **kwargs)
        if operation:
            self.details["operation"] = operation


class ServiceError(BaseServiceException):
    def __init__(
        self,
        message: str = "Service operation failed",
        service_name: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.INTERNAL_ERROR, **kwargs)
        if service_name:
            self.details["service_name"] = service_name


class DeleteError(BaseServiceException):
    def __init__(
        self,
        message: str = "Failed to delete resource",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        reason: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.OPERATION_NOT_ALLOWED, **kwargs)
        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id is not None:
            self.details["resource_id"] = str(resource_id)
        if reason:
            self.details["reason"] = reason


class UpdateError(BaseServiceException):
    def __init__(
        self,
        message: str = "Failed to update resource",
        resource_type: Optional[str] = None,
        resource_id: Optional[Any] = None,
        reason: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.OPERATION_NOT_ALLOWED, **kwargs)
        if resource_type:
            self.details["resource_type"] = resource_type
        if resource_id is not None:
            self.details["resource_id"] = str(resource_id)
        if reason:
            self.details["reason"] = reason


class OperationNotAllowedError(BaseServiceException):
    def __init__(
        self,
        message: str = "Operation not allowed",
        operation: Optional[str] = None,
        reason: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.OPERATION_NOT_ALLOWED, **kwargs)
        if operation:
            self.details["operation"] = operation
        if reason:
            self.details["reason"] = reason


class ResourceConflictError(BaseServiceException):
    def __init__(
        self,
        message: str = "Resource conflict",
        conflicting_resource: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, ErrorCode.RESOURCE_CONFLICT, **kwargs)
        if conflicting_resource:
            self.details["conflicting_resource"] = conflicting_resource


class IntegrityError(DatabaseError):
    def __init__(
        self,
        message: str = "Data integrity constraint violation",
        constraint: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(message, **kwargs)
        self.error_code = ErrorCode.INTEGRITY_ERROR
        if constraint:
            self.details["constraint"] = constraint


DEFAULT_EXCEPTION_MAP: Dict[Type[Exception], int] = {
    ValidationError: 400,
    RuntimeError: 500,
    NotFoundError: 404,
    AlreadyExistsError: 409,
    PermissionDeniedError: 403,
    DatabaseError: 500,
    IntegrityError: 409,
    OperationNotAllowedError: 403,
    ResourceConflictError: 409,
    BaseServiceException: 500,
    ServiceError: 500,
    DeleteError: 403,
    UpdateError: 403,
}


def handle_exceptions(include_stack_trace: bool = False) -> Callable:
    def handle_exc_wrapper(func: T) -> T:
        @wraps(func)
        def handle_exc_inner(*args: Any, **kwargs: Any) -> Tuple[Any, int]:
            try:
                return func(*args, **kwargs)
            except BaseServiceException as e:
                status_code = DEFAULT_EXCEPTION_MAP.get(type(e), 500)
                if status_code < 500:
                    logger_fn = logger.warning
                else:
                    logger_fn = logger.error
                logger_fn(
                    f"{type(e).__name__}: {e.message}",
                    extra={
                        "error_code": e.error_code.value,
                        "details": e.details
                    },
                )

                response_data = e.to_dict()
                if include_stack_trace:
                    import traceback

                    if e.original_exception:
                        stack_trace = "".join(
                            traceback.format_exception(
                                type(e.original_exception),
                                e.original_exception,
                                e.original_exception.__traceback__,
                            )
                        )
                    else:
                        stack_trace = "".join(
                            traceback.format_exception(
                                type(e),
                                e, e.__traceback__
                            )
                        )
                    response_data["stack_trace"] = (
                        f"{type(e).__name__}:\n"
                        f"{stack_trace}"
                    )

                print(
                    "Returning response_data from BaseServiceException:",
                    response_data,
                    "status_code:",
                    status_code,
                )
                return jsonify(response_data), status_code

            except Exception as e:
                for exc_type, status_code in DEFAULT_EXCEPTION_MAP.items():
                    if isinstance(e, exc_type):
                        if status_code < 500:
                            logger_fn = logger.warning
                        else:
                            logger_fn = logger.error
                        logger_fn(f"{exc_type.__name__}: {e}")

                        response_data = {
                            "error": str(e),
                            "error_code": "UNKNOWN_ERROR"
                        }
                        if include_stack_trace:
                            import traceback

                            response_data["stack_trace"] = traceback.format_exc()  # noqa: E501

                        return jsonify(response_data), status_code

                logger.exception(f"Unexpected error: {e}")
                response_data = {
                    "error": "Internal server error",
                    "error_code": "INTERNAL_ERROR",
                }
                if include_stack_trace:
                    import traceback

                    response_data["stack_trace"] = traceback.format_exc()

                return jsonify(response_data), 500

        return cast(T, handle_exc_inner)

    return handle_exc_wrapper


def handle_db_errors(operation: str) -> Callable[
    [Callable[..., T]], Callable[..., T]
                                        ]:
    """Декоратор для обработки ошибок БД.
    Args:
        operation: Название операции для логов.
    Returns:
        Декоратор, сохраняющий сигнатуру исходной функции.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> T:
            try:
                return func(self, *args, **kwargs)
            except IntegrityError as e:
                if hasattr(self, "db"):
                    self.db.rollback()
                if hasattr(self, "logger"):
                    self.logger.error(
                        f"Integrity error during {operation}: {str(e)}")
                raise IntegrityError(
                    operation=operation,
                    original_exception=e
                ) from e
            except SQLAlchemyError as e:
                if hasattr(self, "db"):
                    self.db.rollback()
                if hasattr(self, "logger"):
                    self.logger.exception(f"Database error during {operation}")
                raise DatabaseError(
                    operation=operation,
                    original_exception=e
                ) from e

        return wrapper

    return decorator
