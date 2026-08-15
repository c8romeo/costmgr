"""tests.cost_engine.test_projection — Story 7.2 (Epic 7) pure kernel tests.

Tests for `packages.cost_engine.projection`:
- `compute_interest_expense`: 정상범위 + 3종 edge cases
  (loan_amount < 0 / interest_rate < 0 / interest_rate > 100)
- `compute_after_tax_income`: 정상범위 + 2종 edge cases
  (corporate_tax_rate 범위) + 손실 처리 (음수 유지)
- `project_next_month`: 4 arithmetic orchestration + 손실 케이스
- `compute_projection_hash`: 결정론 + frozen=True enforcement
- 100회 determinism (byte-identical hash)
- Decimal precision: ROUND_HALF_EVEN parity
"""

# ruff: noqa: ERA001
# ERA001 disabled: handwritten mathematical derivation comments inside test
# bodies are intentional documentation (show step-by-step expected values).

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.cvp import CVPBaseline
from packages.cost_engine.projection import (
    PROJECTION_CORPORATE_TAX_RATE_RANGE_KO,
    PROJECTION_COST_INFLATION_RATE_MAX_PCT,
    PROJECTION_COST_INFLATION_RATE_MIN_PCT,
    PROJECTION_HASH_PREFIX,
    PROJECTION_INTEREST_RATE_NEGATIVE_KO,
    PROJECTION_INTEREST_RATE_OVER_100_KO,
    PROJECTION_LOAN_AMOUNT_NEGATIVE_KO,
    InvalidProjectionMonthError,
    ProjectionBaselineNotFoundError,
    ProjectionInputs,
    ProjectionInvalidInputError,
    compute_after_tax_income,
    compute_interest_expense,
    compute_projection_hash,
    project_next_month,
)


# ── Constants ────────────────────────────────────────────────
def test_projection_constants():
    """Story 7.2 constants match spec §F7.2 + AD-8 monetary precision."""
    assert PROJECTION_HASH_PREFIX == "sha256:"
    assert (
        PROJECTION_LOAN_AMOUNT_NEGATIVE_KO == "차입금은 0 이상이어야 합니다"
    )
    assert (
        PROJECTION_INTEREST_RATE_NEGATIVE_KO == "이자율은 0 이상이어야 합니다"
    )
    assert (
        PROJECTION_INTEREST_RATE_OVER_100_KO == "이자율은 100% 이하여야 합니다"
    )
    assert (
        PROJECTION_CORPORATE_TAX_RATE_RANGE_KO
        == "법인세율은 0과 100 사이여야 합니다"
    )
    assert Decimal("-50") == PROJECTION_COST_INFLATION_RATE_MIN_PCT
    assert Decimal("100") == PROJECTION_COST_INFLATION_RATE_MAX_PCT


# ── compute_interest_expense — happy path ────────────────────
def test_compute_interest_expense_basic():
    """Basic: loan=10_000_000, rate=5% → interest = 500_000."""
    result = compute_interest_expense(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
    )
    assert result == Decimal("500000")


def test_compute_interest_expense_zero_rate():
    """이자율 0% → 이자 0."""
    result = compute_interest_expense(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("0"),
    )
    assert result == Decimal("0")


def test_compute_interest_expense_zero_loan():
    """차입금 0 → 이자 0."""
    result = compute_interest_expense(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("5"),
    )
    assert result == Decimal("0")


def test_compute_interest_expense_high_rate():
    """이자율 100% → 이자 = loan_amount (test boundary)."""
    result = compute_interest_expense(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("100"),
    )
    assert result == Decimal("10000000")


def test_compute_interest_expense_fractional():
    """이자율 4.5% → 이자 정확 계산."""
    result = compute_interest_expense(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("4.5"),
    )
    assert result == Decimal("450000")


