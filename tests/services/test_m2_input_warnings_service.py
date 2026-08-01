"""tests.services.test_m2_input_warnings_service — Story 3.3 service helper tests.

Module-level helper tests + typed exception shape tests. AD-1 / AD-5
binding: pure helpers only; DB-touching helpers are tested via handler
integration tests in `tests/api/test_monthly_input_warnings.py` (skipif).

Mapping to spec (Task 7):
- `_load_opening_balance_from_period` (4 tests) — JSONB → dict[UUID, Decimal]
- `_make_row_duck` (3 tests) — product_map lookup + null/unknown paths
- `_warning_to_response` (3 tests) — UUID details + timestamp preservation
- 2 typed exceptions (4 tests) — message + details shape + inheritance
- aggregate helper (2 tests) — AC #5 + severity ASC
= 16 service-layer tests (Story 3.3 §Task 7 — pure helpers slice).

The 5 cross-language parity tests live in
`tests/integration/test_m2_input_label_consistency.py` (added in T5).
DB-backed handler integration tests live in
`tests/api/test_monthly_input_warnings.py` (6 skipif added in T7).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from apps.api.core.db_models import (
    MonthlyInputPeriod,
)
from apps.api.modules.m2_input.services.monthly_input_service import (
    MonthlyInputInventoryProjectionError,
    MonthlyInputWarningsReadOnlyError,
    _ProductProjection,
    _make_row_duck,
    _warning_to_response,
    _load_opening_balance_from_period,
)
from packages.services.m2_input.warnings import (
    Warning,
    aggregate_warnings,
)


# ── Period stub ────────────────────────────────────────────────
class _FakePeriod:
    """Lightweight stand-in for `MonthlyInputPeriod` (opening_inventory only).

    Service helper `_load_opening_balance_from_period` reads via
    `getattr(period, "opening_inventory", None)` so this duck type works.
    """

    def __init__(self, opening_inventory: dict | None = None) -> None:
        self.opening_inventory = opening_inventory or {}


def _make_orm_row(
    *,
    stream: str = "sales",
    product_id: uuid.UUID | None = None,
    qty: Decimal | None = None,
) -> Any:
    """Build an object compatible with `_make_row_duck` (no ORM import)."""
    return type(
        "Row",
        (),
        {"stream": stream, "product_id": product_id, "qty": qty},
    )()


# ── _load_opening_balance_from_period (4 tests) ────────────────
def test_load_opening_balance_empty_returns_empty_dict() -> None:
    """No payload → {} (service fallback to 0 for all products)."""
    period = _FakePeriod(opening_inventory=None)
    assert _load_opening_balance_from_period(period) == {}


def test_load_opening_balance_empty_products_list() -> None:
    """Payload present but products=[] → {}."""
    period = _FakePeriod(opening_inventory={"products": []})
    assert _load_opening_balance_from_period(period) == {}


def test_load_opening_balance_with_two_products() -> None:
    """Two valid entries → 2 keys in dict."""
    pid1, pid2 = uuid.uuid4(), uuid.uuid4()
    period = _FakePeriod(
        opening_inventory={
            "products": [
                {"product_id": str(pid1), "qty": 100.0},
                {"product_id": str(pid2), "qty": 50.5},
            ],
        }
    )
    out = _load_opening_balance_from_period(period)
    assert out[pid1] == Decimal("100.0")
    assert out[pid2] == Decimal("50.5")
    assert len(out) == 2


def test_load_opening_balance_rejects_negative_qty() -> None:
    """Defensive: negative opening_qty MUST be rejected (PRD §6.2)."""
    pid = uuid.uuid4()
    period = _FakePeriod(
        opening_inventory={
            "products": [
                {"product_id": str(pid), "qty": -10},  # rejected
                {"product_id": str(uuid.uuid4()), "qty": 5},  # accepted
            ],
        }
    )
    out = _load_opening_balance_from_period(period)
    assert pid not in out
    assert len(out) == 1


def test_load_opening_balance_skips_invalid_entries() -> None:
    """Non-dict entries / invalid UUIDs / None are skipped silently."""
    pid = uuid.uuid4()
    period = _FakePeriod(
        opening_inventory={
            "products": [
                "not a dict",  # skipped
                {"product_id": "not-a-uuid", "qty": 5},  # skipped
                {"product_id": str(pid)},  # skipped (missing qty)
                {"product_id": str(pid), "qty": "5.5"},  # accepted
                {},
            ],
        }
    )
    out = _load_opening_balance_from_period(period)
    assert out == {pid: Decimal("5.5")}


def test_load_opening_balance_period_is_real_orm() -> None:
    """The helper accepts a real `MonthlyInputPeriod` (duck typing)."""
    period = MonthlyInputPeriod(
        period_id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        mode="month_total",
        baseline_revision=1,
        locked_by_calculation=False,
        opening_inventory={"products": []},
        created_at=datetime.now(tz=UTC),
        updated_at=datetime.now(tz=UTC),
    )
    assert _load_opening_balance_from_period(period) == {}


# ── _make_row_duck (3 tests) ────────────────────────────────────
def test_make_row_duck_with_known_product() -> None:
    """Product in map → product_type propagated."""
    pid = uuid.uuid4()
    product_map = {
        pid: _ProductProjection(
            product_id=pid,
            product_code="PRD-0001",
            name_ko="달걀",
            product_type="material",
        )
    }
    row = _make_orm_row(stream="sales", product_id=pid, qty=Decimal("10"))
    duck = _make_row_duck(row, product_map)
    assert duck.stream == "sales"
    assert duck.product_id == pid
    assert duck.qty == Decimal("10")
    assert duck.product_type == "material"


def test_make_row_duck_with_unknown_product_empty_type() -> None:
    """Product not in map → product_type='' (kernel excludes via set membership)."""
    pid = uuid.uuid4()
    row = _make_orm_row(stream="sales", product_id=pid, qty=Decimal("10"))
    duck = _make_row_duck(row, {})
    assert duck.product_type == ""


def test_make_row_duck_with_null_product_id() -> None:
    """product_id=None → no lookup, product_type='' (labor/expenses path)."""
    row = _make_orm_row(stream="labor", product_id=None, qty=None)
    duck = _make_row_duck(row, {})
    assert duck.product_id is None
    assert duck.product_type == ""


# ── _warning_to_response (3 tests) ──────────────────────────────
def test_warning_to_response_basic_shape() -> None:
    """Pydantic model fields mirror the NamedTuple fields."""
    pid = uuid.uuid4()
    ts = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)
    w = Warning(
        code="NEGATIVE_CLOSING_INVENTORY",
        severity="error",
        message_ko="PRD-0001(달걀) 기말재고 -30 → 음수 경고",
        details={
            "product_id": str(pid),
            "closing_qty": "-30",
            "product_code": "PRD-0001",
        },
        stream="sales",
        trace_id="trace-1",
        timestamp=ts,
    )
    resp = _warning_to_response(w)
    assert resp.code == "NEGATIVE_CLOSING_INVENTORY"
    assert resp.severity == "error"
    assert "PRD-0001(달걀)" in resp.message_ko
    assert resp.details["product_id"] == str(pid)
    assert resp.details["closing_qty"] == "-30"
    assert resp.stream == "sales"
    assert resp.trace_id == "trace-1"
    assert resp.timestamp == ts


def test_warning_to_response_coerces_uuid_details() -> None:
    """UUID values inside details are stringified (defensive guard)."""
    w = Warning(
        code="NEGATIVE_CLOSING_INVENTORY",
        severity="error",
        message_ko="m",
        details={"product_id": uuid.uuid4(), "closing_qty": "-1"},
        stream="sales",
        trace_id="t",
        timestamp=datetime.now(tz=UTC),
    )
    resp = _warning_to_response(w)
    assert isinstance(resp.details["product_id"], str)
    assert resp.details["closing_qty"] == "-1"


def test_warning_to_response_overcapacity_preserves_details() -> None:
    """OVERCAPACITY_OPERATING_RATE path — all 7 details fields preserved."""
    w = Warning(
        code="OVERCAPACITY_OPERATING_RATE",
        severity="error",
        message_ko="조업도 100.6%",
        details={
            "operating_rate_pct": "100.60",
            "total_fte_headcount": "1.09",
            "standard_monthly_hours": 228,
            "total_available_hours": "248.52",
            "production_required_hours": "250",
            "limit_pct": "100",
            "period_key": "2026-07",
        },
        stream="production",
        trace_id="trace-x",
        timestamp=datetime.now(tz=UTC),
    )
    resp = _warning_to_response(w)
    assert resp.code == "OVERCAPACITY_OPERATING_RATE"
    assert resp.details["period_key"] == "2026-07"
    assert resp.details["operating_rate_pct"] == "100.60"
    assert resp.details["standard_monthly_hours"] == 228


# ── Typed exception tests (Story 3.3 AC #7) ────────────────────
def test_warnings_read_only_error_shape() -> None:
    """MonthlyInputWarningsReadOnlyError carries field + tenant_id + trace_id."""
    err = MonthlyInputWarningsReadOnlyError(
        tenant_id=uuid.uuid4(),
        field="warnings",
        trace_id="trace-1",
    )
    assert err.field == "warnings"
    assert err.trace_id == "trace-1"
    assert "warnings" in str(err)


def test_warnings_read_only_error_field_isolated() -> None:
    """Field name round-trips for each of the 4 read-only fields."""
    for field in (
        "warnings",
        "is_blocked",
        "warnings_count",
        "top_n_severity",
    ):
        err = MonthlyInputWarningsReadOnlyError(
            tenant_id=uuid.uuid4(),
            field=field,
            trace_id="trace-1",
        )
        assert err.field == field


def test_inventory_projection_error_shape() -> None:
    """MonthlyInputInventoryProjectionError carries details dict."""
    err = MonthlyInputInventoryProjectionError(
        tenant_id=uuid.uuid4(),
        details={"reason": "negative opening_qty", "row_count": 5},
        trace_id="trace-2",
    )
    assert err.details["row_count"] == 5
    assert err.details["reason"] == "negative opening_qty"
    assert "negative opening_qty" in str(err)


def test_inventory_projection_error_inherits_from_exception() -> None:
    """Defensive — error is catchable as Exception."""
    err = MonthlyInputInventoryProjectionError(
        tenant_id=uuid.uuid4(),
        details={"reason": "test"},
        trace_id="t",
    )
    assert isinstance(err, Exception)


# ── Aggregate helper chain (2 tests) ────────────────────────────
def test_aggregate_inventory_and_overcapacity_combined() -> None:
    """AC #5: independent resolution + combined aggregate."""
    pid = uuid.uuid4()
    ts = datetime.now(tz=UTC)
    inv_w = Warning(
        code="NEGATIVE_CLOSING_INVENTORY",
        severity="error",
        message_ko="inv",
        details={"product_id": str(pid), "closing_qty": "-30"},
        stream="sales",
        trace_id="t",
        timestamp=ts,
    )
    op_w = Warning(
        code="OVERCAPACITY_OPERATING_RATE",
        severity="error",
        message_ko="op",
        details={"operating_rate_pct": "110"},
        stream="production",
        trace_id="t",
        timestamp=ts,
    )
    result = aggregate_warnings([inv_w], op_w)
    assert len(result) == 2
    assert result[0].code == "NEGATIVE_CLOSING_INVENTORY"
    assert result[1].code == "OVERCAPACITY_OPERATING_RATE"


def test_aggregate_severity_asc_orders_error_before_warning() -> None:
    """severity ASC: error before warning before info (PRD §A11)."""
    ts = datetime.now(tz=UTC)
    w_info = Warning(
        code="NEGATIVE_CLOSING_INVENTORY",
        severity="info",
        message_ko="info",
        details={"product_id": "x", "closing_qty": "-1"},
        stream="sales",
        trace_id="t",
        timestamp=ts,
    )
    w_err = Warning(
        code="NEGATIVE_CLOSING_INVENTORY",
        severity="error",
        message_ko="err",
        details={"product_id": "y", "closing_qty": "-1"},
        stream="sales",
        trace_id="t",
        timestamp=ts,
    )
    result = aggregate_warnings([w_info, w_err], None)
    assert result[0].severity == "error"
    assert result[1].severity == "info"
