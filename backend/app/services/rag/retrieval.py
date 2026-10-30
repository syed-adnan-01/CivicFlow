"""
RAG Retrieval Service.
Fetches relevant chunks for a user query from ChromaDB.
Enforces:
1. Only VERIFIED + active chunks are returned.
2. Relevance score meets configured threshold (RAG_MIN_RELEVANCE_SCORE).
3. Service scope compatibility (e.g. PSI Training notice cannot answer Income Certificate).
4. Full citation metadata is preserved.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import settings
from app.services.providers import get_embedding_provider
from app.services.rag.source_governance import SourceGovernance
from app.services.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    title: str
    authority: str
    url: str
    service_scope: str
    page_number: Optional[int]
    retrieved_at: str
    last_checked_at: str
    score: float


class RetrievalService:
    def __init__(self, vector_store: Optional[VectorStore] = None):
        self.vector_store = vector_store or VectorStore()
        self.embedding_provider = get_embedding_provider()
        self.min_score = settings.RAG_MIN_RELEVANCE_SCORE
        self.top_k = settings.RAG_TOP_K

    def retrieve(
        self,
        query: str,
        service_id: Optional[UUID] = None,
        service_name: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[RetrievedChunk]:
        """
        Embeds the query and searches ChromaDB for matching verified chunks.
        Filters out:
        - Chunks from unverified, stale, or inactive sources.
        - Chunks whose relevance score is below min_score.
        - Chunks violating service scope rules (e.g. PSI Training notice vs Income Certificate).
        """
        if not query or not query.strip():
            return []

        limit = top_k or self.top_k

        # 1. Generate query embedding
        try:
            embed_res = self.embedding_provider.embed(query)
            query_embedding = embed_res.embedding
        except Exception as exc:
            logger.error("Failed to generate embedding for query: %s", exc)
            return []

        # 2. Query ChromaDB with active/verified filter
        raw_results = self.vector_store.query(
            query_embedding=query_embedding,
            top_k=limit * 2,  # Fetch extra to allow post-filtering by score and scope
            only_verified=True,
        )

        filtered_chunks: List[RetrievedChunk] = []

        for item in raw_results:
            score = item.get("score", 0.0)
            meta = item.get("metadata", {})

            # Enforce relevance threshold
            if score < self.min_score:
                logger.debug("Chunk %s filtered out: score %.2f < threshold %.2f", item["chunk_id"], score, self.min_score)
                continue

            # Verify chunk is still marked active and verified
            if not SourceGovernance.is_source_retrievable(
                verification_status=meta.get("verification_status", ""),
                active=meta.get("active", False),
            ):
                continue

            # Enforce service scope compatibility
            source_scope = meta.get("service_scope", "")
            if service_name and not SourceGovernance.validate_service_scope_compatibility(source_scope, service_name):
                logger.info(
                    "Scope conflict: chunk %s (scope: '%s') incompatible with requested service '%s'",
                    item["chunk_id"],
                    source_scope,
                    service_name,
                )
                continue

            page_num = meta.get("page_number")
            page_number = int(page_num) if page_num and page_num != -1 else None

            filtered_chunks.append(
                RetrievedChunk(
                    chunk_id=item["chunk_id"],
                    text=item["text"],
                    title=meta.get("page_title", "Official Source"),
                    authority=meta.get("authority", "Government Authority"),
                    url=meta.get("canonical_url", ""),
                    service_scope=source_scope,
                    page_number=page_number,
                    retrieved_at=meta.get("retrieved_at", ""),
                    last_checked_at=meta.get("last_checked_at", ""),
                    score=score,
                )
            )

            if len(filtered_chunks) >= limit:
                break

        return filtered_chunks

