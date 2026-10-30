from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from app.core.database import AsyncSessionLocal
    from app.repositories.counter import CounterRepository
except ImportError:
    from backend.app.core.database import AsyncSessionLocal
    from backend.app.repositories.counter import CounterRepository


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


async def get_counter_repo(db: AsyncSession) -> CounterRepository:
    return CounterRepository(db)
