"""
Documents module router.
POST   /api/v1/documents/upload              — citizen uploads a document.
GET    /api/v1/documents                     — list own documents.
POST   /api/v1/documents/{document_id}/check — trigger/retry OCR check.
GET    /api/v1/documents/{document_id}/check-result — get readiness report.
DELETE /api/v1/documents/{document_id}       — delete document and derived data.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.common.dependencies import get_current_user
from app.schemas.documents import (
    CitizenDocumentList,
    DocumentCheckResult,
    DocumentDeleteResponse,
    DocumentUploadResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile = File(...),
    service_id: UUID = Form(...),
    checklist_version_id: UUID = Form(None),
    current_user=Depends(get_current_user),
):
    """
    Accepts PDF/JPEG/PNG. Validates, stores privately, and creates a processing job.
    Never stores the raw file under a public URL.
    OCR runs asynchronously; poll check-result for the outcome.
    """
    # TODO (Day 12): inject DocumentService and call service.upload(file, service_id, current_user)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "NOT_IMPLEMENTED", "message": "Document upload not yet implemented."},
    )


@router.get("", response_model=CitizenDocumentList)
async def list_documents(current_user=Depends(get_current_user)):
    """Returns only the authenticated citizen's own documents."""
    # TODO (Day 12): inject DocumentService
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "NOT_IMPLEMENTED", "message": "Document list not yet implemented."},
    )


@router.post("/{document_id}/check", status_code=status.HTTP_202_ACCEPTED)
async def trigger_check(document_id: UUID, current_user=Depends(get_current_user)):
    """Trigger or retry an OCR check. Idempotent — returns existing active job if present."""
    # TODO (Day 13): inject DocumentService
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "NOT_IMPLEMENTED", "message": "Document check not yet implemented."},
    )


@router.get("/{document_id}/check-result", response_model=DocumentCheckResult)
async def get_check_result(document_id: UUID, current_user=Depends(get_current_user)):
    """Returns the preliminary readiness report for a document owned by the citizen."""
    # TODO (Day 14): inject DocumentService
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "NOT_IMPLEMENTED", "message": "Check result not yet implemented."},
    )


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: UUID, current_user=Depends(get_current_user)):
    """
    Deletes the file and derived OCR data per the retention policy.
    Citizens can only delete their own documents.
    """
    # TODO (Day 14): inject DocumentService
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail={"code": "NOT_IMPLEMENTED", "message": "Document delete not yet implemented."},
    )

