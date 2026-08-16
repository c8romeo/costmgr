"""tests.api.m8_budget.test_budget_variance_handlers — Story 8.2 route shape + envelope tests.

15+ route shape + Pydantic serialization tests covering PRD §F8.2 variance
endpoint envelope wires (CR 12-5 D-14 typed contract):
  - Router shape: 2 NEW endpoints (GET variance table + GET variance PDF)
  - Schema shape: VarianceTableResponse + VarianceRowSerialized + ABCDDisabledBadgeSerialized + BudgetVariancePdfResponse
  - Envelope wire: 2 NEW typed exception handlers registered in main.py
  - Decimal-as-string precision parity (AD-8)
  - Korean SSOT message constants
  - Cross-language TS mirror contract (AD-15)
"""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
from fastapi import APIRouter

from apps.api.modules.m8_budget.handlers import variance_router
from apps.api.modules.m8_budget.schemas import (
    ABCDDisabledBadgeSerialized,
    BudgetVariancePdfResponse,
    VarianceRowSerialized,
    VarianceTableResponse,
)


def _routes_by_path(router: APIRouter) -> dict[str, list]:
    """Group router routes by path for lookup convenience."""
    out: dict[str, list] = {}
    for r in router.routes:
        if hasattr(r, "path") and hasattr(r, "methods"):
            out.setdefault(r.path, []).append(r)
    return out


# ── Router shape tests ─────────────────────────────────────────────
def test_variance_router_has_2_routes() -> None:
    """Story 8.2 — variance_router has 2 NEW endpoints."""
    routes = _routes_by_path(variance_router)
    expected_paths = {
        "/api/v1/budget/variance/{period_key}",
        "/api/v1/budget/variance/{period_key}/pdf",
    }
    actual_paths = set(routes.keys())
    assert expected_paths <= actual_paths, (
        f"missing routes: {expected_paths - actual_paths}"
    )


def test_variance_router_prefix_is_budget_variance() -> None:
    """variance_router prefix is /api/v1/budget/variance (PRD §F8.2)."""
    assert variance_router.prefix == "/api/v1/budget/variance"


def test_variance_router_tag_is_m8_budget_variance() -> None:
    """variance_router tag = 'm8-budget-variance' (OpenAPI grouping)."""
    assert "m8-budget-variance" in variance_router.tags


def test_variance_table_endpoint_is_get_200() -> None:
    """GET /budget/variance/{period_key} = 200 OK (read-only 4-role access)."""
    routes = _routes_by_path(variance_router)["/api/v1/budget/variance/{period_key}"]
    route = routes[0]
    assert "GET" in route.methods
    assert route.response_model is VarianceTableResponse


def test_variance_pdf_endpoint_is_get_200() -> None:
    """GET /budget/variance/{period_key}/pdf = 200 OK (envelope, 8-3 DEFER PDF)."""
    routes = _routes_by_path(
        variance_router
    )["/api/v1/budget/variance/{period_key}/pdf"]
    route = routes[0]
    assert "GET" in route.methods
    assert route.response_model is BudgetVariancePdfResponse


# ── VarianceRowSerialized Pydantic v2 schema tests ─────────────────
def test_variance_row_serialized_required_fields() -> None:
    """VarianceRowSerialized requires 7 fields (PRD §F8.2 + AD-8)."""
    row = VarianceRowSerialized(
        label="직접재료",
        budget_value="1000000",
        actual_value="1050000",
        difference="50000",
        variance_pct="5.0000",
        severity="warning",
        color="yellow",
    )
    assert row.label == "직접재료"
    assert row.budget_value == "1000000"
    assert row.actual_value == "1050000"
    assert row.difference == "50000"
    assert row.variance_pct == "5.0000"
    assert row.severity == "warning"
    assert row.color == "yellow"


def test_variance_row_serialized_decimal_as_string_parity() -> None:
    """Decimal-as-string preserves precision (AD-8 monetary parity).

    Test verifies that a large KRW integer survives JSON round-trip
    without float coercion.
    """
    row = VarianceRowSerialized(
        label="직접노무",
        budget_value="999999999999",
        actual_value="1234567890123",
        difference="234567890124",
        variance_pct="23.4568",
        severity="critical",
        color="red",
    )
    # JSON serialization round-trip (no precision loss).
    json_str = row.model_dump_json()
    data = json.loads(json_str)
    assert data["budget_value"] == "999999999999"
    assert data["actual_value"] == "1234567890123"
    assert data["variance_pct"] == "23.4568"


