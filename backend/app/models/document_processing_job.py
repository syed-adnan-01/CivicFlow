"""
SQLAlchemy model for document_processing_jobs table.
Tracks OCR job lifecycle separately from checklist outcomes.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentProcessingJob(Base):
    __tablename__ = "document_processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    citizen_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("citizen_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # OCR engine and version recorded for every job
    engine = Column(String(50), nullable=True, comment="paddle | tesseract")
    engine_version = Column(String(50), nullable=True)
    language_packs = Column(String(200), nullable=True)

    # RECEIVED | VALIDATING | OCR_PENDING | OCR_COMPLETE | FAILED | UNAVAILABLE
    status = Column(String(30), nullable=False, default="RECEIVED")
    attempts = Column(Integer, nullable=False, default=0)
    error_code = Column(String(100), nullable=True)
    error_detail = Column(Text, nullable=True,
                          comment="Non-sensitive error summary only — no raw OCR text.")

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    citizen_document = relationship("CitizenDocument", lazy="select")

