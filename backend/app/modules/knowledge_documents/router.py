"""
Knowledge documents admin router.
Admin-only: manage RAG sources — create, verify, list, deactivate, ingest.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.common.dependencies import AuthenticatedUser, get_current_user, get_db
from app.common.permissions import require_role
from app.modules.knowledge_documents.service import KnowledgeDocumentService
from app.schemas.knowledge_document import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentList,
    KnowledgeDocumentRead,
    KnowledgeDocumentVerify,
)
from app.services.rag.source_governance import SourceGovernanceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/knowledge-documents", tags=["admin", "knowledge-documents"])


@router.get("", response_model=KnowledgeDocumentList)
def list_sources(
    verification_status: Optional[str] = Query(None, description="Filter by UNVERIFIED, VERIFIED, STALE, INACTIVE"),
    active_only: bool = Query(False, description="Filter by active status only"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthenticatedUser = Depends(require_role("OFFICE_ADMIN")),
    db: Session = Depends(get_db),
):
    """List all knowledge sources and their verification status."""
    service = KnowledgeDocumentService(db)
    items, total = service.list_sources(verification_status, active_only, limit, offset)
    return KnowledgeDocumentList(items=items, total=total)


@router.post("", response_model=KnowledgeDocumentRead, status_code=status.HTTP_201_CREATED)
def create_source(
    body: KnowledgeDocumentCreate,
    current_user: AuthenticatedUser = Depends(require_role("OFFICE_ADMIN")),
    db: Session = Depends(get_db),
):
    """Register a new knowledge source (starts as UNVERIFIED)."""
    service = KnowledgeDocumentService(db)
    doc = service.register_source(body)
    return doc


@router.get("/{doc_id}", response_model=KnowledgeDocumentRead)
def get_source(
    doc_id: UUID,
    current_user: AuthenticatedUser = Depends(require_role("OFFICE_ADMIN")),
    db: Session = Depends(get_db),
):
    """Get metadata for a specific knowledge document."""
    service = KnowledgeDocumentService(db)
    doc = service.get_source(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SOURCE_NOT_FOUND", "message": "Knowledge document not found."},
        )
    return doc


@router.patch("/{doc_id}/verify", response_model=KnowledgeDocumentRead)
def verify_source(
    doc_id: UUID,
    body: KnowledgeDocumentVerify,
    current_user: AuthenticatedUser = Depends(require_role("OFFICE_ADMIN")),
    db: Session = Depends(get_db),
):
    """Update verification status after manual inspection."""
    service = KnowledgeDocumentService(db)
    try:
        updated = service.verify_source(
            doc_id=doc_id,
            new_status=body.verification_status,
            reviewer_id=current_user.id,
            review_notes=body.review_notes,
        )
        return updated
    except SourceGovernanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "GOVERNANCE_VIOLATION", "message": str(exc)},
        )


@router.post("/{doc_id}/ingest", status_code=status.HTTP_202_ACCEPTED)
def ingest_source(
    doc_id: UUID,
    local_snapshot_path: Optional[str] = Query(None, description="Optional local file path for offline testing"),
    current_user: AuthenticatedUser = Depends(require_role("OFFICE_ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Trigger ingestion for a VERIFIED source — fetch, chunk, embed, upsert into ChromaDB.
    Source must be VERIFIED before this endpoint will proceed.
    """
    service = KnowledgeDocumentService(db)
    try:
        chunk_count = service.ingest_source(doc_id, local_file_path=local_snapshot_path)
        return {
            "status": "INGESTED",
            "document_id": str(doc_id),
            "chunks_indexed": chunk_count,
        }
    except SourceGovernanceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INGESTION_ERROR", "message": str(exc)},
        )
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INGESTION_FAILED", "message": "Failed to ingest source document."},
        )


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_source(
    doc_id: UUID,
    current_user: AuthenticatedUser = Depends(require_role("OFFICE_ADMIN")),
    db: Session = Depends(get_db),
):
    """
    Deactivate a source — marks INACTIVE and purges chunks from ChromaDB immediately.
    Historical metadata is preserved in PostgreSQL.
    """
    service = KnowledgeDocumentService(db)
    try:
        service.deactivate_source(doc_id)
    except SourceGovernanceError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SOURCE_NOT_FOUND", "message": "Knowledge document not found."},
        )