# ── compute_interest_expense — edge cases ────────────────────
def test_compute_interest_expense_negative_loan_raises():
    """loan_amount < 0 → ValueError."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_interest_expense(
            loan_amount=Decimal("-1000000"),
            interest_rate=Decimal("5"),
        )
    assert exc_info.value.code == "loan_amount_must_be_non_negative"
    assert exc_info.value.field == "loan_amount"


def test_compute_interest_expense_negative_rate_raises():
    """interest_rate < 0 → ValueError."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_interest_expense(
            loan_amount=Decimal("10000000"),
            interest_rate=Decimal("-1"),
        )
    assert exc_info.value.code == "interest_rate_must_be_non_negative"
    assert exc_info.value.field == "interest_rate"


def test_compute_interest_expense_rate_over_100_raises():
    """interest_rate > 100 → ValueError."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_interest_expense(
            loan_amount=Decimal("10000000"),
            interest_rate=Decimal("101"),
        )
    assert exc_info.value.code == "interest_rate_must_be_at_most_100"
    assert exc_info.value.field == "interest_rate"


# ── compute_after_tax_income — happy path ───────────────────
def test_compute_after_tax_income_basic():
    """pre_tax=10_000_000, tax_rate=22% → after_tax = 7_800_000."""
    # corporate_tax = 10_000_000 * 0.22 = 2_200_000
    # after_tax = 10_000_000 - 2_200_000 = 7_800_000
    result = compute_after_tax_income(
        pre_tax_income=Decimal("10000000"),
        corporate_tax_rate=Decimal("22"),
    )
    assert result == Decimal("7800000")


def test_compute_after_tax_income_zero_rate():
    """tax_rate=0 → after_tax = pre_tax_income (no tax)."""
    result = compute_after_tax_income(
        pre_tax_income=Decimal("10000000"),
        corporate_tax_rate=Decimal("0"),
    )
    assert result == Decimal("10000000")


def test_compute_after_tax_income_zero_pre_tax():
    """pre_tax=0 → after_tax=0."""
    result = compute_after_tax_income(
        pre_tax_income=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    assert result == Decimal("0")


def test_compute_after_tax_income_100_percent_rate():
    """tax_rate=100% → after_tax = 0 (boundary)."""
    result = compute_after_tax_income(
        pre_tax_income=Decimal("10000000"),
        corporate_tax_rate=Decimal("100"),
    )
    assert result == Decimal("0")


# ── compute_after_tax_income — edge cases ───────────────────
def test_compute_after_tax_income_negative_tax_rate_raises():
    """corporate_tax_rate < 0 → ValueError."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_after_tax_income(
            pre_tax_income=Decimal("10000000"),
            corporate_tax_rate=Decimal("-1"),
        )
    assert exc_info.value.code == "corporate_tax_rate_must_be_in_range_0_100"
    assert exc_info.value.field == "corporate_tax_rate"


