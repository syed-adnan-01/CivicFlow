"""
Unit tests — RAG source governance.
Tests source state transitions, scope filtering, and active-source exclusion.
Run with: pytest tests/unit/test_source_governance.py
"""

from uuid import uuid4
import pytest

from app.schemas.knowledge_document import VerificationStatus
from app.services.rag.source_governance import (
    SourceGovernance,
    SourceGovernanceError,
    SourceScopeError,
)


class TestSourceStateFiltering:
    """Only VERIFIED + active sources should be used in retrieval."""

    def test_unverified_source_excluded_from_retrieval(self):
        # UNVERIFIED source must never be retrievable
        assert SourceGovernance.is_source_retrievable(VerificationStatus.UNVERIFIED, active=True) is False
        assert SourceGovernance.is_source_retrievable(VerificationStatus.UNVERIFIED, active=False) is False

    def test_stale_source_excluded_from_retrieval(self):
        # STALE source must never be retrievable
        assert SourceGovernance.is_source_retrievable(VerificationStatus.STALE, active=True) is False
        assert SourceGovernance.is_source_retrievable(VerificationStatus.STALE, active=False) is False

    def test_inactive_source_excluded_from_retrieval(self):
        # INACTIVE source must never be retrievable
        assert SourceGovernance.is_source_retrievable(VerificationStatus.INACTIVE, active=False) is False

    def test_verified_active_source_included_in_retrieval(self):
        # Only VERIFIED and active=True can be retrieved
        assert SourceGovernance.is_source_retrievable(VerificationStatus.VERIFIED, active=True) is True

    def test_verified_inactive_source_excluded_from_retrieval(self):
        # A VERIFIED source that was deactivated (active=False) must not be retrieved
        assert SourceGovernance.is_source_retrievable(VerificationStatus.VERIFIED, active=False) is False


class TestSourceScopeFiltering:
    """Sources must be scoped to the exact service being queried."""

    def test_source_with_matching_service_allowed(self):
        scope = "Karnataka Revenue Department — Caste Certificate"
        assert SourceGovernance.validate_service_scope_compatibility(scope, "Caste Certificate") is True

    def test_psi_training_source_not_used_for_income_certificate(self):
        # Critical Demo Restriction (Section 7.3):
        # PSI Training notice must NEVER answer Income Certificate questions.
        psi_scope = "Directorate of Minorities — PSI Training Document Verification Notice (6 Oct 2020)"
        is_valid = SourceGovernance.validate_service_scope_compatibility(
            source_scope=psi_scope,
            requested_service_name="Income Certificate Application",
        )
        assert is_valid is False

    def test_psi_training_source_allowed_for_psi_training(self):
        psi_scope = "Directorate of Minorities — PSI Training Document Verification Notice (6 Oct 2020)"
        is_valid = SourceGovernance.validate_service_scope_compatibility(
            source_scope=psi_scope,
            requested_service_name="PSI Training Verification",
        )
        assert is_valid is True


class TestSourceVerificationWorkflow:
    """Source must remain UNVERIFIED until manually marked VERIFIED with reviewer metadata."""

    def test_cannot_mark_verified_without_reviewer_id(self):
        with pytest.raises(SourceGovernanceError, match="reviewer ID"):
            SourceGovernance.validate_verification_transition(
                current_status=VerificationStatus.UNVERIFIED,
                new_status=VerificationStatus.VERIFIED,
                reviewer_id=None,
                review_notes="Checked the official website and it matches.",
            )

    def test_cannot_mark_verified_without_review_notes(self):
        with pytest.raises(SourceGovernanceError, match="Verification notes are required"):
            SourceGovernance.validate_verification_transition(
                current_status=VerificationStatus.UNVERIFIED,
                new_status=VerificationStatus.VERIFIED,
                reviewer_id=uuid4(),
                review_notes="",
            )

    def test_valid_verification_transition_succeeds(self):
        SourceGovernance.validate_verification_transition(
            current_status=VerificationStatus.UNVERIFIED,
            new_status=VerificationStatus.VERIFIED,
            reviewer_id=uuid4(),
            review_notes="Inspected official portal on 2026-10-30; PDF requirements confirmed.",
        )

    def test_content_hashing_consistency(self):
        text1 = "Official Government Notice\n\nAll applicants must submit valid proofs."
        text2 = "Official Government   Notice  All applicants must submit valid proofs."
        # Normalized whitespace should produce the exact same content hash
        hash1 = SourceGovernance.compute_content_hash(text1)
        hash2 = SourceGovernance.compute_content_hash(text2)
        assert hash1 == hash2
        assert len(hash1) == 64
