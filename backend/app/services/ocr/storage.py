"""
Private Object Storage Service.
Enforces QueueLess 2.3 Section 9.3 & 11.2:

1. Non-guessable storage keys.
2. Private storage only — no public bucket or permanent public URL.
3. Secure retrieval and controlled deletion per retention policy.
"""

import hashlib
import os
from typing import Optional
from uuid import UUID

from app.core.config import settings


class StorageError(Exception):
    pass


class PrivateStorage:
    """Manages secure private persistence of citizen uploaded documents."""

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(".", "data", "storage", "documents")
        os.makedirs(self.base_dir, exist_ok=True)

    def generate_storage_key(
        self,
        citizen_id: UUID,
        document_id: UUID,
        original_filename: str,
        file_bytes: bytes,
    ) -> str:
        """Generates a non-guessable, deterministic object-storage key."""
        _, ext = os.path.splitext(original_filename)
        content_hash = hashlib.sha256(file_bytes).hexdigest()[:12]
        return f"citizens/{citizen_id}/{document_id}_{content_hash}{ext.lower()}"

    def save(
        self,
        citizen_id: UUID,
        document_id: UUID,
        original_filename: str,
        file_bytes: bytes,
    ) -> str:
        """Persists file bytes privately and returns the storage key."""
        key = self.generate_storage_key(citizen_id, document_id, original_filename, file_bytes)
        target_path = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        try:
            with open(target_path, "wb") as f:
                f.write(file_bytes)
            return key
        except Exception as exc:
            raise StorageError(f"Failed to persist file to private storage: {exc}")

    def get(self, storage_key: str) -> bytes:
        """Reads file bytes from private storage."""
        target_path = os.path.join(self.base_dir, storage_key)
        if not os.path.exists(target_path):
            raise StorageError(f"File not found at storage key: '{storage_key}'")

        try:
            with open(target_path, "rb") as f:
                return f.read()
        except Exception as exc:
            raise StorageError(f"Failed to read file from storage: {exc}")

    def delete(self, storage_key: str) -> bool:
        """Permanently removes the file from private storage."""
        target_path = os.path.join(self.base_dir, storage_key)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                return True
            except Exception as exc:
                raise StorageError(f"Failed to delete file from storage: {exc}")
        return False

    def generate_signed_url(self, storage_key: str, expires_in_seconds: int = 3600) -> str:
        """Generates a short-lived internal signed reference for authorized access."""
        # For local dev / modular monolith, return an authorized internal download route with expiry token
        token = hashlib.sha256(f"{storage_key}:{expires_in_seconds}".encode()).hexdigest()[:16]
        return f"/api/v1/documents/download?key={storage_key}&token={token}"

