"""
Embedding provider adapter.
Groq has no embeddings API, so Gemini is always used for embeddings,
even when Groq is the active LLM provider.

Credentials: GEMINI_API_KEY (same key used by GeminiProvider fallback)
"""

import logging
from typing import List

from app.core.config import settings
from app.services.providers.embedding_base import EmbeddingProviderBase, EmbeddingResult
from app.services.providers.llm_base import ProviderConfigError, ProviderUnavailableError

logger = logging.getLogger(__name__)


class GeminiEmbeddingProvider(EmbeddingProviderBase):
    """Embedding adapter backed by Google Gemini text-embedding model."""

    def __init__(self) -> None:
        self._model: str = settings.EMBEDDING_MODEL or "models/text-embedding-004"

    def _get_genai(self):
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ProviderConfigError(
                "google-generativeai package is not installed."
            ) from exc

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise ProviderConfigError(
                "GEMINI_API_KEY is required for embeddings. "
                "Groq does not provide an embeddings API."
            )
        genai.configure(api_key=api_key)
        return genai

    def embed(self, text: str) -> EmbeddingResult:
        """Generate a single embedding vector."""
        try:
            genai = self._get_genai()
            result = genai.embed_content(model=self._model, content=text)
            return EmbeddingResult(
                embedding=result["embedding"],
                model=self._model,
            )
        except ProviderConfigError:
            raise
        except Exception as exc:
            logger.error("Embedding generation failed: %s", type(exc).__name__)
            raise ProviderUnavailableError(
                "Embedding provider (Gemini) is temporarily unavailable."
            ) from exc

    def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts sequentially."""
        return [self.embed(t) for t in texts]

    def is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY and self._model)

    def model_name(self) -> str:
        return self._model

    def provider_name(self) -> str:
        return "gemini-embedding"


def get_embedding_provider() -> EmbeddingProviderBase:
    """
    Factory — returns the configured embedding provider.
    Gemini is always used for embeddings (Groq has no embeddings endpoint).
    """
    return GeminiEmbeddingProvider()
