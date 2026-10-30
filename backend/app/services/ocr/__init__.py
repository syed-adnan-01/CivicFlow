"""
OCR and document readiness services package — public exports.
"""

from app.services.ocr.category_classifier import (
    CategoryClassifier,
    CategoryInferenceResult,
)
from app.services.ocr.checklist_matcher import (
    ChecklistItemDefinition,
    ChecklistMatcher,
)
from app.services.ocr.engine_adapter import (
    OCREngineAdapter,
    OCREngineError,
    OCREngineUnavailableError,
    OCRExtractionResult,
)
from app.services.ocr.file_safety import FileSafetyChecker, FileSafetyError
from app.services.ocr.file_validation import (
    FileValidationError,
    FileValidator,
    ValidatedFileInfo,
)
from app.services.ocr.paddle_engine import PaddleEngine
from app.services.ocr.readiness_report import ReadinessReportGenerator
from app.services.ocr.storage import PrivateStorage, StorageError
from app.services.ocr.tesseract_engine import TesseractEngine
from app.services.ocr.text_normalizer import TextNormalizer

__all__ = [
    "CategoryClassifier",
    "CategoryInferenceResult",
    "ChecklistItemDefinition",
    "ChecklistMatcher",
    "FileSafetyChecker",
    "FileSafetyError",
    "FileValidationError",
    "FileValidator",
    "OCREngineAdapter",
    "OCREngineError",
    "OCREngineUnavailableError",
    "OCRExtractionResult",
    "PaddleEngine",
    "PrivateStorage",
    "ReadinessReportGenerator",
    "StorageError",
    "TesseractEngine",
    "TextNormalizer",
    "ValidatedFileInfo",
]

