"""
Pydantic v2 schemas for the RAG assistant API.

POST /api/v1/assistant/chat  — citizen sends a message, receives grounded answer.
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------

class AssistantChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    service_id: Optional[UUID] = Field(None, description="Scope retrieval to this service.")
    language: str = Field("en", description="BCP-47 language tag, e.g. 'en', 'kn', 'hi'.")
    conversation_id: Optional[UUID] = Field(None, description="Optional session grouping ID.")


# ---------------------------------------------------------------------------
# Citation
# ---------------------------------------------------------------------------

class CitationSchema(BaseModel):
    chunk_id: str
    title: str
    authority: str
    url: str
    page_number: Optional[int] = None
    retrieved_at: str
    last_checked_at: str


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------

class AssistantChatResponse(BaseModel):
    answer: str
    status: str = Field(
        ...,
        description=(
            "One of: ANSWERED, INSUFFICIENT_EVIDENCE, "
            "SOURCE_CONFLICT, TEMPORARILY_UNAVAILABLE, INVALID_REQUEST"
        ),
    )
    language: str
    citations: List[CitationSchema] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    request_id: UUID


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class AssistantHealthResponse(BaseModel):
    llm_configured: bool
    embedding_configured: bool
    vector_store_reachable: bool
    status: str  # "healthy" | "degraded" | "unavailable"

