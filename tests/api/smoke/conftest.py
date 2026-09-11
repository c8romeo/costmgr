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

검증 scope: Auth + M0 Onboarding + M1 기준정보 + M2 월데이터입력 + M3 원가계산엔진
+ M5 손익 + M8 예산 + M9 ABC + Audit log + Export (CSV) = 10 flows.

Runtime execution: pytest + project venv + Supabase local emulator 필요.
honest-DEFER: K-4 wire 1 에서 file 생성 + import path 정합 검증만 수행,
runtime test 실행 (pytest) 은 operator 환경에서 실행 결정 wire 보류.
"""

from __future__ import annotations

from typing import Iterator

import pytest
from fastapi import FastAPI


@pytest.fixture(scope="module")
def app() -> FastAPI:
    """FastAPI app fixture — lazy import to avoid boot-time side effects.

    The `apps.api.main:app` import triggers Sentry + OTEL + Supabase clients
    initialization. These require runtime env vars + network. K-4 wire 1
    uses lazy import so test collection does NOT require a live environment.

    To execute runtime tests, operator MUST:
      1. activate the project venv (`uv sync` or `pip install -e .`)
      2. provide `.env` with SUPABASE_* keys + DATABASE_URL
      3. run `pytest tests/api/smoke/ -v`
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
