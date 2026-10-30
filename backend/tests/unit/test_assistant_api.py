"""
Unit tests for Assistant FastAPI router (/api/v1/assistant).
"""

from unittest.mock import MagicMock, patch
import uuid
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.assistant import AssistantChatResponse, CitationSchema
from app.common.dependencies import get_current_user
from app.models.user import User


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    mock_user = User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        firebase_uid="dev_citizen_uid",
        role="CITIZEN",
        is_active=True,
        display_name="Dev Citizen",
    )
    app.dependency_overrides[get_current_user] = lambda: mock_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


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
        assert data["answer"] == mock_resp.answer
        assert data["status"] == "ANSWERED"
        assert len(data["citations"]) == 1
        assert data["citations"][0]["chunk_id"] == "chunk_1"


def test_assistant_chat_validation_empty_message(client):
    payload = {
        "message": "",
        "language": "en",
    }
    res = client.post("/api/v1/assistant/chat", json=payload)
    # Pydantic schema enforces min_length=1 on message
    assert res.status_code == 422
