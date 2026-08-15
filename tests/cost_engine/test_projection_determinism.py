"""tests.cost_engine.test_projection_determinism — Story 7.2 V8 byte-identical CI gate.

NFR16 determinism gate (Epic 4 baseline extension — 8-1 budget_period_key
+ 7-1 cvp pattern + 7-2 projection pattern):

- 100회 동일 입력 → 100회 동일 `compute_projection_hash(projection)` 결정론
- 동일 입력 across calls → 동일 repr → 동일 sha256 digest
- Different inputs → different digests (변경 감지)
"""

from __future__ import annotations

from decimal import Decimal

from packages.cost_engine.cvp import CVPBaseline
from packages.cost_engine.projection import (
    ProjectionInputs,
    compute_projection_hash,
    project_next_month,
)


def _make_baseline() -> CVPBaseline:
    return CVPBaseline(
        fixed_cost=Decimal("1000000"),
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )


def _make_inputs(
    loan: str = "10000000",
    rate: str = "5",
    inflation: str = "0",
    tax: str = "22",
) -> ProjectionInputs:
    return ProjectionInputs(
        loan_amount=Decimal(loan),
        interest_rate=Decimal(rate),
        cost_inflation_rate=Decimal(inflation),
        corporate_tax_rate=Decimal(tax),
    )


# ── V8 byte-identical — NextMonthProjection ─────────────────
def test_projection_hash_100x_byte_identical():
    """100회 동일 NextMonthProjection → 100회 byte-identical sha256 digest."""
    baseline = _make_baseline()
    inputs = _make_inputs()
    result = project_next_month(baseline_cvp=baseline, projection_inputs=inputs)
    expected = compute_projection_hash(result)
    for _ in range(100):
        assert compute_projection_hash(result) == expected


def test_projection_hash_100x_byte_identical_loss_scenario():
    """100회 동일 손실 케이스 → 100회 byte-identical."""
    # Force loss with negative inflation + extreme low revenue.
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),  # high fixed cost
        unit_variable_cost=Decimal("10000"),
        unit_price=Decimal("10000"),  # low unit price
        operating_rate=Decimal("1.0"),
    )
    # negative inflation → revenue goes DOWN → loss
    inputs = ProjectionInputs(
        loan_amount=Decimal("0"),
        interest_rate=Decimal("0"),
        cost_inflation_rate=Decimal("-50"),
        corporate_tax_rate=Decimal("22"),
    )
    result = project_next_month(baseline_cvp=baseline, projection_inputs=inputs)
    assert result.pre_tax_income < 0  # confirm loss scenario
    expected = compute_projection_hash(result)
    for _ in range(100):
        assert compute_projection_hash(result) == expected


def test_projection_hash_100x_byte_identical_profit_scenario():
    """100회 동일 profit 시나리오 → 100회 byte-identical."""
    # Force profit with high-revenue baseline.
    baseline = CVPBaseline(
        fixed_cost=Decimal("100000"),
        unit_variable_cost=Decimal("100"),
        unit_price=Decimal("10000000"),
        operating_rate=Decimal("1.0"),
    )
    inputs = _make_inputs(loan="0", rate="0", inflation="0", tax="22")
    result = project_next_month(baseline_cvp=baseline, projection_inputs=inputs)
    assert result.pre_tax_income > 0  # confirm profit
    expected = compute_projection_hash(result)
    for _ in range(100):
        assert compute_projection_hash(result) == expected


# ── Cross-input variation ────────────────────────────────────
def test_projection_hash_varies_with_loan_amount():
    """loan_amount 변동 → hash 변동 (변경 감지)."""
    baseline = _make_baseline()
    r1 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(loan="10000000"),
    )
    r2 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(loan="20000000"),  # different
    )
    assert compute_projection_hash(r1) != compute_projection_hash(r2)


def test_projection_hash_varies_with_interest_rate():
    """interest_rate 변동 → hash 변동."""
    baseline = _make_baseline()
    r1 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(rate="5"),
    )
    r2 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(rate="7"),  # different
    )
    assert compute_projection_hash(r1) != compute_projection_hash(r2)


def test_projection_hash_varies_with_inflation_rate():
    """cost_inflation_rate 변동 → hash 변동."""
    baseline = _make_baseline()
    r1 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(inflation="0"),
    )
    r2 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(inflation="10"),  # different
    )
    assert compute_projection_hash(r1) != compute_projection_hash(r2)


def test_projection_hash_varies_with_tax_rate():
    """corporate_tax_rate 변동 → hash 변동."""
    baseline = _make_baseline()
    r1 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(tax="22"),
    )
    r2 = project_next_month(
        baseline_cvp=baseline,
        projection_inputs=_make_inputs(tax="25"),  # different
    )
    assert compute_projection_hash(r1) != compute_projection_hash(r2)


def test_projection_hash_varies_with_baseline():
    """baseline 변동 → hash 변동."""
    inputs = _make_inputs()
    r1 = project_next_month(
        baseline_cvp=_make_baseline(),
        projection_inputs=inputs,
    )
    r2 = project_next_month(
        baseline_cvp=CVPBaseline(
            fixed_cost=Decimal("2000000"),  # different
            unit_variable_cost=Decimal("10000"),
            unit_price=Decimal("10000000"),
            operating_rate=Decimal("1.0"),
        ),
        projection_inputs=inputs,
    )
    assert compute_projection_hash(r1) != compute_projection_hash(r2)
