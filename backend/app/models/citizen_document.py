"""
SQLAlchemy model for citizen_documents table.
Stores metadata for files uploaded by citizens for OCR readiness checks.
Raw OCR text is NOT stored here. Storage key is non-guessable.

Coordinate schema with Member 1 — foreign key to users table.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base


class CitizenDocument(Base):
    __tablename__ = "citizen_documents"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # FK to users.id — Member 1 owns the users table
    citizen_id = Column(
        Uuid(as_uuid=True),
        nullable=False,
        index=True,
        comment="FK to users.id — coordinated with Member 1",
    )

    # Optional FK to services.id — Member 1 owns services
    service_id = Column(
        Uuid(as_uuid=True),
        nullable=True,
        comment="FK to services.id — coordinated with Member 1",
    )

    # Non-guessable object-storage key — never a public URL
    storage_key = Column(String(500), nullable=False, unique=True)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(10), nullable=False, comment="pdf | jpeg | png")
    file_size_bytes = Column(Integer, nullable=True)

    # RECEIVED | VALIDATING | OCR_PENDING | OCR_COMPLETE | VALIDATION_FAILED | OCR_FAILED | DELETED
    processing_status = Column(String(30), nullable=False, default="RECEIVED")

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

