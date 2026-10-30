"""
Assistant module router.
POST /api/v1/assistant/chat  — citizen asks a service question.
GET  /api/v1/assistant/health — provider health (no auth required, safe for monitoring).
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.dependencies import AuthenticatedUser, get_current_user
from app.core.database import get_db
from app.modules.assistant.service import AssistantService
from app.schemas.assistant import (
    AssistantChatRequest,
    AssistantChatResponse,
    AssistantHealthResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
async def chat(
    request: AssistantChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Citizen sends a message and receives a grounded answer with citations.
    Enforces RAG source governance, citation verification, and boundary refusal policies.
    """
    try:
        service = AssistantService(db=db)
        return service.answer(request=request, user=current_user)
    except Exception as exc:
        logger.error("Unhandled error in assistant chat endpoint: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INTERNAL_ERROR", "message": "Failed to process assistant request."},
        )


@router.get("/health", response_model=AssistantHealthResponse)
async def health():
    """
    Returns provider health without exposing credentials.
    Checks Groq (primary), Gemini (fallback) and embedding configuration.
    """
    from app.services.providers.groq_provider import GroqProvider
    from app.services.providers.gemini_provider import GeminiProvider
    from app.services.providers.embedding_provider import get_embedding_provider

    groq_ok = GroqProvider().is_configured()
    gemini_ok = GeminiProvider().is_configured()
    embed_ok = get_embedding_provider().is_configured()

    # Vector store reachability check (light — no query)
    chroma_ok = False
    try:
        import chromadb  # type: ignore
        from app.core.config import settings
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        client.heartbeat()
        chroma_ok = True
    except Exception:
        pass

    llm_ok = groq_ok or gemini_ok
    overall = "healthy" if (llm_ok and embed_ok) else ("degraded" if llm_ok else "unavailable")

    return AssistantHealthResponse(
        llm_configured=llm_ok,
        embedding_configured=embed_ok,
        vector_store_reachable=chroma_ok,
        status=overall,
    )
