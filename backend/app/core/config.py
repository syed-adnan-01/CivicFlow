"""
Application settings — loaded from environment variables / .env file.
All secret values must come from environment, never hardcoded.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # App
    # -------------------------------------------------------------------------
    APP_ENV: str = "development"          # development | test | production
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # -------------------------------------------------------------------------
    # Database (Member 1)
    # -------------------------------------------------------------------------
    DATABASE_URL: str = ""

    # -------------------------------------------------------------------------
    # Firebase (Member 1)
    # -------------------------------------------------------------------------
    FIREBASE_PROJECT_ID: str = ""
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    FIREBASE_CHECK_REVOKED: bool = False

    # -------------------------------------------------------------------------
    # QR / Idempotency (Member 1)
    # -------------------------------------------------------------------------
    QR_ROTATION_LIMIT: int = 3
    QR_ROTATION_WINDOW_SECONDS: int = 600
    IDEMPOTENCY_RETENTION_HOURS: int = 24

    # -------------------------------------------------------------------------
    # Groq — PRIMARY LLM provider
    # -------------------------------------------------------------------------
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # -------------------------------------------------------------------------
    # Gemini — FALLBACK LLM provider + sole embedding provider
    # Groq has no embeddings API; Gemini is always used for embeddings.
    # -------------------------------------------------------------------------
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"

    # -------------------------------------------------------------------------
    # Embeddings (always Gemini)
    # -------------------------------------------------------------------------
    EMBEDDING_PROVIDER: str = "gemini"
    EMBEDDING_MODEL: str = "models/text-embedding-004"

    # -------------------------------------------------------------------------
    # ChromaDB vector store
    # -------------------------------------------------------------------------
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHROMA_COLLECTION: str = "queueless_verified_sources_v1"

    # -------------------------------------------------------------------------
    # RAG retrieval
    # -------------------------------------------------------------------------
    RAG_TOP_K: int = 5
    RAG_MIN_RELEVANCE_SCORE: float = 0.70
    RAG_MAX_CONTEXT_CHARS: int = 12000

    # -------------------------------------------------------------------------
    # OCR engine (chosen after test gate in Phase 4)
    # -------------------------------------------------------------------------
    OCR_ENGINE: Optional[str] = None      # paddle | tesseract
    OCR_LANGUAGE_PACKS: str = "eng"
    OCR_MAX_FILE_MB: int = 10
    OCR_MAX_PAGES: int = 10

    # -------------------------------------------------------------------------
    # Document storage
    # -------------------------------------------------------------------------
    DOCUMENT_STORAGE_BUCKET: Optional[str] = None
    DOCUMENT_RETENTION_DAYS: int = 30


# Single shared instance — import this everywhere
settings = Settings()

