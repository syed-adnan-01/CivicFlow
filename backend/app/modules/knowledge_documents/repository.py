"""
Database repository for knowledge documents and chunks.
Manages persistence in PostgreSQL.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.schemas.knowledge_document import KnowledgeDocumentCreate, VerificationStatus


class KnowledgeDocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: KnowledgeDocumentCreate) -> KnowledgeDocument:
        now = datetime.now(timezone.utc)
        doc = KnowledgeDocument(
            title=data.title,
            authority=data.authority,
            source_url=str(data.source_url),
            service_scope=data.service_scope,
            effective_date=data.effective_date,
            review_notes=data.review_notes,
            retrieved_at=now,
            verification_status=VerificationStatus.UNVERIFIED,
            active=False,
            version=1,
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)
        return doc

    def get_by_id(self, doc_id: UUID) -> Optional[KnowledgeDocument]:
        return self.db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id).first()

    def get_by_url(self, url: str) -> Optional[KnowledgeDocument]:
        return self.db.query(KnowledgeDocument).filter(KnowledgeDocument.source_url == url).first()

    def list_all(
        self,
        verification_status: Optional[str] = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[KnowledgeDocument], int]:
        query = self.db.query(KnowledgeDocument)
        if verification_status:
            query = query.filter(KnowledgeDocument.verification_status == verification_status)
        if active_only:
            query = query.filter(KnowledgeDocument.active.is_(True))

        total = query.count()
        items = query.order_by(KnowledgeDocument.created_at.desc()).offset(offset).limit(limit).all()
        return items, total

    def get_all_verified_active(self) -> List[KnowledgeDocument]:
        return (
            self.db.query(KnowledgeDocument)
            .filter(
                and_(
                    KnowledgeDocument.verification_status == VerificationStatus.VERIFIED,
                    KnowledgeDocument.active.is_(True),
                )
            )
            .all()
        )

    def update_verification(
        self,
        doc_id: UUID,
        status: str,
        reviewer_id: Optional[UUID],
        review_notes: Optional[str],
    ) -> Optional[KnowledgeDocument]:
        doc = self.get_by_id(doc_id)
        if not doc:
            return None

        now = datetime.now(timezone.utc)
        doc.verification_status = status
        doc.reviewed_by = reviewer_id
        if review_notes:
            doc.review_notes = review_notes
        doc.last_checked_at = now
        # Active only if status is explicitly VERIFIED
        doc.active = (status == VerificationStatus.VERIFIED)
        doc.updated_at = now

        self.db.commit()
        self.db.refresh(doc)
        return doc

    def deactivate(self, doc_id: UUID) -> Optional[KnowledgeDocument]:
        doc = self.get_by_id(doc_id)
        if not doc:
            return None

        now = datetime.now(timezone.utc)
        doc.verification_status = VerificationStatus.INACTIVE
        doc.active = False
        doc.updated_at = now

        # Also mark associated chunks inactive
        self.db.query(KnowledgeChunk).filter(KnowledgeChunk.knowledge_document_id == doc_id).update(
            {"active": False}
        )

        self.db.commit()
        self.db.refresh(doc)
        return doc

    def save_chunks(self, chunks: List[KnowledgeChunk]) -> None:
        self.db.bulk_save_objects(chunks)
        self.db.commit()

    def get_chunks_for_document(self, doc_id: UUID) -> List[KnowledgeChunk]:
        return (
            self.db.query(KnowledgeChunk)
            .filter(KnowledgeChunk.knowledge_document_id == doc_id)
            .order_by(KnowledgeChunk.chunk_index)
            .all()
        )

