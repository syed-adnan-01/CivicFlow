"""
Provider factory and fallback chain.

Usage (anywhere in the app):
    from app.services.providers.provider_factory import get_llm_provider

    llm = get_llm_provider()
    response = llm.generate(system_prompt, user_prompt)
    # response.provider tells you which provider actually answered ("groq" or "gemini")

Fallback order:
    1. Groq   — fast, free tier; raises ProviderQuotaError on 429
    2. Gemini — activated automatically when Groq quota is exhausted

If both providers fail, ProviderUnavailableError is raised so the assistant
API returns TEMPORARILY_UNAVAILABLE — never a fabricated answer.
"""

import logging
from typing import List

from app.services.providers.llm_base import (
    LLMProviderBase,
    LLMResponse,
    ProviderConfigError,
    ProviderQuotaError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Fallback chain provider
# ---------------------------------------------------------------------------

class FallbackLLMProvider(LLMProviderBase):
    """
    Tries each provider in order.
    Moves to the next provider only on ProviderQuotaError (rate limit).
    Any other failure (config error, network error) is raised immediately.
    """

    def __init__(self, providers: List[LLMProviderBase]) -> None:
        if not providers:
            raise ValueError("FallbackLLMProvider requires at least one provider.")
        self._providers = providers
        self._last_used: str = ""

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        last_exc: Exception = ProviderUnavailableError("No providers configured.")

        for provider in self._providers:
            if not provider.is_configured():
                logger.debug(
                    "Skipping provider %r — not configured.", provider.provider_name()
                )
                continue

            try:
                logger.debug("Trying LLM provider: %s", provider.provider_name())
                response = provider.generate(system_prompt, user_prompt)
                self._last_used = provider.provider_name()
                return response

            except ProviderQuotaError as exc:
                # Quota exhausted → try the next provider in the chain
                logger.warning(
                    "Provider %r quota exhausted — trying next provider. (%s)",
                    provider.provider_name(),
                    type(exc).__name__,
                )
                last_exc = exc
                continue

            except ProviderConfigError:
                # Config errors are not retried — surface immediately
                raise

            except ProviderUnavailableError as exc:
                # Transient failure — surface immediately, don't silently fallback
                logger.error(
                    "Provider %r unavailable: %s", provider.provider_name(), type(exc).__name__
                )
                raise

        # All providers in the chain exhausted their quotas
        logger.error("All LLM providers quota-exhausted or unavailable.")
        raise ProviderUnavailableError(
            "All LLM providers are currently unavailable or quota-exhausted."
        ) from last_exc

    def is_configured(self) -> bool:
        """True if at least one provider in the chain is configured."""
        return any(p.is_configured() for p in self._providers)

    def provider_name(self) -> str:
        """Returns the name of the provider used for the last successful call."""
        return self._last_used or " → ".join(p.provider_name() for p in self._providers)


# ---------------------------------------------------------------------------
# Factory — single entry point for the rest of the app
# ---------------------------------------------------------------------------

def get_llm_provider() -> FallbackLLMProvider:
    """
    Returns a FallbackLLMProvider with:
      1. Groq  (primary — fast, free tier)
      2. Gemini (fallback — activated on Groq quota/rate-limit)

    Import this function wherever an LLM call is needed.
    Do NOT instantiate GroqProvider or GeminiProvider directly in service code.
    """
    from app.services.providers.groq_provider import GroqProvider
    from app.services.providers.gemini_provider import GeminiProvider

    return FallbackLLMProvider(
        providers=[
            GroqProvider(),    # tried first
            GeminiProvider(),  # fallback on ProviderQuotaError
        ]
    )

