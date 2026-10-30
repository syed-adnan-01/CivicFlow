from sqlalchemy import Column, String, Enum, DateTime, Integer, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum
import uuid
from datetime import datetime
try:
    from app.core.database import Base
except ImportError:
    from backend.app.core.database import Base

class TokenSource(str, enum.Enum):
    APPOINTMENT = "APPOINTMENT"
    WALK_IN = "WALK_IN"

class TokenStatus(str, enum.Enum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    SERVING = "SERVING"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"

class QueueToken(Base):
    __tablename__ = "queue_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    public_token_number = Column(String, nullable=False)
    office_id = Column(UUID(as_uuid=True), nullable=False)
    service_id = Column(UUID(as_uuid=True), nullable=False)
    operating_date = Column(DateTime, nullable=False)
    source = Column(Enum(TokenSource), nullable=False)
    appointment_id = Column(UUID(as_uuid=True), nullable=True)
    citizen_user_id = Column(UUID(as_uuid=True), nullable=True)
    citizen_display_name = Column(String, nullable=True)
    status = Column(Enum(TokenStatus), nullable=False, default=TokenStatus.WAITING)
    priority_class = Column(String, nullable=False)
    checked_in_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    called_at = Column(DateTime(timezone=True), nullable=True)
    first_called_at = Column(DateTime(timezone=True), nullable=True)
    last_called_at = Column(DateTime(timezone=True), nullable=True)
    call_attempt_count = Column(Integer, nullable=False, default=0)
    service_started_at = Column(DateTime(timezone=True), nullable=True)
    last_resumed_at = Column(DateTime(timezone=True), nullable=True)
    hold_started_at = Column(DateTime(timezone=True), nullable=True)
    total_hold_seconds = Column(Integer, nullable=False, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    assigned_counter_id = Column(UUID(as_uuid=True), nullable=True)
    promoted_for_fairness = Column(Boolean, nullable=False, default=False)
    policy_version = Column(String, nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    version = Column(Integer, nullable=True)

    __table_args__ = (
        UniqueConstraint('appointment_id', name='uq_queue_tokens_appointment_id'),
        Index('idx_queue_token_selection', 'office_id', 'service_id', 'operating_date', 'status', 'checked_in_at'),
        Index('idx_counter_active_token', 'assigned_counter_id', 'status'),
    )
