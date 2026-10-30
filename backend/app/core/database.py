import os
from typing import Generator, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Base declarative class shared across all SQLAlchemy models
Base = declarative_base()

# ---------------------------------------------------------------------------
# Synchronous Engine & Session
# Authoritative for Member 1 core app, Member 4 RAG/OCR modules, and tests.
# If DATABASE_URL references PostgreSQL but the driver is unavailable (e.g.
# during unit tests on a dev machine without psycopg), falls back to SQLite.
# ---------------------------------------------------------------------------
_sync_db_url: str = settings.DATABASE_URL or ""

_connect_args = {}
if _sync_db_url.startswith("sqlite"):
    _connect_args["check_same_thread"] = False
    engine = create_engine(_sync_db_url, connect_args=_connect_args, echo=False)
elif _sync_db_url.startswith("postgresql"):
    try:
        engine = create_engine(
            _sync_db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        # Validate driver is importable
        from sqlalchemy import event  # noqa – just ensure import chain works
    except Exception:
        # PostgreSQL driver not available in this environment – use SQLite dev fallback
        _sqlite_url = "sqlite:///./data/queueless_dev.db"
        engine = create_engine(
            _sqlite_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
else:
    # Unset or custom URL — use SQLite dev fallback
    _sqlite_url = "sqlite:///./data/queueless_dev.db"
    engine = create_engine(
        _sqlite_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session with clean rollback on error."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Asynchronous Engine & Session
# Supports Member 2 async queue and counter operations.
# Imported lazily so tests/dev machines without asyncpg/greenlet don't break.
# ---------------------------------------------------------------------------
_raw_async_url = os.getenv("ASYNC_DATABASE_URL", settings.DATABASE_URL or "")
if _raw_async_url.startswith("postgresql://"):
    ASYNC_DATABASE_URL = _raw_async_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _raw_async_url.startswith("postgresql+psycopg://"):
    ASYNC_DATABASE_URL = _raw_async_url.replace("postgresql+psycopg://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = _raw_async_url

async_engine: Optional[object] = None
AsyncSessionLocal: Optional[object] = None

if ASYNC_DATABASE_URL and ASYNC_DATABASE_URL.startswith("postgresql"):
    try:
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker as _sm
        async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)
        AsyncSessionLocal = _sm(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
    except Exception:
        async_engine = None
        AsyncSessionLocal = None


async def get_async_db():
    """FastAPI dependency for yielding asynchronous database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError(
            "AsyncSessionLocal is not initialized (PostgreSQL + asyncpg required for async operations)."
        )
    async with AsyncSessionLocal() as session:
        yield session
