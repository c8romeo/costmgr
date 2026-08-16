"""tests.services.test_m8_budget_variance_service — Story 8.2.

Service-layer unit tests for `BudgetVarianceService`. These tests
exercise the pure-kernel delegation + 8-2 read-only fetch (PRD §F8.2)
+ ABCD 회색 배지 placeholder (PRD §15 NON-GOAL #1).

Mocking strategy:
  - DB session: AsyncMock + MagicMock (no Postgres dependency)
  - 8-2 atomic wire: `_aggregate_variance_rows` returns empty list
    (8-3 follow-up sprint will wire the production JOIN query honestly)

Kernel-level parity is already covered by
`tests/cost_engine/test_budget_variance.py` (55 tests).

Async tests use `asyncio.run` pattern (CR 4-3 lessons — no pytest-asyncio).
"""

from __future__ import annotations

import asyncio
import dataclasses
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.m8_budget.exceptions import (
    BudgetVarianceNotFoundError,
    BudgetVariancePdfNotReadyError,
    InvalidVariancePeriodError,
)
from apps.api.modules.m8_budget.services.budget_variance_service import (
    BudgetVarianceService,
    VarianceAggregationRow,
    _to_budget_variance_row,
    validate_variance_inputs,
)
from packages.cost_engine.budget_variance import (
    ABCDDisabledBadge,
    VarianceRow,
)


def _make_orm_row(
    *,
    scenario_id: uuid.UUID | None = None,
    tenant_id: uuid.UUID | None = None,
    period_key: str = "2026-07#B1",
    real_period_key: str = "2026-07",
    scenario_index: int = 1,
    scenario_hash: str = "sha256:abc123",
    created_by: uuid.UUID | None = None,
    created_at_kst: datetime | None = None,
) -> Any:
    """Build a mock ORM row (avoid DB dependency)."""
    row = MagicMock()
    row.id = scenario_id or uuid.uuid4()
    row.tenant_id = tenant_id or uuid.uuid4()
    row.period_key = period_key
    row.real_period_key = real_period_key
    row.scenario_index = scenario_index
    row.scenario_hash = scenario_hash
    row.created_by = created_by or uuid.uuid4()
    row.created_at_kst = created_at_kst or datetime.now(UTC)
    return row


def _make_session(
    *,
    scalar_one_or_none_result: Any = None,
) -> AsyncMock:
    """Build a mock AsyncSession with controllable scalar_one_or_none()."""
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = scalar_one_or_none_result
    session.execute = AsyncMock(return_value=execute_result)
    return session


# ── Service __init__ + constructor tests ────────────────────────────
def test_service_init_stores_attrs() -> None:
    """Service stores session + tenant_id + actor_id + trace_id."""
    session = _make_session()
    tenant_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    trace_id = "trace-variance-001"

    service = BudgetVarianceService(
        session,
        tenant_id=tenant_id,
        actor_id=actor_id,
        trace_id=trace_id,
    )

    assert service.session is session
    assert service.tenant_id == tenant_id
    assert service.actor_id == actor_id
    assert service.trace_id == trace_id


# ── fetch_variance_table tests ──────────────────────────────────────
def test_fetch_variance_table_invalid_period_key_raises() -> None:
    """Invalid period_key pattern → InvalidVariancePeriodError (CR 12-5 D-14)."""
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-002",
    )

    with pytest.raises(InvalidVariancePeriodError) as exc_info:
        asyncio.run(service.fetch_variance_table(period_key="not-virtual-format"))

    assert exc_info.value.period_key == "not-virtual-format"
    # DB read should NOT have been attempted (validation guards first).
    session.execute.assert_not_called()


def test_fetch_variance_table_real_period_key_only_raises_invalid() -> None:
    """Real fiscal key `2026-07` (no virtual `#B<n>`) → InvalidVariancePeriodError.

    AD-24: variance endpoint requires VIRTUAL (8-1 wire) period key.
    """
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-003",
    )

    with pytest.raises(InvalidVariancePeriodError):
        asyncio.run(service.fetch_variance_table(period_key="2026-07"))


