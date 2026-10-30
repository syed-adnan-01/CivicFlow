import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

# Base declarative class shared across all SQLAlchemy models
Base = declarative_base()

# Synchronous Engine & Session (authoritative for Member 1 & core app dependencies)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
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


# Asynchronous Engine & Session (supports Member 2 async queue and counter operations)
_raw_db_url = os.getenv("ASYNC_DATABASE_URL", settings.DATABASE_URL)
if _raw_db_url.startswith("postgresql://"):
    ASYNC_DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = _raw_db_url

try:
    async_engine: AsyncEngine = create_async_engine(ASYNC_DATABASE_URL, echo=False, future=True)
    AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
except Exception:
    async_engine = None
    AsyncSessionLocal = None


async def get_async_db():
    """FastAPI dependency for yielding asynchronous database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("AsyncSessionLocal is not initialized.")
    async with AsyncSessionLocal() as session:
        yield session
