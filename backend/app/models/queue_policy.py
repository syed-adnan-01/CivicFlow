import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.time import utc_now


class QueuePolicy(Base):
    __tablename__ = "queue_policy"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    slot_duration_minutes: Mapped[int] = mapped_column(
        Integer,
        default=15,
        nullable=False,
    )
    walk_in_share: Mapped[float] = mapped_column(
        Float,
        default=0.20,
        nullable=False,
    )
    max_walk_in_wait_minutes: Mapped[int] = mapped_column(
        Integer,
        default=60,
        nullable=False,
    )
    checkin_open_minutes: Mapped[int] = mapped_column(
        Integer,
        default=15,
        nullable=False,
    )
    checkin_close_minutes: Mapped[int] = mapped_column(
        Integer,
        default=10,
        nullable=False,
    )
    policy_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relationships
    office = relationship("Office", back_populates="policies")
    service = relationship("Service", back_populates="policies")
