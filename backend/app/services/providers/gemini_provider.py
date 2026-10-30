"""
Gemini LLM provider adapter.
Acts as the FALLBACK provider — activated automatically when Groq hits its quota.
Also used as the sole embedding provider (Groq has no embeddings API).

SDK: google-generativeai  (pip install google-generativeai)
Credentials: GEMINI_API_KEY (separate from GROQ_API_KEY)
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

_DEFAULT_MODEL = "gemini-1.5-flash"

# Strings that appear in Gemini quota/rate-limit exceptions
_QUOTA_SIGNALS = ("429", "RESOURCE_EXHAUSTED", "quota", "rate", "rateLimitExceeded")


class GeminiProvider(LLMProviderBase):
    """Adapter for Google Gemini — used as LLM fallback and embedding provider."""

    def __init__(self) -> None:
        self._client: Optional[object] = None
        self._model_name: Optional[str] = None

    def _get_client(self):
        """Lazily initialise the Gemini generative client."""
        if self._client is not None:
            return self._client

        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:
            raise ProviderConfigError(
                "google-generativeai package is not installed. Run: pip install google-generativeai"
            ) from exc

        api_key = settings.GEMINI_API_KEY
        model_name = settings.GEMINI_MODEL or _DEFAULT_MODEL

        if not api_key:
            raise ProviderConfigError(
                "GEMINI_API_KEY is not set. Add it to your .env file."
            )

        genai.configure(api_key=api_key)
        self._model_name = model_name
        self._client = genai.GenerativeModel(model_name)
        return self._client

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """
        Call Gemini with system + user prompt.
        Raises ProviderQuotaError on RESOURCE_EXHAUSTED / 429.
        Raises ProviderUnavailableError on other transient failures.
        """
        try:
            client = self._get_client()
            combined = f"{system_prompt}\n\n{user_prompt}"
            response = client.generate_content(combined)
            return LLMResponse(
                content=response.text,
                model=self._model_name or _DEFAULT_MODEL,
                provider="gemini",
                finish_reason=None,
            )

        except ProviderConfigError:
            raise

        except Exception as exc:
            exc_type = type(exc).__name__
            exc_msg  = str(exc).lower()

            # Detect Gemini quota / rate-limit errors
            if any(signal.lower() in exc_msg for signal in _QUOTA_SIGNALS):
                logger.warning("Gemini quota/rate-limit hit (%s).", exc_type)
                raise ProviderQuotaError(
                    "Gemini rate limit reached — no further fallback available."
                ) from exc

            logger.error("Gemini generate failed: %s", exc_type)
            raise ProviderUnavailableError(
                "Gemini provider is temporarily unavailable."
            ) from exc

    def is_configured(self) -> bool:
        return bool(settings.GEMINI_API_KEY)

    def provider_name(self) -> str:
        return "gemini"
