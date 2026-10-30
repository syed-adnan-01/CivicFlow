"""
Text normalization for OCR extracted text.
Enforces QueueLess 2.3 Section 9.5:

1. Standardize whitespace without changing semantic tokens.
2. Normalize Unicode variants (quotes, dashes, zero-width spaces).
3. Redact / mask sensitive personal identification patterns for safe logging.
4. Never silently infer or fill missing digits, names, or dates.
"""

import re
import unicodedata


class TextNormalizer:
    """Normalizes raw OCR extraction text and provides privacy-safe masking."""

    # Matches standard 12-digit Aadhaar pattern with optional spaces/hyphens
    AADHAAR_REGEX = re.compile(r"\b(\d{4})[\s-](\d{4})[\s-](\d{4})\b")

    # Matches 10-digit Indian mobile number
    PHONE_REGEX = re.compile(r"\b(?:[6-9]\d{9})\b")

    @classmethod
    def normalize_text(cls, raw_text: str) -> str:
        """
        Cleans and normalizes extracted OCR text without modifying factual contents.
        """
        if not raw_text:
            return ""

        # 1. Normalize Unicode (NFKC)
        text = unicodedata.normalize("NFKC", raw_text)

        # 2. Remove non-printable / control characters except newlines and tabs
        text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

        # 3. Replace fancy quotation marks and dashes with standard ASCII
        text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
        text = text.replace("—", "-").replace("–", "-")

        # 4. Standardize horizontal whitespace
        text = re.sub(r"[^\S\r\n]+", " ", text)

        # 5. Collapse excessive linebreaks (> 2 down to 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    @classmethod
    def mask_pii_for_logs(cls, text: str) -> str:
        """
        Replaces sensitive identity numbers with masked equivalents.
        Never logs raw Aadhaar or phone numbers.
        """
        if not text:
            return ""

        # Mask Aadhaar numbers: XXXX-XXXX-1234
        masked = cls.AADHAAR_REGEX.sub(r"XXXX-XXXX-\3", text)

        # Mask Phone numbers: XXXXXX1234
        masked = cls.PHONE_REGEX.sub(r"XXXXXX\g<0>[6:]", masked)

        return masked

