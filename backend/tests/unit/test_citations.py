"""
Unit tests — citation validation.
Tests that citations reference only retrieved chunks and valid sources.
"""

import pytest


class TestCitationIDValidation:
    def test_valid_chunk_id_accepted(self):
        # chunk_id present in current retrieval set → accepted
        pytest.skip("Implementation pending — Day 9")

    def test_invented_chunk_id_rejected(self):
        # chunk_id not in retrieval set → answer must be refused
        pytest.skip("Implementation pending — Day 9")

    def test_model_generated_url_stripped(self):
        # URL not from stored metadata must not appear in response
        pytest.skip("Implementation pending — Day 9")


class TestSourceStateAtResponseTime:
    def test_deactivated_source_citation_rejected(self):
        # If a source is deactivated between retrieval and response, citation must be refused
        pytest.skip("Implementation pending — Day 9")

    def test_only_verified_source_returned_in_citation(self):
        pytest.skip("Implementation pending — Day 9")


class TestPromptInjectionInSources:
    def test_source_instruction_text_not_treated_as_system_command(self):
        # Retrieved content that looks like a prompt override must be ignored
        pytest.skip("Implementation pending — Day 9")

