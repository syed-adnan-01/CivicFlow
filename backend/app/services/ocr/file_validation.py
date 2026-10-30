"""
File validation for document uploads.
Enforces QueueLess 2.3 Section 9.3:

1. Allowed file types: PDF, JPEG, PNG.
2. Magic bytes / MIME signature verification (guards against MIME spoofing).
3. Size limits (enforces maximum size, rejects zero-byte files).
4. Path traversal and unsafe filename guards.
"""

import os
import re
from dataclasses import dataclass
from typing import Dict, Set


class FileValidationError(Exception):
    """Raised when an uploaded file fails validation."""
    pass


@dataclass
class ValidatedFileInfo:
    filename: str
    extension: str
    mime_type: str
    size_bytes: int


class FileValidator:
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".jpg", ".jpeg", ".png"}

    # Magic byte signatures
    MAGIC_SIGNATURES: Dict[str, bytes] = {
        "pdf": b"%PDF",
        "jpeg": b"\xff\xd8\xff",
        "png": b"\x89PNG\r\n\x1a\n",
    }

    MIME_TYPES: Dict[str, str] = {
        "pdf": "application/pdf",
        "jpeg": "image/jpeg",
        "png": "image/png",
    }

    DEFAULT_MAX_MB = 10
    DEFAULT_MAX_PAGES = 10

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Removes directory traversal sequences and unsafe characters."""
        if not filename:
            raise FileValidationError("Filename cannot be empty.")
        # Strip directory paths
        base = os.path.basename(filename).replace("\\", "/").split("/")[-1]
        # Remove any path traversal sequences
        safe = re.sub(r"\.\.+", "", base).strip()
        # Remove dangerous or non-printable characters
        safe = re.sub(r"[^\w\.\-\s]", "_", safe)
        if not safe or safe.startswith("."):
            raise FileValidationError(f"Invalid or unsafe filename: '{filename}'")
        return safe

    @classmethod
    def validate_extension(cls, filename: str) -> str:
        """Validates that the file has an allowed extension (.pdf, .jpg, .jpeg, .png)."""
        safe_name = cls.sanitize_filename(filename)
        _, ext = os.path.splitext(safe_name)
        ext = ext.lower()
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise FileValidationError(
                f"Unsupported file extension '{ext}'. Only PDF, JPEG, and PNG files are accepted."
            )
        return ext

    @classmethod
    def validate_size(cls, file_bytes: bytes, max_mb: int = DEFAULT_MAX_MB) -> int:
        """Enforces that file is non-empty and does not exceed max size limit."""
        size = len(file_bytes)
        if size == 0:
            raise FileValidationError("Uploaded file is empty (0 bytes).")
        max_bytes = max_mb * 1024 * 1024
        if size > max_bytes:
            raise FileValidationError(
                f"File size ({size / (1024 * 1024):.2f} MB) exceeds maximum allowed limit of {max_mb} MB."
            )
        return size

    @classmethod
    def validate_magic_bytes(cls, file_bytes: bytes, extension: str) -> str:
        """
        Validates actual file header bytes against the claimed extension.
        Rejects MIME spoofing (e.g. an HTML or EXE file renamed to .jpg or .pdf).
        """
        ext = extension.lower().lstrip(".")
        normalized_ext = "jpeg" if ext in ("jpg", "jpeg") else ext

        if normalized_ext not in cls.MAGIC_SIGNATURES:
            raise FileValidationError(f"Unsupported file format for signature verification: '{ext}'")

        expected_sig = cls.MAGIC_SIGNATURES[normalized_ext]

        # Check executable signatures
        if file_bytes.startswith(b"MZ") or file_bytes.startswith(b"\x7fELF"):
            raise FileValidationError("Executable file rejected.")

        # Check HTML signatures in non-HTML uploads
        if file_bytes.lstrip()[:15].lower().startswith((b"<!doctype html", b"<html", b"<head")):
            raise FileValidationError("HTML file uploaded under image or PDF extension; rejected.")

        if not file_bytes.startswith(expected_sig):
            raise FileValidationError(
                f"File content signature does not match the claimed .{ext} extension."
            )

        return cls.MIME_TYPES[normalized_ext]

    @classmethod
    def validate_upload(
        cls,
        filename: str,
        file_bytes: bytes,
        max_mb: int = DEFAULT_MAX_MB,
    ) -> ValidatedFileInfo:
        """Runs the complete suite of file validation checks."""
        safe_name = cls.sanitize_filename(filename)
        ext = cls.validate_extension(safe_name)
        size = cls.validate_size(file_bytes, max_mb=max_mb)
        mime = cls.validate_magic_bytes(file_bytes, ext)
        return ValidatedFileInfo(
            filename=safe_name,
            extension=ext,
            mime_type=mime,
            size_bytes=size,
        )

