"""tests.services.test_m2_input_fte — pure-function tests for FTE math.

Story 3.1 — Task 1.3 (FTE hook surface, read-only display).

These tests verify:
- `format_fte_headcount` ROUND_HALF_EVEN parity with TS mirror
- `compute_fte_wage_krw` integer rounding
- Edge cases (zero workers, zero days, zero workdays)
- Story 3.2 AC #1 canonical: 3명 × 8일 / 22 ≈ 1.09

Why banker's rounding (ROUND_HALF_EVEN) — TS `Math.round` is
half-away-from-zero. We diverge deliberately so both sides produce
identical output for the exact `.5` boundary case (precision matters
when the wage is multiplied by `monthly_salary_basis_krw` later).
"""

from __future__ import annotations

from decimal import Decimal

from packages.services.m2_input.stream_completion import (
    compute_fte_wage_krw,
    format_fte_headcount,
)


# ───────────────────────────────────────────────────────────────
# format_fte_headcount (Story 3.2 AC #1)
# ───────────────────────────────────────────────────────────────
def test_format_fte_3_workers_8_days_22_workdays() -> None:
    """Story 3.2 AC #1 canonical: 3 × 8 / 22 ≈ 1.09 (round_half_even)."""
    # 3 × 8 / 22 = 24 / 22 = 1.09090909... → ROUND_HALF_EVEN at 2dp → 1.09
    assert format_fte_headcount(3, 8, 22) == Decimal("1.09")


def test_format_fte_zero_workers_returns_zero() -> None:
    """workers=0 → 0.00 (no division)."""
    assert format_fte_headcount(0, 8, 22) == Decimal("0.00")


def test_format_fte_zero_days_returns_zero() -> None:
    """days_per_worker=0 → 0.00 (no division)."""
    assert format_fte_headcount(3, 0, 22) == Decimal("0.00")


def test_format_fte_zero_workdays_returns_zero() -> None:
    """workdays_in_month=0 → 0.00 (defensive: division by zero 방지)."""
    assert format_fte_headcount(3, 8, 0) == Decimal("0.00")


def test_format_fte_negative_workers_returns_zero() -> None:
    """workers < 0 → 0.00 (defensive; 입력 검증은 service layer에서)."""
    assert format_fte_headcount(-1, 8, 22) == Decimal("0.00")


def test_format_fte_30_workdays_30_workers() -> None:
    """30 workers × 30 days / 30 workdays = 30.00 (정확히 정수)."""
    assert format_fte_headcount(30, 30, 30) == Decimal("30.00")


def test_format_fte_rounding_half_even_at_2dp() -> None:
    """ROUND_HALF_EVEN 동작 확인 — 0.005 경계에서 짝수 방향으로 반올림.

    예: 5 × 11 / 22 = 2.5 → ROUND_HALF_EVEN → 2.50 (이미 2dp이므로 동일)
    더 명확한 예: 1 × 1 / 8 = 0.125 → ROUND_HALF_EVEN at 2dp → 0.12
    (0.125의 3째 자리 5 → 짝수 방향 → 0.12)
    """
    assert format_fte_headcount(1, 1, 8) == Decimal("0.12")


def test_format_fte_decimal_returned_at_2_places() -> None:
    """결과는 항상 2자리 Decimal."""
    result = format_fte_headcount(3, 8, 22)
    assert isinstance(result, Decimal)
    # quantize 결과는 항상 2dp → exponent = -2
    assert result.as_tuple().exponent == -2


# ───────────────────────────────────────────────────────────────
# compute_fte_wage_krw
# ───────────────────────────────────────────────────────────────
def test_compute_fte_wage_1_09_times_2_500_000() -> None:
    """Story 3.2 AC #1: 1.09 × 2,500,000 = 2,725,000원."""
    assert compute_fte_wage_krw(Decimal("1.09"), 2_500_000) == 2_725_000


def test_compute_fte_wage_zero_fte_returns_zero() -> None:
    """FTE=0 → 0원."""
    assert compute_fte_wage_krw(Decimal("0.00"), 2_500_000) == 0


def test_compute_fte_wage_zero_basis_returns_zero() -> None:
    """basis=0 → 0원 (PRD default fallback 경로)."""
    assert compute_fte_wage_krw(Decimal("1.09"), 0) == 0


def test_compute_fte_wage_negative_basis_returns_zero() -> None:
    """basis < 0 → 0원 (defensive)."""
    assert compute_fte_wage_krw(Decimal("1.09"), -100) == 0


def test_compute_fte_wage_negative_fte_returns_zero() -> None:
    """FTE < 0 → 0원 (defensive)."""
    assert compute_fte_wage_krw(Decimal("-1.00"), 2_500_000) == 0


def test_compute_fte_wage_rounds_half_even_to_integer() -> None:
    """ROUND_HALF_EVEN이 정수 KRW에도 적용됨.

    예: 0.5 × 1000 = 500 (정확) / 0.5 × 1 = 0.5 → ROUND_HALF_EVEN → 0
    """
    assert compute_fte_wage_krw(Decimal("0.50"), 1) == 0
    assert compute_fte_wage_krw(Decimal("1.50"), 1) == 2


def test_compute_fte_wage_integration_with_format_fte() -> None:
    """통합: format_fte → compute_fte_wage (Story 3.2 AC #1 end-to-end)."""
    fte = format_fte_headcount(3, 8, 22)
    assert fte == Decimal("1.09")
    wage = compute_fte_wage_krw(fte, 2_500_000)
    assert wage == 2_725_000


def test_compute_fte_wage_typical_payroll_value() -> None:
    """PRD default 월급여 기준액 = 2,500,000원 → 1 FTE = 2,500,000원."""
    assert compute_fte_wage_krw(Decimal("1.00"), 2_500_000) == 2_500_000


def test_compute_fte_wage_typical_payroll_300() -> None:
    """PRD default 월급여 기준액 3,000,000원 → 1 FTE = 3,000,000원."""
    assert compute_fte_wage_krw(Decimal("1.00"), 3_000_000) == 3_000_000


def test_compute_fte_wage_high_fte_count() -> None:
    """큰 FTE (10명 × 22일 / 22 = 10.00) × 2,500,000 = 25,000,000원."""
    fte = format_fte_headcount(10, 22, 22)
    assert fte == Decimal("10.00")
    assert compute_fte_wage_krw(fte, 2_500_000) == 25_000_000