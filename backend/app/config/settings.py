"""Pydantic settings loaded from environment variables.

All runtime configuration is read here. Other modules must use Settings /
get_settings() instead of os.environ.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Folio repo root (…/backend/app/config/settings.py → parents[3])
_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILES = tuple(
    str(path)
    for path in (_ROOT / ".env.local", _ROOT / ".env")
    if path.is_file()
)


class Settings(BaseSettings):
    """Runtime configuration for Folio."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILES or ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = ""
    database_url_unpooled: str = ""
    neon_branch: str = ""
    clerk_secret_key: str = ""
    next_public_clerk_publishable_key: str = ""
    clerk_jwks_url: str = ""
    clerk_jwt_audience: str = ""
    clerk_jwt_issuer: str = ""
    folio_encryption_key: str = ""
    sentry_dsn: str = ""
    folio_disable_trial: bool = False
    folio_env: str = "development"
    folio_cors_origin: str = "http://localhost:3000"
    folio_sample_groq_key: str = ""
    folio_embed_cache_dir: str = ""
    vercel: str = Field(default="", validation_alias="VERCEL")

    max_file_mb: int = 10
    max_pages: int = 100
    max_documents_per_user: int = 20
    max_chunks_per_document: int = 50
    daily_question_limit: int = 200
    uploads_per_hour: int = 10

    @property
    def on_vercel(self) -> bool:
        return self.vercel == "1"

    @property
    def is_development(self) -> bool:
        return self.folio_env == "development"

    @property
    def app_database_url(self) -> str:
        """Pooled URL for application traffic (falls back to unpooled)."""
        return (self.database_url or self.database_url_unpooled).strip()

    @property
    def migration_database_url(self) -> str:
        """Direct URL for schema migrations (falls back to pooled)."""
        return (self.database_url_unpooled or self.database_url).strip()


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
