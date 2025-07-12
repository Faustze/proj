import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, Sequence, Type, TypeVar, Union

from flask import g
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, handle_db_errors
from app.logger import setup_logger
from app.models import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseService(Generic[T], ABC):
    def __init__(
        self,
        db: Session,
        model: Type[T],
        logger: Optional[logging.Logger] = None,
    ):
        self.db = db
        self.model = model
        self.logger = logger or setup_logger(self.__class__.__name__)

    @abstractmethod
    def validate_before_create(self, **kwargs: Any) -> Dict[str, Any]:
        return kwargs

    @abstractmethod
    def validate_before_update(self, instance: T, **kwargs: Any) -> Dict[str, Any]:
        return kwargs

    def _validate_fields(self, **kwargs: Any) -> Dict[str, Any]:
        valid_fields = {}
        model_columns = {col.name for col in self.model.__table__.columns}

        for key, value in kwargs.items():
            if key in model_columns:
                valid_fields[key] = value
            else:
                self.logger.warning(
                    f"Field '{key}' not found in model {self.model.__name__}"
                )

        return valid_fields

    @handle_db_errors("create_item")
    def create_item(self, validate_fields: bool = True, **kwargs: Any) -> T:
        kwargs = self.validate_before_create(**kwargs)
        if validate_fields:
            kwargs = self._validate_fields(**kwargs)

        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        self.logger.info(f"Created {self.model.__name__} with id={instance.id}")
        return instance

    @handle_db_errors("get_by_id")
    def get_by_id(self, _id: Union[int, str]) -> Optional[T]:
        stmt = select(self.model).where(self.model.id == _id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_id_or_raise(self, _id: Union[int, str]) -> T:
        instance = self.get_by_id(_id)
        if not instance:
            raise NotFoundError(f"{self.model.__name__} with id {_id} not found")
        return instance

    @handle_db_errors("get_all_with_pagination")
    def get_all_with_pagination(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[str] = None,
        desc_order: bool = False,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Sequence[T]:
        stmt = select(self.model)

        user_field_candidates = ["user_id", "owner_id", "author_id", "id"]

        if hasattr(g, "current_user"):
            for field_name in user_field_candidates:
                if hasattr(self.model, field_name):
                    model_field = getattr(self.model, field_name)
                    user_value = g.current_user.id

                    if field_name == "id" and self.model.__name__.lower() == "user":
                        stmt = stmt.where(model_field == user_value)
                        break
                    elif field_name != "id":
                        stmt = stmt.where(model_field == user_value)
                        break

        if filters:
            for attr, value in filters.items():
                if hasattr(self.model, attr):
                    stmt = stmt.where(getattr(self.model, attr) == value)

        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            stmt = stmt.order_by(desc(order_column) if desc_order else asc(order_column))

        if offset:
            stmt = stmt.offset(offset)
        if limit:
            stmt = stmt.limit(limit)

        return self.db.execute(stmt).scalars().all()

    @handle_db_errors("get_by_filter")
    def get_by_filter(self, **filters: Any) -> Sequence[T]:
        stmt = select(self.model)

        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(
                    getattr(self.model, key).in_(value)
                    if isinstance(value, list)
                    else getattr(self.model, key) == value
                )

        return self.db.execute(stmt).scalars().all()

    @handle_db_errors("count_by_filters")
    def count_by_filters(self, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self.model)

        for key, value in filters.items():
            if not hasattr(self.model, key):
                raise ValueError(
                    f"Invalid filter key: '{key}' is not a field of {self.model.__name__}"
                )
            stmt = stmt.where(getattr(self.model, key) == value)

        return self.db.execute(stmt).scalar_one()

    @handle_db_errors("update_by_id")
    def update_by_id(
        self, _id: Union[int, str], validate_fields: bool = True, **kwargs: Any
    ) -> T:
        instance = self.get_by_id_or_raise(_id)
        kwargs = self.validate_before_update(instance, **kwargs)
        if validate_fields:
            kwargs = self._validate_fields(**kwargs)

        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        self.db.commit()
        self.db.refresh(instance)
        self.logger.info(f"Updated {self.model.__name__} with id={instance.id}")
        return instance

    @handle_db_errors("delete_by_id")
    def delete_by_id(self, _id: Union[int, str]) -> bool:
        instance = self.get_by_id(_id)
        if not instance:
            self.logger.warning(
                f"{self.model.__name__} with id={_id} not found for deletion"
            )
            return False

        self.db.delete(instance)
        self.db.commit()
        self.logger.info(f"Deleted {self.model.__name__} with id={_id}")
        return True
