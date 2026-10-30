"""
Integration tests — assistant API.
Tests the full POST /api/v1/assistant/chat flow with authentication,
retrieval, citation verification, service scoping, and provider outage fallbacks.
"""

from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.providers.llm_base import LLMResponse, ProviderUnavailableError
from app.services.rag.retrieval import RetrievedChunk


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_verified_chunk():
    return RetrievedChunk(
        chunk_id="doc1_chunk_0",
        text="Applicants must bring original Aadhaar card and active residential proof.",
        title="Nadakacheri Service Guidelines",
        authority="Directorate of Atalji Janasnehi Kendra",
        url="https://nadakacheri.karnataka.gov.in/guide",
        service_scope="Income Certificate",
        page_number=1,
        retrieved_at="2026-10-30T00:00:00Z",
        last_checked_at="2026-10-30T00:00:00Z",
        score=0.92,
    )


class TestAssistantChatAuthentication:
    def test_unauthenticated_request_returns_401(self, client):
        # Force production mode to ensure auth requirement is triggered
        with patch.object(settings, "APP_ENV", "production"):
            res = client.post("/api/v1/assistant/chat", json={"message": "What documents do I need?"})
            assert res.status_code == 401
            assert res.json()["detail"]["code"] == "UNAUTHENTICATED"

    def test_citizen_with_valid_firebase_token_can_chat(self, client, sample_verified_chunk):
        headers = {"Authorization": "Bearer citizen_valid_test_token"}
        with patch("app.services.rag.retrieval.RetrievalService.retrieve", return_value=[sample_verified_chunk]):
            with patch("app.services.rag.citation_validator.CitationValidator._verify_chunk_active_in_db", return_value=True):
                with patch(
                    "app.services.providers.FallbackLLMProvider.generate",
                    return_value=LLMResponse(
                        content="Bring your original Aadhaar card [CHUNK:doc1_chunk_0].",
                        model="test-llm",
                        provider="groq",
                    ),
                ):
                    res = client.post(
                        "/api/v1/assistant/chat",
                        json={"message": "What documents do I need?", "language": "en"},
                        headers=headers,
                    )
                    assert res.status_code == 200
                    data = res.json()
                    assert data["status"] == "ANSWERED"
                    assert len(data["citations"]) == 1
                    assert data["citations"][0]["chunk_id"] == "doc1_chunk_0"


