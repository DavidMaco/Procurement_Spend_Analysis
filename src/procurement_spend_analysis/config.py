from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed runtime settings for API, security, and observability."""

    model_config = SettingsConfigDict(env_prefix="PROCUREMENT_", env_file=".env", extra="ignore")

    app_name: str = "procurement-spend-analysis"
    environment: str = "dev"
    log_level: str = "INFO"
    allow_origins: list[str] = Field(default_factory=lambda: ["http://localhost:8501", "http://localhost:8000"])
    max_upload_file_size_mb: int = 25
    max_upload_rows_per_file: int = 500_000
    api_port: int = 8000
    dashboard_port: int = 8501
    metrics_enabled: bool = True
    request_timeout_seconds: int = 30
    package_version: str = "0.1.0"
    fmcg_event_log_path: str = Field(
        default_factory=lambda: str(Path("logs") / "fmcg_recommendation_events.jsonl")
    )
    fmcg_event_archive_path: str = Field(
        default_factory=lambda: str(Path("logs") / "fmcg_recommendation_events.archive.jsonl")
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
