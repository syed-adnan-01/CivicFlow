"""
Unit tests — RAG source governance.
Tests source state transitions, scope filtering, and active-source exclusion.
Run with: pytest tests/unit/test_source_governance.py
"""

import pytest


class TestSourceStateFiltering:
    """Only VERIFIED + active sources should be used in retrieval."""

    def test_unverified_source_excluded_from_retrieval(self):
        # TODO (Day 4): assert that a source with verification_status=UNVERIFIED
        # is never returned by the retrieval service.
        pytest.skip("Implementation pending — Day 4")

    def test_stale_source_excluded_from_retrieval(self):
        # TODO (Day 4): assert STALE sources are excluded.
        pytest.skip("Implementation pending — Day 4")

    def test_inactive_source_excluded_from_retrieval(self):
        # TODO (Day 4): assert INACTIVE sources are excluded after deactivation.
        pytest.skip("Implementation pending — Day 4")

    def test_verified_active_source_included_in_retrieval(self):
        # TODO (Day 4): assert a VERIFIED + active source is retrievable.
        pytest.skip("Implementation pending — Day 4")


class TestSourceScopeFiltering:
    """Sources must be scoped to the exact service being queried."""

    def test_source_for_different_service_not_returned(self):
        # TODO (Day 7): retrieval with service_id=A must not return chunks
        # from a source scoped to service_id=B.
        pytest.skip("Implementation pending — Day 7")

    def test_psi_training_source_not_used_for_income_certificate(self):
        # Regression: PSI Training notice must never answer Income Certificate questions.
        pytest.skip("Implementation pending — Day 7")


class TestSourceVerificationWorkflow:
    """Source must remain UNVERIFIED until manually marked VERIFIED."""

    def test_newly_created_source_is_unverified(self):
        # TODO (Day 4): creating a source via the service sets status=UNVERIFIED.
        pytest.skip("Implementation pending — Day 4")

    def test_ingestion_does_not_auto_verify_source(self):
        # A source must not become VERIFIED merely because indexing succeeded.
        pytest.skip("Implementation pending — Day 5")

