"""
RAG services package — public exports.
"""

from app.services.rag.answer_generator import AnswerGenerator
from app.services.rag.chunker import GeneratedChunk, TextChunker
from app.services.rag.citation_validator import CitationValidationResult, CitationValidator
from app.services.rag.prompt_builder import PromptBuilder
from app.services.rag.refusal_policy import RefusalPolicy
from app.services.rag.retrieval import RetrievalService, RetrievedChunk
from app.services.rag.source_fetch import SourceFetchError, SourceFetcher
from app.services.rag.source_governance import (
    SourceGovernance,
    SourceGovernanceError,
    SourceScopeError,
)
from app.services.rag.source_parser import SourceParser
from app.services.rag.vector_store import VectorStore, VectorStoreError

__all__ = [
    "AnswerGenerator",
    "CitationValidationResult",
    "CitationValidator",
    "GeneratedChunk",
    "PromptBuilder",
    "RefusalPolicy",
    "RetrievalService",
    "RetrievedChunk",
    "SourceFetchError",
    "SourceFetcher",
    "SourceGovernance",
    "SourceGovernanceError",
    "SourceParser",
    "SourceScopeError",
    "TextChunker",
    "VectorStore",
    "VectorStoreError",
]
