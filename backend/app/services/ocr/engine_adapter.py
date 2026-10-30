"""
Base interface and result contracts for OCR engine adapters.
Enforces QueueLess 2.3 Section 9.4:
Keep provider SDK calls behind adapters so the application is not coupled to a single vendor.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


class OCREngineError(Exception):
    """Raised when an OCR engine encounters an internal failure during extraction."""
    pass


class OCREngineUnavailableError(OCREngineError):
    """Raised when the configured OCR engine/binary is not installed or unreachable."""
    pass


@dataclass
class OCRExtractionResult:
    text: str
    confidence: float
    confidence_band: str  # HIGH | MEDIUM | LOW | UNKNOWN
    page_count: int
    engine: str
    engine_version: str
    language_packs: str = "eng"


class OCREngineAdapter(ABC):
    """Abstract base class for OCR extraction adapters."""

    @abstractmethod
    def extract_text(self, file_bytes: bytes, file_type: str) -> OCRExtractionResult:
        """
        Extracts text and confidence from the provided file binary.
        Must never invent text or fill missing digits.
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Returns True if the engine dependencies and binaries are ready."""
        ...

    @abstractmethod
    def engine_name(self) -> str:
        """Returns human-readable name of the engine."""
        ...

    @staticmethod
    def calculate_confidence_band(score: float) -> str:
        """Maps 0.0–1.0 score to standardized confidence band."""
        if score >= 0.80:
            return "HIGH"
        elif score >= 0.60:
            return "MEDIUM"
        elif score > 0.0:
            return "LOW"
        return "UNKNOWN"

