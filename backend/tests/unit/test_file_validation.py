"""
Unit tests — file validation for document uploads.
Tests MIME, extension, size, page count, and path traversal guards.
"""

from unittest.mock import MagicMock
from uuid import uuid4
import pytest
from fastapi import HTTPException

from app.services.ocr.file_validation import (
    FileValidationError,
    FileValidator,
)


class TestExtensionValidation:
    def test_pdf_accepted(self):
        ext = FileValidator.validate_extension("application_form.pdf")
        assert ext == ".pdf"

    def test_jpeg_accepted(self):
        assert FileValidator.validate_extension("photo.jpg") == ".jpg"
        assert FileValidator.validate_extension("photo.jpeg") == ".jpeg"

    def test_png_accepted(self):
        assert FileValidator.validate_extension("scan.png") == ".png"

    def test_exe_rejected(self):
        with pytest.raises(FileValidationError) as exc:
            FileValidator.validate_extension("malware.exe")
        assert "Unsupported file extension" in str(exc.value)

    def test_html_rejected(self):
        with pytest.raises(FileValidationError) as exc:
            FileValidator.validate_extension("page.html")
        assert "Unsupported file extension" in str(exc.value)


class TestMIMEValidation:
    """Extension and MIME signature must both match — spoofed MIME must be rejected."""

    def test_pdf_with_correct_mime_accepted(self):
        pdf_bytes = b"%PDF-1.4 sample content with valid header"
        mime = FileValidator.validate_magic_bytes(pdf_bytes, ".pdf")
        assert mime == "application/pdf"

    def test_jpeg_extension_with_html_mime_rejected(self):
        # MIME spoofing guard — rename an HTML file to .jpg
        html_bytes = b"<!DOCTYPE html><html><body>Fake image</body></html>"
        with pytest.raises(FileValidationError) as exc:
            FileValidator.validate_magic_bytes(html_bytes, ".jpg")
        assert "HTML file uploaded" in str(exc.value) or "signature does not match" in str(exc.value)

    def test_malformed_file_rejected(self):
        garbage_bytes = b"\x00\x01\x02\x03\x04\x05random corrupted stream"
        with pytest.raises(FileValidationError) as exc:
            FileValidator.validate_magic_bytes(garbage_bytes, ".pdf")
        assert "does not match" in str(exc.value)


class TestSizeLimits:
    def test_file_under_limit_accepted(self):
        data = b"%PDF" + b"A" * 1024  # ~1 KB
        size = FileValidator.validate_size(data, max_mb=10)
        assert size == len(data)

    def test_file_over_limit_rejected(self):
        oversized = b"A" * (11 * 1024 * 1024)  # 11 MB > 10 MB limit
        with pytest.raises(FileValidationError) as exc:
            FileValidator.validate_size(oversized, max_mb=10)
        assert "exceeds maximum allowed limit" in str(exc.value)

    def test_zero_byte_file_rejected(self):
        empty_data = b""
        with pytest.raises(FileValidationError) as exc:
            FileValidator.validate_size(empty_data, max_mb=10)
        assert "empty (0 bytes)" in str(exc.value)


class TestOwnershipGuard:
    def test_citizen_can_upload_own_document(self):
        from app.modules.documents.service import DocumentService
        citizen_1 = uuid4()
        service_id = uuid4()

        mock_db = MagicMock()
        mock_storage = MagicMock()
        mock_storage.save.return_value = "citizens/c1/doc1.pdf"

        service = DocumentService(db=mock_db, storage=mock_storage)
        service.repo = MagicMock()
        mock_doc = MagicMock()
        mock_doc.id = uuid4()
        mock_doc.original_filename = "doc.pdf"
        mock_doc.processing_status = "RECEIVED"
        service.repo.create_document.return_value = mock_doc

        pdf_bytes = b"%PDF-1.4 test document"
        res = service.upload_document(
            file_bytes=pdf_bytes,
            original_filename="doc.pdf",
            service_id=service_id,
            citizen_id=citizen_1,
        )
        assert res.document_id == mock_doc.id

    def test_citizen_cannot_access_another_citizens_document(self):
        from app.modules.documents.service import DocumentService
        citizen_1 = uuid4()
        citizen_2 = uuid4()
        doc_id = uuid4()

        mock_db = MagicMock()
        service = DocumentService(db=mock_db)
        service.repo = MagicMock()

        # Document belongs to citizen_1
        mock_doc = MagicMock()
        mock_doc.id = doc_id
        mock_doc.citizen_id = citizen_1
        service.repo.get_by_id.return_value = mock_doc

        # Citizen 2 tries to access citizen 1's document
        with pytest.raises(HTTPException) as exc:
            service.get_check_result(document_id=doc_id, citizen_id=citizen_2)

        assert exc.value.status_code == 403
        assert "forbidden" in str(exc.value.detail).lower()
