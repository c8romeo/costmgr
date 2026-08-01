"""tests.services.test_m2_input_labor_conversion — Story 3.2 pure helpers.

Mirrors Story 3.1's `test_m2_input_completion.py` pattern:
- Pure-Python tests (no DB, no clock, no random)
- AD-1/AD-5 binding: every assertion operates on the pure functions in
  `packages.services.m2_input.labor_conversion`
- Cross-language parity covered separately by
  `tests/integration/test_m2_input_label_consistency.py`

Acceptance Criteria mapping (Story 3.2):
- AC #1: pay_type='daily' 3×8/22 → 1.09 + 1.09 × 2_500_000 = 2_725_000 (basis 환산)
        + direct sum path 3×8×150_000 = 3_600_000 (new in 3.2)
- AC #2: pay_type='monthly' breakdown 5 fields + company_burden_rate → 7_617_250
- AC #3: tenant_settings.payroll.* override (per-field)
- AC #4: daily-mode rollup Σ sum
- AC #5: fte_* read-only (defense at service layer, not tested here)
- AC #6: capability unchanged (not tested here — covered by Story 3.1 tests)
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.services.m2_input import (
    DEFAULT_PAYROLL,
    FteDisplay,
    PayType,
    PayTypeBreakdown,
    PayrollSettings,
    build_fte_display,
    compute_fte_for_daily,
    compute_fte_for_monthly,
    compute_fte_wage_for_daily,
    compute_fte_wage_for_monthly,
    compute_pay_type_breakdown,
    merge_payroll_settings,
    rollup_daily_fte,
)
from packages.services.m2_input.stream_completion import format_fte_headcount


# ── PayType enum (sanity) ───────────────────────────────────
def test_pay_type_monthly_value() -> None:
    """PayType.MONTHLY.value == 'monthly' (AD-15 snake_case)."""
    assert PayType.MONTHLY.value == "monthly"


def test_pay_type_daily_value() -> None:
    """PayType.DAILY.value == 'daily'."""
    assert PayType.DAILY.value == "daily"


# ── PayrollSettings defaults (PRD §6.1) ─────────────────────
def test_default_payroll_values() -> None:
    """PRD §6.1 defaults: 2_500_000 / 22 / 228 / 0.115."""
    p = DEFAULT_PAYROLL
    assert p.monthly_salary_basis_krw == 2_500_000
    assert p.workdays_in_month == 22
    assert p.standard_monthly_hours == 228
    assert p.company_burden_rate == Decimal("0.115")


# ── merge_payroll_settings: per-field override ──────────────
def test_merge_payroll_settings_none_returns_defaults() -> None:
    """override=None → DEFAULT_PAYROLL identity."""
    assert merge_payroll_settings(None) == DEFAULT_PAYROLL


def test_merge_payroll_settings_empty_dict_returns_defaults() -> None:
    """override={} → DEFAULT_PAYROLL identity."""
    assert merge_payroll_settings({}) == DEFAULT_PAYROLL


def test_merge_payroll_settings_all_fields_overridden() -> None:
    """All 4 keys overridden → all used."""
    p = merge_payroll_settings(
        {
            "monthly_salary_basis_krw": 3_500_000,
            "workdays_in_month": 20,
            "standard_monthly_hours": 176,
            "company_burden_rate": "0.123",
        }
    )
    assert p.monthly_salary_basis_krw == 3_500_000
    assert p.workdays_in_month == 20
    assert p.standard_monthly_hours == 176
    assert p.company_burden_rate == Decimal("0.123")


def test_merge_payroll_settings_partial_per_field_fallback() -> None:
    """Only monthly_salary_basis_krw overridden → others stay default."""
    p = merge_payroll_settings({"monthly_salary_basis_krw": 3_500_000})
    assert p.monthly_salary_basis_krw == 3_500_000
    assert p.workdays_in_month == 22  # default preserved
    assert p.standard_monthly_hours == 228  # default preserved
    assert p.company_burden_rate == Decimal("0.115")  # default preserved


def test_merge_payroll_settings_none_value_treated_as_missing() -> None:
    """override key with None value → treated as missing (default applied)."""
    p = merge_payroll_settings({"monthly_salary_basis_krw": None})
    assert p.monthly_salary_basis_krw == 2_500_000


def test_merge_payroll_settings_rejects_negative_basis() -> None:
    """monthly_salary_basis_krw=-1 → ValueError."""
    with pytest.raises(ValueError, match="monthly_salary_basis_krw"):
        merge_payroll_settings({"monthly_salary_basis_krw": -1})


def test_merge_payroll_settings_rejects_out_of_range_burden() -> None:
    """company_burden_rate=1.5 → ValueError (defense-in-depth)."""
    with pytest.raises(ValueError, match="company_burden_rate"):
        merge_payroll_settings({"company_burden_rate": 1.5})


def test_merge_payroll_settings_rejects_workdays_zero() -> None:
    """workdays_in_month=0 → ValueError."""
    with pytest.raises(ValueError, match="workdays_in_month"):
        merge_payroll_settings({"workdays_in_month": 0})


# ── compute_pay_type_breakdown (AC #2) ─────────────────────
def test_compute_pay_type_breakdown_zero_inputs() -> None:
    """All zeros → total_krw=0."""
    b = compute_pay_type_breakdown(0, 0, 0, 0, 0, Decimal("0.115"))
    assert b.base_krw == 0
    assert b.overtime_krw == 0
    assert b.welfare_krw == 0
    assert b.bonus_krw == 0
    assert b.retirement_reserve_krw == 0
    assert b.retirement_burden_krw == 0
    assert b.company_burden_rate == Decimal("0.115")
    assert b.total_krw == 0


def test_compute_pay_type_breakdown_ac2_fixture() -> None:
    """AC #2: workers=2, basis=3M, overtime=200K, welfare=100K, bonus=500K,
    retirement=150K, burden=0.115 → total = 2 × (3M+200K+100K+500K) + 150K×0.115
    = 2 × 3_800_000 + 17_250 = 7_600_000 + 17_250 = 7_617_250.
    Per-worker breakdown total = 3_808_625.
    """
    b = compute_pay_type_breakdown(
        monthly_salary_basis_krw=3_000_000,
        overtime_krw=200_000,
        welfare_krw=100_000,
        bonus_krw=500_000,
        retirement_reserve_krw=150_000,
        company_burden_rate=Decimal("0.115"),
    )
    # retirement_burden = 150_000 × 0.115 = 17_250
    assert b.retirement_burden_krw == 17_250
    # per-worker total = 3_000_000 + 200_000 + 100_000 + 500_000 + 17_250
    # = 3_817_250
    assert b.total_krw == 3_817_250


def test_compute_pay_type_breakdown_basis_only() -> None:
    """basis only → total = basis (no overtime/welfare/bonus/retirement)."""
    b = compute_pay_type_breakdown(2_500_000, 0, 0, 0, 0, Decimal("0.115"))
    assert b.total_krw == 2_500_000
    assert b.retirement_burden_krw == 0


def test_compute_pay_type_breakdown_rejects_negative_krw() -> None:
    """Any negative KRW input → ValueError."""
    with pytest.raises(ValueError, match="overtime_krw"):
        compute_pay_type_breakdown(2_500_000, -1, 0, 0, 0, Decimal("0.115"))


def test_compute_pay_type_breakdown_rejects_burden_above_1() -> None:
    """company_burden_rate=1.5 → ValueError."""
    with pytest.raises(ValueError, match="company_burden_rate"):
        compute_pay_type_breakdown(0, 0, 0, 0, 0, Decimal("1.5"))


def test_compute_pay_type_breakdown_half_even_rounding() -> None:
    """ROUND_HALF_EVEN on retirement_burden: 100K × 0.115 = 11500 (exact)."""
    b = compute_pay_type_breakdown(0, 0, 0, 0, 100_000, Decimal("0.115"))
    assert b.retirement_burden_krw == 11_500


# ── compute_fte_for_daily (AC #1) ──────────────────────────
def test_compute_fte_for_daily_ac1_fixture() -> None:
    """AC #1: workers=3, days=8, payroll default → 3×8/22 = 1.0909.. → 1.09."""
    assert compute_fte_for_daily(3, 8) == Decimal("1.09")


