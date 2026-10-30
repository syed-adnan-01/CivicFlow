"""
Pydantic v2 schemas for document check sub-items.
Used internally and in detailed check result endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentCheckItemRead(BaseModel):
    id: UUID
    check_id: UUID
    checklist_item_id: UUID
    result: str
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_band: Optional[str] = None
    review_note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

