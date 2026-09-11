"""tests.api.smoke.test_mvp_critical_smoke — K-4 wire 1 MVP-critical smoke test.

K-4 wire 1 (cj-style 294번째, 2026-09-11 KST, D-3) — option β docs+test entry.
K-3 chain 5/5 DONE (PRD ↔ capability matrix v1.54 EXTENSION ↔ source code 정합 종합
검증 DONE, ~64 sprints 정직 회복) + K-4 entry decision wire (cj-style 293번째) 의
4 ideas 평가 + K-4 narrow scope (MVP-critical 10 flows) + 3-step verification
method (option α docs-only entry → option β runtime smoke test → option γ blocker-
fix-only) 의 Step 2 진입.

본 파일은 **runtime smoke test entry**:
- PROD source 변경 0건
- test 변경만 (NEW `tests/api/smoke/test_mvp_critical_smoke.py` + NEW
  `tests/api/smoke/conftest.py` + NEW `tests/api/smoke/__init__.py`)
- capability matrix EXTENSION 가능 (K-4 wire 1 scope 외, honestly DEFER)

검증 scope: 10 flows × ~3-4 cases = ~30-35 test cases (lightweight smoke)
- router registration 검증 (apps/api/main.py 의 include_router 정합)
- endpoint path + HTTP method 정합 검증
- response_model schema import 정합 검증
- PRD §F cross-section 정합 (간접 검증)

runtime execution: pytest + project venv + Supabase local emulator 필요.
honest-DEFER: K-4 wire 1 에서 file 생성 + import path 정합 검증만 수행,
runtime test 실행 (pytest) 은 operator 환경에서 실행 결정 wire 보류.

다음 sprint 옵션 (K-4 wire 1.x 보류):
- K-4 wire 1.1 = smoke test runtime execution + blocker surface
- K-4 wire 1.2 = blocker-bug-fix only (option γ scoped)
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI

from tests.api.smoke.conftest import (
    _count_routes_with_prefix,
    _find_route,
    _routes_with_prefix,
)


# ─────────────────────────────────────────────────────────────────────────
# 1. Auth flow smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_auth_routes_registered(app: FastAPI) -> None:
    """Auth 라우터들이 main app 에 등록되어 있다."""
    auth_paths = _routes_with_prefix(app, "/auth")
    assert len(auth_paths) > 0, f"No auth routes registered. Sample: {_routes_with_prefix(app, '')[:5]}"


def test_auth_signup_router_registered(app: FastAPI) -> None:
    """M0 signup_router 가 main app 에 등록되어 있다 (auth 진입점)."""
    # /api/v1/onboarding/complete-signup
    assert _find_route(app, "/api/v1/onboarding/complete-signup", "POST"), \
        "POST /api/v1/onboarding/complete-signup not registered"


def test_auth_audit_router_registered(app: FastAPI) -> None:
    """Auth audit 라우터 (/api/v1/auth/audit) 가 등록되어 있다."""
    auth_audit_paths = _routes_with_prefix(app, "/auth/audit")
    assert len(auth_audit_paths) > 0, "Auth audit router not registered"


# ─────────────────────────────────────────────────────────────────────────
# 2. M0 Onboarding smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_m0_onboarding_tenant_settings_router_registered(app: FastAPI) -> None:
    """M0 onboarding tenant-settings 라우터 (/api/v1/tenant-settings) 가 등록되어 있다."""
    paths = _routes_with_prefix(app, "/tenant-settings")
    assert len(paths) > 0, "M0 onboarding tenant-settings router not registered"


def test_m0_onboarding_has_post_endpoints(app: FastAPI) -> None:
    """M0 onboarding 에는 최소 1개 POST endpoint 가 있어야 한다."""
    posts = [r for r in app.routes if hasattr(r, "path") and hasattr(r, "methods")
             and "/tenant-settings" in r.path and "POST" in r.methods]
    assert len(posts) > 0, "M0 onboarding has no POST endpoints"


def test_m0_onboarding_signup_response_model_exists() -> None:
    """M0 SignupCompleteResponse pydantic 스키마가 import 가능하다."""
    from apps.api.modules.m0_onboarding.schemas import SignupCompleteResponse
    assert SignupCompleteResponse is not None
    # response fields 검증
    fields = SignupCompleteResponse.model_fields
    for required in ("tenant_id", "role", "industry", "settings_version", "trace_id"):
        assert required in fields, f"SignupCompleteResponse missing field: {required}"


# ─────────────────────────────────────────────────────────────────────────
# 3. M1 기준정보 smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_m1_baseline_router_registered(app: FastAPI) -> None:
    """M1 baseline 라우터 (/api/v1/baseline) 가 등록되어 있다."""
    paths = _routes_with_prefix(app, "/baseline")
    assert len(paths) > 0, "M1 baseline router not registered"


def test_m1_baseline_endpoints_have_crud_methods(app: FastAPI) -> None:
    """M1 baseline 엔드포인트들이 GET + POST 를 갖추고 있다 (CRUD 검증)."""
    gets = [r for r in app.routes if hasattr(r, "path") and hasattr(r, "methods")
            and "/baseline" in r.path and "GET" in r.methods]
    posts = [r for r in app.routes if hasattr(r, "path") and hasattr(r, "methods")
             and "/baseline" in r.path and "POST" in r.methods]
    assert len(gets) > 0, "M1 baseline has no GET endpoints"
    assert len(posts) > 0, "M1 baseline has no POST endpoints"


# ─────────────────────────────────────────────────────────────────────────
# 4. M2 월데이터입력 smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_m2_input_router_registered(app: FastAPI) -> None:
    """M2 input 라우터 (/api/v2/monthly-input) 가 등록되어 있다 (v2 prefix 결정 wire 보존)."""
    paths = _routes_with_prefix(app, "/monthly-input")
    assert len(paths) > 0, "M2 input router not registered"


def test_m2_input_has_endpoints(app: FastAPI) -> None:
    """M2 input 엔드포인트들이 등록되어 있다."""
    gets = [r for r in app.routes if hasattr(r, "path") and hasattr(r, "methods")
            and "/monthly-input" in r.path and "GET" in r.methods]
    assert len(gets) > 0, "M2 input has no GET endpoints"


# ─────────────────────────────────────────────────────────────────────────
# 5. M3 원가계산엔진 smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_m3_calculate_router_registered(app: FastAPI) -> None:
    """M3 calculate 라우터가 등록되어 있다 (prefix=/api/v1, path=/calc)."""
    assert _find_route(app, "/api/v1/calc", "POST"), \
        "POST /api/v1/calc not registered (M3 cost calculation endpoint)"


def test_m3_calculate_dual_route_capability_support() -> None:
    """M3 dual-route dispatch (AD-19 + A29 forward-lock) 가 capability 모듈에 정합."""
    from apps.api.core.capability import Capability
    # COST_CALCULATION + ABC_CALCULATION 둘 다 enum 에 존재
    assert hasattr(Capability, "COST_CALCULATION"), "Capability.COST_CALCULATION missing"
    assert hasattr(Capability, "ABC_CALCULATION"), "Capability.ABC_CALCULATION missing"


# ─────────────────────────────────────────────────────────────────────────
# 6. M5 손익보고서 smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_m5_reports_router_registered(app: FastAPI) -> None:
    """M5 reports 라우터 (/api/v1/reports) 가 등록되어 있다."""
    paths = _routes_with_prefix(app, "/reports")
    assert len(paths) > 0, "M5 reports router not registered"


def test_m5_reports_has_get_endpoints(app: FastAPI) -> None:
    """M5 reports 에 GET 엔드포인트가 있다 (조회)."""
    gets = [r for r in app.routes if hasattr(r, "path") and hasattr(r, "methods")
            and "/reports" in r.path and "GET" in r.methods]
    assert len(gets) > 0, "M5 reports has no GET endpoints"


# ─────────────────────────────────────────────────────────────────────────
# 7. M8 예산 smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_m8_budget_scenarios_router_registered(app: FastAPI) -> None:
    """M8 budget scenarios 라우터 (/api/v1/budget/scenarios) 가 등록되어 있다."""
    paths = _routes_with_prefix(app, "/budget/scenarios")
    assert len(paths) > 0, "M8 budget scenarios router not registered"


def test_m8_budget_variance_router_registered(app: FastAPI) -> None:
    """M8 budget variance 라우터 (/api/v1/budget/variance) 가 등록되어 있다."""
    paths = _routes_with_prefix(app, "/budget/variance")
    assert len(paths) > 0, "M8 budget variance router not registered"


def test_m8_budget_has_post_endpoints(app: FastAPI) -> None:
    """M8 budget 에 POST endpoint 가 있다 (시나리오 생성)."""
    posts = [r for r in app.routes if hasattr(r, "path") and hasattr(r, "methods")
             and "/budget/" in r.path and "POST" in r.methods]
    assert len(posts) > 0, "M8 budget has no POST endpoints"


# ─────────────────────────────────────────────────────────────────────────
# 8. M9 ABC smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_m9_abc_router_registered(app: FastAPI) -> None:
    """M9 ABC 라우터 (/api/v1/abc) 가 등록되어 있다."""
    paths = _routes_with_prefix(app, "/abc")
    assert len(paths) > 0, "M9 ABC router not registered"


def test_m9_abc_has_endpoints(app: FastAPI) -> None:
    """M9 ABC 엔드포인트들이 등록되어 있다."""
    gets = [r for r in app.routes if hasattr(r, "path") and hasattr(r, "methods")
            and "/abc" in r.path and "GET" in r.methods]
    assert len(gets) > 0, "M9 ABC has no GET endpoints"


# ─────────────────────────────────────────────────────────────────────────
# 9. Audit log smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_audit_log_router_registered(app: FastAPI) -> None:
    """Audit log 라우터가 등록되어 있다 (PRD §F21 정합)."""
    paths = _routes_with_prefix(app, "/audit-log")
    assert len(paths) > 0, "Audit log router not registered"


def test_audit_log_query_endpoint_exists(app: FastAPI) -> None:
    """GET /audit-log 엔드포인트가 존재한다."""
    assert _find_route(app, "/api/v1/audit-log", "GET"), \
        "GET /api/v1/audit-log not registered"


def test_audit_log_count_endpoint_exists(app: FastAPI) -> None:
    """GET /audit-log/count 엔드포인트가 존재한다."""
    assert _find_route(app, "/api/v1/audit-log/count", "GET"), \
        "GET /api/v1/audit-log/count not registered"


# ─────────────────────────────────────────────────────────────────────────
# 10. Export (CSV) smoke tests
# ─────────────────────────────────────────────────────────────────────────


def test_export_routes_registered(app: FastAPI) -> None:
    """Export 라우터들 (csv/email/pdf/scheduled) 이 등록되어 있다 (cj-282a wire 정합)."""
    exports_csv = _routes_with_prefix(app, "/exports/csv")
    assert len(exports_csv) > 0, "Export CSV routes not registered"


def test_export_csv_endpoint_exists(app: FastAPI) -> None:
    """GET /exports/csv 엔드포인트가 존재한다 (cj-287 AD-56(c) capability gate 정합)."""
    assert _find_route(app, "/api/v1/exports/csv", "GET"), \
        "GET /api/v1/exports/csv not registered"


# ─────────────────────────────────────────────────────────────────────────
# Summary — comprehensive coverage check
# ─────────────────────────────────────────────────────────────────────────


def test_mvp_critical_10_flows_all_registered(app: FastAPI) -> None:
    """MVP-critical 10 flows 의 모든 핵심 라우터가 main app 에 등록되어 있다.

    K-4 narrow scope 결정 wire 보존:
    Auth + M0 Onboarding + M1 기준정보 + M2 월데이터입력 + M3 원가계산엔진
    + M5 손익 + M8 예산 + M9 ABC + Audit log + Export (CSV)
    """
    flows = {
        "Auth (/api/v1/auth/audit)": "/auth/audit",
        "M0 Onboarding (tenant-settings)": "/tenant-settings",
        "M0 Onboarding (signup /onboarding)": "/onboarding",
        "M1 기준정보 (baseline)": "/baseline",
        "M2 월데이터입력 (monthly-input)": "/monthly-input",
        "M3 원가계산엔진 (calc)": "/api/v1/calc",
        "M5 손익 (reports)": "/reports",
        "M8 예산 (budget/scenarios)": "/budget/scenarios",
        "M9 ABC (/abc)": "/abc",
        "Audit log (/audit-log)": "/audit-log",
        "Export CSV (/exports/csv)": "/exports/csv",
    }
    missing: list[str] = []
    for flow_name, prefix in flows.items():
        count = _count_routes_with_prefix(app, prefix)
        if count == 0:
            missing.append(f"{flow_name} (prefix={prefix})")
    assert not missing, (
        f"MVP-critical flow router(s) NOT registered: {missing}. "
        f"Check apps/api/main.py include_router() calls."
    )


def test_mvp_critical_health_endpoint_exists(app: FastAPI) -> None:
    """Health check endpoint 가 등록되어 있다 (smoke test baseline)."""
    # /health (root) 또는 /api/v1/health 둘 중 하나
    found = _find_route(app, "/health", "GET") or _find_route(app, "/api/v1/health", "GET")
    assert found, "Health check endpoint not found"


# ─────────────────────────────────────────────────────────────────────────
# Total route count baseline
# ─────────────────────────────────────────────────────────────────────────


def test_mvp_critical_total_routes_baseline(app: FastAPI) -> None:
    """main app 에 등록된 전체 라우트 수가 baseline 이상이다.

    K-3 chain 5/5 DONE 시점 baseline = ~50+ routes (10 flows × ~5 routes 평균).
    본 test 는 regression detection 용도 (baseline drift 추적).
    """
    total_routes = sum(1 for r in app.routes if hasattr(r, "path"))
    assert total_routes >= 40, (
        f"Total routes ({total_routes}) below baseline (40). "
        f"Possible MVP-critical router missing or main.py regression."
    )
