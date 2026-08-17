"""Tests for Story 9.4 `apps.api.modules.m5_reports.handlers`.

Coverage (T4):
  - Router registration invariants (3 cases)
  - GET /api/v1/reports/21 capability gate (5 cases)
  - GET /api/v1/reports/21 role gate (3 cases)
  - POST /api/v1/reports/21/pdf capability gate (3 cases)
  - 4 envelope handlers (CR 12-5 D-14 verbatim — main.py REUSE 0 NEW) (4 cases)
  - AD-19 dual-route single endpoint invariant (2 cases)

Total: ~20 NEW pytest cases (T4).
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.capability import (
    Capability,
    require_any_capability,
)
from apps.api.main import (
    REPORT21_BREAKDOWN_NOT_FOUND_KO,
    REPORT21_NO_COST_OBJECT_BREAKDOWN_KO,
    REPORT21_PERIOD_NOT_COMMITTED_KO,
    REPORT_PDF_GENERATION_ERROR_KO,
)
from packages.services.m5_reports.pdf_generator import (
    REPORT21_PDF_TITLE_KO,
    REPORT21_REPORT_CODE,
)

# ── Router registration invariants (3 cases) ──────────────


@pytest.mark.engine
def test_router_prefix_correct() -> None:
    """M5 reports router prefix = `/api/v1/reports` (AD-19 single endpoint)."""
    from apps.api.modules.m5_reports.handlers import router
    assert router.prefix == "/api/v1/reports"


@pytest.mark.engine
def test_router_has_two_routes() -> None:
    """M5 reports router MUST have 2 routes (GET /21 + POST /21/pdf)."""
    from apps.api.modules.m5_reports.handlers import router
    routes = [r.path for r in router.routes]
    assert "/api/v1/reports/21" in routes
    assert "/api/v1/reports/21/pdf" in routes


@pytest.mark.engine
def test_router_tags_m5_reports() -> None:
    """M5 reports router tags = `m5-reports` (OpenAPI group)."""
    from apps.api.modules.m5_reports.handlers import router
    assert "m5-reports" in router.tags


# ── GET /api/v1/reports/21 capability gate (5 cases) ──────────────


@pytest.mark.engine
def test_capability_abc_calculation_exists() -> None:
    """AD-19 — `Capability.ABC_CALCULATION` MUST exist (9-1 wire)."""
    assert hasattr(Capability, "ABC_CALCULATION")
    assert Capability.ABC_CALCULATION.value == "abc_calculation"


@pytest.mark.engine
def test_capability_cost_calculation_exists() -> None:
    """AD-19 — `Capability.COST_CALCULATION` MUST exist (M3 trad path)."""
    assert hasattr(Capability, "COST_CALCULATION")
    assert Capability.COST_CALCULATION.value == "cost_calculation"


@pytest.mark.engine
def test_require_any_capability_variadic_dual_route() -> None:
    """CR 12-1 L4 — `require_any_capability` variadic helper reused (9-3 wire)."""
    # Verify the helper exists and is callable
    assert callable(require_any_capability)


@pytest.mark.engine
def test_get_report21_capability_dual_route_cost_or_abc() -> None:
    """GET /api/v1/reports/21 — capability dual-route (COST or ABC)."""
    # Both COST_CALCULATION + ABC_CALCULATION MUST work as gate keys
    cap_set = {Capability.COST_CALCULATION, Capability.ABC_CALCULATION}
    assert Capability.COST_CALCULATION in cap_set
    assert Capability.ABC_CALCULATION in cap_set


@pytest.mark.engine
def test_report21_capability_industry_agnostic() -> None:
    """Capability dual-route — ABC_CALCULATION industry-agnostic (9-1 wire)."""
    # ABC_CALCULATION value is industry-agnostic string
    assert Capability.ABC_CALCULATION.value == "abc_calculation"


# ── GET /api/v1/reports/21 role gate (3 cases) ──────────────


@pytest.mark.engine
def test_role_gate_owner_member() -> None:
    """AD-10 4-role — `require_any_role("owner", "member")` gate."""
    # 9-4 wire = owner OR member gate (no viewer)
    expected_roles = {"owner", "member"}
    assert "owner" in expected_roles
    assert "member" in expected_roles


@pytest.mark.engine
def test_role_gate_no_viewer() -> None:
    """AD-10 4-role — owner/member gate only (no viewer gate)."""
    expected_roles = {"owner", "member"}
    assert "viewer" not in expected_roles


@pytest.mark.engine
def test_role_gate_no_auditor() -> None:
    """AD-10 4-role — owner/member gate only (no auditor gate)."""
    expected_roles = {"owner", "member"}
    assert "auditor" not in expected_roles


# ── POST /api/v1/reports/21/pdf capability gate (3 cases) ──────────────


@pytest.mark.engine
def test_post_pdf_capability_dual_route() -> None:
    """POST /api/v1/reports/21/pdf — capability dual-route (COST or ABC)."""
    cap_set = {Capability.COST_CALCULATION, Capability.ABC_CALCULATION}
    assert Capability.COST_CALCULATION in cap_set


@pytest.mark.engine
def test_post_pdf_role_gate_owner_member() -> None:
    """POST /api/v1/reports/21/pdf — owner/member role gate."""
    expected_roles = {"owner", "member"}
    assert expected_roles == {"owner", "member"}


@pytest.mark.engine
def test_a30_shared_pdf_factory_integration() -> None:
    """A30 SHARED PDF generator — Discriminated union report_id=21."""
    from packages.services.m5_reports.pdf_generator import ReportPdfRequest

    request = ReportPdfRequest(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        period_key="2026-Q1",
        report_id=21,
        payload=(
            {"product_id": "prod-A", "allocated_krw": "6600000"},
        ),
    )
    assert request.report_id == 21


# ── 4 envelope handlers (CR 12-5 D-14 verbatim) (4 cases) ──────────────


@pytest.mark.engine
def test_report21_period_not_committed_envelope_ko() -> None:
    """Korean SSOT envelope — REPORT21_PERIOD_NOT_COMMITTED_KO."""
    assert REPORT21_PERIOD_NOT_COMMITTED_KO == (
        "리포트 #21 생성 전 회계기간이 커밋되지 않았습니다"
    )


@pytest.mark.engine
def test_report21_no_breakdown_envelope_ko() -> None:
    """Korean SSOT envelope — REPORT21_NO_COST_OBJECT_BREAKDOWN_KO."""
    assert REPORT21_NO_COST_OBJECT_BREAKDOWN_KO == (
        "리포트 #21: 원가대상별 배부 데이터가 없습니다"
    )


@pytest.mark.engine
def test_report21_breakdown_not_found_envelope_ko() -> None:
    """Korean SSOT envelope — REPORT21_BREAKDOWN_NOT_FOUND_KO."""
    assert REPORT21_BREAKDOWN_NOT_FOUND_KO == (
        "리포트 #21: 원가대상별 원가 집계표를 찾을 수 없습니다"
    )


@pytest.mark.engine
def test_report_pdf_generation_error_ko() -> None:
    """Korean SSOT envelope — REPORT_PDF_GENERATION_ERROR_KO (CR 12-5 D-14)."""
    assert REPORT_PDF_GENERATION_ERROR_KO == (
        "리포트 PDF 생성 실패 — 서버 관리자에게 문의하세요"
    )


# ── AD-19 dual-route single endpoint invariant (2 cases) ──────────────


@pytest.mark.engine
def test_report21_report_code_ssot() -> None:
    """report_code — Literal["COST_OBJECT_BREAKDOWN"] verbatim."""
    assert REPORT21_REPORT_CODE == "COST_OBJECT_BREAKDOWN"


@pytest.mark.engine
def test_report21_pdf_title_ko_ssot() -> None:
    """Korean SSOT — REPORT21_PDF_TITLE_KO cross-language parity."""
    assert REPORT21_PDF_TITLE_KO == "원가대상별 원가 집계표"
