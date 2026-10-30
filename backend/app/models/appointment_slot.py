import uuid
from datetime import datetime, date
from sqlalchemy import (
    String,
    Integer,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.time import utc_now


class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

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
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    operating_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )
    block_start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    capacity: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    booked_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="OPEN",
        nullable=False,
        index=True,
    )
    capacity_policy_version: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("booked_count >= 0", name="chk_slot_booked_count_non_negative"),
        CheckConstraint("capacity >= 0", name="chk_slot_capacity_non_negative"),
        CheckConstraint("booked_count <= capacity", name="chk_slot_booked_count_le_capacity"),
        CheckConstraint("ends_at > starts_at", name="chk_slot_ends_at_after_starts_at"),
        UniqueConstraint("office_id", "service_id", "starts_at", name="uq_slot_office_service_starts_at"),
        Index("ix_slots_lookup", "office_id", "service_id", "operating_date", "status"),
    )

    # Relationships
    office = relationship("Office", back_populates="appointment_slots")
    service = relationship("Service", back_populates="appointment_slots")
    appointments = relationship("Appointment", back_populates="slot")
