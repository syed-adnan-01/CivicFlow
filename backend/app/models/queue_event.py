from sqlalchemy import Column, String, Enum, DateTime, Integer, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid
from datetime import datetime
from backend.app.core.database import Base

class EventType(str, enum.Enum):
    TOKEN_CREATED = "TOKEN_CREATED"
    WALK_IN_CREATED = "WALK_IN_CREATED"
    # Add other event types as needed

class QueueEvent(Base):
    __tablename__ = "queue_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    queue_token_id = Column(UUID(as_uuid=True), ForeignKey("queue_tokens.id"), nullable=False)
    office_id = Column(UUID(as_uuid=True), nullable=False)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    reason = Column(String, nullable=True)
    metadata = Column(String, nullable=True)  # JSON string if needed
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (
        Index('idx_queue_event_token', 'queue_token_id'),
    )
