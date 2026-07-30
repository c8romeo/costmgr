"""apps.api.core.settings — Pydantic Settings (env-driven, AD-9 Seoul region).

Story 0.1 stub: defines the env-var surface; real wiring (Supabase, Stripe) lands in
Epic 0 Story 0.2 (Supabase) and Epic 12 (account/backup/billing).

Per AD-9: backend region is `ap-northeast-2` (Seoul). Per AD-3 RLS — the database
URL is read here but never logged. Per AD-15: snake_case env var names.

This module is the SINGLE place where os.environ is read inside apps/api.
Other modules receive the loaded Settings object via FastAPI dependency injection
(`get_settings()`).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings — values read from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Service identity ──────────────────────────────────────
    service_name: str = "costmgr-api"
    service_version: str = "0.1.0"
    environment: str = Field(
        default="development", description="development | staging | production"
    )

    # ── AD-9: Region pin (Seoul) ──────────────────────────────
    region: str = "ap-northeast-2"

    # ── Supabase (Story 0.2 wires these) ─────────────────────
    supabase_url: str | None = None
    supabase_anon_key: str | None = None
    supabase_service_role_key: str | None = None  # server-side only; never exposed
    supabase_jwt_secret: str | None = None  # HS256 secret for Supabase auth JWTs
    database_url: str | None = None

    # ── JWT (Story 0.2) — clock-skew tolerance for Supabase tokens ─
    jwt_leeway_sec: int | None = None  # default 30s if None

    # ── Logging ───────────────────────────────────────────────
    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor — call this from FastAPI dependencies."""
    return Settings()
