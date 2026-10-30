"""
Database engine, sessionmaker, and Base model for QueueLess backend.
Supports PostgreSQL via DATABASE_URL or SQLite in-memory fallback for unit testing.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# If DATABASE_URL is not set (e.g. during local tests before postgres is up),
# use a local SQLite DB so imports and models work seamlessly.
db_url = settings.DATABASE_URL
if not db_url:
    db_url = "sqlite:///./data/queueless_dev.db"

connect_args = {}
if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    db_url,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

