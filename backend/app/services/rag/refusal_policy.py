"""
RAG Refusal Policy and Safety Boundary Guard.
Enforces non-negotiable safeguards from QueueLess 2.3 Spec (Section 2.1, 2.2, 8.5):

1. Refuses legal eligibility predictions or approval guarantees.
2. Refuses questions outside civic service visit preparation.
3. Defends against prompt injections / jailbreaks.
4. Generates standardized fallback responses for INSUFFICIENT_EVIDENCE,
   SOURCE_CONFLICT, TEMPORARILY_UNAVAILABLE, and INVALID_REQUEST.
"""

import re
from typing import List, Optional, Tuple
from uuid import uuid4

from app.schemas.assistant import AssistantChatResponse, CitationSchema
from app.services.rag.retrieval import RetrievedChunk


class RefusalPolicy:
    """Evaluates user requests against boundary rules and generates safe refusals."""

    # Patterns indicating requests for legal eligibility decisions or approval predictions
    ELIGIBILITY_PATTERNS = [
        r"\bam\s+i\s+eligible\b",
        r"\bcan\s+i\s+get\s+approved\b",
        r"\bwill\s+(my\s+application|i)\s+(be|get)\s+approved\b",
        r"\bchance\s+of\s+approval\b",
        r"\bguarantee\s+(acceptance|approval)\b",
        r"\bpredict\s+my\s+eligibility\b",
        r"\bwill\s+they\s+reject\s+(me|my)\b",
        r"\bcan\s+you\s+approve\s+(my|this)\b",
        r"\bverify\s+my\s+legal\s+status\b",
    ]

    # Patterns indicating queries completely outside civic services
    UNRELATED_PATTERNS = [
        r"\b(recipe|cook|bake|ingredients\s+for)\b",
        r"\b(write\s+code|python\s+script|javascript\s+function|debug\s+my\s+code)\b",
        r"\b(movie|song|celebrity|football|cricket|match|ipl|sports)\b",
        r"\b(crypto|bitcoin|stock\s+tips|forex\s+trading)\b",
        r"\b(tell\s+me\s+a\s+joke|write\s+a\s+poem|story\s+about)\b",
    ]

    # Prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(all\s+)?instructions",
        r"system\s+prompt\s+override",
        r"you\s+are\s+now\s+(an\s+unfiltered|dan|jailbroken)",
        r"print\s+(your\s+)?system\s+instructions",
        r"bypass\s+(all\s+)?safety\s+filters",
    ]

    def check_eligibility_refusal(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Detects if query asks for legal eligibility decision or approval prediction.
        Returns (refusal_text, limitation_reason) or None.
        """
        normalized = query.lower()
        for pattern in self.ELIGIBILITY_PATTERNS:
            if re.search(pattern, normalized):
                refusal_text = (
                    "QueueLess provides procedural guidance, required document checklists, and office visit "
                    "coordination, but cannot determine legal eligibility, predict application approval, or "
                    "guarantee acceptance. Only the authorized departmental verification officer at the citizen "
                    "service centre can evaluate your specific eligibility and decide upon government applications."
                )
                limitation = "QueueLess does not evaluate legal eligibility or predict approval outcomes."
                return refusal_text, limitation
        return None

    def check_unrelated_topic(self, query: str) -> Optional[Tuple[str, str]]:
        """
        Detects if query is unrelated to civic services or office visit preparation.
        Returns (refusal_text, limitation_reason) or None.
        """
        normalized = query.lower()
        for pattern in self.UNRELATED_PATTERNS:
            if re.search(pattern, normalized):
                refusal_text = (
                    "QueueLess is an assistant dedicated to government citizen services, required document "
                    "checklists, and physical office visit preparation. I cannot answer questions on unrelated topics."
                )
                limitation = "Query outside civic services scope."
                return refusal_text, limitation
        return None

    def check_prompt_injection(self, query: str) -> bool:
        """
        Returns True if the query exhibits clear prompt injection or jailbreak attempts.
        """
        normalized = query.lower()
        for pattern in self.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, normalized):
                return True
        return False

    def build_insufficient_evidence_response(
        self,
        query: str,
        language: str = "en",
        service_name: Optional[str] = None,
        disclaimer_note: Optional[str] = None,
    ) -> AssistantChatResponse:
        """
        Safe fallback when no relevant verified chunks exist or retrieval score is too low.
        """
        scope_clause = f" for '{service_name}'" if service_name else ""
        answer = (
            f"The verified knowledge corpus does not contain sufficient authoritative information{scope_clause} "
            f"to accurately answer: \"{query}\".\n\n"
            f"To ensure you receive correct statutory details, please consult the official portal "
            f"(e.g., Nadakacheri or Seva Sindhu) or speak with an official verification officer at the citizen "
            f"service centre."
        )
        limitations = [
            "Official corpus lacks verified data to answer this specific query.",
            disclaimer_note or "Citizens should verify statutory details at official portals or office counters.",
        ]
        return AssistantChatResponse(
            answer=answer,
            status="INSUFFICIENT_EVIDENCE",
            language=language,
            citations=[],
            limitations=[l for l in limitations if l],
            request_id=uuid4(),
        )

    def build_source_conflict_response(
        self,
        conflicting_chunks: List[RetrievedChunk],
        language: str = "en",
    ) -> AssistantChatResponse:
        """
        Fallback when multiple verified sources provide contradictory guidance.
        """
        citations: List[CitationSchema] = []
        for c in conflicting_chunks:
            citations.append(
                CitationSchema(
                    chunk_id=c.chunk_id,
                    title=c.title,
                    authority=c.authority,
                    url=c.url,
                    page_number=c.page_number,
                    retrieved_at=c.retrieved_at,
                    last_checked_at=c.last_checked_at,
                )
            )

        answer = (
            "The verified official sources in our records contain conflicting or differing guidance "
            "regarding this requirement. To avoid carrying incorrect documents, please consult the issuing "
            "department directly before your physical office visit."
        )
        return AssistantChatResponse(
            answer=answer,
            status="SOURCE_CONFLICT",
            language=language,
            citations=citations,
            limitations=["Verified sources present conflicting guidance on this topic."],
            request_id=uuid4(),
        )

    def build_temporarily_unavailable_response(
        self,
        language: str = "en",
        reason: Optional[str] = None,
    ) -> AssistantChatResponse:
        """
        Fallback when LLM, ChromaDB, or embeddings are down.
        Ensures core appointment booking and queue participation remain unblocked.
        """
        answer = (
            "The AI assistant is temporarily unavailable. "
            "You can still access the standard service checklist, schedule an appointment, "
            "or visit the citizen service centre without interruption."
        )
        return AssistantChatResponse(
            answer=answer,
            status="TEMPORARILY_UNAVAILABLE",
            language=language,
            citations=[],
            limitations=[reason or "AI provider or vector store temporarily unavailable."],
            request_id=uuid4(),
        )

    def build_invalid_request_response(
        self,
        reason: str,
        language: str = "en",
    ) -> AssistantChatResponse:
        return AssistantChatResponse(
            answer=f"Invalid request: {reason}",
            status="INVALID_REQUEST",
            language=language,
            citations=[],
            limitations=["Request validation failed."],
            request_id=uuid4(),
        )
