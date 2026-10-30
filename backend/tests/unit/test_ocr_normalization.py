"""
Unit tests for OCR text normalization and category classification.
"""

from app.services.ocr.category_classifier import CategoryClassifier
from app.services.ocr.text_normalizer import TextNormalizer


class TestTextNormalization:
    def test_whitespace_and_unicode_normalization(self):
        raw = "GOVERNMENT   OF  INDIA\n\n\n\n“Aadhaar” — Unique   Identification\r\n\tCard"
        normalized = TextNormalizer.normalize_text(raw)

        # Standard ASCII quotes, collapsed whitespace, max 2 consecutive newlines
        assert "“" not in normalized
        assert '"' in normalized
        assert "   " not in normalized
        assert "\n\n\n" not in normalized
        assert "GOVERNMENT OF INDIA" in normalized

    def test_pii_masking_for_logs(self):
        text_with_aadhaar = "Resident Aadhaar: 1234 5678 9012, verified at counter."
        masked = TextNormalizer.mask_pii_for_logs(text_with_aadhaar)

        assert "1234 5678" not in masked
        assert "XXXX-XXXX-9012" in masked


class TestCategoryClassification:
    def test_aadhaar_card_classification(self):
        text = (
            "Government of India\n"
            "Unique Identification Authority of India (UIDAI)\n"
            "Mera Aadhaar, Meri Pehchan\n"
            "DOB: 01/01/1990\n"
            "1234 5678 9012"
        )
        result = CategoryClassifier.classify(text)

        assert result.predicted_category == "AADHAAR_CARD"
        assert result.confidence >= 0.70
        assert result.confidence_band in ("HIGH", "MEDIUM")
        assert result.status == "CATEGORY_MATCHED"
        assert any("aadhaar" in s.lower() for s in result.signals)

    def test_voter_id_classification(self):
        text = (
            "ELECTION COMMISSION OF INDIA\n"
            "ELECTOR PHOTO IDENTITY CARD - EPIC NO: ABC1234567\n"
            "Elector Name: Citizen Sample\n"
            "Constituency: 154 - Rajajinagar"
        )
        result = CategoryClassifier.classify(text)

        assert result.predicted_category == "VOTER_ID"
        assert result.confidence >= 0.70
        assert result.status == "CATEGORY_MATCHED"

    def test_unreadable_or_ambiguous_text_becomes_needs_review(self):
        noisy_text = "Some random blurred page 1234 ?? xyz receipt counter"
        result = CategoryClassifier.classify(noisy_text)

        assert result.status == "NEEDS_REVIEW"
        assert result.confidence < 0.70

