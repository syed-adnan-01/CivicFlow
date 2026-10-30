"""
RAG Answer Generator.
Orchestrates:
1. Input validation and prompt injection defenses.
2. Refusal policy checks (eligibility predictions, out-of-scope queries).
3. Retrieval from ChromaDB with verified/active filters.
4. Constrained prompt construction (system + reference excerpts).
5. LLM call via FallbackLLMProvider (Groq primary -> Gemini fallback).
6. Strict citation extraction and canonical URL validation.
7. Safe fallback to INSUFFICIENT_EVIDENCE or TEMPORARILY_UNAVAILABLE if validation fails.
"""

import logging
from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse
from app.services.providers import get_llm_provider
from app.services.providers.llm_base import LLMProviderBase, ProviderUnavailableError
from app.services.rag.citation_validator import CitationValidator
from app.services.rag.prompt_builder import PromptBuilder
from app.services.rag.refusal_policy import RefusalPolicy
from app.services.rag.retrieval import RetrievalService

logger = logging.getLogger(__name__)


class AnswerGenerator:
    """End-to-end RAG answer generation and safety pipeline."""

    def __init__(
        self,
        retrieval_service: Optional[RetrievalService] = None,
        llm_provider: Optional[LLMProviderBase] = None,
        prompt_builder: Optional[PromptBuilder] = None,
        citation_validator: Optional[CitationValidator] = None,
        refusal_policy: Optional[RefusalPolicy] = None,
    ):
        self.retrieval_service = retrieval_service or RetrievalService()
        self.llm_provider = llm_provider or get_llm_provider()
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.citation_validator = citation_validator or CitationValidator()
        self.refusal_policy = refusal_policy or RefusalPolicy()

    def generate(
        self,
        request: AssistantChatRequest,
        db: Optional[Session] = None,
        service_name: Optional[str] = None,
    ) -> AssistantChatResponse:
        """
        Processes a citizen query and returns a verified, cited answer or safe refusal.
        """
        # 1. Input sanitization & validation
        message = (request.message or "").strip()
        if not message:
            return self.refusal_policy.build_invalid_request_response(
                "Message must not be empty.", language=request.language
            )

        # 2. Prompt injection defense
        if self.refusal_policy.check_prompt_injection(message):
            logger.warning("Prompt injection attempt intercepted: %s", message[:100])
            return self.refusal_policy.build_invalid_request_response(
                "Your request contains invalid instruction override patterns.",
                language=request.language,
            )

        # 3. Refusal check: legal eligibility or approval predictions
        eligibility_refusal = self.refusal_policy.check_eligibility_refusal(message)
        if eligibility_refusal:
            refusal_text, limitation = eligibility_refusal
            return AssistantChatResponse(
                answer=refusal_text,
                status="ANSWERED",
                language=request.language,
                citations=[],
                limitations=[limitation],
                request_id=uuid4(),
            )

        # 4. Refusal check: queries completely unrelated to civic services
        unrelated_refusal = self.refusal_policy.check_unrelated_topic(message)
        if unrelated_refusal:
            refusal_text, limitation = unrelated_refusal
            return AssistantChatResponse(
                answer=refusal_text,
                status="ANSWERED",
                language=request.language,
                citations=[],
                limitations=[limitation],
                request_id=uuid4(),
            )

        # 5. Retrieve verified chunks from ChromaDB
        try:
            chunks = self.retrieval_service.retrieve(
                query=message,
                service_id=request.service_id,
                service_name=service_name,
            )
        except Exception as exc:
            logger.error("Error during chunk retrieval: %s", exc)
            return self.refusal_policy.build_temporarily_unavailable_response(
                language=request.language,
                reason="Knowledge base retrieval service is currently unavailable.",
            )

        # If no verified chunks meet relevance threshold -> INSUFFICIENT_EVIDENCE
        if not chunks:
            return self.refusal_policy.build_insufficient_evidence_response(
                query=message,
                language=request.language,
                service_name=service_name,
            )

        # 6. Build constrained prompts
        system_prompt = self.prompt_builder.build_system_prompt(language=request.language)
        user_prompt = self.prompt_builder.build_user_prompt(
            message=message,
            chunks=chunks,
            language=request.language,
            service_name=service_name,
        )

        # 7. Call LLM provider (Groq with Gemini fallback)
        try:
            llm_res = self.llm_provider.generate(system_prompt, user_prompt)
        except ProviderUnavailableError as exc:
            logger.error("LLM provider unavailable: %s", exc)
            return self.refusal_policy.build_temporarily_unavailable_response(
                language=request.language,
                reason="AI answer generation provider is currently unavailable.",
            )
        except Exception as exc:
            logger.error("Unexpected error during LLM generation: %s", exc)
            return self.refusal_policy.build_temporarily_unavailable_response(
                language=request.language,
                reason="An unexpected error occurred while communicating with the AI service.",
            )

        # 8. Validate citations and source grounding
        validation = self.citation_validator.validate_and_format(
            raw_answer=llm_res.content,
            retrieved_chunks=chunks,
            db=db,
        )

        # If the answer claims facts but all citations were hallucinated/invalid,
        # fail safe: do NOT return an ungrounded or fabricated answer.
        if not validation.is_grounded:
            logger.warning("Generated answer failed citation grounding check; falling back.")
            return self.refusal_policy.build_insufficient_evidence_response(
                query=message,
                language=request.language,
                service_name=service_name,
                disclaimer_note="Generated response lacked verified source backing and was safely withheld.",
            )

        limitations = [
            f"This answer is grounded strictly in {len(validation.citations)} verified official source excerpt(s)."
        ]
        if validation.warnings:
            limitations.extend(validation.warnings)

        return AssistantChatResponse(
            answer=validation.cleaned_answer,
            status="ANSWERED",
            language=request.language,
            citations=validation.citations,
            limitations=limitations,
            request_id=uuid4(),
        )

