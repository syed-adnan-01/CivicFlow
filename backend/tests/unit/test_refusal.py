"""
Unit tests — refusal policy and safety boundaries.
Tests that the assistant refuses to answer unsupported questions,
rejects eligibility predictions, handles provider outages gracefully,
and prevents hallucinated statutory requirements.
"""

from unittest.mock import MagicMock
from uuid import uuid4
import pytest

from app.schemas.assistant import AssistantChatRequest
from app.services.providers.llm_base import LLMResponse, ProviderUnavailableError
from app.services.rag.answer_generator import AnswerGenerator
from app.services.rag.refusal_policy import RefusalPolicy
from app.services.rag.retrieval import RetrievedChunk


@pytest.fixture
def refusal_policy():
    return RefusalPolicy()


@pytest.fixture
def sample_chunk():
    return RetrievedChunk(
        chunk_id="doc1_chunk_0",
        text="Application requires voter ID or Aadhaar card.",
        title="Official Guide",
        authority="Revenue Department",
        url="https://revenue.karnataka.gov.in",
        service_scope="Income Certificate",
        page_number=1,
        retrieved_at="2026-10-30T00:00:00Z",
        last_checked_at="2026-10-30T00:00:00Z",
        score=0.90,
    )


class TestInsufficientEvidenceRefusal:
    def test_no_relevant_chunks_returns_insufficient_evidence(self, refusal_policy):
        resp = refusal_policy.build_insufficient_evidence_response(
            query="Can I apply for special defense quota?",
            language="en",
            service_name="Income Certificate",
        )
        assert resp.status == "INSUFFICIENT_EVIDENCE"
        assert len(resp.citations) == 0
        assert "Income Certificate" in resp.answer or "sufficient" in resp.answer.lower()
        assert any("official portal" in resp.answer.lower() for _ in [1])

    def test_unverified_only_chunks_returns_refusal(self):
        # Retrieval service filtered out unverified chunks, leaving empty list -> AnswerGenerator returns INSUFFICIENT_EVIDENCE
        mock_retrieval = MagicMock()
        mock_retrieval.retrieve.return_value = []

        generator = AnswerGenerator(retrieval_service=mock_retrieval)
        req = AssistantChatRequest(message="What is the process?")
        resp = generator.generate(req)

        assert resp.status == "INSUFFICIENT_EVIDENCE"
        assert len(resp.citations) == 0

    def test_conflicting_sources_returns_source_conflict_status(self, refusal_policy, sample_chunk):
        chunk2 = RetrievedChunk(
            chunk_id="doc2_chunk_0",
            text="Aadhaar is not accepted; only passport is accepted.",
            title="Old Circular",
            authority="Revenue Department",
            url="https://revenue.karnataka.gov.in/old",
            service_scope="Income Certificate",
            page_number=1,
            retrieved_at="2026-10-30T00:00:00Z",
            last_checked_at="2026-10-30T00:00:00Z",
            score=0.85,
        )

        resp = refusal_policy.build_source_conflict_response([sample_chunk, chunk2])
        assert resp.status == "SOURCE_CONFLICT"
        assert len(resp.citations) == 2
        assert "conflicting" in resp.answer.lower()


class TestOutOfScopeRefusal:
    def test_eligibility_question_refused(self, refusal_policy):
        queries = [
            "Am I eligible for this income certificate?",
            "Will I get approved if my income is 2 lakhs?",
            "What is my chance of approval?",
            "Can you approve my application?",
        ]
        for q in queries:
            result = refusal_policy.check_eligibility_refusal(q)
            assert result is not None, f"Expected eligibility refusal for query: '{q}'"
            refusal_text, limitation = result
            assert "cannot determine legal eligibility" in refusal_text
            assert "verification officer" in refusal_text

    def test_approval_prediction_refused(self):
        generator = AnswerGenerator()
        req = AssistantChatRequest(message="Will my application be approved by tomorrow?")
        resp = generator.generate(req)

        assert resp.status == "ANSWERED"
        assert "cannot determine legal eligibility" in resp.answer
        assert len(resp.citations) == 0

    def test_fee_not_in_corpus_refused(self, sample_chunk):
        # When corpus does not contain fees and user asks for fee:
        # If LLM invents a chunk ID or claims without citation, AnswerGenerator catches it
        mock_retrieval = MagicMock()
        mock_retrieval.retrieve.return_value = [sample_chunk]

        mock_llm = MagicMock()
        mock_llm.generate.return_value = LLMResponse(
            content="The statutory fee is Rs 100 [CHUNK:fake_fee_chunk].",
            model="test-model",
            provider="test",
        )

        generator = AnswerGenerator(
            retrieval_service=mock_retrieval,
            llm_provider=mock_llm,
        )
        req = AssistantChatRequest(message="What is the fee?")
        resp = generator.generate(req)

        # Because the cited chunk was invented/invalid, the answer is withheld and returns INSUFFICIENT_EVIDENCE
        assert resp.status == "INSUFFICIENT_EVIDENCE"

    def test_unrelated_topic_returns_scope_message(self, refusal_policy):
        unrelated_queries = [
            "Give me a recipe for chocolate cake",
            "Write a python script to reverse a list",
            "Who won the cricket match yesterday?",
            "What crypto coins should I buy?",
        ]
        for q in unrelated_queries:
            result = refusal_policy.check_unrelated_topic(q)
            assert result is not None, f"Expected out-of-scope refusal for: '{q}'"
            refusal_text, limitation = result
            assert "dedicated to government citizen services" in refusal_text


class TestProviderOutageRefusal:
    def test_llm_unavailable_returns_temporarily_unavailable(self, sample_chunk):
        mock_retrieval = MagicMock()
        mock_retrieval.retrieve.return_value = [sample_chunk]

        mock_llm = MagicMock()
        mock_llm.generate.side_effect = ProviderUnavailableError("LLM API Timeout")

        generator = AnswerGenerator(
            retrieval_service=mock_retrieval,
            llm_provider=mock_llm,
        )
        req = AssistantChatRequest(message="What documents do I need?")
        resp = generator.generate(req)

        assert resp.status == "TEMPORARILY_UNAVAILABLE"
        assert len(resp.citations) == 0
        assert "temporarily unavailable" in resp.answer.lower()

    def test_chroma_unavailable_returns_temporarily_unavailable(self):
        mock_retrieval = MagicMock()
        mock_retrieval.retrieve.side_effect = RuntimeError("ChromaDB connection refused")

        generator = AnswerGenerator(retrieval_service=mock_retrieval)
        req = AssistantChatRequest(message="What documents do I need?")
        resp = generator.generate(req)

        assert resp.status == "TEMPORARILY_UNAVAILABLE"
        assert len(resp.citations) == 0
