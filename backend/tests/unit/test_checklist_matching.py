"""
Unit tests for Checklist Matching and Readiness Report Generation.
"""

from uuid import uuid4
import pytest

from app.schemas.documents import ChecklistItemResult, ProcessingStatus
from app.services.ocr.category_classifier import CategoryInferenceResult
from app.services.ocr.checklist_matcher import ChecklistItemDefinition, ChecklistMatcher
from app.services.ocr.readiness_report import ReadinessReportGenerator


@pytest.fixture
def sample_checklist():
    return [
        ChecklistItemDefinition(
            id=uuid4(),
            label="Identity Proof (Aadhaar Card)",
            target_category="AADHAAR_CARD",
            is_mandatory=True,
        ),
        ChecklistItemDefinition(
            id=uuid4(),
            label="Residential / Domicile Certificate",
            target_category="RESIDENTIAL_CERTIFICATE",
            is_mandatory=True,
        ),
    ]


class TestChecklistMatching:
    def test_confidently_matched_category_marked_present_candidate(self, sample_checklist):
        cat_result = CategoryInferenceResult(
            predicted_category="AADHAAR_CARD",
            confidence=0.90,
            confidence_band="HIGH",
            signals=["primary_signal:aadhaar"],
            status="CATEGORY_MATCHED",
        )

        matched = ChecklistMatcher.match_checklist(
            category_result=cat_result,
            checklist_items=sample_checklist,
        )

        assert len(matched) == 2
        aadhaar_item = next(i for i in matched if "Aadhaar" in i.label)
        residence_item = next(i for i in matched if "Residential" in i.label)

        assert aadhaar_item.result == ChecklistItemResult.PRESENT_CANDIDATE
        assert aadhaar_item.confidence_band == "HIGH"
        assert residence_item.result == ChecklistItemResult.MISSING

    def test_low_confidence_category_marked_needs_review(self, sample_checklist):
        cat_result = CategoryInferenceResult(
            predicted_category="AADHAAR_CARD",
            confidence=0.55,
            confidence_band="LOW",
            signals=["secondary_signal:dob"],
            status="NEEDS_REVIEW",
        )

        matched = ChecklistMatcher.match_checklist(
            category_result=cat_result,
            checklist_items=sample_checklist,
        )

        aadhaar_item = next(i for i in matched if "Aadhaar" in i.label)
        assert aadhaar_item.result == ChecklistItemResult.NEEDS_REVIEW


class TestReadinessReport:
    def test_overall_status_needs_review_when_items_missing(self, sample_checklist):
        cat_result = CategoryInferenceResult(
            predicted_category="AADHAAR_CARD",
            confidence=0.90,
            confidence_band="HIGH",
            status="CATEGORY_MATCHED",
        )
        items = ChecklistMatcher.match_checklist(cat_result, sample_checklist)

        doc_id = uuid4()
        report = ReadinessReportGenerator.generate_report(
            document_id=doc_id,
            processing_status=ProcessingStatus.OCR_COMPLETE,
            items=items,
        )

        assert report.overall_status == "NEEDS_REVIEW"
        assert "Preliminary readiness check only" in report.disclaimer

    def test_ocr_failure_yields_unavailable_status(self):
        doc_id = uuid4()
        report = ReadinessReportGenerator.generate_report(
            document_id=doc_id,
            processing_status=ProcessingStatus.OCR_FAILED,
            items=[],
        )

        assert report.overall_status == "UNAVAILABLE"
        assert report.processing_status == ProcessingStatus.OCR_FAILED

