"""
Integration tests — document pipeline.
Tests upload → validation → OCR job → check result flow.
Uses synthetic test documents from tests/fixtures/synthetic_documents/.
"""

import pytest


class TestDocumentUploadValidation:
    def test_valid_pdf_upload_returns_202_with_document_id(self):
        pytest.skip("Implementation pending — Day 12")

    def test_invalid_extension_returns_422(self):
        pytest.skip("Implementation pending — Day 12")

    def test_oversized_file_returns_413(self):
        pytest.skip("Implementation pending — Day 12")

    def test_mime_spoofed_file_returns_422(self):
        pytest.skip("Implementation pending — Day 12")


class TestDocumentOwnership:
    def test_citizen_can_view_own_document_result(self):
        pytest.skip("Implementation pending — Day 12")

    def test_citizen_cannot_view_another_citizens_document(self):
        pytest.skip("Implementation pending — Day 12")

    def test_citizen_can_delete_own_document(self):
        pytest.skip("Implementation pending — Day 12")

    def test_citizen_cannot_delete_another_citizens_document(self):
        pytest.skip("Implementation pending — Day 12")


class TestOCRFailureBehavior:
    def test_ocr_failure_sets_processing_status_to_failed(self):
        pytest.skip("Implementation pending — Day 13")

    def test_ocr_failure_does_not_block_appointment_booking(self):
        # Core P0 journey must work even when OCR is unavailable
        pytest.skip("Implementation pending — Day 13")

    def test_citizen_can_manually_confirm_checklist_item_after_ocr_failure(self):
        pytest.skip("Implementation pending — Day 14")

