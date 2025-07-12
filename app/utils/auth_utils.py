from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Optional

import jwt
from flask import abort, g, request

from app.logger import setup_logger
from config import settings

logger = setup_logger(__name__)


class JWTManager:
    ACCESS_EXP = timedelta(minutes=30)
    REFRESH_EXP = timedelta(days=7)

    @staticmethod
    def generate_tokens(user_id: int, username: str) -> dict:
        now = datetime.now(timezone.utc)

        access_payload = {
            "user_id": user_id,
            "username": username,
            "type": "access",
            "exp": now + JWTManager.ACCESS_EXP,
            "iat": now,
        }

        refresh_payload = {
            "user_id": user_id,
            "username": username,
            "type": "refresh",
            "exp": now + JWTManager.REFRESH_EXP,
            "iat": now,
        }

        access_token = jwt.encode(
            access_payload, settings.SECRET_KEY, algorithm="HS256"
        )
        refresh_token = jwt.encode(
            refresh_payload, settings.SECRET_KEY, algorithm="HS256"
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise

    @staticmethod
    def verify_refresh_token(token: str) -> dict:
        try:
            payload = JWTManager.decode_token(token)
            if payload.get("type") != "refresh":
                raise jwt.InvalidTokenError("Not a refresh token")
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            raise

    @staticmethod
    def extract_token_from_header() -> Optional[str]:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        return auth_header[7:].strip()


def jwt_required(f):
    @wraps(f)
    def jwt_wrapper(*args, **kwargs):
        token = JWTManager.extract_token_from_header()
        if not token:
            abort(401, description="Missing or invalid token")

        try:
            payload = JWTManager.decode_token(token)
            if payload.get("type") != "access":
                abort(401, description="Invalid token type")
            g.current_user = payload
        except jwt.ExpiredSignatureError:
            abort(401, description="Access token expired")
        except jwt.InvalidTokenError:
            abort(401, description="Invalid token")

        return f(*args, **kwargs)

    return jwt_wrapper


def with_current_user(func):
    from functools import wraps

    from flask import abort, g

    @wraps(func)
    def wrapper(*args, **kwargs):
        from app.services import get_user_service

        current = g.get("current_user")
        if not current or "user_id" not in current:
            abort(401, description="Missing or invalid current user")

        user_id = current["user_id"]

        with get_user_service() as service:
            user = service.get_by_id(user_id)

        if not user:
            abort(404, description="User not found")

        g.current_user = user
        logger.debug(f"current_user in g: {g.get('current_user')}")
        return func(*args, **kwargs)

    return wrapper
