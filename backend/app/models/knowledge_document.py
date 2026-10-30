"""
SQLAlchemy model for knowledge_documents table.
Stores RAG source metadata. Only VERIFIED + active records are used in retrieval.

Coordinate migration order with Member 1 — this table has no FK to Member 1's tables
but audit_events references internal user IDs for reviewed_by.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    authority = Column(String(300), nullable=False)
    source_url = Column(Text, nullable=False)
    service_scope = Column(Text, nullable=False,
                           comment="Exact service/notice this source is scoped to.")

    retrieved_at = Column(DateTime(timezone=True), nullable=False)
    last_checked_at = Column(DateTime(timezone=True), nullable=True)
    effective_date = Column(DateTime(timezone=True), nullable=True)

    content_hash = Column(String(64), nullable=True, comment="SHA-256 of fetched content.")
    version = Column(Integer, nullable=False, default=1)

    # UNVERIFIED | VERIFIED | STALE | INACTIVE
    verification_status = Column(String(20), nullable=False, default="UNVERIFIED")

    # FK to internal user UUID — nullable; coordinate with Member 1 users table
    reviewed_by = Column(UUID(as_uuid=True), nullable=True)
    review_notes = Column(Text, nullable=True)

    active = Column(Boolean, nullable=False, default=False,
                    comment="True only when VERIFIED and ready for retrieval.")

    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False,
                        default=datetime.utcnow, onupdate=datetime.utcnow)