def test_compute_fte_for_daily_with_overridden_workdays() -> None:
    """Override workdays_in_month=20 → 3×8/20 = 1.20."""
    p = PayrollSettings(
        monthly_salary_basis_krw=2_500_000,
        workdays_in_month=20,
        standard_monthly_hours=228,
        company_burden_rate=Decimal("0.115"),
    )
    assert compute_fte_for_daily(3, 8, p) == Decimal("1.20")


def test_compute_fte_for_daily_zero_workers() -> None:
    """workers=0 → Decimal('0.00')."""
    assert compute_fte_for_daily(0, 8) == Decimal("0.00")


def test_compute_fte_for_daily_zero_days() -> None:
    """days=0 → Decimal('0.00')."""
    assert compute_fte_for_daily(3, 0) == Decimal("0.00")


def test_compute_fte_for_daily_negative_workers_returns_zero() -> None:
    """workers=-1 → Decimal('0.00') (silent no-op, matches Story 3.1 format_fte_headcount).

    Defense-in-depth: silent 0 is the conservative behavior for invalid
    inputs. The Pydantic schema (`workers: int = Field(ge=0)`) catches
    negatives at the API boundary; the pure layer just returns 0.
    """
    assert compute_fte_for_daily(-1, 8) == Decimal("0.00")


