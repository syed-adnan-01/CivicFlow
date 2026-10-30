from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.models.queue_token import QueueToken, TokenStatus
from backend.app.models.queue_event import QueueEvent, EventType
from datetime import datetime, timezone
import uuid

class QueueTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: QueueToken) -> QueueToken:
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_by_office_service_date(self, office_id: uuid.UUID, service_id: uuid.UUID, operating_date: datetime):
        stmt = select(QueueToken).where(
            QueueToken.office_id == office_id,
            QueueToken.service_id == service_id,
            QueueToken.operating_date == operating_date,
            QueueToken.status == "WAITING"
        ).order_by(QueueToken.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()

class QueueEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event: QueueEvent) -> QueueEvent:
        self.db.add(event)
        await self.db.flush()
        return event
