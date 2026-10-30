"""
Unit tests for Documents API endpoints (/api/v1/documents).
"""

import io
from unittest.mock import MagicMock, patch
import uuid
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.documents import (
    CitizenDocumentList,
    CitizenDocumentRead,
    DocumentCheckResult,
    DocumentDeleteResponse,
    DocumentUploadResponse,
)
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


def test_upload_document_endpoint_success(client):
    doc_id = uuid4()
    mock_upload_resp = DocumentUploadResponse(
        document_id=doc_id,
        processing_status="RECEIVED",
        file_name="aadhaar_sample.pdf",
        message="Upload received.",
    )

    with patch("app.modules.documents.service.DocumentService.upload_document", return_value=mock_upload_resp):
        pdf_bytes = b"%PDF-1.4 sample PDF bytes"
        files = {"file": ("aadhaar_sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {"service_id": str(uuid4())}

        res = client.post("/api/v1/documents/upload", files=files, data=data)
        assert res.status_code == 202
        body = res.json()
        assert body["document_id"] == str(doc_id)
        assert body["processing_status"] == "RECEIVED"


def test_list_citizen_documents_endpoint(client):
    doc_id = uuid4()
    from datetime import datetime, timezone
    mock_list_resp = CitizenDocumentList(
        items=[
            CitizenDocumentRead(
                document_id=doc_id,
                file_name="my_doc.pdf",
                service_id=uuid4(),
                processing_status="OCR_COMPLETE",
                created_at=datetime.now(timezone.utc),
            )
        ],
        total=1,
    )

    with patch("app.modules.documents.service.DocumentService.list_documents", return_value=mock_list_resp):
        res = client.get("/api/v1/documents")
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 1
        assert len(body["items"]) == 1


def test_get_check_result_endpoint(client):
    doc_id = uuid4()
    mock_check_resp = DocumentCheckResult(
        document_id=doc_id,
        processing_status="OCR_COMPLETE",
        items=[],
        overall_status="NEEDS_REVIEW",
        disclaimer="Preliminary check only.",
    )

    with patch("app.modules.documents.service.DocumentService.get_check_result", return_value=mock_check_resp):
        res = client.get(f"/api/v1/documents/{doc_id}/check-result")
        assert res.status_code == 200
        body = res.json()
        assert body["overall_status"] == "NEEDS_REVIEW"
        assert "disclaimer" in body


def test_delete_document_endpoint(client):
    doc_id = uuid4()
    mock_del_resp = DocumentDeleteResponse(
        document_id=doc_id,
        status="DELETED",
        message="Document deleted.",
    )

    with patch("app.modules.documents.service.DocumentService.delete_document", return_value=mock_del_resp):
        res = client.delete(f"/api/v1/documents/{doc_id}")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "DELETED"
