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
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# cj-style N+7 (admin 시점 verification gate fix) — `env_file=".env"` 는
# 상대경로 → uvicorn 시작 cwd 에 의존. 어느 shell 에서 시작해도 항상
# `apps/api/.env` 를 읽도록 절대경로로 고정. 결정 wire 보존: env-free
# local dev only, LOW risk (config 1 attr).
# `apps/api/core/settings.py` → parents[0]=core/ [1]=api/ [2]=apps/api/.
_BACKEND_ROOT = Path(__file__).resolve().parents[1]  # apps/api/
_ENV_FILE = _BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    """Application settings — values read from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
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
