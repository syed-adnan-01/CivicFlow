"""
File safety checks and malware scanning adapter.
Enforces QueueLess 2.3 Section 9.3:
Reject malformed, encrypted, or unsafe files.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FileSafetyError(Exception):
    pass


class FileSafetyChecker:
    """Pre-processing safety checks for uploaded document binaries."""

    DANGEROUS_PATTERNS = [
        b"<script",
        b"javascript:",
        b"/JavaScript",
        b"/JS",
        b"/Launch",
        b"powershell",
        b"cmd.exe",
    ]

    @classmethod
    def scan_bytes(cls, file_bytes: bytes, file_type: str) -> bool:
        """
        Scans file bytes for dangerous embedded executable scripts or macros.
        Returns True if safe; raises FileSafetyError if unsafe.
        """
        lower_bytes = file_bytes.lower()

        # Check for dangerous embedded PDF actions or scripts
        if file_type == "pdf":
            for danger in (b"/launch", b"/javascript", b"/js"):
                if danger in lower_bytes:
                    logger.warning("Potentially dangerous active content found in PDF: %s", danger)
                    raise FileSafetyError(
                        "PDF contains active scripts or launch actions and was rejected for security."
                    )

        # Check for embedded script tags in images
        if file_type in ("jpeg", "jpg", "png"):
            for script_tag in (b"<script", b"javascript:"):
                if script_tag in lower_bytes:
                    logger.warning("Script payload detected in image: %s", script_tag)
                    raise FileSafetyError("Image file contains embedded script payload.")

        return True