def test_compute_fte_for_daily_matches_stream_completion_format() -> None:
    """Cross-check: compute_fte_for_daily(3, 8, default) == format_fte_headcount(3, 8)."""
    assert compute_fte_for_daily(3, 8) == format_fte_headcount(3, 8)


def test_compute_fte_for_daily_3_27_round_half_even() -> None:
    """workers=3, days=24 → 72/22 = 3.2727.. → 3.27 (banker's rounding)."""
    # 72 / 22 = 3.272727...
    # ROUND_HALF_EVEN at 2dp: 3.27 (digit after is 2, round down)
    assert compute_fte_for_daily(3, 24) == Decimal("3.27")


# ── compute_fte_for_monthly ─────────────────────────────────
def test_compute_fte_for_monthly_workers_as_is() -> None:
    """workers=2 → Decimal('2.00') (정규직은 정규화 완료)."""
    assert compute_fte_for_monthly(2) == Decimal("2.00")


def test_compute_fte_for_monthly_zero() -> None:
    """workers=0 → Decimal('0.00')."""
    assert compute_fte_for_monthly(0) == Decimal("0.00")


def test_compute_fte_for_monthly_negative_returns_zero() -> None:
    """workers=-1 → Decimal('0.00') (silent no-op).

    Matches `format_fte_headcount` pattern. Pydantic schema catches at
    API boundary; pure layer returns 0.
    """
    assert compute_fte_for_monthly(-1) == Decimal("0.00")


# ── compute_fte_wage_for_daily (AC #1 direct sum) ─────────
def test_compute_fte_wage_for_daily_ac1_direct_sum() -> None:
    """AC #1: 3명 × 8일 × 150_000원 = 3_600_000원 (NOT basis 환산)."""
    assert compute_fte_wage_for_daily(150_000, 3, 8) == 3_600_000


def test_compute_fte_wage_for_daily_zero() -> None:
    """Any zero input → 0 (silent no-op, matches format_fte_headcount)."""
    assert compute_fte_wage_for_daily(0, 3, 8) == 0
    assert compute_fte_wage_for_daily(150_000, 0, 8) == 0
    assert compute_fte_wage_for_daily(150_000, 3, 0) == 0


def test_compute_fte_wage_for_daily_rejects_negative() -> None:
    """Negative input → ValueError."""
    with pytest.raises(ValueError, match="non-negative"):
        compute_fte_wage_for_daily(-1, 3, 8)


# ── compute_fte_wage_for_monthly (AC #2 basis 환산) ────────
def test_compute_fte_wage_for_monthly_ac2() -> None:
    """AC #2: workers=2 × per_worker_total(3_817_250) = 7_634_500."""
    b = compute_pay_type_breakdown(
        monthly_salary_basis_krw=3_000_000,
        overtime_krw=200_000,
        welfare_krw=100_000,
        bonus_krw=500_000,
        retirement_reserve_krw=150_000,
        company_burden_rate=Decimal("0.115"),
    )
    assert compute_fte_wage_for_monthly(2, b) == 7_634_500


def test_compute_fte_wage_for_monthly_workers_zero() -> None:
    """workers=0 → 0 (silent no-op)."""
    b = compute_pay_type_breakdown(2_500_000, 0, 0, 0, 0, Decimal("0.115"))
    assert compute_fte_wage_for_monthly(0, b) == 0


