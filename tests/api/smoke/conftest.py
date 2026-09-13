"""tests.api.smoke.conftest — K-4 wire 1 MVP-critical smoke test fixtures.

K-4 wire 1 (cj-style 294번째, 2026-09-11 KST, D-3) — option β docs+test entry.
K-3 chain 5/5 DONE + K-4 entry decision wire (cj-style 293번째) DONE 후 MVP-critical
10 flows 의 runtime smoke test scaffolding.

K-4 wire 1.2+ (cj-style 298번째, 2026-09-11 KST, D-3) — B-TEST-1 fix:
test helpers (_find_route, _count_routes_with_prefix, _routes_with_prefix)
were iterating `app.routes` top-level only, missing the 36 `_IncludedRouter`
sub-router references. Switched to `app.openapi()` which correctly flattens
all registered paths (sub-router routes included). 27 cases previously
3 PASS + 24 FAIL due to B-TEST-1 → now expected 27/27 PASS.

K-4 wire 3 main + Sprint 0 환경 준비 (cj-style N+7, 2026-09-13 KST, D-1):
embedded-postgres 18.6.3 자동 다운로드 + ephemeral instance + DATABASE_URL 자동 설정.
Q1 환경 결정: 옵션 (d-1) embedded-postgres 자동 다운로드 (Docker Desktop / PostgreSQL
native 모두 미설치 환경). Production 100% parity (RLS / JSONB / UUID / GIN 모두 정상).
`gen_random_uuid()` built-in 사용 (uuid-ossp extension 의존성 회피).

검증 scope: Auth + M0 Onboarding + M1 기준정보 + M2 월데이터입력 + M3 원가계산엔진
+ M5 손익 + M8 예산 + M9 ABC + Audit log + Export (CSV) = 10 flows.

Runtime execution: pytest + project venv + embedded-postgres 18.6.3 (auto-download).
honest-DEFER: K-4 wire 1 에서 file 생성 + import path 정합 검증만 수행,
runtime test 실행 (pytest) 은 operator 환경에서 실행 결정 wire 보류.
"""

from __future__ import annotations

# IMPORTANT: OTEL_SDK_DISABLED must be set BEFORE `from apps.api.main import app`
# because apps.api.main calls init_tracing() at module level (main.py:338), which
# reads os.environ["OTEL_SDK_DISABLED"] at import time (tracing.py:66). Without
# this env var, init_tracing() tries to import opentelemetry.exporter.otlp.* and
# crashes with ModuleNotFoundError on host venv (B1 blocker from K-4 wire 1.1b,
# same root cause as cj-303 stack pin EXTENSION scope: tracing.py lazy imports).
import os

if "OTEL_SDK_DISABLED" not in os.environ:
    os.environ["OTEL_SDK_DISABLED"] = "true"

from pathlib import Path
from typing import Iterator

import pytest
from fastapi import FastAPI

# Sprint 0 (cj-style N+7): embedded-postgres 18.6.3 lazy import
# K-4 wire 3 main runtime execution 의 DATABASE_URL 환경 의존 해결
_epg_server = None
_epg_pgdata: Path | None = None


@pytest.fixture(scope="session")
def embedded_pg():
    """Session-scoped embedded-postgres fixture — auto-downloads PostgreSQL 18.6.

    Q1 환경 결정: 옵션 (d-1) embedded-postgres 자동 다운로드.
    Production 100% parity (RLS, JSONB, UUID, GIN 모두 정상).
    ephemeral instance — pytest session 종료 시 자동 cleanup.
    DATABASE_URL 환경 변수 자동 설정 (K-4 wire 3 main skipif guard 우회).

    Lifecycle:
      1. tempfile.mkdtemp(prefix='pgdata_mvp_') → pgdata directory
      2. PostgresServer(pgdata).ensure_pgdata_inited() → initdb
      3. PostgresServer.ensure_postgres_running() → postgres on free port
      4. os.environ['DATABASE_URL'] = postgresql://postgres@host:port/postgres
      5. yield (test execution)
      6. server.cleanup() + shutil.rmtree(pgdata)
    """
    global _epg_server, _epg_pgdata
    import tempfile
    import shutil
    import embedded_postgres

    _epg_pgdata = Path(tempfile.mkdtemp(prefix="pgdata_mvp_"))
    _epg_server = embedded_postgres.PostgresServer(_epg_pgdata)
    _epg_server.ensure_pgdata_inited()
    _epg_server.ensure_postgres_running()

    info = _epg_server.get_postmaster_info()
    host, port = info.hostname, int(info.port)
    database_url = f"postgresql://postgres@{host}:{port}/postgres"
    os.environ["DATABASE_URL"] = database_url
    os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-for-mvp-local-32chars-minimum")
    os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-mvp-local-32chars-minimum")

    print(f"\n[embedded_pg] DATABASE_URL = {database_url}")
    print(f"[embedded_pg] PostgreSQL {info.pid} running on {host}:{port}")

    yield {
        "server": _epg_server,
        "pgdata": _epg_pgdata,
        "host": host,
        "port": port,
        "database_url": database_url,
        "user": "postgres",
        "password": "",
        "database": "postgres",
    }

    if _epg_server is not None:
        _epg_server.cleanup()
    if _epg_pgdata is not None and _epg_pgdata.exists():
        shutil.rmtree(_epg_pgdata, ignore_errors=True)
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]


