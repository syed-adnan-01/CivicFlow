"""
Unit tests — refusal policy.
Tests that the assistant refuses to answer unsupported questions.
"""

import pytest


class TestInsufficientEvidenceRefusal:
    def test_no_relevant_chunks_returns_insufficient_evidence(self):
        pytest.skip("Implementation pending — Day 9")

    def test_unverified_only_chunks_returns_refusal(self):
        pytest.skip("Implementation pending — Day 9")

    def test_conflicting_sources_returns_source_conflict_status(self):
        pytest.skip("Implementation pending — Day 9")


class TestOutOfScopeRefusal:
    def test_eligibility_question_refused(self):
        # "Am I eligible for this certificate?" → must not answer
        pytest.skip("Implementation pending — Day 9")

    def test_approval_prediction_refused(self):
        # "Will my application be approved?" → must not answer
        pytest.skip("Implementation pending — Day 9")

    def test_fee_not_in_corpus_refused(self):
        # Fee not in any verified chunk → must not invent one
        pytest.skip("Implementation pending — Day 9")

    def test_unrelated_topic_returns_scope_message(self):
        pytest.skip("Implementation pending — Day 9")


class TestProviderOutageRefusal:
    def test_llm_unavailable_returns_temporarily_unavailable(self):
        pytest.skip("Implementation pending — Day 10")

    def test_chroma_unavailable_returns_temporarily_unavailable(self):
        pytest.skip("Implementation pending — Day 10")

