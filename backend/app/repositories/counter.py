from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

try:
    from app.models.counter import Counter
    from app.models.queue_token import QueueToken, TokenStatus
except ImportError:
    from backend.app.models.counter import Counter
    from backend.app.models.queue_token import QueueToken, TokenStatus


class CounterRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, counter_id: uuid.UUID) -> Counter | None:
        stmt = select(Counter).where(Counter.id == counter_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def is_eligible(self, counter: Counter) -> bool:
        # Must be active, staffed, and not currently busy (no token assigned)
        return bool(counter.is_active and counter.is_staffed and counter.current_token_id is None)

    async def assign_token(self, counter: Counter, token: QueueToken) -> None:
        counter.current_token_id = token.id
        if hasattr(token, "assigned_counter_id"):
            token.assigned_counter_id = counter.id
        self.db.add(counter)
        self.db.add(token)

    async def clear_current_token(self, counter: Counter) -> None:
        counter.current_token_id = None
        self.db.add(counter)