def test_fetch_variance_table_scenario_not_found_raises() -> None:
    """No scenario row → BudgetVarianceNotFoundError (CR 12-5 D-14 envelope 404)."""
    session = _make_session(scalar_one_or_none_result=None)
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-004",
    )

    with pytest.raises(BudgetVarianceNotFoundError) as exc_info:
        asyncio.run(service.fetch_variance_table(period_key="2026-07#B1"))

    assert exc_info.value.period_key == "2026-07#B1"


def test_fetch_variance_table_happy_path_empty_aggregation() -> None:
    """Scenario exists but aggregation returns empty → empty list (8-3 follow-up)."""
    scenario_row = _make_orm_row(period_key="2026-07#B1")
    session = _make_session(scalar_one_or_none_result=scenario_row)
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-005",
    )

    rows = asyncio.run(service.fetch_variance_table(period_key="2026-07#B1"))

    # 8-2 wire: empty aggregation (8-3 follow-up will wire the JOIN).
    assert rows == []
    session.execute.assert_called_once()


# ── _to_budget_variance_row boundary conversion tests ───────────────
def test_to_budget_variance_row_orm_to_kernel_boundary() -> None:
    """`_to_budget_variance_row` converts DTO → frozen kernel dataclass.

    CR 12-1 L3 precedent — service-layer ORM→kernel boundary conversion.
    """
    agg = VarianceAggregationRow(
        label="직접재료",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1050000"),
    )

    row = _to_budget_variance_row(agg)

    assert isinstance(row, VarianceRow)
    assert row.label == "직접재료"
    assert row.variance.budget_value == Decimal("1000000")
    assert row.variance.actual_value == Decimal("1050000")
    assert row.variance.difference == Decimal("50000")
    # 5% boundary → normal (yellow only at ±5% threshold).
    assert row.color in ("gray", "yellow", "red")


def test_to_budget_variance_row_with_warning_severity() -> None:
    """Variance at exactly +5% → yellow (boundary)."""
    agg = VarianceAggregationRow(
        label="직접노무",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1050000"),
    )

    row = _to_budget_variance_row(agg)

    assert row.color == "yellow"  # +5% exactly → boundary
    assert row.variance.severity == "warning"


def test_to_budget_variance_row_with_critical_severity() -> None:
    """Variance > +10% → red (PRD §F8.2 verbatim)."""
    agg = VarianceAggregationRow(
        label="제조경비",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1100001"),
    )

    row = _to_budget_variance_row(agg)

    assert row.color == "red"
    assert row.variance.severity == "critical"


def test_to_budget_variance_row_zero_budget_normal_color() -> None:
    """budget_value=0 → variance_pct=0 → gray (normal)."""
    agg = VarianceAggregationRow(
        label="기타",
        budget_value=Decimal("0"),
        actual_value=Decimal("0"),
    )

    row = _to_budget_variance_row(agg)

    assert row.color == "gray"
    assert row.variance.severity == "normal"


# ── compute_variance_total tests ────────────────────────────────────
def test_compute_variance_total_empty_rows_returns_zero() -> None:
    """Empty rows → zero 합계 row (defense-in-depth)."""
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-006",
    )

    total = asyncio.run(service.compute_variance_total(rows=[]))

    assert total.label == "합계"
    assert total.variance.budget_value == Decimal("0")
    assert total.variance.actual_value == Decimal("0")
    assert total.variance.difference == Decimal("0")
    assert total.variance.variance_pct == Decimal("0")
    assert total.color == "gray"


def test_compute_variance_total_sum_multiple_rows() -> None:
    """Sum of rows → 합계 row with correct totals (PRD §F8.2 verbatim).

    Row 1: budget=1,000,000 actual=1,050,000 (+5% warning)
    Row 2: budget=500,000 actual=500,000 (0% normal)
    Total: budget=1,500,000 actual=1,550,000 (~+3.33% normal)
    """
    agg1 = VarianceAggregationRow(
        label="직접재료",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1050000"),
    )
    agg2 = VarianceAggregationRow(
        label="직접노무",
        budget_value=Decimal("500000"),
        actual_value=Decimal("500000"),
    )
    row1 = _to_budget_variance_row(agg1)
    row2 = _to_budget_variance_row(agg2)

    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-007",
    )

    total = asyncio.run(service.compute_variance_total(rows=[row1, row2]))

    assert total.label == "합계"
    assert total.variance.budget_value == Decimal("1500000")
    assert total.variance.actual_value == Decimal("1550000")
    assert total.variance.difference == Decimal("50000")
    # Decimal ROUND_HALF_EVEN at 4 decimals.
    assert total.variance.variance_pct == Decimal("3.3333")
    assert total.color == "gray"  # < 5% threshold


