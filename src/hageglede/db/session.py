"""Database session management for Helix applications."""
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .schema import Base

SessionLocal = sessionmaker()


def init_sqlite(db_path: str = "data/hageglede.db") -> None:
    """Initialize SQLite database with all tables."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session(db_path: str = "data/hageglede.db") -> Generator[Session, None, None]:
    """Get a database session with proper cleanup.

    Usage:
        with get_session() as session:
            # use session
    """
    engine = create_engine(f"sqlite:///{db_path}")
    local_session = sessionmaker(bind=engine)
    session = local_session()
    try:
        yield session
    finally:
        session.close()