from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.exceptions import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
)
from app.models import Task, User
from app.services.base_service import BaseService


class TaskService(BaseService[Task]):
    def __init__(self, db: Session):
        super().__init__(db, Task)

    def validate_before_create(self, **kwargs: Any) -> Dict[str, Any]:
        if "title" not in kwargs or not kwargs["title"]:
            raise ValidationError("Title is required")

        if "user_id" not in kwargs:
            raise ValidationError("User ID is required")

        user = self.db.get(User, kwargs["user_id"])
        if not user:
            raise ValidationError(f"User with id={kwargs['user_id']} does not exist")

        existing_tasks = self.get_by_filter(
            self, title=kwargs["title"], user_id=kwargs["user_id"]
        )

        if existing_tasks:
            raise AlreadyExistsError(
                f"Task with title '{kwargs['title']}' already exists for this user"
            )

        return kwargs

    def validate_before_update(self, instance: Task, **kwargs: Any) -> Dict[str, Any]:
        if "user_id" in kwargs and kwargs["user_id"] != instance.user_id:
            raise ValidationError("Cannot change task owner")

        if "title" in kwargs and kwargs["title"] != instance.title:
            existing_tasks = self.get_by_filter(
                self, title=kwargs["title"], user_id=instance.user_id
            )
            existing_tasks = [t for t in existing_tasks if t.id != instance.id]
            if existing_tasks:
                raise AlreadyExistsError(
                    f"Task with title '{kwargs['title']}' already exists for this user"
                )

        if "is_completed" in kwargs:
            if not isinstance(kwargs["is_completed"], bool):
                raise ValidationError("is_completed must be boolean")

        return kwargs

    def create_task(
        self, user_id: int, title: str, description: Optional[str] = None
    ) -> Task:
        task = self.create_item(
            self, title=title, description=description, user_id=user_id
        )
        self._update_user_activity(user_id)
        return task

    def get_task_by_user_and_id(self, user_id: int, task_id: int) -> Task:
        task = self.get_by_id_or_raise(task_id)

        if task.user_id != user_id:
            raise NotFoundError(f"Task with id {task_id} not found for user {user_id}")

        return task

    def get_tasks_by_status(self, user_id: int, is_completed: bool) -> List[Task]:
        return self.get_by_filter(self, user_id=user_id, is_completed=is_completed)

    def update_task_by_user_and_id(
        self, user_id: int, task_id: int, **kwargs: Any
    ) -> Task:
        self.get_task_by_user_and_id(user_id, task_id)
        updated_task = self.update_by_id(task_id, **kwargs)
        self._update_user_activity(user_id)
        self._update_task_status(task_id)
        return updated_task

    def delete_task_by_user_and_id(self, user_id: int, task_id: int) -> bool:
        self.get_task_by_user_and_id(user_id, task_id)
        result = self.delete_by_id(task_id)
        if result:
            self._update_user_activity(user_id)
        return result

    def _update_user_activity(self, user_id: int) -> None:
        task_count = self.count_by_filters(self, user_id=user_id)
        user = self.db.get(User, user_id)
        if user:
            user.is_active = task_count > 0
            self.db.commit()

    def _update_task_status(self, task_id: int) -> None:
        task = self.db.get(Task, task_id)
        if task:
            task.is_completed = True
            self.db.commit()


@contextmanager
def get_task_service() -> Generator[TaskService, None, None]:
    with SessionLocal() as db:
        yield TaskService(db)
