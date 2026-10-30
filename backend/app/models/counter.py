import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.core.database import Base

class Counter(Base):
    __tablename__ = "counters"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    office_id = Column(PGUUID(as_uuid=True), ForeignKey("offices.id"), nullable=False)
    service_id = Column(PGUUID(as_uuid=True), ForeignKey("services.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_staffed = Column(Boolean, nullable=False, default=False)
    current_token_id = Column(PGUUID(as_uuid=True), ForeignKey("queue_tokens.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships (optional, for convenience)
    current_token = relationship("QueueToken", back_populates="counter", uselist=False)
