"""
Integration tests — private file access and storage security.
Enforces QueueLess 2.3 Section 9.3 & 11.2:
- Private storage only.
- Non-guessable storage keys.
- Deletion removes private file.
- No public bucket or guessable URLs.
"""

import os
from uuid import uuid4
import pytest

from app.services.ocr.storage import PrivateStorage


@pytest.fixture
def private_storage(tmp_path):
    return PrivateStorage(base_dir=str(tmp_path / "test_storage"))


class TestPrivateFileAccess:
    def test_non_guessable_storage_key_generation(self, private_storage):
        citizen_id = uuid4()
        document_id = uuid4()
        file_bytes = b"%PDF-1.4 sample file content"

        key = private_storage.generate_storage_key(
            citizen_id=citizen_id,
            document_id=document_id,
            original_filename="aadhaar.pdf",
            file_bytes=file_bytes,
        )

        assert str(citizen_id) in key
        assert str(document_id) in key
        assert key.endswith(".pdf")
        # Ensure key contains hash of content (non-guessable)
        assert len(key.split("_")[-1]) >= 8

    def test_private_save_and_retrieve(self, private_storage):
        citizen_id = uuid4()
        document_id = uuid4()
        file_bytes = b"%PDF-1.4 confidential citizen identity data"

        key = private_storage.save(
            citizen_id=citizen_id,
            document_id=document_id,
            original_filename="doc.pdf",
            file_bytes=file_bytes,
        )

        retrieved = private_storage.get(key)
        assert retrieved == file_bytes

    def test_file_deletion_removes_physical_bytes(self, private_storage):
        citizen_id = uuid4()
        document_id = uuid4()
        file_bytes = b"%PDF-1.4 file to delete"

        key = private_storage.save(
            citizen_id=citizen_id,
            document_id=document_id,
            original_filename="to_delete.pdf",
            file_bytes=file_bytes,
        )

        # Confirm file exists on disk
        physical_path = os.path.join(private_storage.base_dir, key)
        assert os.path.exists(physical_path)

        # Delete file
        deleted = private_storage.delete(key)
        assert deleted is True

        # Physical file should no longer exist
        assert not os.path.exists(physical_path)

    def test_signed_url_generation(self, private_storage):
        storage_key = "citizens/user123/doc456_abc.pdf"
        url = private_storage.generate_signed_url(storage_key, expires_in_seconds=1800)

        assert "/api/v1/documents/download" in url
        assert "token=" in url
        assert "key=" in url