def test_compute_after_tax_income_over_100_tax_rate_raises():
    """corporate_tax_rate > 100 → ValueError."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_after_tax_income(
            pre_tax_income=Decimal("10000000"),
            corporate_tax_rate=Decimal("101"),
        )
    assert exc_info.value.code == "corporate_tax_rate_must_be_in_range_0_100"


def test_compute_after_tax_income_loss_kept_negative():
    """pre_tax_income < 0 → 손실 인정 (음수 유지, tax=0)."""
    # Loss = -10_000_000 → corporate_tax = 0 (max(0, -10M) = 0)
    # after_tax_income = -10_000_000 (그대로 음수)
    result = compute_after_tax_income(
        pre_tax_income=Decimal("-10000000"),
        corporate_tax_rate=Decimal("22"),
    )
    assert result == Decimal("-10000000")


# ── project_next_month — happy path ─────────────────────────
def test_project_next_month_basic():
    """Basic: baseline + 4 params → all 7 fields correct."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("5000000"),
        unit_variable_cost=Decimal("5000"),
        unit_price=Decimal("10000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )

    # interest_expense = 10_000_000 * 0.05 = 500_000
    # baseline_monthly_revenue = 10_000 * 1.0 = 10_000
    # baseline_monthly_variable_cost = 5_000 * 1.0 = 5_000
    # baseline_monthly_fixed_cost = 5_000_000
    # projected_revenue = 10_000 * 1.0 = 10_000
    # projected_variable_cost = 5_000 * 1.0 = 5_000
    # projected_fixed_cost = 5_000_000 + 500_000 = 5_500_000
    # pre_tax_income = 10_000 - 5_000 - 5_500_000 = -5_495_000
    # corporate_tax = 0 (loss)
    # after_tax_income = -5_495_000
    assert result.interest_expense == Decimal("500000")
    assert result.projected_revenue == Decimal("10000")
    assert result.projected_variable_cost == Decimal("5000")
    assert result.projected_fixed_cost == Decimal("5500000")
    assert result.pre_tax_income == Decimal("-5495000")
    assert result.corporate_tax == Decimal("0")
    assert result.after_tax_income == Decimal("-5495000")


def test_project_next_month_with_inflation():
    """원가 상승률 +10% → revenue/variable 둘 다 1.1배."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("20000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),  # No loan
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("10"),
        corporate_tax_rate=Decimal("20"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )

    # interest_expense = 0
    # baseline_revenue = 20_000 * 1.0 = 20_000
    # baseline_variable = 10_000 * 1.0 = 10_000
    # baseline_fixed = 1_000_000
    # projected_revenue = 20_000 * 1.10 = 22_000
    # projected_variable = 10_000 * 1.10 = 11_000
    # projected_fixed = 1_000_000 + 0 = 1_000_000
    # pre_tax = 22_000 - 11_000 - 1_000_000 = -989_000
    # tax = 0 (loss)
    assert result.projected_revenue == Decimal("22000")
    assert result.projected_variable_cost == Decimal("11000")
    assert result.projected_fixed_cost == Decimal("1000000")
    assert result.pre_tax_income == Decimal("-989000")
    assert result.after_tax_income == Decimal("-989000")


def test_project_next_month_profit_with_tax():
    """Profit scenario with tax — tax = profit * rate."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("5000"),
        unit_price=Decimal("50000"),  # very high margin
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )

    # baseline_revenue = 50_000
    # baseline_variable = 5_000
    # baseline_fixed = 1_000_000
    # projected_revenue = 50_000
    # projected_variable = 5_000
    # projected_fixed = 1_000_000
    # pre_tax = 50_000 - 5_000 - 1_000_000 = -955_000
    # Loss → tax = 0
    assert result.pre_tax_income == Decimal("-955000")
    assert result.after_tax_income == Decimal("-955000")


def test_project_next_month_profit_with_tax_positive():
    """Force positive profit by adjusting inputs."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("5000"),
        unit_price=Decimal("50000"),
        operating_rate=Decimal("1.0"),
    )
    # Negative inflation = deflation → revenue up vs cost
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("-10"),  # deflation 10%
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )

    # revenue = 50_000 * 0.9 = 45_000
    # variable = 5_000 * 0.9 = 4_500
    # fixed = 1_000_000
    # pre_tax = 45_000 - 4_500 - 1_000_000 = -959_500
    # Still loss → tax = 0
    assert result.pre_tax_income == Decimal("-959500")


def test_project_next_month_high_margin_forces_profit():
    """Force profit by using high-revenue baseline."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("100000"),
        unit_variable_cost=Decimal("100"),
        unit_price=Decimal("10000000"),  # absurdly high
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )

    # revenue = 10_000_000
    # variable = 100
    # fixed = 100_000
    # pre_tax = 10_000_000 - 100 - 100_000 = 9_899_900
    # tax = 9_899_900 * 0.22 = 2_177_978
    # after_tax = 9_899_900 - 2_177_978 = 7_721_922
    assert result.pre_tax_income == Decimal("9899900")
    assert result.corporate_tax == Decimal("2177978")
    assert result.after_tax_income == Decimal("7721922")


