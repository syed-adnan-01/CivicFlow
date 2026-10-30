from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # -------------------------------------------------------------------------
    # Database (PostgreSQL with psycopg v3 driver)
    # -------------------------------------------------------------------------
    DATABASE_URL: str = "postgresql+psycopg://queueless:queueless_secret@localhost:5432/queueless_db"

    # -------------------------------------------------------------------------
    # Firebase Authentication & Client Config
    # -------------------------------------------------------------------------
    FIREBASE_PROJECT_ID: str = "civicflow-18c55"
    FIREBASE_API_KEY: Optional[str] = None
    FIREBASE_AUTH_DOMAIN: Optional[str] = None
    FIREBASE_STORAGE_BUCKET: Optional[str] = None
    FIREBASE_MESSAGING_SENDER_ID: Optional[str] = None
    FIREBASE_APP_ID: Optional[str] = None
    FIREBASE_MEASUREMENT_ID: Optional[str] = None

    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    FIREBASE_CHECK_REVOKED: bool = False

    # -------------------------------------------------------------------------
    # QR Rotation Policy
    # -------------------------------------------------------------------------
    QR_ROTATION_LIMIT: int = 3
    QR_ROTATION_WINDOW_SECONDS: int = 600

    # -------------------------------------------------------------------------
    # Idempotency
    # -------------------------------------------------------------------------
    IDEMPOTENCY_RETENTION_HOURS: int = 24

    # -------------------------------------------------------------------------
    # Groq — PRIMARY LLM provider (Member 4)
    # -------------------------------------------------------------------------
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # -------------------------------------------------------------------------
    # Gemini — FALLBACK LLM provider + sole embedding provider (Member 4)
    # -------------------------------------------------------------------------
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    EMBEDDING_MODEL: str = "models/text-embedding-004"
    EMBEDDING_PROVIDER: str = "gemini"

    # -------------------------------------------------------------------------
    # ChromaDB — RAG vector store (Member 4)
    # -------------------------------------------------------------------------
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHROMA_COLLECTION: str = "queueless_verified_sources_v1"

    # -------------------------------------------------------------------------
    # RAG retrieval parameters (Member 4)
    # -------------------------------------------------------------------------
    RAG_TOP_K: int = 5
    RAG_MIN_RELEVANCE_SCORE: float = 0.70
    RAG_MAX_CONTEXT_CHARS: int = 12000

    # -------------------------------------------------------------------------
    # OCR configuration (Member 4)
    # -------------------------------------------------------------------------
    OCR_ENGINE: str = "tesseract"
    OCR_LANGUAGE_PACKS: str = "eng"
    OCR_MAX_FILE_MB: int = 10
    OCR_MAX_PAGES: int = 10

    # -------------------------------------------------------------------------
    # Document storage (Member 4)
    # -------------------------------------------------------------------------
    DOCUMENT_STORAGE_BUCKET: str = "./data/storage"
    DOCUMENT_RETENTION_DAYS: int = 90

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
