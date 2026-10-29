from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = Field(default=8000, ge=1, le=65535)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    collection_connect_timeout_seconds: float = Field(default=10.0, gt=0)
    collection_read_timeout_seconds: float = Field(default=15.0, gt=0)
    collection_total_timeout_seconds: float = Field(default=60.0, gt=0)
    collection_max_redirects: int = Field(default=5, ge=0)
    collection_max_response_bytes: int = Field(default=5_242_880, gt=0)

    db_host: str
    db_port: int = Field(default=5432, ge=1, le=65535)
    db_name: str
    db_user: str
    db_password: SecretStr

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