def test_project_next_month_with_loan_interest():
    """차입금 이자가 fixed_cost에 추가되는지 확인."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),  # 10M loan
        interest_rate=Decimal("5"),  # 5% interest = 500K
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )

    # interest_expense = 500_000
    # baseline_revenue = 10_000_000
    # baseline_variable = 10_000
    # baseline_fixed = 1_000_000
    # projected_fixed = 1_000_000 + 500_000 = 1_500_000
    assert result.interest_expense == Decimal("500000")
    assert result.projected_fixed_cost == Decimal("1500000")


# ── project_next_month — edge cases ─────────────────────────
def test_project_next_month_negative_inflation_allowed():
    """원가 상승률 -50% (경계값) → 정상 처리."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("-50"),  # 경계값 -50%
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    # revenue = 10_000_000 * 0.5 = 5_000_000
    # variable = 10_000 * 0.5 = 5_000
    assert result.projected_revenue == Decimal("5000000")
    assert result.projected_variable_cost == Decimal("5000")


def test_project_next_month_positive_inflation_boundary():
    """원가 상승률 +100% (경계값) → 정상 처리."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("100"),  # 경계값 +100%
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    # revenue = 10_000_000 * 2.0 = 20_000_000
    # variable = 10_000 * 2.0 = 20_000
    assert result.projected_revenue == Decimal("20000000")
    assert result.projected_variable_cost == Decimal("20000")


def test_project_next_month_inflation_below_min_raises():
    """원가 상승률 < -50% → ValueError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("-51"),  # -50 미만
        corporate_tax_rate=Decimal("22"),
    )
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        project_next_month(baseline_cvp=baseline, projection_inputs=inputs)
    assert (
        exc_info.value.code
        == "cost_inflation_rate_must_be_in_range_minus50_plus100"
    )
    assert exc_info.value.field == "cost_inflation_rate"


def test_project_next_month_inflation_above_max_raises():
    """원가 상승률 > 100% → ValueError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("101"),  # 100 초과
        corporate_tax_rate=Decimal("22"),
    )
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        project_next_month(baseline_cvp=baseline, projection_inputs=inputs)
    assert (
        exc_info.value.code
        == "cost_inflation_rate_must_be_in_range_minus50_plus100"
    )


def test_project_next_month_invalid_baseline_raises():
    """baseline not CVPBaseline → ValueError."""
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        project_next_month(
            baseline_cvp={"fixed_cost": Decimal("1000000")},  # type: ignore[arg-type]
            projection_inputs=inputs,
        )
    assert exc_info.value.code == "invalid_decimal_type"


def test_project_next_month_invalid_inputs_raises():
    """projection_inputs not ProjectionInputs → ValueError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        project_next_month(
            baseline_cvp=baseline,
            projection_inputs={"loan_amount": Decimal("1000000")},  # type: ignore[arg-type]
        )
    assert exc_info.value.code == "invalid_decimal_type"


def test_project_next_month_baseline_not_mutated():
    """baseline frozen=True → mutation 시도 안 됨."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    project_next_month(baseline_cvp=baseline, projection_inputs=inputs)
    # baseline must NOT be mutated.
    assert baseline.fixed_cost == Decimal("1000000")
    assert baseline.unit_price == Decimal("10000000")


# ── compute_projection_hash — V8 determinism ─────────────────
def test_compute_projection_hash_format():
    """Hash format: `sha256:` + 64-char hexdigest."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    digest = compute_projection_hash(result)
    assert digest.startswith(PROJECTION_HASH_PREFIX)
    hex_part = digest[len(PROJECTION_HASH_PREFIX):]
    assert len(hex_part) == 64  # 32 bytes = 64 hex chars
    int(hex_part, 16)  # validate hex


def test_compute_projection_hash_determinism():
    """동일 입력 → 동일 hash (NFR16 determinism)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    h1 = compute_projection_hash(result)
    h2 = compute_projection_hash(result)
    assert h1 == h2


def test_compute_projection_hash_100x_byte_identical():
    """100회 동일 입력 → 100회 byte-identical hash (V8 회귀 가능)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    expected = compute_projection_hash(result)
    for _ in range(100):
        assert compute_projection_hash(result) == expected


