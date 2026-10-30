"""
Assistant Service.
Orchestrates citizen service questions, grounding checks, and response generation.
"""

import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.common.dependencies import AuthenticatedUser
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.rag.answer_generator import AnswerGenerator

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(self, db: Session, answer_generator: Optional[AnswerGenerator] = None):
        self.db = db
        self.answer_generator = answer_generator or AnswerGenerator()

    def answer(
        self,
        request: AssistantChatRequest,
        user: Optional[AuthenticatedUser] = None,
    ) -> AssistantChatResponse:
        """
        Coordinates RAG answer generation, scope verification, and audit logging.
        Safe operational metadata is logged; citizen PII is never logged.
        """
        user_id_str = str(user.id) if user else "anonymous"

        logger.info(
            "Processing assistant query. user=%s, service_id=%s, lang=%s, msg_len=%d",
            user_id_str,
            str(request.service_id) if request.service_id else "none",
            request.language,
            len(request.message),
        )

        # Resolve service name if service_id is provided and service table exists
        service_name: Optional[str] = None
        if request.service_id:
            try:
                from app.models.service import Service  # type: ignore
                svc = self.db.query(Service).filter(Service.id == request.service_id).first()
                if svc:
                    service_name = getattr(svc, "name", None)
            except Exception:
                pass

        response = self.answer_generator.generate(
            request=request,
            db=self.db,
            service_name=service_name,
        )

        logger.info(
            "Assistant query completed. request_id=%s, status=%s, citations_count=%d",
            str(response.request_id),
            response.status,
            len(response.citations),
        )

        return response

