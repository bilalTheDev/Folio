"""Pydantic settings loaded from environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for Folio."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    clerk_secret_key: str = ""
    next_public_clerk_publishable_key: str = ""
    clerk_jwks_url: str = ""
    folio_encryption_key: str = ""
    sentry_dsn: str = ""
    folio_disable_trial: bool = False
    folio_env: str = "development"
    folio_cors_origin: str = "http://localhost:3000"

    max_file_mb: int = 10
    max_pages: int = 100
    max_documents_per_user: int = 20
    daily_question_limit: int = 200
    uploads_per_hour: int = 10


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
