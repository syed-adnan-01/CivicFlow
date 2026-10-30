"""
Base interface for all LLM providers.
All provider implementations must inherit from LLMProviderBase.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LLMResponse:
    content: str
    model: str
    provider: str = ""          # which provider actually served the request
    finish_reason: Optional[str] = None


class LLMProviderBase(ABC):
    """Abstract base class for LLM provider adapters."""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        Send a prompt to the LLM and return a structured response.

        Raises:
            ProviderQuotaError   — rate-limit / quota exhausted (triggers fallback).
            ProviderUnavailableError — transient connection / timeout failure.
            ProviderConfigError  — missing or invalid credentials/config.
        Must never expose raw API keys in exceptions or logs.
        """
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the provider credentials and model are set."""
        ...

    @abstractmethod
    def provider_name(self) -> str:
        """Return a human-readable provider name for health checks."""
        ...


# ---------------------------------------------------------------------------
# Typed exceptions — ordered from most specific to most general
# ---------------------------------------------------------------------------

class ProviderConfigError(Exception):
    """Missing or invalid provider credentials / configuration."""
    pass


class ProviderUnavailableError(Exception):
    """Provider is temporarily unavailable (network, timeout, 5xx)."""
    pass


class ProviderQuotaError(ProviderUnavailableError):
    """
    Rate-limit or quota exhausted (HTTP 429 / RESOURCE_EXHAUSTED).
    The FallbackLLMProvider catches this to switch to the next provider in the chain.
    """
    pass
