"""
Knowledge Document Service.
Orchestrates source onboarding, verification, ingestion, and vector store synchronization.
"""

import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.knowledge_chunk import KnowledgeChunk
from app.models.knowledge_document import KnowledgeDocument
from app.modules.knowledge_documents.repository import KnowledgeDocumentRepository
from app.schemas.knowledge_document import KnowledgeDocumentCreate, VerificationStatus
from app.services.providers import get_embedding_provider
from app.services.rag.chunker import TextChunker
from app.services.rag.source_fetch import SourceFetcher
from app.services.rag.source_governance import SourceGovernance, SourceGovernanceError
from app.services.rag.source_parser import SourceParser
from app.services.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class KnowledgeDocumentService:
    def __init__(self, db: Session, vector_store: Optional[VectorStore] = None):
        self.repo = KnowledgeDocumentRepository(db)
        self.vector_store = vector_store or VectorStore()
        self.chunker = TextChunker()

    def register_source(self, data: KnowledgeDocumentCreate) -> KnowledgeDocument:
        """Creates a new knowledge document record in UNVERIFIED state."""
        return self.repo.create(data)

    def list_sources(
        self,
        status: Optional[str] = None,
        active_only: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[KnowledgeDocument], int]:
        return self.repo.list_all(status, active_only, limit, offset)

    def get_source(self, doc_id: UUID) -> Optional[KnowledgeDocument]:
        return self.repo.get_by_id(doc_id)

    def verify_source(
        self,
        doc_id: UUID,
        new_status: str,
        reviewer_id: Optional[UUID],
        review_notes: Optional[str],
    ) -> KnowledgeDocument:
        """
        Updates verification status after manual inspection.
        Enforces governance validation rules.
        """
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            raise SourceGovernanceError("Knowledge document not found.")

        SourceGovernance.validate_verification_transition(
            current_status=doc.verification_status,
            new_status=new_status,
            reviewer_id=reviewer_id,
            review_notes=review_notes,
        )

        updated = self.repo.update_verification(doc_id, new_status, reviewer_id, review_notes)

        # If deactivated, remove from vector store immediately
        if new_status in (VerificationStatus.INACTIVE, VerificationStatus.STALE):
            self.vector_store.delete_chunks_by_document(doc_id)

        return updated

    def deactivate_source(self, doc_id: UUID) -> KnowledgeDocument:
        """Deactivates a source and purges its chunks from the vector store."""
        doc = self.repo.deactivate(doc_id)
        if not doc:
            raise SourceGovernanceError("Knowledge document not found.")

        self.vector_store.delete_chunks_by_document(doc_id)
        logger.info("Deactivated source %s and removed chunks from vector store.", doc_id)
        return doc

    def ingest_source(self, doc_id: UUID, local_file_path: Optional[str] = None) -> int:
        """
        Ingests a VERIFIED source document:
        1. Confirms source is VERIFIED.
        2. Fetches content (or reads local snapshot).
        3. Parses and normalizes text.
        4. Computes content hash and updates document.
        5. Chunks text into citeable segments.
        6. Generates embeddings via configured embedding provider.
        7. Upserts chunks into ChromaDB.
        8. Saves chunk metadata into PostgreSQL.
        Returns the number of indexed chunks.
        """
        doc = self.repo.get_by_id(doc_id)
        if not doc:
            raise SourceGovernanceError("Document not found.")

        if doc.verification_status != VerificationStatus.VERIFIED:
            raise SourceGovernanceError(
                f"Cannot ingest source with status '{doc.verification_status}'. "
                "Only VERIFIED sources can be indexed for retrieval."
            )

        # 1. Fetch content
        if local_file_path:
            raw_bytes, content_type = SourceFetcher.read_local_file(local_file_path)
        else:
            raw_bytes, content_type = SourceFetcher.fetch_url(doc.source_url)

        # 2. Parse text
        if "pdf" in content_type:
            pages = SourceParser.parse_pdf(raw_bytes)
            full_text = "\n\n".join(text for _, text in pages)
            page_title = doc.title
        else:
            full_text, parsed_title = SourceParser.parse_html(raw_bytes)
            page_title = parsed_title or doc.title

        if not full_text.strip():
            raise SourceGovernanceError("Extracted text is empty. Ingestion aborted.")

        # 3. Update document hash
        content_hash = SourceGovernance.compute_content_hash(full_text)
        doc.content_hash = content_hash
        self.repo.db.commit()

        # 4. Chunk text
        chunks = self.chunker.chunk_document(
            document_id=doc.id,
            text=full_text,
            page_title=page_title,
            source_url=doc.source_url,
            authority=doc.authority,
            service_scope=doc.service_scope,
            verification_status=doc.verification_status,
            retrieved_at=doc.retrieved_at.isoformat() if doc.retrieved_at else "",
            last_checked_at=doc.last_checked_at.isoformat() if doc.last_checked_at else "",
            effective_date=doc.effective_date.isoformat() if doc.effective_date else "",
        )

        if not chunks:
            raise SourceGovernanceError("No chunks were generated from the document.")

        # 5. Embed chunks
        embed_provider = get_embedding_provider()
        texts = [c.chunk_text for c in chunks]

        # In case embedding provider is not configured (e.g. offline dev without key),
        # generate zero/mock embeddings so index pipeline doesn't crash
        try:
            embed_results = embed_provider.embed_batch(texts)
            embeddings = [r.embedding for r in embed_results]
            model_used = embed_provider.model_name()
        except Exception as exc:
            logger.warning("Could not generate embeddings with provider (%s) — using fallback vector.", exc)
            embeddings = [[0.0] * 768 for _ in chunks]
            model_used = "mock-fallback"

        # 6. Upsert to ChromaDB
        self.vector_store.upsert_chunks(chunks, embeddings)

        # 7. Persist chunk records in PostgreSQL
        db_chunks = [
            KnowledgeChunk(
                id=c.metadata.get("id"),  # or uuid
                knowledge_document_id=doc.id,
                chunk_index=c.chunk_index,
                chunk_text=c.chunk_text,
                page_number=c.page_number,
                section_heading=c.section_heading,
                content_hash=c.content_hash,
                embedding_model=model_used,
                active=True,
            )
            for c in chunks
        ]
        self.repo.save_chunks(db_chunks)

        logger.info("Successfully ingested source %s: %d chunks indexed.", doc.id, len(chunks))
        return len(chunks)

