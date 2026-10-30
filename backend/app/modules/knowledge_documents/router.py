"""
Knowledge documents admin router.
Admin-only: manage RAG sources — create, verify, list, deactivate.
GET    /api/v1/admin/knowledge-documents
POST   /api/v1/admin/knowledge-documents
PATCH  /api/v1/admin/knowledge-documents/{doc_id}/verify
DELETE /api/v1/admin/knowledge-documents/{doc_id}
POST   /api/v1/admin/knowledge-documents/{doc_id}/ingest
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.common.dependencies import get_current_user
from app.common.permissions import require_role
from app.schemas.knowledge_document import (
    KnowledgeDocumentCreate,
    KnowledgeDocumentList,
    KnowledgeDocumentRead,
    KnowledgeDocumentVerify,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/knowledge-documents", tags=["admin", "knowledge-documents"])


@router.get("", response_model=KnowledgeDocumentList)
async def list_sources(current_user=Depends(require_role("OFFICE_ADMIN"))):
    """List all knowledge sources and their verification status."""
    # TODO (Day 4): inject KnowledgeDocumentService
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={"code": "NOT_IMPLEMENTED"})


@router.post("", response_model=KnowledgeDocumentRead, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: KnowledgeDocumentCreate,
    current_user=Depends(require_role("OFFICE_ADMIN")),
):
    """Register a new knowledge source (starts as UNVERIFIED)."""
    # TODO (Day 4): inject KnowledgeDocumentService
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={"code": "NOT_IMPLEMENTED"})


@router.patch("/{doc_id}/verify", response_model=KnowledgeDocumentRead)
async def verify_source(
    doc_id: UUID,
    body: KnowledgeDocumentVerify,
    current_user=Depends(require_role("OFFICE_ADMIN")),
):
    """Update verification status after manual inspection."""
    # TODO (Day 4): inject KnowledgeDocumentService
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={"code": "NOT_IMPLEMENTED"})


@router.post("/{doc_id}/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_source(
    doc_id: UUID,
    current_user=Depends(require_role("OFFICE_ADMIN")),
):
    """
    Trigger ingestion for a VERIFIED source — fetch, chunk, embed, upsert into ChromaDB.
    Source must be VERIFIED before this endpoint will proceed.
    """
    # TODO (Day 5–6): inject IngestionService
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={"code": "NOT_IMPLEMENTED"})


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_source(
    doc_id: UUID,
    current_user=Depends(require_role("OFFICE_ADMIN")),
):
    """
    Deactivate a source — marks INACTIVE, removes from ChromaDB retrieval immediately.
    Historical metadata is preserved for auditability.
    """
    # TODO (Day 4): inject KnowledgeDocumentService
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail={"code": "NOT_IMPLEMENTED"})