def test_compute_variance_total_sum_three_rows_mixed_severity() -> None:
    """3 rows with mixed severity → total severity follows aggregated total.

    Row 1: +5% warning
    Row 2: -5% warning
    Row 3: 0% normal
    Total = 0% (balanced).
    """
    agg1 = VarianceAggregationRow(
        label="A",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1050000"),
    )
    agg2 = VarianceAggregationRow(
        label="B",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("950000"),
    )
    agg3 = VarianceAggregationRow(
        label="C",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1000000"),
    )

    rows = [
        _to_budget_variance_row(a)
        for a in (agg1, agg2, agg3)
    ]

    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-008",
    )

    total = asyncio.run(service.compute_variance_total(rows=rows))

    assert total.label == "합계"
    assert total.variance.budget_value == Decimal("3000000")
    assert total.variance.actual_value == Decimal("3000000")
    assert total.variance.variance_pct == Decimal("0")
    assert total.color == "gray"


# ── fetch_abcd_disabled_badge tests ─────────────────────────────────
def test_fetch_abcd_disabled_badge_default_variant_variance() -> None:
    """Default variant='variance' → A×B×C×D 회색 배지 placeholder (PRD §15 NON-GOAL)."""
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-009",
    )

    badge = asyncio.run(service.fetch_abcd_disabled_badge())

    assert isinstance(badge, dict)
    assert badge["variant"] == "variance"
    assert badge["disabled"] is True
    # Disabled placeholder semantics: label describes placeholder purpose
    # (PRD §15 NON-GOAL #1 + §10 M8 (b)) + tooltip explains "미구현".
    assert badge["label"]  # non-empty
    assert badge["tooltip"]
    assert "미구현" in badge["tooltip"] or "A×B×C×D" in badge["tooltip"]


def test_fetch_abcd_disabled_badge_trend_variant() -> None:
    """variant='trend' → 회색 배지 with trend note."""
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-010",
    )

    badge = asyncio.run(service.fetch_abcd_disabled_badge(variant="trend"))

    assert badge["variant"] == "trend"
    assert badge["disabled"] is True


def test_fetch_abcd_disabled_badge_sensitivity_variant() -> None:
    """variant='sensitivity' → 회색 배지 with sensitivity note."""
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-011",
    )

    badge = asyncio.run(service.fetch_abcd_disabled_badge(variant="sensitivity"))

    assert badge["variant"] == "sensitivity"
    assert badge["disabled"] is True


def test_fetch_abcd_disabled_badge_invalid_variant_raises() -> None:
    """Unknown variant → ValueError (kernel delegation pattern check)."""
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-012",
    )

    with pytest.raises(ValueError, match="variant"):
        asyncio.run(service.fetch_abcd_disabled_badge(variant="unknown"))


# ── generate_budget_variance_pdf tests (8-3 honestly DEFER) ─────────
def test_generate_budget_variance_pdf_returns_empty_bytes() -> None:
    """8-3 wire activation — no pre-standard snapshot → 425 envelope.

    8-2 atomic wire: returns empty bytes (placeholder).
    8-3 wire (8-2 spec line 273 placeholder 해소): delegates to
    BudgetPreStandardService.generate_budget_variance_pdf → 425 if
    pre-standard snapshot NOT yet inserted.
    """
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-013",
    )

    with pytest.raises(BudgetVariancePdfNotReadyError):
        asyncio.run(
            service.generate_budget_variance_pdf(period_key="2026-07#B1")
        )


def test_generate_budget_variance_pdf_with_scenario_index() -> None:
    """scenario_index parameter accepted (default=1) → 425 if not ready.

    8-3 wire: scenario_index != 1 is rejected at pre-standard service
    level (MVP lock). For default scenario_index=1 → 425 if no snapshot.
    """
    session = _make_session()
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-014",
    )

    with pytest.raises(BudgetVariancePdfNotReadyError):
        asyncio.run(
            service.generate_budget_variance_pdf(
                period_key="2026-07#B1",
                scenario_index=1,
            )
        )


