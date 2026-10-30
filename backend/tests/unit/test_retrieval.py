"""
Unit tests — RAG retrieval service.
Tests similarity thresholding, verified-only filtering, scope compatibility,
and citation preservation.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock
import pytest

from app.services.rag.retrieval import RetrievalService, RetrievedChunk


class MockVectorStore:
    def __init__(self, mock_results: List[Dict[str, Any]]):
        self.mock_results = mock_results

    def query(self, query_embedding, top_k=5, service_scope=None, only_verified=True):
        return self.mock_results


class TestRetrievalService:
    def test_empty_query_returns_empty_list(self):
        service = RetrievalService(vector_store=MockVectorStore([]))
        results = service.retrieve("")
        assert results == []

    def test_relevance_threshold_filters_low_scoring_chunks(self):
        raw_chunks = [
            {
                "chunk_id": "chunk_high",
                "text": "Highly relevant government instruction text.",
                "score": 0.85,
                "metadata": {
                    "page_title": "Official Guide",
                    "authority": "Revenue Dept",
                    "canonical_url": "https://gov.in/guide",
                    "service_scope": "General",
                    "verification_status": "VERIFIED",
                    "active": True,
                    "retrieved_at": "2026-10-30T00:00:00Z",
                    "page_number": 1,
                },
            },
            {
                "chunk_id": "chunk_low",
                "text": "Irrelevant generic text.",
                "score": 0.45,  # Below default 0.70 threshold
                "metadata": {
                    "page_title": "Other Page",
                    "authority": "Other",
                    "canonical_url": "https://gov.in/other",
                    "service_scope": "General",
                    "verification_status": "VERIFIED",
                    "active": True,
                    "retrieved_at": "2026-10-30T00:00:00Z",
                    "page_number": 2,
                },
            },
        ]

        store = MockVectorStore(raw_chunks)
        service = RetrievalService(vector_store=store)
        service.embedding_provider.embed = MagicMock(return_value=MagicMock(embedding=[0.1] * 768))

        results = service.retrieve("What are the requirements?")
        assert len(results) == 1
        assert results[0].chunk_id == "chunk_high"
        assert results[0].score == 0.85
        assert results[0].url == "https://gov.in/guide"
        assert results[0].page_number == 1

    def test_psi_training_notice_rejected_for_income_certificate_service(self):
        psi_chunks = [
            {
                "chunk_id": "psi_chunk_1",
                "text": "Documents required for Directorate of Minorities PSI Training candidate verification.",
                "score": 0.90,
                "metadata": {
                    "page_title": "PSI Training Verification Notice",
                    "authority": "Directorate of Minorities",
                    "canonical_url": "https://gok.gov.in/psi-notice",
                    "service_scope": "Directorate of Minorities PSI Training Document Verification",
                    "verification_status": "VERIFIED",
                    "active": True,
                    "retrieved_at": "2026-10-30T00:00:00Z",
                    "page_number": 1,
                },
            }
        ]

        store = MockVectorStore(psi_chunks)
        service = RetrievalService(vector_store=store)
        service.embedding_provider.embed = MagicMock(return_value=MagicMock(embedding=[0.1] * 768))

        # Critical restriction test: querying for general Income Certificate must NOT return PSI training chunk
        results = service.retrieve(
            query="What are the documents needed for an income certificate?",
            service_name="Income Certificate Application",
        )
        assert len(results) == 0

    def test_psi_training_notice_allowed_when_querying_psi_training(self):
        psi_chunks = [
            {
                "chunk_id": "psi_chunk_1",
                "text": "Documents required for Directorate of Minorities PSI Training candidate verification.",
                "score": 0.90,
                "metadata": {
                    "page_title": "PSI Training Verification Notice",
                    "authority": "Directorate of Minorities",
                    "canonical_url": "https://gok.gov.in/psi-notice",
                    "service_scope": "Directorate of Minorities PSI Training Document Verification",
                    "verification_status": "VERIFIED",
                    "active": True,
                    "retrieved_at": "2026-10-30T00:00:00Z",
                    "page_number": 1,
                },
            }
        ]

        store = MockVectorStore(psi_chunks)
        service = RetrievalService(vector_store=store)
        service.embedding_provider.embed = MagicMock(return_value=MagicMock(embedding=[0.1] * 768))

        results = service.retrieve(
            query="What documents do I need for PSI training verification?",
            service_name="PSI Training Candidate Verification",
        )
        assert len(results) == 1
        assert results[0].chunk_id == "psi_chunk_1"