def test_compute_fte_wage_for_monthly_basis_only() -> None:
    """basis only × workers=1 → basis (no rounding)."""
    b = compute_pay_type_breakdown(2_500_000, 0, 0, 0, 0, Decimal("0.115"))
    assert compute_fte_wage_for_monthly(1, b) == 2_500_000


# ── rollup_daily_fte (AC #4 Σ sum) ─────────────────────────
def test_rollup_daily_fte_empty_list() -> None:
    """empty list → (Decimal('0.00'), 0)."""
    fte, wage = rollup_daily_fte([])
    assert fte == Decimal("0.00")
    assert wage == 0


def test_rollup_daily_fte_sum_31_days() -> None:
    """31 identical days → 31× single-day values (Σ sum, not avg)."""
    per_day = [(Decimal("0.10"), 100_000)] * 31
    fte, wage = rollup_daily_fte(per_day)
    assert fte == Decimal("3.10")
    assert wage == 3_100_000


def test_rollup_daily_fte_mixed_values() -> None:
    """Mixed per-day values → exact sum."""
    per_day = [
        (Decimal("0.50"), 50_000),
        (Decimal("1.00"), 100_000),
        (Decimal("0.25"), 25_000),
    ]
    fte, wage = rollup_daily_fte(per_day)
    assert fte == Decimal("1.75")
    assert wage == 175_000


# ── build_fte_display (AC #1 + #2 + #3) ───────────────────
def test_build_fte_display_ac1_daily() -> None:
    """AC #1: pay_type='daily', workers=3, days=8, daily=150_000
    → fte_headcount=1.09, fte_wage_krw=3_600_000, breakdown=None.
    """
    d = build_fte_display(
        pay_type=PayType.DAILY,
        workers=3,
        days_per_worker=8,
        daily_wage_krw=150_000,
        monthly_salary_basis_krw=None,
        overtime_krw=None,
        welfare_krw=None,
        bonus_krw=None,
        retirement_reserve_krw=None,
        company_burden_rate=None,
        payroll=DEFAULT_PAYROLL,
        source_rows=1,
    )
    assert isinstance(d, FteDisplay)
    assert d.pay_type == PayType.DAILY
    assert d.fte_headcount == Decimal("1.09")
    assert d.fte_wage_krw == 3_600_000
    assert d.breakdown is None
    assert d.source_rows == 1


def test_build_fte_display_ac2_monthly_with_breakdown() -> None:
    """AC #2: pay_type='monthly', workers=2, basis=3M, ... → 7_634_500."""
    d = build_fte_display(
        pay_type=PayType.MONTHLY,
        workers=2,
        days_per_worker=None,
        daily_wage_krw=None,
        monthly_salary_basis_krw=3_000_000,
        overtime_krw=200_000,
        welfare_krw=100_000,
        bonus_krw=500_000,
        retirement_reserve_krw=150_000,
        company_burden_rate=Decimal("0.115"),
        payroll=DEFAULT_PAYROLL,
        source_rows=1,
    )
    assert d.pay_type == PayType.MONTHLY
    assert d.fte_headcount == Decimal("2.00")
    assert d.fte_wage_krw == 7_634_500
    assert d.breakdown is not None
    assert d.breakdown["base_krw"] == 3_000_000
    assert d.breakdown["overtime_krw"] == 200_000
    assert d.breakdown["welfare_krw"] == 100_000
    assert d.breakdown["bonus_krw"] == 500_000
    assert d.breakdown["retirement_reserve_krw"] == 150_000
    assert d.breakdown["retirement_burden_krw"] == 17_250
    assert d.breakdown["total_krw"] == 3_817_250


def test_build_fte_display_monthly_basis_only() -> None:
    """workers=1, basis=2_500_000 → fte=1.00, wage=2_500_000, breakdown.total=2.5M."""
    d = build_fte_display(
        pay_type=PayType.MONTHLY,
        workers=1,
        days_per_worker=None,
        daily_wage_krw=None,
        monthly_salary_basis_krw=2_500_000,
        overtime_krw=0,
        welfare_krw=0,
        bonus_krw=0,
        retirement_reserve_krw=0,
        company_burden_rate=None,  # fallback to DEFAULT_PAYROLL
        payroll=DEFAULT_PAYROLL,
        source_rows=1,
    )
    assert d.fte_headcount == Decimal("1.00")
    assert d.fte_wage_krw == 2_500_000
    assert d.breakdown is not None
    assert d.breakdown["total_krw"] == 2_500_000


