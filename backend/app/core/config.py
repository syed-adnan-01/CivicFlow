from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # PostgreSQL Database
    DATABASE_URL: str = "postgresql+psycopg://queueless:queueless_secret@localhost:5432/queueless_db"

    # Firebase Authentication
    FIREBASE_PROJECT_ID: str = "queueless-dev"
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    FIREBASE_CHECK_REVOKED: bool = False

    # QR Rotation Policy
    QR_ROTATION_LIMIT: int = 3
    QR_ROTATION_WINDOW_SECONDS: int = 600

    # Idempotency
    IDEMPOTENCY_RETENTION_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
