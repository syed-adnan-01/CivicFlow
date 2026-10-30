"""
Groq LLM provider adapter.
Primary provider — fast inference, free tier.
On RateLimitError (HTTP 429), raises ProviderQuotaError so the
FallbackLLMProvider can switch to Gemini automatically.

SDK: groq  (pip install groq)
Docs: https://console.groq.com/docs/openai
"""

import logging
from typing import Optional

from app.core.config import settings
from app.services.providers.llm_base import (
    LLMProviderBase,
    LLMResponse,
    ProviderConfigError,
    ProviderQuotaError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)

# Groq's recommended default model — change via GROQ_MODEL env var
_DEFAULT_MODEL = "llama-3.1-70b-versatile"


class GroqProvider(LLMProviderBase):
    """Adapter for Groq Cloud inference API."""

    def __init__(self) -> None:
        self._client: Optional[object] = None

    def _get_client(self):
        """Lazily initialise the Groq client."""
        if self._client is not None:
            return self._client

        try:
            from groq import Groq  # type: ignore
        except ImportError as exc:
            raise ProviderConfigError(
                "groq package is not installed. Run: pip install groq"
            ) from exc

        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ProviderConfigError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )

        self._client = Groq(api_key=api_key)
        return self._client

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        Send a chat completion to Groq.
        Raises ProviderQuotaError on 429 so the fallback chain activates Gemini.
        Raises ProviderUnavailableError on other transient failures.
        """
        model = settings.GROQ_MODEL or _DEFAULT_MODEL
        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.2,      # low temperature for factual RAG answers
                max_tokens=2048,
            )
            return LLMResponse(
                content=completion.choices[0].message.content or "",
                model=model,
                provider="groq",
                finish_reason=completion.choices[0].finish_reason,
            )

        except ProviderConfigError:
            raise

        except Exception as exc:
            exc_type = type(exc).__name__

            # Groq SDK surfaces rate limits as groq.RateLimitError
            # Also guard against the class name in case the import failed partially
            if "RateLimitError" in exc_type or _is_rate_limit(exc):
                logger.warning(
                    "Groq quota/rate-limit hit (%s). Fallback to Gemini will activate.",
                    exc_type,
                )
                raise ProviderQuotaError(
                    "Groq rate limit reached — switching to fallback provider."
                ) from exc

            # Authentication errors are config problems, not transient failures
            if "AuthenticationError" in exc_type:
                logger.error("Groq authentication failed — check GROQ_API_KEY.")
                raise ProviderConfigError(
                    "Groq authentication failed. Verify GROQ_API_KEY."
                ) from exc

            logger.error("Groq generate failed: %s", exc_type)
            raise ProviderUnavailableError(
                "Groq provider is temporarily unavailable."
            ) from exc

    def is_configured(self) -> bool:
        return bool(settings.GROQ_API_KEY and (settings.GROQ_MODEL or _DEFAULT_MODEL))

    def provider_name(self) -> str:
        return "groq"


def _is_rate_limit(exc: Exception) -> bool:
    """
    Heuristic check for rate-limit responses when the exact class can't be
    imported (e.g., groq not installed). Checks HTTP status codes in the exception.
    """
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    return status == 429

