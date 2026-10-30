"""
Documents module router.
POST   /api/v1/documents/upload              — citizen uploads a document.
GET    /api/v1/documents                     — list own documents.
POST   /api/v1/documents/{document_id}/check — trigger/retry OCR check.
GET    /api/v1/documents/{document_id}/check-result — get readiness report.
DELETE /api/v1/documents/{document_id}       — delete document and derived data.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.common.dependencies import AuthenticatedUser, get_current_user
from app.core.database import get_db
from app.modules.documents.service import DocumentService
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
    service_id: Optional[UUID] = Form(None),
    checklist_version_id: Optional[UUID] = Form(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Accepts PDF/JPEG/PNG. Validates, stores privately, and creates a processing job.
    Never stores the raw file under a public URL.
    """
    try:
        contents = await file.read()
        service = DocumentService(db=db)
        return service.upload_document(
            file_bytes=contents,
            original_filename=file.filename or "upload.pdf",
            service_id=service_id,
            citizen_id=current_user.id,
            checklist_version_id=checklist_version_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to upload document: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "UPLOAD_ERROR", "message": "Failed to process document upload."},
        )


@router.get("", response_model=CitizenDocumentList)
async def list_documents(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns only the authenticated citizen's own documents."""
    service = DocumentService(db=db)
    return service.list_documents(citizen_id=current_user.id)


@router.post("/{document_id}/check", response_model=DocumentCheckResult, status_code=status.HTTP_202_ACCEPTED)
async def trigger_check(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger or retry an OCR check. Idempotent."""
    service = DocumentService(db=db)
    return service.process_document(document_id=document_id, citizen_id=current_user.id)


@router.get("/{document_id}/check-result", response_model=DocumentCheckResult)
async def get_check_result(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns the preliminary readiness report for a document owned by the citizen."""
    service = DocumentService(db=db)
    return service.get_check_result(document_id=document_id, citizen_id=current_user.id)


@router.delete("/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    document_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Deletes the file and derived OCR data per the retention policy.
    Citizens can only delete their own documents.
    """
    service = DocumentService(db=db)
    return service.delete_document(document_id=document_id, citizen_id=current_user.id)
