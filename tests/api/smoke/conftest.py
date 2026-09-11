"""tests.api.smoke.conftest — K-4 wire 1 MVP-critical smoke test fixtures.

K-4 wire 1 (cj-style 294번째, 2026-09-11 KST, D-3) — option β docs+test entry.
K-3 chain 5/5 DONE + K-4 entry decision wire (cj-style 293번째) DONE 후 MVP-critical
10 flows 의 runtime smoke test scaffolding.

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


def _find_route(app_obj: FastAPI, full_path: str, method: str) -> bool:
    """Find if a route with given full path + method exists in the app."""
    for route in app_obj.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            if route.path == full_path and method.upper() in route.methods:
                return True
    return False


def _count_routes_with_prefix(app_obj: FastAPI, prefix: str) -> int:
    """Count routes that match a given prefix substring."""
    return sum(
        1
        for r in app_obj.routes
        if hasattr(r, "path") and prefix in r.path
    )


def _routes_with_prefix(app_obj: FastAPI, prefix: str) -> list[str]:
    """List route paths matching a given prefix substring."""
    return sorted(
        {r.path for r in app_obj.routes if hasattr(r, "path") and prefix in r.path}
    )
