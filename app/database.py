from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.logger import setup_logger
from config import settings

log = setup_logger(__name__)
DATABASE_URL = settings.database_url_psycopg2
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    repr_cols_num: int = 3
    repr_cols: tuple[str, ...] = ()

    def __repr__(self) -> str:
        cols: list[str] = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")
        return f"<{self.__class__.__name__} {', '.join(cols)}>"


def drop_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    log.info("Database dropped successfully!")


def init_db() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    log.info("Database initialized successfully!")


def seed_data() -> None:
    from sqlalchemy.orm import Session

    from app.models import Task, User
    from app.utils import JWTManager, PasswordManager

    session: Session = SessionLocal()

    session.query(Task).delete()
    session.query(User).delete()
    session.commit()

    password = "StrongP@ssw0rd"
    hashed_password = PasswordManager.hash_password(password)

    user1 = User(
        username="alice",
        email="alice@example.com",
        password_hash=hashed_password
    )
    user2 = User(
        username="bob",
        email="bob@example.com",
        password_hash=hashed_password
    )
    session.add_all([user1, user2])
    session.flush()

    tasks = [
        Task(
            title="Buy groceries",
            description="Milk, Bread, Eggs",
            is_completed=False,
            user_id=user1.id,
        ),
        Task(
            title="Read a book",
            description="Finish reading '1984'",
            is_completed=True,
            user_id=user1.id,
        ),
        Task(
            title="Workout",
            description="30 minutes cardio",
            is_completed=False,
            user_id=user2.id,
        ),
    ]
    session.add_all(tasks)
    session.commit()

    tokens_user1 = JWTManager.generate_tokens(user1.id, user1.username)
    tokens_user2 = JWTManager.generate_tokens(user2.id, user2.username)

    log.info("✅ Seeding complete.")
    log.info(f"\n🔑 User: alice\nEmail: {user1.email}\nPassword: {password}")
    log.info(f"Access Token:\n{tokens_user1['access_token']}")
    log.info(f"Refresh Token:\n{tokens_user1['refresh_token']}\n")

    log.info(f"🔑 User: bob\nEmail: {user2.email}\nPassword: {password}")
    log.info(f"Access Token:\n{tokens_user2['access_token']}")
    log.info(f"Refresh Token:\n{tokens_user2['refresh_token']}\n")

    session.close()
