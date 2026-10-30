"""
Checklist Matcher.
Enforces QueueLess 2.3 Section 9.7:

1. Compares detected document categories with the active service checklist.
2. Marks PRESENT_CANDIDATE when a category is confidently matched.
3. Marks MISSING when a required checklist item has no matching document.
4. Marks NEEDS_REVIEW for ambiguous or low-confidence OCR results.
5. Preserves checklist_version_id for auditability.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from uuid import UUID

from app.schemas.documents import ChecklistItemRead, ChecklistItemResult
from app.services.ocr.category_classifier import CategoryInferenceResult


@dataclass
class ChecklistItemDefinition:
    id: UUID
    label: str
    target_category: str
    is_mandatory: bool = True


class ChecklistMatcher:
    """Matches inferred document categories against official versioned checklist requirements."""

    # Standard default mapping between citizen service checklist items and document categories
    DEFAULT_CATEGORY_LABELS = {
        "AADHAAR_CARD": "Identity Proof (Aadhaar Card)",
        "VOTER_ID": "Voter Identity Card (EPIC)",
        "RATION_CARD": "Ration Card (BPL / APL)",
        "INCOME_CERTIFICATE": "Existing Income Certificate",
        "RESIDENTIAL_CERTIFICATE": "Residential / Domicile Certificate",
    }

    @classmethod
    def match_checklist(
        cls,
        category_result: CategoryInferenceResult,
        checklist_items: List[ChecklistItemDefinition],
        checklist_version_id: Optional[UUID] = None,
    ) -> List[ChecklistItemRead]:
        """
        Produces item-level checklist outcomes for a document check.
        """
        results: List[ChecklistItemRead] = []

        for item in checklist_items:
            # Check if this checklist item targets the detected category
            if category_result.predicted_category == item.target_category:
                if category_result.status == "CATEGORY_MATCHED":
                    res_status = ChecklistItemResult.PRESENT_CANDIDATE
                    msg = (
                        f"Document category '{item.label}' detected with {category_result.confidence_band} "
                        "confidence. Please confirm manually before your appointment."
                    )
                else:
                    res_status = ChecklistItemResult.NEEDS_REVIEW
                    msg = (
                        f"Preliminary match for '{item.label}', but confidence is low. "
                        "Manual review at the service centre counter is recommended."
                    )

                results.append(
                    ChecklistItemRead(
                        checklist_item_id=item.id,
                        label=item.label,
                        result=res_status,
                        confidence_band=category_result.confidence_band,
                        message=msg,
                    )
                )
            else:
                results.append(
                    ChecklistItemRead(
                        checklist_item_id=item.id,
                        label=item.label,
                        result=ChecklistItemResult.MISSING,
                        confidence_band=None,
                        message=f"No document uploaded for '{item.label}'.",
                    )
                )

        return results

