"""
Integration tests — assistant API.
Tests the full POST /api/v1/assistant/chat flow with a real test database and
synthetic verified source corpus. LLM and embedding calls use a mock adapter.
"""

import pytest


class TestAssistantChatAuthentication:
    def test_unauthenticated_request_returns_401(self):
        pytest.skip("Implementation pending — Day 10")

    def test_citizen_with_valid_firebase_token_can_chat(self):
        pytest.skip("Implementation pending — Day 10")


class TestAssistantChatRetrieval:
    def test_verified_source_returns_grounded_answer_with_citations(self):
        pytest.skip("Implementation pending — Day 10")

    def test_unverified_source_never_cited_in_response(self):
        pytest.skip("Implementation pending — Day 10")

    def test_stale_source_not_returned_after_deactivation(self):
        pytest.skip("Implementation pending — Day 10")

    def test_service_scoped_query_does_not_return_other_service_chunks(self):
        pytest.skip("Implementation pending — Day 10")


class TestAssistantChatFallback:
    def test_llm_outage_returns_503_with_safe_message(self):
        pytest.skip("Implementation pending — Day 10")

    def test_embedding_outage_returns_503_with_safe_message(self):
        pytest.skip("Implementation pending — Day 10")

    def test_chroma_outage_returns_503_with_safe_message(self):
        pytest.skip("Implementation pending — Day 10")

