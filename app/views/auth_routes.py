from typing import Any, Tuple

from flask import Blueprint, g

from app.exceptions import NotFoundError, ValidationError, handle_exceptions
from app.middleware.rate_limiting import limiter
from app.schemas import LoginSchema, RefreshTokenSchema, UserCreateSchema
from app.services import get_user_service
from app.utils import (
    EmailValidator,
    JWTManager,
    PasswordManager,
    RequestValidator,
    ResponseFormatter,
    jwt_required,
    with_current_user,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
@handle_exceptions()
@limiter.limit("5 per minute")
def register() -> Tuple[Any, int]:
    data = RequestValidator.validate_json(UserCreateSchema)

    if not EmailValidator.is_valid(data["email"]):
        raise ValidationError("Invalid email format")

    is_strong, password_errors = PasswordManager.is_password_strong(
        data["password"])
    if not is_strong:
        raise ValidationError(
            f"Password is too weak: {'; '.join(password_errors)}")

    with get_user_service() as service:
        hashed_password = PasswordManager.hash_password(data["password"])
        user = service.create_user(
            username=data["username"].strip(),
            email=data["email"].strip().lower(),
            password_hash=hashed_password,
        )

    tokens = JWTManager.generate_tokens(user.id, user.username)

    return ResponseFormatter.success_response(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        },
        message="User registered successfully",
        status_code=201,
    )


@auth_bp.route("/login", methods=["POST"])
@handle_exceptions()
@limiter.limit("5 per minute")
def login() -> Tuple[Any, int]:
    data = RequestValidator.validate_json(LoginSchema)

    with get_user_service() as service:
        users = service.get_by_filter(username=data["username"])
        if not users:
            raise NotFoundError("Invalid username or password")

        user = users[0]

        if not PasswordManager.verify_password(data["password"], user.password_hash):
            raise NotFoundError("Invalid username or password")

        tokens = JWTManager.generate_tokens(user.id, user.username)

        return ResponseFormatter.success_response(
            {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            },
            message="Login successful",
        )


@auth_bp.route("/verify", methods=["GET"])
@handle_exceptions()
@jwt_required
@with_current_user
def verify_token() -> Tuple[Any, int]:
    user = g.current_user
    if not user:
        raise ValidationError("Invalid token or user not found")

    return ResponseFormatter.success_response(
        {
            "valid": True,
            "user_id": user.id,
            "username": user.username,
        },
        message="Token is valid",
        status_code=200,
    )


@auth_bp.route("/refresh", methods=["POST"])
@handle_exceptions()
def refresh_token() -> Tuple[Any, int]:
    data = RequestValidator.validate_json(RefreshTokenSchema)
    _refresh_token = data["refresh_token"]

    try:
        payload = JWTManager.verify_refresh_token(_refresh_token)
    except Exception:
        raise ValidationError("Invalid or expired refresh token")

    user_id = payload["user_id"]
    username = payload["username"]

    tokens = JWTManager.generate_tokens(user_id, username)

    return ResponseFormatter.success_response(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
        },
        "Token refreshed successfully",
    )
