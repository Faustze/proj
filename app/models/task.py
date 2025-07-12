from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models import User


class Task(BaseModel):
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="tasks")

    repr_cols = ("title", "description", "is_completed")

    __table_args__ = (Index("idx_task_title_active", "title", "is_completed"),)

    def to_dict(self, include_sensitive: bool = False) -> dict:
        data = super().to_dict()
        if not include_sensitive:
            data.pop("description", None)
        return data
