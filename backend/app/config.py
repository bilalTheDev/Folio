from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
TEN_MB = 10 * 1024 * 1024


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    app_env: Literal["development", "test", "production"] = "development"

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "folio"

    jwt_secret: str = Field(min_length=32)
    jwt_refresh_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=15, gt=0)
    refresh_token_expire_days: int = Field(default=7, gt=0)
    refresh_cookie_name: str = "folio_refresh"
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    encryption_key: str

    cors_origin: str = "http://localhost:3000"

    storage_dir: Path = Path("storage")
    # The product caps uploads at 10MB; the setting may lower it but never raise it.
    max_upload_bytes: int = Field(default=TEN_MB, gt=0, le=TEN_MB)

    embed_model: str = "BAAI/bge-small-en-v1.5"
    chunk_size: int = Field(default=512, gt=0)
    chunk_overlap: int = Field(default=50, ge=0)
    retrieval_top_k: int = Field(default=5, gt=0, le=20)

    hf_router_base_url: str = "https://router.huggingface.co/v1"
    llm_timeout_seconds: int = Field(default=60, gt=0)

    rate_limit_auth: str = "10/minute"
    rate_limit_upload: str = "20/minute"
    rate_limit_chat: str = "30/minute"

    @property
    def storage_root(self) -> Path:
        root = self.storage_dir if self.storage_dir.is_absolute() else BACKEND_DIR / self.storage_dir
        return root.resolve()

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
