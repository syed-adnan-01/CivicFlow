"""
SQLAlchemy model for knowledge_chunks table.
Stores chunk-level metadata alongside the vector store (ChromaDB).
PostgreSQL is the authoritative record; ChromaDB is the retrieval index.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index = Column(Integer, nullable=False, comment="0-based position within the document.")
    # Chunk text is stored for citation traceability; never contains personal data.
    chunk_text = Column(Text, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_heading = Column(String(500), nullable=True)
    content_hash = Column(String(64), nullable=True)

    # Embedding model version stored alongside the chunk — required for index rebuild validation.
    embedding_model = Column(String(200), nullable=True)

    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    document = relationship("KnowledgeDocument", lazy="select")

