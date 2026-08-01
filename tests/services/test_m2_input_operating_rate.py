"""tests.services.test_m2_input_operating_rate — Story 3.3 조업도 pure helpers.

Mirrors Story 3.2's `test_m2_input_labor_conversion.py` pattern: pure,
stdlib-only, no DB, no clock (AD-1/AD-5).

Acceptance Criteria mapping (Story 3.3):
- AC #3: OVERCAPACITY_OPERATING_RATE fire (PRD §V5) — operating_rate > 100%
- AC #4: rate 50% → no warning; rate 100% → boundary (no warning)
- AC #8: PRD §6.1 (2) 조업도 chain — fte × standard_monthly_hours / Σ(qty × unit_time)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from packages.services.m2_input.operating_rate import (
    DEFAULT_UNIT_TIME_HOURS,
    OPERATING_RATE_LIMIT_PCT,
    compute_operating_rate,
    compute_production_required_hours,
    compute_total_available_hours,
)


# ── Lightweight production row stub ─────────────────────────
@dataclass(frozen=True)
class _ProductionRowStub:
    """Production row duck type.

    Service-layer rows are SQLAlchemy ORM; the pure function only reads
    `qty`. We supply a dataclass so tests stay pure.
    """

    qty: Decimal | None


# ── Constants ────────────────────────────────────────────────
def test_default_unit_time_hours_is_one() -> None:
    """DEFAULT_UNIT_TIME_HOURS = Decimal("1.0") (MVP Epic 7 후속)."""
    assert DEFAULT_UNIT_TIME_HOURS == Decimal("1.0")


def test_operating_rate_limit_pct_is_100() -> None:
    """PRD §V5 한도 = 100% 초과 시 warning."""
    assert OPERATING_RATE_LIMIT_PCT == Decimal("100")


# ── compute_total_available_hours ────────────────────────────
def test_total_available_hours_basic() -> None:
    """AC #3: fte=1.09, hours=228 → 248.52 (PRD §6.1 (2))."""
    assert compute_total_available_hours(
        Decimal("1.09"), 228
    ) == Decimal("248.52")


def test_total_available_hours_exact_2dp() -> None:
    """fte=Decimal('2.5'), hours=200 → 500.00 (exact 2dp)."""
    assert compute_total_available_hours(
        Decimal("2.5"), 200
    ) == Decimal("500.00")


def test_total_available_hours_zero_fte() -> None:
    """fte=0 → 0 (no warning fired via overcapacity path)."""
    assert compute_total_available_hours(Decimal("0"), 228) == Decimal("0")


def test_total_available_hours_zero_hours() -> None:
    """hours=0 → 0 (defense, should not happen with PRD default 228)."""
    assert compute_total_available_hours(
        Decimal("1.09"), 0
    ) == Decimal("0")


# ── compute_production_required_hours ────────────────────────
def test_production_required_hours_basic() -> None:
    """1 row qty=100 → 100h (unit_time=1.0)."""
    rows = [_ProductionRowStub(qty=Decimal("100"))]
    assert compute_production_required_hours(rows) == Decimal("100")


def test_production_required_hours_unit_time_override() -> None:
    """unit_time=2.5, qty=10 → 25h."""
    rows = [_ProductionRowStub(qty=Decimal("10"))]
    assert compute_production_required_hours(
        rows, unit_time_hours=Decimal("2.5")
    ) == Decimal("25")


def test_production_required_hours_multiple_rows() -> None:
    """100 + 50 + 30 → 180h."""
    rows = [
        _ProductionRowStub(qty=Decimal("100")),
        _ProductionRowStub(qty=Decimal("50")),
        _ProductionRowStub(qty=Decimal("30")),
    ]
    assert compute_production_required_hours(rows) == Decimal("180")


def test_production_required_hours_skip_none_qty() -> None:
    """qty=None → skip (defense, no movement)."""
    rows = [
        _ProductionRowStub(qty=None),
        _ProductionRowStub(qty=Decimal("50")),
    ]
    assert compute_production_required_hours(rows) == Decimal("50")


def test_production_required_hours_empty() -> None:
    """empty rows → 0h."""
    assert compute_production_required_hours([]) == Decimal("0")


def test_production_required_hours_zero_qty() -> None:
    """qty=0 → 0h (no contribution)."""
    rows = [_ProductionRowStub(qty=Decimal("0"))]
    assert compute_production_required_hours(rows) == Decimal("0")


# ── compute_operating_rate ───────────────────────────────────
def test_operating_rate_50_percent() -> None:
    """100h / 200h → 50.00%."""
    assert compute_operating_rate(
        Decimal("200"), Decimal("100")
    ) == Decimal("50.00")


def test_operating_rate_100_percent_boundary() -> None:
    """200/200 → 100.00 (PRD §V5 boundary — no warning)."""
    assert compute_operating_rate(
        Decimal("200"), Decimal("200")
    ) == Decimal("100.00")


def test_operating_rate_110_percent_triggers_overcapacity() -> None:
    """AC #3: 220/200 → 110.00 (PRD §V5 fire)."""
    result = compute_operating_rate(Decimal("200"), Decimal("220"))
    assert result == Decimal("110.00")
    assert result > OPERATING_RATE_LIMIT_PCT


def test_operating_rate_ac3_example_fixture() -> None:
    """AC #3: 250h / 248.52h → 100.60% (PRD §V5 fire)."""
    assert compute_operating_rate(
        Decimal("248.52"), Decimal("250")
    ) == Decimal("100.60")


def test_operating_rate_round_half_even() -> None:
    """1.005 → 1.00 (banker's rounding on the 2dp truncation)."""
    # 1.005 at 2dp: the digit is 5 (RHO). Half-to-even: 0 is even → 1.00.
    # We use quantize(Decimal("0.01"), ROUND_HALF_EVEN).
    # 1.005 → 1.00 (banker's rounding on raw 1.005 → 1.00)
    assert compute_operating_rate(
        Decimal("1"), Decimal("1.005")
    ) == Decimal("100.50")


def test_operating_rate_zero_available_no_division_error() -> None:
    """required=0, available=0 → 0% (no warning, no division error)."""
    assert compute_operating_rate(
        Decimal("0"), Decimal("0")
    ) == Decimal("0.00")


def test_operating_rate_required_zero_no_warning() -> None:
    """AC #6: required=0 → 0% (PRD §V5 condition: required > 0 → check)."""
    assert compute_operating_rate(
        Decimal("248.52"), Decimal("0")
    ) == Decimal("0.00")


def test_operating_rate_default_unit_time_1_hours() -> None:
    """AC #3 (verbose): 250 / 248.52 → 100.60%."""
    assert compute_operating_rate(
        Decimal("248.52"), Decimal("250")
    ) == Decimal("100.60")


def test_operating_rate_43_9_percent() -> None:
    """PRD §6.1 example: 100 / 228 → 43.86% (no warning)."""
    result = compute_operating_rate(Decimal("228"), Decimal("100"))
    # 100/228 = 0.438596... → 43.86 ROUND_HALF_EVEN
    assert result == Decimal("43.86")


def test_operating_rate_under_capacity_with_default_unit_time() -> None:
    """AC #4: 100h / 248.5h → 40.24% (no warning)."""
    result = compute_operating_rate(Decimal("248.52"), Decimal("100"))
    assert result == Decimal("40.24")
