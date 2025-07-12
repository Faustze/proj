from sqlalchemy import Connection, event, func, select, update
from sqlalchemy.orm import Mapper

from app.models import Task, User


@event.listens_for(Task, "after_insert")
@event.listens_for(Task, "after_delete")
def update_user_is_active(
    mapper: Mapper,
    connection: Connection,
    target: Task,
) -> None:
    user_id = target.user_id

    task_count = connection.execute(
        select(func.count()).select_from(Task).where(Task.user_id == user_id)
    ).scalar_one()

    connection.execute(
        update(User).where(User.id == user_id).values(is_active=(task_count > 0))
    )