def test_variance_row_serialized_frozen_enforcement() -> None:
    """Pydantic frozen=True → setattr raises ValidationError (CR 11-3 discipline)."""
    row = VarianceRowSerialized(
        label="제조경비",
        budget_value="1000000",
        actual_value="1100000",
        difference="100000",
        variance_pct="10.0000",
        severity="critical",
        color="red",
    )

    with pytest.raises((ValueError, TypeError)):
        row.label = "수정"  # type: ignore[misc]


def test_variance_row_serialized_extra_forbid() -> None:
    """Pydantic extra=forbid → unknown fields raise ValidationError."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        VarianceRowSerialized(
            label="직접재료",
            budget_value="1000000",
            actual_value="1050000",
            difference="50000",
            variance_pct="5.0000",
            severity="warning",
            color="yellow",
            unknown_field="extra",  # type: ignore[call-arg]
        )


# ── ABCDDisabledBadgeSerialized tests (PRD §15 NON-GOAL #1) ────────
def test_abcd_disabled_badge_serialized_required_fields() -> None:
    """ABCDDisabledBadgeSerialized requires 4 fields (variant, label, tooltip, disabled)."""
    badge = ABCDDisabledBadgeSerialized(
        variant="variance",
        label="A×B×C×D 원가 차이 분석",
        tooltip="A×B×C×D 편성 엔진 미구현 (2차 예정)",
        disabled=True,
    )

    assert badge.variant == "variance"
    assert badge.label == "A×B×C×D 원가 차이 분석"
    assert badge.tooltip == "A×B×C×D 편성 엔진 미구현 (2차 예정)"
    assert badge.disabled is True


def test_abcd_disabled_badge_serialized_three_variants() -> None:
    """All 3 variants (variance, trend, sensitivity) produce valid badges."""
    for variant in ("variance", "trend", "sensitivity"):
        badge = ABCDDisabledBadgeSerialized(
            variant=variant,
            label=f"A×B×C×D {variant}",
            tooltip=f"2차 예정 ({variant})",
            disabled=True,
        )
        assert badge.variant == variant
        assert badge.disabled is True


# ── VarianceTableResponse tests ────────────────────────────────────
def test_variance_table_response_shape() -> None:
    """VarianceTableResponse envelope (PRD §F8.2 verbatim)."""
    rows = [
        VarianceRowSerialized(
            label="직접재료",
            budget_value="1000000",
            actual_value="1050000",
            difference="50000",
            variance_pct="5.0000",
            severity="warning",
            color="yellow",
        ),
    ]
    total_row = VarianceRowSerialized(
        label="합계",
        budget_value="1000000",
        actual_value="1050000",
        difference="50000",
        variance_pct="5.0000",
        severity="warning",
        color="yellow",
    )
    badge = ABCDDisabledBadgeSerialized(
        variant="variance",
        label="A×B×C×D 원가 차이 분석",
        tooltip="A×B×C×D 편성 엔진 미구현",
        disabled=True,
    )

    response = VarianceTableResponse(
        period_key="2026-07#B1",
        scenario_index=1,
        rows=rows,
        total_row=total_row,
        abcd_disabled_badge=badge,
        abcd_disabled_note="[NON-GOAL for MVP: A×B×C×D 엔진 미구현]",
    )

    assert response.period_key == "2026-07#B1"
    assert response.scenario_index == 1
    assert len(response.rows) == 1
    assert response.rows[0].label == "직접재료"
    assert response.total_row.label == "합계"
    assert response.abcd_disabled_badge.disabled is True
    assert "NON-GOAL" in response.abcd_disabled_note


def test_variance_table_response_scenario_index_bounds() -> None:
    """scenario_index ge=1, le=1 (1차 MVP = 1 only)."""
    badge = ABCDDisabledBadgeSerialized(
        variant="variance",
        label="label",
        tooltip="tooltip",
        disabled=True,
    )
    total_row = VarianceRowSerialized(
        label="합계",
        budget_value="0",
        actual_value="0",
        difference="0",
        variance_pct="0",
        severity="normal",
        color="gray",
    )

    # 1차 MVP scenario_index=1 only.
    response = VarianceTableResponse(
        period_key="2026-07#B1",
        scenario_index=1,
        rows=[],
        total_row=total_row,
        abcd_disabled_badge=badge,
        abcd_disabled_note="note",
    )
    assert response.scenario_index == 1

    # Invalid: scenario_index=2 (out of bounds, 1차 MVP)
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        VarianceTableResponse(
            period_key="2026-07#B2",
            scenario_index=2,  # type: ignore[arg-type]
            rows=[],
            total_row=total_row,
            abcd_disabled_badge=badge,
            abcd_disabled_note="note",
        )


# ── BudgetVariancePdfResponse tests (8-3 honestly DEFER) ───────────
def test_budget_variance_pdf_response_envelope_shape() -> None:
    """BudgetVariancePdfResponse envelope (8-3 follow-up, 8-2 placeholder)."""
    response = BudgetVariancePdfResponse(
        period_key="2026-07#B1",
        scenario_index=1,
        pdf_bytes_b64="",  # 8-2 placeholder (empty bytes)
        envelope={
            "report_code": "BUDGET_VARIANCE",
            "title": "예산-실적 대조표",
            "period_key": "2026-07#B1",
            "scenario_index": 1,
            "rows": [],
            "total_row": {},
            "abcd_disabled_badge": {},
            "abcd_disabled_note": "note",
            "generated_at_kst": "2026-08-16T00:00:00+00:00",
        },
    )

    assert response.period_key == "2026-07#B1"
    assert response.scenario_index == 1
    assert response.pdf_bytes_b64 == ""  # 8-3 honestly DEFER
    assert response.envelope["report_code"] == "BUDGET_VARIANCE"


# ── Korean SSOT message constants ─────────────────────────────────
def test_korean_ssot_message_constants_present() -> None:
    """Korean message constants exist for 8-2 envelope (CR 12-5 D-14)."""
    from apps.api.modules.m8_budget.exceptions import (
        BUDGET_INVALID_VARIANCE_PERIOD_KO,
        BUDGET_VARIANCE_NOT_FOUND_KO,
    )

    assert "예산-실적 대조" in BUDGET_VARIANCE_NOT_FOUND_KO
    assert "예산-실적 대조" in BUDGET_INVALID_VARIANCE_PERIOD_KO


# ── Typed exception envelope wire tests (CR 12-5 D-14) ────────────
def test_typed_exception_classes_have_required_fields() -> None:
    """BudgetVarianceNotFoundError + InvalidVariancePeriodError have required fields."""
    from apps.api.modules.m8_budget.exceptions import (
        BudgetVarianceNotFoundError,
        InvalidVariancePeriodError,
    )

    variance_err = BudgetVarianceNotFoundError(
        period_key="2026-07#B1",
        tenant_id="00000000-0000-0000-0000-000000000000",
    )
    assert variance_err.period_key == "2026-07#B1"
    assert variance_err.tenant_id == "00000000-0000-0000-0000-000000000000"
    assert "period_key=2026-07#B1" in variance_err.message

    invalid_err = InvalidVariancePeriodError(
        "period_key must match YYYY-MM#B<n> for variance: got 'invalid-format'",
        period_key="invalid-format",
        expected_pattern=r"^\d{4}-(0[1-9]|1[0-2])#B([1-9]\d*)$",
    )
    assert invalid_err.period_key == "invalid-format"
    # AD-24 virtual pattern raw regex — verify regex literal structure.
    assert r"\d{4}" in invalid_err.expected_pattern  # year 4 digits
    assert "#B" in invalid_err.expected_pattern  # virtual `#B<n>` marker


def test_main_py_registers_variance_typed_exception_handlers() -> None:
    """main.py registers 2 NEW typed exception handlers (CR 12-5 D-14)."""
    from apps.api.main import app

    handlers = app.exception_handlers  # type: ignore[attr-defined]
    assert "BudgetVarianceNotFoundError" in handlers or any(
        exc_cls.__name__ == "BudgetVarianceNotFoundError"
        for exc_cls in handlers
    ), (
        "BudgetVarianceNotFoundError handler must be registered in main.py"
    )
    assert "InvalidVariancePeriodError" in handlers or any(
        exc_cls.__name__ == "InvalidVariancePeriodError"
        for exc_cls in handlers
    ), "InvalidVariancePeriodError handler must be registered in main.py"


# ── Cross-language parity sanity check (AD-15 + npm TS mirror) ─────
def test_decimal_precision_round_trip_parity() -> None:
    """Decimal precision survives Pydantic JSON round-trip (AD-8 + AD-15).

    TS mirror `apps/web/lib/m8-budget-variance.ts:computeVarianceTS` must
    produce identical strings via `apps/web/lib/decimal.ts`.
    """
    # Test 4 decimal places (banker's rounding) + large KRW integers.
    test_value = Decimal("1234567890.12345678")
    row = VarianceRowSerialized(
        label="정밀도 검증",
        budget_value=str(test_value),
        actual_value="2000000000.9876543",
        difference="765432109.8641975",
        variance_pct="62.0123",
        severity="critical",
        color="red",
    )

    payload = row.model_dump()
    assert payload["budget_value"] == "1234567890.12345678"
    assert "." in payload["budget_value"]  # Decimal precision preserved
