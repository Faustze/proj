from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.exceptions import AlreadyExistsError, ValidationError
from app.models import User
from app.models.base import BaseModel
from app.services.base_service import BaseService
from app.utils import EmailValidator, PasswordManager


class UserService(BaseService[User]):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def validate_before_create(self, **kwargs: Any) -> Dict[str, Any]:
        username = kwargs.get("username")
        email = kwargs.get("email")

        if username is None or email is None:
            raise ValueError("Username and email must be provided")

        self._validate_user_data(username, email)
        self._check_user_exists(username, email)

        return kwargs

    def validate_before_update(
        self, instance: BaseModel, **kwargs: Any
    ) -> Dict[str, Any]:
        if "username" in kwargs:
            username = kwargs["username"]
            existing = self.get_by_filter(username=username)
            if existing and existing[0].id != instance.id:
                raise AlreadyExistsError(f"Username '{username}' already exists")

        if "email" in kwargs:
            email = kwargs["email"]
            existing = self.get_by_filter(email=email)
            if existing and existing[0].id != instance.id:
                raise AlreadyExistsError(f"Email '{email}' already exists")

        return kwargs

    def create_user(
        self, username: str, email: str, password_hash: Optional[str] = None
    ) -> User:
        return self.create_item(
            username=username.strip(),
            email=email.strip().lower(),
            password_hash=password_hash,
        )

    def update_profile(self, user: User, update_data: dict) -> User:
        update_fields = {}

        username = update_data.get("username")
        if username:
            update_fields["username"] = username.strip()

        email = update_data.get("email")
        if email:
            email = email.strip().lower()
            if not EmailValidator.is_valid(email):
                raise ValidationError("Invalid email format")
            update_fields["email"] = email

        old_password = update_data.get("old_password")
        new_password = update_data.get("new_password")
        if old_password and new_password:
            if not PasswordManager.verify_password(old_password, user.password_hash):
                raise ValidationError("Old password is incorrect")

            is_strong, errors = PasswordManager.is_password_strong(new_password)
            if not is_strong:
                raise ValidationError(f"Weak password: {'; '.join(errors)}")

            update_fields["password_hash"] = PasswordManager.hash_password(new_password)

        if not update_fields:
            raise ValidationError("No valid fields provided for update")

        return self.update_by_id(user.id, **update_fields)

    def get_user_task_status(self, user: User) -> dict:
        from app.models import Task

        total_tasks, completed_tasks = (
            self.db.query(
                func.count(Task.id), func.count(case((Task.is_completed.is_(True), 1)))
            )
            .filter(Task.user_id == user.id)
            .one()
        )

        all_completed = total_tasks > 0 and total_tasks == completed_tasks

        return {
            "user_id": user.id,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "all_tasks_completed": all_completed,
            **({"is_active": user.is_active} if all_completed else {}),
        }

    @staticmethod
    def _validate_user_data(username: str, email: str) -> None:
        if username is None or email is None:
            raise ValidationError("Username and email are required")

        if not EmailValidator.is_valid(email):
            raise ValidationError("Invalid email format")

        if len(username) < 3:
            raise ValidationError("Username must be at least 3 characters")

    def _check_user_exists(self, username: str, email: str) -> None:
        existing = (
            self.db.query(User)
            .filter(or_(User.username == username, User.email == email.lower()))
            .first()
        )

        if existing:
            raise AlreadyExistsError("User with this username or email already exists")


@contextmanager
def get_user_service() -> Generator[UserService, None, None]:
    with SessionLocal() as db:
        yield UserService(db)