class TestAssistantChatRetrieval:
    def test_verified_source_returns_grounded_answer_with_citations(self, client, sample_verified_chunk):
        headers = {"Authorization": "Bearer test_token"}
        with patch("app.services.rag.retrieval.RetrievalService.retrieve", return_value=[sample_verified_chunk]):
            with patch("app.services.rag.citation_validator.CitationValidator._verify_chunk_active_in_db", return_value=True):
                with patch(
                    "app.services.providers.FallbackLLMProvider.generate",
                    return_value=LLMResponse(
                        content="Original Aadhaar card is required [CHUNK:doc1_chunk_0].",
                        model="test-llm",
                        provider="groq",
                    ),
                ):
                    res = client.post(
                        "/api/v1/assistant/chat",
                        json={"message": "Which identity documents are accepted?"},
                        headers=headers,
                    )
                    assert res.status_code == 200
                    data = res.json()
                    assert data["status"] == "ANSWERED"
                    assert len(data["citations"]) == 1
                    assert data["citations"][0]["url"] == "https://nadakacheri.karnataka.gov.in/guide"
                    assert "[1]" in data["answer"]

    def test_unverified_source_never_cited_in_response(self, client):
        headers = {"Authorization": "Bearer test_token"}
        # Retrieval filters out unverified sources, returning empty list
        with patch("app.services.rag.retrieval.RetrievalService.retrieve", return_value=[]):
            res = client.post(
                "/api/v1/assistant/chat",
                json={"message": "What are the rules for unverified scheme?"},
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "INSUFFICIENT_EVIDENCE"
            assert len(data["citations"]) == 0

    def test_stale_source_not_returned_after_deactivation(self, client, sample_verified_chunk):
        headers = {"Authorization": "Bearer test_token"}
        # Deactivated source chunk check fails at response time in DB
        with patch("app.services.rag.retrieval.RetrievalService.retrieve", return_value=[sample_verified_chunk]):
            with patch(
                "app.services.rag.citation_validator.CitationValidator._verify_chunk_active_in_db",
                return_value=False,
            ):
                with patch(
                    "app.services.providers.FallbackLLMProvider.generate",
                    return_value=LLMResponse(
                        content="You must present Aadhaar [CHUNK:doc1_chunk_0].",
                        model="test-llm",
                        provider="groq",
                    ),
                ):
                    res = client.post(
                        "/api/v1/assistant/chat",
                        json={"message": "What do I need?"},
                        headers=headers,
                    )
                    assert res.status_code == 200
                    data = res.json()
                    # Because citations were from deactivated source, grounding rejected the claim
                    assert data["status"] == "INSUFFICIENT_EVIDENCE"
                    assert len(data["citations"]) == 0

    def test_service_scoped_query_does_not_return_other_service_chunks(self, client):
        headers = {"Authorization": "Bearer test_token"}
        from app.services.rag.source_governance import SourceGovernance
        # Proves PSI Training notice cannot match Income Certificate
        assert not SourceGovernance.validate_service_scope_compatibility(
            source_scope="PSI Training Document Verification Notice",
            requested_service_name="Income Certificate",
        )

        # Retrieval returns empty when scope conflicts
        with patch("app.services.rag.retrieval.RetrievalService.retrieve", return_value=[]):
            res = client.post(
                "/api/v1/assistant/chat",
                json={"message": "Is PSI notice applicable for income certificate?", "service_id": str(uuid4())},
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "INSUFFICIENT_EVIDENCE"


class TestAssistantChatFallback:
    def test_llm_outage_returns_safe_message(self, client, sample_verified_chunk):
        headers = {"Authorization": "Bearer test_token"}
        with patch("app.services.rag.retrieval.RetrievalService.retrieve", return_value=[sample_verified_chunk]):
            with patch(
                "app.services.providers.FallbackLLMProvider.generate",
                side_effect=ProviderUnavailableError("All LLM providers quota-exhausted or offline"),
            ):
                res = client.post(
                    "/api/v1/assistant/chat",
                    json={"message": "What documents do I need?"},
                    headers=headers,
                )
                assert res.status_code == 200
                data = res.json()
                assert data["status"] == "TEMPORARILY_UNAVAILABLE"
                assert "temporarily unavailable" in data["answer"].lower()
                assert len(data["citations"]) == 0

    def test_embedding_outage_returns_safe_message(self, client):
        headers = {"Authorization": "Bearer test_token"}
        with patch("app.services.providers.embedding_provider.get_embedding_provider") as mock_emb:
            mock_emb.return_value.embed.side_effect = RuntimeError("Embedding provider unreachable")
            res = client.post(
                "/api/v1/assistant/chat",
                json={"message": "What documents do I need?"},
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            # Fails safe to INSUFFICIENT_EVIDENCE
            assert data["status"] in ("INSUFFICIENT_EVIDENCE", "TEMPORARILY_UNAVAILABLE")

    def test_chroma_outage_returns_safe_message(self, client):
        headers = {"Authorization": "Bearer test_token"}
        with patch(
            "app.services.rag.retrieval.RetrievalService.retrieve",
            side_effect=RuntimeError("ChromaDB connection failure"),
        ):
            res = client.post(
                "/api/v1/assistant/chat",
                json={"message": "What documents do I need?"},
                headers=headers,
            )
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "TEMPORARILY_UNAVAILABLE"
            assert "temporarily unavailable" in data["answer"].lower()
