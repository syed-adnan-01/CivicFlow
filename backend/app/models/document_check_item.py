"""
SQLAlchemy model for document_check_items table.
One row per checklist item per document check result.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentCheckItem(Base):
    __tablename__ = "document_check_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    check_id = Column(
        UUID(as_uuid=True),
        ForeignKey("document_checks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FK to checklist items table — Member 1 owns service_documents table
    checklist_item_id = Column(UUID(as_uuid=True), nullable=False)

    # PRESENT_CANDIDATE | MISSING | NEEDS_REVIEW | REPLACEMENT_REQUESTED | USER_CONFIRMED
    result = Column(String(30), nullable=False)

    confidence = Column(Float, nullable=True, comment="0.0–1.0 OCR confidence score.")
    confidence_band = Column(String(10), nullable=True, comment="HIGH | MEDIUM | LOW | UNKNOWN")

    # Non-sensitive review note only — never raw personal data
    review_note = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    check = relationship("DocumentCheck", back_populates="items")

