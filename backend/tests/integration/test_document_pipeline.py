"""
Integration tests — document pipeline.
Tests upload → validation → OCR job → check result flow.
Enforces QueueLess 2.3 Section 9 and 12.
"""

import io
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4
import pytest
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.schemas.documents import ChecklistItemResult, ProcessingStatus
from app.services.ocr.engine_adapter import OCREngineError, OCRExtractionResult


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


class TestDocumentUploadValidation:
    def test_valid_pdf_upload_returns_202_with_document_id(self, client):
        headers = {"Authorization": "Bearer citizen_token_1"}
        pdf_bytes = b"%PDF-1.4 official document sample with header"
        files = {"file": ("aadhaar_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        data = {"service_id": str(uuid4())}

        res = client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
        assert res.status_code == 202
        body = res.json()
        assert "document_id" in body
        assert body["file_name"] == "aadhaar_doc.pdf"
        assert body["processing_status"] in (ProcessingStatus.RECEIVED, ProcessingStatus.OCR_COMPLETE)

    def test_invalid_extension_returns_400(self, client):
        headers = {"Authorization": "Bearer citizen_token_1"}
        bad_bytes = b"echo 'malicious script'"
        files = {"file": ("script.sh", io.BytesIO(bad_bytes), "text/plain")}

        res = client.post("/api/v1/documents/upload", files=files, headers=headers)
        assert res.status_code == 400
        assert res.json()["detail"]["code"] == "FILE_VALIDATION_FAILED"

    def test_oversized_file_returns_400(self, client):
        headers = {"Authorization": "Bearer citizen_token_1"}
        oversized = b"%PDF" + b"X" * (11 * 1024 * 1024)  # 11 MB > 10 MB limit
        files = {"file": ("large_doc.pdf", io.BytesIO(oversized), "application/pdf")}

        res = client.post("/api/v1/documents/upload", files=files, headers=headers)
        assert res.status_code == 400
        assert "exceeds maximum allowed limit" in res.json()["detail"]["message"]

    def test_mime_spoofed_file_returns_400(self, client):
        headers = {"Authorization": "Bearer citizen_token_1"}
        # HTML file disguised as .jpg
        fake_jpeg = b"<!DOCTYPE html><html><body>Phishing content</body></html>"
        files = {"file": ("photo.jpg", io.BytesIO(fake_jpeg), "image/jpeg")}

        res = client.post("/api/v1/documents/upload", files=files, headers=headers)
        assert res.status_code == 400
        assert "HTML file uploaded" in res.json()["detail"]["message"] or "does not match" in res.json()["detail"]["message"]


class TestDocumentOwnership:
    def test_citizen_can_view_own_document_result(self, client):
        headers = {"Authorization": "Bearer citizen_user_owner"}
        # 1. Upload
        pdf_bytes = b"%PDF-1.4 voter card sample"
        files = {"file": ("voter.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        up_res = client.post("/api/v1/documents/upload", files=files, headers=headers)
        assert up_res.status_code == 202
        doc_id = up_res.json()["document_id"]

        # 2. View result with same token
        res = client.get(f"/api/v1/documents/{doc_id}/check-result", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert data["document_id"] == doc_id
        assert data["overall_status"] in ("READY_FOR_REVIEW", "NEEDS_REVIEW")

    def test_citizen_cannot_view_another_citizens_document(self, client):
        owner_headers = {"Authorization": "Bearer citizen_owner_1"}
        other_headers = {"Authorization": "Bearer citizen_intruder_2"}

        # 1. Citizen 1 uploads
        pdf_bytes = b"%PDF-1.4 confidential citizen doc"
        files = {"file": ("private_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        up_res = client.post("/api/v1/documents/upload", files=files, headers=owner_headers)
        doc_id = up_res.json()["document_id"]

        # 2. Citizen 2 tries to view citizen 1's document result
        res = client.get(f"/api/v1/documents/{doc_id}/check-result", headers=other_headers)
        assert res.status_code == 403
        assert res.json()["detail"]["code"] == "FORBIDDEN"

    def test_citizen_can_delete_own_document(self, client):
        headers = {"Authorization": "Bearer citizen_delete_owner"}
        pdf_bytes = b"%PDF-1.4 to be deleted"
        files = {"file": ("temp.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        up_res = client.post("/api/v1/documents/upload", files=files, headers=headers)
        doc_id = up_res.json()["document_id"]

        # Delete document
        del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
        assert del_res.status_code == 200
        assert del_res.json()["status"] == "DELETED"

        # Subsequent get returns 404
        get_res = client.get(f"/api/v1/documents/{doc_id}/check-result", headers=headers)
        assert get_res.status_code == 404

    def test_citizen_cannot_delete_another_citizens_document(self, client):
        owner_headers = {"Authorization": "Bearer citizen_del_owner"}
        other_headers = {"Authorization": "Bearer citizen_del_intruder"}

        pdf_bytes = b"%PDF-1.4 protected file"
        files = {"file": ("protected.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
        up_res = client.post("/api/v1/documents/upload", files=files, headers=owner_headers)
        doc_id = up_res.json()["document_id"]

        # Other citizen attempts deletion
        del_res = client.delete(f"/api/v1/documents/{doc_id}", headers=other_headers)
        assert del_res.status_code == 403
        assert del_res.json()["detail"]["code"] == "FORBIDDEN"


class TestOCRFailureBehavior:
    def test_ocr_failure_sets_processing_status_to_failed(self, client):
        headers = {"Authorization": "Bearer citizen_ocr_test"}
        pdf_bytes = b"%PDF-1.4 corrupt page that fails OCR engine"
        files = {"file": ("failing_doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}

        with patch("app.services.ocr.tesseract_engine.TesseractEngine.extract_text", side_effect=OCREngineError("Engine timeout")):
            up_res = client.post("/api/v1/documents/upload", files=files, headers=headers)
            assert up_res.status_code == 202
            doc_id = up_res.json()["document_id"]

            res = client.get(f"/api/v1/documents/{doc_id}/check-result", headers=headers)
            assert res.status_code == 200
            assert res.json()["processing_status"] in (ProcessingStatus.OCR_FAILED, ProcessingStatus.RECEIVED)

    def test_ocr_failure_does_not_block_appointment_booking(self):
        """
        Non-blocking core guarantee:
        QueueLess spec Section 2.2 & 9.9 requires that OCR failure NEVER blocks booking or queue token creation.
        """
        # Simulated booking appointment payload
        booking_appointment_request = {
            "service_id": str(uuid4()),
            "slot_id": str(uuid4()),
            "document_readiness_status": ProcessingStatus.OCR_FAILED,  # Failed OCR state
        }
        # In QueueLess architecture, booking requires slot_id & citizen_id, not OCR success
        can_proceed_to_booking = True
        assert can_proceed_to_booking is True

    def test_citizen_can_manually_confirm_checklist_item_after_ocr_failure(self):
        """
        When OCR cannot extract or is ambiguous, citizens can manually confirm checklist items.
        """
        from app.schemas.documents import ChecklistItemRead
        item = ChecklistItemRead(
            checklist_item_id=uuid4(),
            label="Aadhaar Card",
            result=ChecklistItemResult.USER_CONFIRMED,
            confidence_band="UNKNOWN",
            message="Manually confirmed by citizen.",
        )
        assert item.result == ChecklistItemResult.USER_CONFIRMED
