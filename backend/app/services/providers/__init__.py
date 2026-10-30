"""
providers package — public API.

Import from here in service code:
    from app.services.providers import get_llm_provider, get_embedding_provider
"""

from app.services.providers.provider_factory import get_llm_provider, FallbackLLMProvider
from app.services.providers.embedding_provider import get_embedding_provider
from app.services.providers.llm_base import (
    LLMProviderBase,
    LLMResponse,
    ProviderConfigError,
    ProviderQuotaError,
    ProviderUnavailableError,
)

__all__ = [
    "get_llm_provider",
    "get_embedding_provider",
    "FallbackLLMProvider",
    "LLMProviderBase",
    "LLMResponse",
    "ProviderConfigError",
    "ProviderQuotaError",
    "ProviderUnavailableError",
]

