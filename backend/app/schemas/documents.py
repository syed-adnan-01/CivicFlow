"""
Pydantic v2 schemas for citizen document upload and OCR processing.

POST /api/v1/documents/upload
GET  /api/v1/documents
POST /api/v1/documents/{document_id}/check
GET  /api/v1/documents/{document_id}/check-result
DELETE /api/v1/documents/{document_id}
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Processing states (file-level)
# ---------------------------------------------------------------------------

class ProcessingStatus:
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    OCR_PENDING = "OCR_PENDING"
    OCR_COMPLETE = "OCR_COMPLETE"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    OCR_FAILED = "OCR_FAILED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    UNAVAILABLE = "UNAVAILABLE"
    DELETED = "DELETED"


# ---------------------------------------------------------------------------
# Checklist item outcomes (separate from file state)
# ---------------------------------------------------------------------------

class ChecklistItemResult:
    PRESENT_CANDIDATE = "PRESENT_CANDIDATE"
    MISSING = "MISSING"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    REPLACEMENT_REQUESTED = "REPLACEMENT_REQUESTED"
    USER_CONFIRMED = "USER_CONFIRMED"


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------

class DocumentUploadResponse(BaseModel):
    document_id: UUID
    processing_status: str
    file_name: str
    message: str = "Upload received. This is a preliminary document check only."


# ---------------------------------------------------------------------------
# Document list item (safe metadata — no raw OCR text)
# ---------------------------------------------------------------------------

class CitizenDocumentRead(BaseModel):
    document_id: UUID
    file_name: str
    service_id: Optional[UUID]
    processing_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CitizenDocumentList(BaseModel):
    items: List[CitizenDocumentRead]
    total: int


# ---------------------------------------------------------------------------
# Check result
# ---------------------------------------------------------------------------

class ChecklistItemRead(BaseModel):
    checklist_item_id: UUID
    label: str
    result: str
    confidence_band: Optional[str] = None  # HIGH | MEDIUM | LOW | UNKNOWN
    message: Optional[str] = None


class DocumentCheckResult(BaseModel):
    document_id: UUID
    processing_status: str
    checklist_version_id: Optional[UUID] = None
    items: List[ChecklistItemRead] = Field(default_factory=list)
    overall_status: str  # NEEDS_REVIEW | READY_FOR_REVIEW | UNAVAILABLE
    disclaimer: str = (
        "Preliminary readiness check only. "
        "Confirm current requirements on the official service portal or with the relevant office."
    )


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------

class DocumentDeleteResponse(BaseModel):
    document_id: UUID
    status: str  # DELETED | SCHEDULED_FOR_DELETION
    message: str

