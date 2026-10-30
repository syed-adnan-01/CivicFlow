"""
Pydantic v2 schemas for knowledge document (RAG source) management.
Used by the admin-only /api/v1/admin/knowledge-documents endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


# ---------------------------------------------------------------------------
# Verification states
# ---------------------------------------------------------------------------

class VerificationStatus:
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    INACTIVE = "INACTIVE"


# ---------------------------------------------------------------------------
# Create / update
# ---------------------------------------------------------------------------

class KnowledgeDocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    authority: str = Field(..., min_length=1, max_length=300)
    source_url: str = Field(..., description="Canonical URL of the official source.")
    service_scope: str = Field(..., min_length=1, max_length=500,
                               description="Exact service and notice scope this source covers.")
    effective_date: Optional[datetime] = None
    review_notes: Optional[str] = Field(None, max_length=2000)


class KnowledgeDocumentVerify(BaseModel):
    verification_status: str = Field(..., description="VERIFIED | STALE | INACTIVE")
    review_notes: Optional[str] = Field(None, max_length=2000)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

class KnowledgeDocumentRead(BaseModel):
    id: UUID
    title: str
    authority: str
    source_url: str
    service_scope: str
    retrieved_at: datetime
    last_checked_at: Optional[datetime]
    effective_date: Optional[datetime]
    content_hash: Optional[str]
    version: int
    verification_status: str
    reviewed_by: Optional[UUID]
    review_notes: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocumentList(BaseModel):
    items: List[KnowledgeDocumentRead]
    total: int