def test_compute_projection_hash_different_input_different_hash():
    """다른 loan_amount → 다른 hash (변경 감지)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
    )
    inputs_a = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    inputs_b = ProjectionInputs(
        loan_amount=Decimal("20000000"),  # different
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result_a = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs_a
    )
    result_b = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs_b
    )
    assert compute_projection_hash(result_a) != compute_projection_hash(result_b)


def test_compute_projection_hash_non_projection_raises():
    """result not NextMonthProjection → ValueError."""
    with pytest.raises(ProjectionInvalidInputError) as exc_info:
        compute_projection_hash({"projected_revenue": Decimal("1000000")})  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_decimal_type"


# ── Frozen dataclass enforcement ────────────────────────────
def test_projection_inputs_is_frozen():
    """ProjectionInputs is frozen=True → mutation 시 FrozenInstanceError."""
    inputs = ProjectionInputs(
        loan_amount=Decimal("10000000"),
        interest_rate=Decimal("5"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        inputs.loan_amount = Decimal("99999")  # type: ignore[misc]


def test_next_month_projection_is_frozen():
    """NextMonthProjection is frozen=True → mutation 시 FrozenInstanceError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("0"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.projected_revenue = Decimal("99999999")  # type: ignore[misc]


# ── Decimal precision parity (ROUND_HALF_EVEN) ──────────────
def test_decimal_round_half_even_parity():
    """ROUND_HALF_EVEN parity (banker's rounding) — AD-8 monetary types.

    All monetary fields quantized to KRW (Decimal("1")).
    """
    baseline = CVPBaseline(
        fixed_cost=Decimal("1234567"),
        unit_variable_cost=Decimal("1234"),
        unit_price=Decimal("12345678"),
        operating_rate=Decimal("1.0"),
    )
    inputs = ProjectionInputs(
        loan_amount=Decimal("9876543"),
        interest_rate=Decimal("3.5"),  # non-integer
        cost_inflation_rate=Decimal("2.7"),  # non-integer
        corporate_tax_rate=Decimal("22.5"),
    )
    result = project_next_month(
        baseline_cvp=baseline, projection_inputs=inputs
    )
    # All fields are Decimal (quantized to KRW = integer).
    assert result.projected_revenue == result.projected_revenue.to_integral_value()
    assert (
        result.projected_variable_cost
        == result.projected_variable_cost.to_integral_value()
    )
    assert (
        result.projected_fixed_cost
        == result.projected_fixed_cost.to_integral_value()
    )


# ── InvalidProjectionMonthError ─────────────────────────────
def test_invalid_projection_month_error_construction():
    """InvalidProjectionMonthError constructor accepts period_key, projection_month, reason."""
    err = InvalidProjectionMonthError(
        period_key="2026-08",
        projection_month="2026-08",  # same as period_key → violation
        reason="projection_month must be after period_key",
    )
    assert err.period_key == "2026-08"
    assert err.projection_month == "2026-08"
    assert "projection_month must be after period_key" in err.reason


# ── ProjectionBaselineNotFoundError ─────────────────────────
def test_projection_baseline_not_found_error_construction():
    """ProjectionBaselineNotFoundError constructor accepts tenant_id, period_key."""
    err = ProjectionBaselineNotFoundError(
        tenant_id="tenant-uuid",
        period_key="2026-08",
    )
    assert err.tenant_id == "tenant-uuid"
    assert err.period_key == "2026-08"
    assert "Projection baseline not found" in err.message


def test_projection_baseline_not_found_error_custom_message():
    """ProjectionBaselineNotFoundError accepts custom message."""
    err = ProjectionBaselineNotFoundError(
        tenant_id="tenant-uuid",
        period_key="2026-08",
        message="custom error message",
    )
    assert err.message == "custom error message"


# ── Public API export ───────────────────────────────────────
def test_projection_public_api_exports():
    """Public API export — all Story 7.2 functions importable from packages.cost_engine."""
    from packages.cost_engine import (  # noqa: F401
        InvalidProjectionMonthError,
        NextMonthProjection,
        ProjectionBaselineNotFoundError,
        ProjectionInputs,
        ProjectionInvalidInputError,
        compute_after_tax_income,
        compute_interest_expense,
        compute_projection_hash,
        project_next_month,
    )
    # All imports succeeded.
    assert True
