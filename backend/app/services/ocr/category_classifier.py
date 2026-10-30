"""
Document Category Inference Classifier.
Enforces QueueLess 2.3 Section 9.6:

1. Small explicit set of supported categories matching official service checklists.
2. Confidence score and band calculation.
3. Privacy: records evidence signals as non-sensitive labels, never PII.
4. If score < threshold, categorizes as NEEDS_REVIEW without blocking citizen.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CategoryInferenceResult:
    predicted_category: Optional[str]
    confidence: float
    confidence_band: str  # HIGH | MEDIUM | LOW | UNKNOWN
    signals: List[str] = field(default_factory=list)
    status: str = "NEEDS_REVIEW"  # CATEGORY_MATCHED | NEEDS_REVIEW


class CategoryClassifier:
    """Classifies normalized document text into supported citizen checklist categories."""

    CONFIDENCE_THRESHOLD = 0.70

    # Explicit signal patterns for supported categories
    CATEGORY_PATTERNS: Dict[str, Dict[str, any]] = {
        "AADHAAR_CARD": {
            "required_signals": [
                r"\b(aadhaar|uidai|unique\s+identification|mera\s+aadhaar|government\s+of\s+india)\b",
            ],
            "secondary_signals": [
                r"\b(enrollment|enrolment\s+no|vid\b|male|female|dob\b|year\s+of\s+birth)\b",
                r"\b\d{4}\s+\d{4}\s+\d{4}\b",
            ],
            "weight": 0.5,
        },
        "VOTER_ID": {
            "required_signals": [
                r"\b(election\s+commission\s+of\s+india|elector\s+photo\s+identity|epic\s+no)\b",
            ],
            "secondary_signals": [
                r"\b(elector|constituency|polling\s+station|vidhan\s+sabha|lok\s+sabha)\b",
                r"\b[A-Z]{3}[0-9]{7}\b",
            ],
            "weight": 0.5,
        },
        "RATION_CARD": {
            "required_signals": [
                r"\b(food\s+and\s+civil\s+supplies|ahara|ration\s+card|bpl|apl|antyodaya)\b",
            ],
            "secondary_signals": [
                r"\b(fair\s+price\s+shop|fps|card\s+holder|head\s+of\s+family|family\s+members)\b",
            ],
            "weight": 0.5,
        },
        "INCOME_CERTIFICATE": {
            "required_signals": [
                r"\b(income\s+certificate|nadakacheri|revenue\s+department|tahasildar|tahsildar)\b",
            ],
            "secondary_signals": [
                r"\b(annual\s+income|gross\s+income|rupees|ajk|rd\d{10,})\b",
            ],
            "weight": 0.5,
        },
        "RESIDENTIAL_CERTIFICATE": {
            "required_signals": [
                r"\b(residence\s+certificate|domicile\s+certificate|residential\s+proof)\b",
            ],
            "secondary_signals": [
                r"\b(residing\s+at|period\s+of\s+stay|native\s+of|tahasildar)\b",
            ],
            "weight": 0.5,
        },
    }

    @classmethod
    def classify(cls, normalized_text: str) -> CategoryInferenceResult:
        """
        Infers document category based on keyword signals.
        Returns confidence score, band, signals, and matched status.
        """
        if not normalized_text or not normalized_text.strip():
            return CategoryInferenceResult(
                predicted_category=None,
                confidence=0.0,
                confidence_band="UNKNOWN",
                signals=[],
                status="NEEDS_REVIEW",
            )

        text_lower = normalized_text.lower()
        best_category: Optional[str] = None
        best_score = 0.0
        best_signals: List[str] = []

        for category, config in cls.CATEGORY_PATTERNS.items():
            score = 0.0
            signals: List[str] = []

            # Check primary required signals
            for pat in config["required_signals"]:
                matches = re.findall(pat, text_lower)
                if matches:
                    score += 0.50
                    for m in matches:
                        sig = m if isinstance(m, str) else m[0]
                        sig_label = f"primary_signal:{sig}"
                        if sig_label not in signals:
                            signals.append(sig_label)

            # Check secondary signals
            for pat in config["secondary_signals"]:
                matches = re.findall(pat, text_lower)
                if matches:
                    score += 0.25
                    for m in matches:
                        sig = m if isinstance(m, str) else m[0]
                        sig_label = f"secondary_signal:{sig}"
                        if sig_label not in signals:
                            signals.append(sig_label)

            score = min(1.0, score)

            if score > best_score:
                best_score = score
                best_category = category
                best_signals = signals

        # Confidence band calculation
        if best_score >= 0.80:
            band = "HIGH"
        elif best_score >= 0.60:
            band = "MEDIUM"
        elif best_score > 0.0:
            band = "LOW"
        else:
            band = "UNKNOWN"

        is_matched = (best_score >= cls.CONFIDENCE_THRESHOLD)
        status = "CATEGORY_MATCHED" if is_matched else "NEEDS_REVIEW"

        return CategoryInferenceResult(
            predicted_category=best_category if best_score > 0.0 else None,
            confidence=round(best_score, 2),
            confidence_band=band,
            signals=best_signals,
            status=status,
        )