@pytest.fixture(scope="module")
def app(embedded_pg) -> FastAPI:
    """FastAPI app fixture — lazy import to avoid boot-time side effects.

    Depends on `embedded_pg` so DATABASE_URL is set BEFORE app import.
    The `apps.api.main:app` import triggers Sentry + OTEL + Supabase clients
    initialization. K-4 wire 1 uses lazy import so test collection does NOT
    require a live environment; K-4 wire 3 main adds embedded-postgres for
    full DATABASE_URL coverage.

    To execute runtime tests:
      1. activate the project venv (`uv sync` or `pip install -e .`)
      2. run `pytest tests/api/smoke/ -v` (embedded-postgres auto-downloads)
    """
    from apps.api.main import app as fastapi_app

    return fastapi_app


def _all_paths(app_obj: FastAPI) -> dict[str, dict]:
    """Return the full OpenAPI paths dict (sub-router routes included).

    FastAPI's `app.routes` contains top-level Route objects plus
    `_IncludedRouter` references for `app.include_router(...)` calls.
    Iterating `app.routes` directly misses sub-router routes — instead,
    use `app.openapi()` which flattens every registered path (including
    those behind nested routers) into a single `{path: path_item}` dict.
    """
    return app_obj.openapi().get("paths", {})


def _find_route(app_obj: FastAPI, full_path: str, method: str) -> bool:
    """Find if a route with given full path + method exists in the app.

    Uses `app.openapi()` so sub-router routes are included.
    """
    paths = _all_paths(app_obj)
    methods_at_path = paths.get(full_path, {})
    return method.lower() in methods_at_path


def _count_routes_with_prefix(app_obj: FastAPI, prefix: str) -> int:
    """Count routes that match a given prefix substring.

    Uses `app.openapi()` so sub-router routes are included.
    """
    paths = _all_paths(app_obj)
    return sum(1 for p in paths if prefix in p)


def _routes_with_prefix(app_obj: FastAPI, prefix: str) -> list[str]:
    """List route paths matching a given prefix substring.

    Uses `app.openapi()` so sub-router routes are included.
    Preserves the original substring-match semantics (`prefix in p`)
    so existing callers (e.g. `prefix="/auth"`, `prefix="/tenant-settings"`)
    continue to behave as before.
    """
    paths = _all_paths(app_obj)
    return sorted(p for p in paths if prefix in p)


def _routes_with_prefix_and_method(
    app_obj: FastAPI, prefix: str, method: str
) -> list[str]:
    """List route paths matching a given prefix substring AND having the given HTTP method.

    Uses `app.openapi()` so sub-router routes are included.
    OpenAPI spec normalizes method keys to lowercase ("get", "post", etc.) — we
    accept both `"GET"` (typical caller style) and `"get"` (spec style) by
    lowercasing on compare. Preserves substring-match semantics (`prefix in p`).
    """
    paths = _all_paths(app_obj)
    target = method.lower()
    return sorted(
        p for p, item in paths.items() if prefix in p and target in item
    )


def _total_route_paths(app_obj: FastAPI) -> int:
    """Return total number of registered route paths via OpenAPI.

    Uses `app.openapi()` to count all registered paths across sub-routers.
    """
    return len(_all_paths(app_obj))
