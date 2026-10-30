"""
Unit tests — file validation for document uploads.
Tests MIME, extension, size, page count, and path traversal guards.
"""

import pytest


class TestExtensionValidation:
    def test_pdf_accepted(self):
        pytest.skip("Implementation pending — Day 12")

    def test_jpeg_accepted(self):
        pytest.skip("Implementation pending — Day 12")

    def test_png_accepted(self):
        pytest.skip("Implementation pending — Day 12")

    def test_exe_rejected(self):
        pytest.skip("Implementation pending — Day 12")

    def test_html_rejected(self):
        pytest.skip("Implementation pending — Day 12")


class TestMIMEValidation:
    """Extension and MIME signature must both match — spoofed MIME must be rejected."""

    def test_pdf_with_correct_mime_accepted(self):
        pytest.skip("Implementation pending — Day 12")

    def test_jpeg_extension_with_html_mime_rejected(self):
        # MIME spoofing guard — rename an HTML file to .jpg
        pytest.skip("Implementation pending — Day 12")

    def test_malformed_file_rejected(self):
        pytest.skip("Implementation pending — Day 12")


class TestSizeLimits:
    def test_file_under_limit_accepted(self):
        pytest.skip("Implementation pending — Day 12")

    def test_file_over_limit_rejected(self):
        pytest.skip("Implementation pending — Day 12")

    def test_zero_byte_file_rejected(self):
        pytest.skip("Implementation pending — Day 12")


class TestOwnershipGuard:
    def test_citizen_can_upload_own_document(self):
        pytest.skip("Implementation pending — Day 12")

    def test_citizen_cannot_access_another_citizens_document(self):
        pytest.skip("Implementation pending — Day 12")

