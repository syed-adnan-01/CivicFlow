"""
SQLAlchemy model for document_checks table.
Stores the top-level checklist comparison result for a document.
Must be kept separate from document processing state (CitizenDocument.processing_status).
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentCheck(Base):
    __tablename__ = "document_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    citizen_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("citizen_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # FK to service_checklist_versions — Member 1 owns that table
    checklist_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_checklist_versions.id", ondelete="RESTRICT"),
        nullable=True,
    )

    # NEEDS_REVIEW | READY_FOR_REVIEW | UNAVAILABLE
    overall_status = Column(String(30), nullable=False, default="NEEDS_REVIEW")

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)

    items = relationship("DocumentCheckItem", back_populates="check", lazy="select")
    citizen_document = relationship("CitizenDocument", lazy="select")

