from contextlib import contextmanager
from typing import Iterator

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite:///"):
    db_path = Path(settings.database_url.replace("sqlite:///", "", 1))
    if db_path.parent:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    """Create database tables."""

    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager providing a database session."""

    with Session(engine) as session:
        yield session