def test_build_fte_display_daily_rejects_missing_daily_wage() -> None:
    """pay_type='daily' with daily_wage_krw=None → ValueError."""
    with pytest.raises(ValueError, match="daily_wage_krw"):
        build_fte_display(
            pay_type=PayType.DAILY,
            workers=3,
            days_per_worker=8,
            daily_wage_krw=None,
            monthly_salary_basis_krw=None,
            overtime_krw=None,
            welfare_krw=None,
            bonus_krw=None,
            retirement_reserve_krw=None,
            company_burden_rate=None,
            payroll=DEFAULT_PAYROLL,
            source_rows=1,
        )


def test_build_fte_display_monthly_rejects_missing_basis() -> None:
    """pay_type='monthly' with monthly_salary_basis_krw=None → ValueError."""
    with pytest.raises(ValueError, match="monthly_salary_basis_krw"):
        build_fte_display(
            pay_type=PayType.MONTHLY,
            workers=1,
            days_per_worker=None,
            daily_wage_krw=None,
            monthly_salary_basis_krw=None,
            overtime_krw=0,
            welfare_krw=0,
            bonus_krw=0,
            retirement_reserve_krw=0,
            company_burden_rate=None,
            payroll=DEFAULT_PAYROLL,
            source_rows=1,
        )


def test_build_fte_display_daily_with_overridden_payroll() -> None:
    """AC #3: payroll.workdays_in_month=20 → 3×8/20 = 1.20."""
    p = PayrollSettings(
        monthly_salary_basis_krw=2_500_000,
        workdays_in_month=20,
        standard_monthly_hours=228,
        company_burden_rate=Decimal("0.115"),
    )
    d = build_fte_display(
        pay_type=PayType.DAILY,
        workers=3,
        days_per_worker=8,
        daily_wage_krw=150_000,
        monthly_salary_basis_krw=None,
        overtime_krw=None,
        welfare_krw=None,
        bonus_krw=None,
        retirement_reserve_krw=None,
        company_burden_rate=None,
        payroll=p,
        source_rows=1,
    )
    assert d.fte_headcount == Decimal("1.20")
    # Direct sum path is unchanged by payroll override (only 환산 uses
    # workdays_in_month; the wage uses daily_wage directly).
    assert d.fte_wage_krw == 3_600_000


def test_build_fte_display_unknown_pay_type() -> None:
    """Unknown pay_type → ValueError (defense)."""
    with pytest.raises(ValueError, match="pay_type"):
        build_fte_display(
            pay_type="hourly",  # type: ignore[arg-type]
            workers=1,
            days_per_worker=None,
            daily_wage_krw=None,
            monthly_salary_basis_krw=None,
            overtime_krw=None,
            welfare_krw=None,
            bonus_krw=None,
            retirement_reserve_krw=None,
            company_burden_rate=None,
            payroll=DEFAULT_PAYROLL,
            source_rows=1,
        )


# ── Cross-cutting ──────────────────────────────────────────
def test_paytypebreakdown_dataclass_frozen() -> None:
    """PayTypeBreakdown is frozen (immutable result)."""
    b = compute_pay_type_breakdown(2_500_000, 0, 0, 0, 0, Decimal("0.115"))
    with pytest.raises((AttributeError, Exception)):
        b.base_krw = 0  # type: ignore[misc]


def test_ftedisplay_dataclass_frozen() -> None:
    """FteDisplay is frozen (immutable result)."""
    d = build_fte_display(
        pay_type=PayType.DAILY,
        workers=3,
        days_per_worker=8,
        daily_wage_krw=150_000,
        monthly_salary_basis_krw=None,
        overtime_krw=None,
        welfare_krw=None,
        bonus_krw=None,
        retirement_reserve_krw=None,
        company_burden_rate=None,
        payroll=DEFAULT_PAYROLL,
        source_rows=1,
    )
    with pytest.raises((AttributeError, Exception)):
        d.fte_wage_krw = 0  # type: ignore[misc]
