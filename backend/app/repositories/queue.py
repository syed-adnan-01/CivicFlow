from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

try:
    from app.models.queue_token import QueueToken, TokenStatus
    from app.models.queue_event import QueueEvent, EventType
except ImportError:
    from backend.app.models.queue_token import QueueToken, TokenStatus
    from backend.app.models.queue_event import QueueEvent, EventType


class QueueTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: QueueToken) -> QueueToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_by_office_service_date(self, office_id: uuid.UUID, service_id: uuid.UUID, operating_date: datetime):
        stmt = (
            select(QueueToken)
            .where(
                QueueToken.office_id == office_id,
                QueueToken.service_id == service_id,
                QueueToken.operating_date == operating_date,
                QueueToken.status == "WAITING",
            )
            .order_by(QueueToken.created_at)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, token_id: uuid.UUID) -> QueueToken | None:
        stmt = select(QueueToken).where(QueueToken.id == token_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
