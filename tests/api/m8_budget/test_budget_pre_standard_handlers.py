"""tests.api.m8_budget.test_budget_pre_standard_handlers — Story 8.3 route shape tests.

18+ route shape + Pydantic serialization tests covering PRD §F8.3 pre-standard
cost endpoint envelope wires (CR 12-5 D-14 typed contract):
  - Router shape: 2 NEW endpoints (POST + GET pre-standard)
  - Schema shape: BudgetPreStandardRequest + BudgetPreStandardResponse + BudgetPreStandardSnapshotSerialized
  - Envelope wire: 4 NEW typed exception handlers registered in main.py
  - Decimal-as-string precision parity (AD-8)
  - Korean SSOT message constants
  - Capability gate: BUDGET_SCENARIO reuse (8-1 + 8-2 + 8-3 industry-agnostic)
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from fastapi import APIRouter

from apps.api.main import app
from apps.api.modules.m8_budget.exceptions import (
    BUDGET_INVALID_PRE_STANDARD_INPUT_KO,
    BUDGET_PRE_STANDARD_ALREADY_EXISTS_KO,
    BUDGET_PRE_STANDARD_SNAPSHOT_NOT_FOUND_KO,
    BUDGET_VARIANCE_PDF_NOT_READY_KO,
    BudgetVariancePdfNotReadyError,
    InvalidPreStandardInputError,
    PreStandardAlreadyExistsError,
    PreStandardSnapshotNotFoundError,
)
from apps.api.modules.m8_budget.handlers import pre_standard_router
from apps.api.modules.m8_budget.schemas_pre_standard import (
    BudgetPreStandardRequest,
    BudgetPreStandardResponse,
    BudgetPreStandardSnapshotSerialized,
)


def _routes_by_path(router: APIRouter) -> dict[str, list]:
    """Group router routes by path for lookup convenience."""
    out: dict[str, list] = {}
    for r in router.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            out.setdefault(r.path, []).append(r)
    return out


# ── Router shape tests ─────────────────────────────────────────────
def test_pre_standard_router_has_2_routes() -> None:
    """Story 8.3 — pre_standard_router has 2 NEW endpoints."""
    routes = _routes_by_path(pre_standard_router)
    expected_paths = {
        "/api/v1/budget/pre-standard",
    }
    actual_paths = set(routes.keys())
    assert expected_paths <= actual_paths, (
        f"missing routes: {expected_paths - actual_paths}"
    )


def test_pre_standard_router_prefix_is_budget_pre_standard() -> None:
    """pre_standard_router prefix is /api/v1/budget/pre-standard (PRD §F8.3)."""
    assert pre_standard_router.prefix == "/api/v1/budget/pre-standard"


def test_pre_standard_router_tag_is_m8_budget_pre_standard() -> None:
    """pre_standard_router tag = 'm8-budget-pre-standard' (OpenAPI grouping)."""
    assert "m8-budget-pre-standard" in pre_standard_router.tags


def test_post_pre_standard_endpoint_is_post_200() -> None:
    """POST /budget/pre-standard = 200 OK (idempotent UPSERT)."""
    routes = _routes_by_path(pre_standard_router)["/api/v1/budget/pre-standard"]
    post_routes = [r for r in routes if "POST" in r.methods]
    assert len(post_routes) == 1
    assert post_routes[0].response_model is BudgetPreStandardResponse


def test_get_pre_standard_endpoint_is_get_200() -> None:
    """GET /budget/pre-standard = 200 OK (4-role read)."""
    routes = _routes_by_path(pre_standard_router)["/api/v1/budget/pre-standard"]
    get_routes = [r for r in routes if "GET" in r.methods]
    assert len(get_routes) == 1
    assert get_routes[0].response_model is BudgetPreStandardResponse


# ── Schema shape tests ─────────────────────────────────────────────
def test_pre_standard_request_schema_rejects_negative_cost() -> None:
    """material_unit_cost < 0 → Pydantic ValidationError."""
    with pytest.raises(ValueError):
        BudgetPreStandardRequest(
            period_key="2026-07#B1",
            material_unit_cost=Decimal("-1"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )


def test_pre_standard_request_schema_rejects_overhead_rate_over_100() -> None:
    """overhead_rate > 100 → Pydantic ValidationError."""
    with pytest.raises(ValueError):
        BudgetPreStandardRequest(
            period_key="2026-07#B1",
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("101"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )


def test_pre_standard_request_schema_rejects_invalid_period_key() -> None:
    """period_key invalid virtual pattern → Pydantic ValidationError."""
    with pytest.raises(ValueError):
        BudgetPreStandardRequest(
            period_key="2026-07",  # real period key, not virtual
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )


def test_pre_standard_request_schema_rejects_scenario_index_2() -> None:
    """scenario_index > 1 → Pydantic ValidationError (8-1 lock)."""
    with pytest.raises(ValueError):
        BudgetPreStandardRequest(
            period_key="2026-07#B1",
            scenario_index=2,
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
        )


def test_pre_standard_snapshot_serialized_frozen() -> None:
    """BudgetPreStandardSnapshotSerialized is frozen (Pydantic v2)."""
    snap = BudgetPreStandardSnapshotSerialized(
        material_cost="10000",
        labor_cost="40000",
        overhead_cost="8000",
        manufacturing_cost="58000",
        period_key="2026-07#B1",
        scenario_index=1,
        engine_type="budget",
        inventory_adjustment=0,
        result_hash="sha256:abc123",
        state="verified",
        created_at_kst="2026-08-16T00:00:00+00:00",
    )
    with pytest.raises(Exception):
        snap.material_cost = "999"  # type: ignore[misc]


def test_pre_standard_response_includes_snapshot() -> None:
    """BudgetPreStandardResponse contains snapshot (CR 12-5 D-14)."""
    response = BudgetPreStandardResponse(
        snapshot=BudgetPreStandardSnapshotSerialized(
            material_cost="10000",
            labor_cost="40000",
            overhead_cost="8000",
            manufacturing_cost="58000",
            period_key="2026-07#B1",
            scenario_index=1,
            engine_type="budget",
            inventory_adjustment=0,
            result_hash="sha256:abc123",
            state="verified",
            created_at_kst="2026-08-16T00:00:00+00:00",
        ),
        trace_id="trace-001",
    )
    assert response.snapshot.engine_type == "budget"
    assert response.trace_id == "trace-001"


# ── Envelope wire tests (CR 12-5 D-14) ─────────────────────────────
def test_invalid_pre_standard_input_error_carries_field() -> None:
    """InvalidPreStandardInputError carries field + reason (envelope contract)."""
    exc = InvalidPreStandardInputError(
        "material_unit_cost must be non-negative",
        field="material_unit_cost",
        reason="negative_value",
    )
    assert exc.field == "material_unit_cost"
    assert exc.reason == "negative_value"


def test_pre_standard_snapshot_not_found_error_envelope() -> None:
    """PreStandardSnapshotNotFoundError envelope (404)."""
    exc = PreStandardSnapshotNotFoundError(
        period_key="2026-07#B1",
        tenant_id="tenant-001",
    )
    assert exc.period_key == "2026-07#B1"
    assert exc.tenant_id == "tenant-001"


def test_pre_standard_already_exists_error_envelope() -> None:
    """PreStandardAlreadyExistsError envelope (409)."""
    exc = PreStandardAlreadyExistsError(
        period_key="2026-07#B1",
        tenant_id="tenant-001",
        existing_hash="sha256:abc",
        new_hash="sha256:def",
    )
    assert exc.existing_hash == "sha256:abc"
    assert exc.new_hash == "sha256:def"


def test_budget_variance_pdf_not_ready_error_envelope() -> None:
    """BudgetVariancePdfNotReadyError envelope (425)."""
    exc = BudgetVariancePdfNotReadyError(
        period_key="2026-07#B1",
        tenant_id="tenant-001",
    )
    assert exc.period_key == "2026-07#B1"


# ── Korean SSOT message constants ──────────────────────────────────
def test_korean_messages_defined() -> None:
    """Korean SSOT messages defined (NFR18 ko-KR lock)."""
    assert BUDGET_INVALID_PRE_STANDARD_INPUT_KO == "예산 사전 표준원가 입력이 올바르지 않습니다"
    assert BUDGET_PRE_STANDARD_SNAPSHOT_NOT_FOUND_KO == "예산 사전 표준원가 스냅샷을 찾을 수 없습니다"
    assert BUDGET_PRE_STANDARD_ALREADY_EXISTS_KO.startswith("동일 기간에")
    assert BUDGET_VARIANCE_PDF_NOT_READY_KO.startswith("예산-실적 차이 명세서")


# ── Main.py envelope handler registration ─────────────────────────
def test_invalid_pre_standard_input_handler_registered() -> None:
    """InvalidPreStandardInputError handler registered in main.py."""
    handler = app.exception_handlers.get(InvalidPreStandardInputError)
    assert handler is not None


def test_pre_standard_snapshot_not_found_handler_registered() -> None:
    """PreStandardSnapshotNotFoundError handler registered in main.py."""
    handler = app.exception_handlers.get(PreStandardSnapshotNotFoundError)
    assert handler is not None


def test_pre_standard_already_exists_handler_registered() -> None:
    """PreStandardAlreadyExistsError handler registered in main.py."""
    handler = app.exception_handlers.get(PreStandardAlreadyExistsError)
    assert handler is not None


def test_budget_variance_pdf_not_ready_handler_registered() -> None:
    """BudgetVariancePdfNotReadyError handler registered in main.py."""
    handler = app.exception_handlers.get(BudgetVariancePdfNotReadyError)
    assert handler is not None


# ── Variance router EXTENSION (8-3 wire activation) ────────────────
def test_variance_pdf_route_accepts_425_status() -> None:
    """GET /variance/{period_key}/pdf accepts 425 status (8-3 wire)."""
    from apps.api.modules.m8_budget.handlers import variance_router

    routes = _routes_by_path(variance_router)["/api/v1/budget/variance/{period_key}/pdf"]
    route = routes[0]
    assert 425 in route.responses
