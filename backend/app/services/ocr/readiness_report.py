"""
Document Readiness Report Generator.
Enforces QueueLess 2.3 Section 9.7 & 9.8:

1. Produces preliminary item-level readiness reports.
2. Assigns overall status (READY_FOR_REVIEW | NEEDS_REVIEW | UNAVAILABLE).
3. Attaches standard non-negotiable citizen disclaimer.
4. Ensures failure never blocks booking or counter operations.
"""

from typing import List, Optional
from uuid import UUID

from app.schemas.documents import (
    ChecklistItemRead,
    ChecklistItemResult,
    DocumentCheckResult,
    ProcessingStatus,
)


class ReadinessReportGenerator:
    """Aggregates checklist item outcomes into an authoritative citizen readiness report."""

    DEFAULT_DISCLAIMER = (
        "Preliminary readiness check only. Confirm current requirements on the "
        "official service portal or with the relevant office. This check does not "
        "guarantee legal eligibility or application approval."
    )

    @classmethod
    def generate_report(
        cls,
        document_id: UUID,
        processing_status: str,
        items: List[ChecklistItemRead],
        checklist_version_id: Optional[UUID] = None,
    ) -> DocumentCheckResult:
        """
        Calculates overall readiness status and builds response schema.
        """
        if processing_status in (ProcessingStatus.UNAVAILABLE, ProcessingStatus.OCR_FAILED):
            return DocumentCheckResult(
                document_id=document_id,
                processing_status=processing_status,
                checklist_version_id=checklist_version_id,
                items=items,
                overall_status="UNAVAILABLE",
                disclaimer=cls.DEFAULT_DISCLAIMER,
            )

        # Check if all items are present candidate or confirmed
        all_ready = bool(
            items
            and all(
                item.result in (ChecklistItemResult.PRESENT_CANDIDATE, ChecklistItemResult.USER_CONFIRMED)
                for item in items
            )
        )

        overall = "READY_FOR_REVIEW" if all_ready else "NEEDS_REVIEW"

        return DocumentCheckResult(
            document_id=document_id,
            processing_status=processing_status,
            checklist_version_id=checklist_version_id,
            items=items,
            overall_status=overall,
            disclaimer=cls.DEFAULT_DISCLAIMER,
        )

