"""
Unit tests — document chunking and metadata preservation.
Tests chunk splitting, overlap, section headings, and Section 7.7 metadata attributes.
"""

from uuid import uuid4
import pytest

from app.services.rag.chunker import TextChunker


class TestTextChunker:
    @pytest.fixture
    def chunker(self):
        return TextChunker(min_chars=200, max_chars=600, overlap_chars=100)

    @pytest.fixture
    def sample_text(self):
        return (
            "## 1. Introduction\n\n"
            "This official citizen guide explains the prerequisites for Nadakacheri service applications. "
            "Please read all instructions carefully before visiting the citizen service centre.\n\n"
            "## 2. Required Documents\n\n"
            "Applicants must provide a valid government photo identity document such as an Aadhaar card or voter ID. "
            "In addition, an active residential proof certificate issued within the past 6 months is required.\n\n"
            "## 3. Working Hours and Fees\n\n"
            "The office operates Monday to Friday from 9:30 AM to 5:30 PM IST. "
            "Statutory application fees must be paid through authorized counters only."
        )

    def test_chunking_creates_chunks_with_metadata(self, chunker, sample_text):
        doc_id = uuid4()
        chunks = chunker.chunk_document(
            document_id=doc_id,
            text=sample_text,
            page_title="Nadakacheri Service Guide",
            source_url="https://nadakacheri.karnataka.gov.in/guide",
            authority="Directorate of Atalji Janasnehi Kendra",
            service_scope="Income and Caste Certificates",
            verification_status="VERIFIED",
            retrieved_at="2026-10-30T00:00:00Z",
            last_checked_at="2026-10-30T00:00:00Z",
        )

        assert len(chunks) >= 2

        for idx, chunk in enumerate(chunks):
            assert chunk.chunk_id == f"{doc_id}_chunk_{idx}"
            assert chunk.chunk_index == idx
            assert len(chunk.chunk_text) > 0
            assert chunk.content_hash is not None

            # Verify Section 7.7 metadata completeness
            meta = chunk.metadata
            assert meta["knowledge_document_id"] == str(doc_id)
            assert meta["page_title"] == "Nadakacheri Service Guide"
            assert meta["canonical_url"] == "https://nadakacheri.karnataka.gov.in/guide"
            assert meta["authority"] == "Directorate of Atalji Janasnehi Kendra"
            assert meta["service_scope"] == "Income and Caste Certificates"
            assert meta["verification_status"] == "VERIFIED"
            assert meta["active"] is True

    def test_empty_text_returns_empty_list(self, chunker):
        doc_id = uuid4()
        chunks = chunker.chunk_document(
            document_id=doc_id,
            text="",
            page_title="Empty",
            source_url="https://example.gov.in",
            authority="Gov",
            service_scope="All",
            verification_status="VERIFIED",
            retrieved_at="2026-10-30T00:00:00Z",
        )
        assert chunks == []

    def test_unverified_source_metadata_sets_active_false(self, chunker, sample_text):
        doc_id = uuid4()
        chunks = chunker.chunk_document(
            document_id=doc_id,
            text=sample_text,
            page_title="Draft Unverified Guide",
            source_url="https://example.gov.in",
            authority="Gov",
            service_scope="General",
            verification_status="UNVERIFIED",
            retrieved_at="2026-10-30T00:00:00Z",
        )
        for chunk in chunks:
            assert chunk.metadata["active"] is False
            assert chunk.metadata["verification_status"] == "UNVERIFIED"

