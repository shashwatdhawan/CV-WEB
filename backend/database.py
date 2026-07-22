from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy import inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'cloudverse.db'}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from backend import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_sqlite()


def migrate_sqlite() -> None:
    if not DATABASE_URL.startswith("sqlite:///"):
        return

    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    existing = {column["name"] for column in inspector.get_columns("users")}
    additions = {
        "minecraft_account_type": "ALTER TABLE users ADD COLUMN minecraft_account_type VARCHAR(16)",
        "minecraft_premium": "ALTER TABLE users ADD COLUMN minecraft_premium BOOLEAN DEFAULT 0 NOT NULL",
        "is_admin": "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0 NOT NULL",
        "suspended": "ALTER TABLE users ADD COLUMN suspended BOOLEAN DEFAULT 0 NOT NULL",
    }
    with engine.begin() as connection:
        for column, statement in additions.items():
            if column not in existing:
                connection.execute(text(statement))


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
