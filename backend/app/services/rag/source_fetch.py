"""
Source fetcher for downloading official web pages or loading local document snapshots.
Enforces timeout, max-size limits, and safe error handling.
"""

import os
import logging
from typing import Tuple
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

# 10 MB maximum download size to prevent resource exhaustion
MAX_DOWNLOAD_BYTES = 10 * 1024 * 1024
DEFAULT_TIMEOUT_SECONDS = 15


class SourceFetchError(Exception):
    """Raised when fetching a source document fails."""
    pass


class SourceFetcher:
    """Safely retrieves document snapshots from remote URLs or local file paths."""

    @staticmethod
    def fetch_url(url: str, timeout: int = DEFAULT_TIMEOUT_SECONDS) -> Tuple[bytes, str]:
        """
        Fetches raw content from an HTTP/HTTPS URL.
        Returns: (content_bytes, content_type)
        """
        if not url.startswith(("http://", "https://")):
            raise SourceFetchError(f"Unsupported URL scheme: {url}")

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "QueueLess-Source-Verifier/1.0 (+https://queueless.gov.in)",
                "Accept": "text/html,application/pdf,application/xhtml+xml,text/plain",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content_type = response.headers.get_content_type() or "text/html"
                data = response.read(MAX_DOWNLOAD_BYTES + 1)
                if len(data) > MAX_DOWNLOAD_BYTES:
                    raise SourceFetchError(f"Source exceeds maximum allowed size of {MAX_DOWNLOAD_BYTES} bytes.")
                return data, content_type
        except urllib.error.HTTPError as exc:
            logger.error("HTTP error fetching %s: %s", url, exc.code)
            raise SourceFetchError(f"HTTP {exc.code} fetching official source.") from exc
        except urllib.error.URLError as exc:
            logger.error("Network error fetching %s: %s", url, exc.reason)
            raise SourceFetchError("Unable to reach official source endpoint.") from exc
        except Exception as exc:
            logger.error("Unexpected error fetching %s: %s", url, type(exc).__name__)
            raise SourceFetchError(f"Error fetching source: {type(exc).__name__}") from exc

    @staticmethod
    def read_local_file(file_path: str) -> Tuple[bytes, str]:
        """Reads a local snapshot file for offline testing or manual ingestion."""
        if not os.path.exists(file_path):
            raise SourceFetchError(f"Local source file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        content_type = "application/pdf" if ext == ".pdf" else "text/html"

        try:
            with open(file_path, "rb") as f:
                data = f.read(MAX_DOWNLOAD_BYTES + 1)
                if len(data) > MAX_DOWNLOAD_BYTES:
                    raise SourceFetchError("Local file exceeds maximum allowed size.")
                return data, content_type
        except Exception as exc:
            raise SourceFetchError(f"Failed to read local snapshot: {exc}") from exc

