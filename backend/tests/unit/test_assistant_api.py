"""
Unit tests for Assistant FastAPI router (/api/v1/assistant).
"""

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.assistant import AssistantChatResponse, CitationSchema


@pytest.fixture
def client():
    return TestClient(app)


def test_assistant_health_endpoint(client):
    response = client.get("/api/v1/assistant/health")
    assert response.status_code == 200
    data = response.json()
    assert "llm_configured" in data
    assert "embedding_configured" in data
    assert "vector_store_reachable" in data
    assert data["status"] in ("healthy", "degraded", "unavailable")


def test_assistant_chat_endpoint_success(client):
    from uuid import uuid4

    mock_resp = AssistantChatResponse(
        answer="Applicants must provide Aadhaar card [1].",
        status="ANSWERED",
        language="en",
        citations=[
            CitationSchema(
                chunk_id="chunk_1",
                title="Nadakacheri Guide",
                authority="Revenue Dept",
                url="https://nadakacheri.karnataka.gov.in",
                page_number=1,
                retrieved_at="2026-10-30T00:00:00Z",
                last_checked_at="2026-10-30T00:00:00Z",
            )
        ],
        limitations=["Verified source excerpt."],
        request_id=uuid4(),
    )

    with patch("app.modules.assistant.service.AssistantService.answer", return_value=mock_resp):
        payload = {
            "message": "What documents do I need?",
            "language": "en",
        }
        res = client.post("/api/v1/assistant/chat", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ANSWERED"
        assert len(data["citations"]) == 1
        assert data["citations"][0]["chunk_id"] == "chunk_1"
        assert data["citations"][0]["url"] == "https://nadakacheri.karnataka.gov.in"


def test_assistant_chat_validation_empty_message(client):
    payload = {
        "message": "",
        "language": "en",
    }
    res = client.post("/api/v1/assistant/chat", json=payload)
    # Pydantic schema enforces min_length=1 on message
    assert res.status_code == 422

