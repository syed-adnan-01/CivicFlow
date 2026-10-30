"""
Base interface for all embedding providers.
All embedding implementations must inherit from EmbeddingProviderBase.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class EmbeddingResult:
    embedding: List[float]
    model: str
    token_count: int = 0


class EmbeddingProviderBase(ABC):
    """Abstract base class for embedding provider adapters."""

    @abstractmethod
    def embed(self, text: str) -> EmbeddingResult:
        """
        Generate an embedding vector for the given text.
        Must use the same model/version used during ingestion.
        Must raise ProviderUnavailableError on failures.
        """
        ...

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for a batch of texts."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the embedding provider is properly configured."""
        ...

    @abstractmethod
    def model_name(self) -> str:
        """Return the model identifier used — stored with every chunk for version tracking."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Return a human-readable provider name for health checks."""
        ...

