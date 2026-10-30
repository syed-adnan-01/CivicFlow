import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.core.time import utc_now


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointment_slots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="BOOKED",
        nullable=False,
        index=True,
    )
    booking_reference: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        index=True,
    )
    slot_start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    check_in_open_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    check_in_close_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    rescheduled_from_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
    )
    rescheduled_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("appointments.id", ondelete="SET NULL"),
        nullable=True,
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancellation_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    no_show_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    no_show_reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    reminder_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        nullable=False,
    )
    qr_rotated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
        # Partial unique index for duplicate active booking prevention
        Index(
            "uq_active_citizen_slot_booking",
            "citizen_id",
            "office_id",
            "service_id",
            "slot_id",
            unique=True,
            postgresql_where=(status == "BOOKED"),
        ),
        Index("ix_appointments_citizen_history", "citizen_id", "created_at"),
    )

    # Relationships
    citizen = relationship("User", back_populates="appointments")
    office = relationship("Office", back_populates="appointments")
    service = relationship("Service", back_populates="appointments")
    slot = relationship("AppointmentSlot", back_populates="appointments")
    checkin_references = relationship("CheckinReference", back_populates="appointment", cascade="all, delete-orphan")