# ── fetch_variance_with_total atomic convenience method ────────────
def test_fetch_variance_with_total_empty_returns_zero_total() -> None:
    """Atomic convenience wrapper returns (rows, total_row) tuple (AC #3)."""
    scenario_row = _make_orm_row(period_key="2026-07#B1")
    session = _make_session(scalar_one_or_none_result=scenario_row)
    service = BudgetVarianceService(
        session,
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-015",
    )

    rows, total_row = asyncio.run(
        service.fetch_variance_with_total(period_key="2026-07#B1")
    )

    assert rows == []
    assert total_row.label == "합계"
    assert total_row.color == "gray"


# ── validate_variance_inputs service-layer tests ────────────────────
def test_validate_variance_inputs_happy_path() -> None:
    """valid YYYY-MM#B<n> → no exception."""
    validate_variance_inputs(period_key="2026-07#B1")


def test_validate_variance_inputs_invalid_raises_typed_exception() -> None:
    """invalid period_key → InvalidVariancePeriodError (CR 12-5 D-14 422)."""
    with pytest.raises(InvalidVariancePeriodError) as exc_info:
        validate_variance_inputs(period_key="invalid-format")

    assert exc_info.value.period_key == "invalid-format"
    # expected_pattern holds the raw regex (AD-24 verbatim — 8-1 wire baseline).
    assert exc_info.value.expected_pattern == r"^\d{4}-(0[1-9]|1[0-2])#B([1-9]\d*)$"
    # Message contains human-readable YYYY-MM#B<n> hint (CR 12-5 D-14).
    assert "YYYY-MM#B<n>" in exc_info.value.message


def test_validate_variance_inputs_real_period_key_raises() -> None:
    """Real fiscal key without virtual `#B<n>` → InvalidVariancePeriodError."""
    with pytest.raises(InvalidVariancePeriodError):
        validate_variance_inputs(period_key="2026-07")


# ── VarianceAggregationRow frozen dataclass tests ──────────────────
def test_variance_aggregation_row_frozen() -> None:
    """`VarianceAggregationRow` is frozen (setattr raises FrozenInstanceError)."""
    agg = VarianceAggregationRow(
        label="직접재료",
        budget_value=Decimal("1000000"),
        actual_value=Decimal("1050000"),
    )

    with pytest.raises((AttributeError, Exception)):
        agg.label = "수정"  # type: ignore[misc]


def test_variance_aggregation_row_decimal_preserved() -> None:
    """Decimal values preserved (no float coercion)."""
    agg = VarianceAggregationRow(
        label="직접재료",
        budget_value=Decimal("1234567.89"),
        actual_value=Decimal("999999.999"),
    )

    assert agg.budget_value == Decimal("1234567.89")
    assert agg.actual_value == Decimal("999999.999")


# ── Public API + pure kernel delegation sanity tests ───────────────
def test_kernel_color_threshold_constants_match_spec() -> None:
    """Spec severity thresholds: ±5% yellow / ±10% red (PRD §F8.2 verbatim)."""
    from packages.cost_engine.budget_variance import (
        SEVERITY_THRESHOLD_CRITICAL_PCT,
        SEVERITY_THRESHOLD_WARNING_PCT,
    )

    assert Decimal("5") == SEVERITY_THRESHOLD_WARNING_PCT
    assert Decimal("10") == SEVERITY_THRESHOLD_CRITICAL_PCT


def test_kernel_abcd_disabled_badge_dataclass_shape() -> None:
    """ABCDDisabledBadge is a frozen dataclass with 4 fields."""
    badge = ABCDDisabledBadge(
        variant="variance",
        label="2차 예정",
        tooltip="A×B×C×D 편성 엔진 미구현",
        disabled=True,
    )

    assert badge.variant == "variance"
    assert badge.disabled is True
    # Frozen check.
    with pytest.raises((AttributeError, dataclasses.FrozenInstanceError)):
        badge.disabled = False  # type: ignore[misc]
