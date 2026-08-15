"""tests.cost_engine.test_cvp_determinism — Story 7.1 V8 byte-identical CI gate.

NFR16 determinism gate (Epic 4 baseline extension — 8-1 budget_period_key
+ 7-1 cvp pattern):

- 100회 동일 입력 → 100회 동일 `compute_bep_hash(result)` 결정론
- 동일 입력 across calls → 동일 repr → 동일 sha256 digest
- Different inputs → different digests (변경 감지)
"""

from __future__ import annotations

from decimal import Decimal

from packages.cost_engine.cvp import (
    CVPBaseline,
    CVPDelta,
    compute_bep,
    compute_bep_hash,
    compute_target_profit,
    simulate_cvp,
)


# ── V8 byte-identical — BEPResult ────────────────────────────
def test_bep_hash_100x_byte_identical():
    """100회 동일 BEPResult → 100회 byte-identical sha256 digest."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    expected = compute_bep_hash(result)
    for _ in range(100):
        assert compute_bep_hash(result) == expected


# ── V8 byte-identical — CVPResult ────────────────────────────
def test_cvp_result_hash_100x_byte_identical():
    """100회 동일 CVPResult → 100회 byte-identical sha256 digest."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
        target_profit=Decimal("5000000"),
    )
    delta = CVPDelta(
        unit_price_delta_pct=Decimal("0.1"),
        unit_variable_cost_delta_pct=Decimal("-0.05"),
    )
    result = simulate_cvp(baseline=baseline, delta=delta)
    expected = compute_bep_hash(result)
    for _ in range(100):
        assert compute_bep_hash(result) == expected


# ── V8 byte-identical — TargetProfitResult ───────────────────
def test_target_profit_hash_100x_byte_identical():
    """100회 동일 TargetProfitResult → 100회 byte-identical sha256 digest."""
    result = compute_target_profit(
        target_profit=Decimal("5000000"),
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    expected = compute_bep_hash(result)
    for _ in range(100):
        assert compute_bep_hash(result) == expected


# ── Cross-input variation ────────────────────────────────────
def test_bep_hash_varies_with_fixed_cost():
    """fixed_cost 변동 → hash 변동 (변경 감지)."""
    r1 = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    r2 = compute_bep(
        fixed_cost=Decimal("12000000"),  # different
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    assert compute_bep_hash(r1) != compute_bep_hash(r2)


def test_cvp_result_hash_varies_with_delta():
    """delta 변동 → hash 변동 (변경 감지)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    r1 = simulate_cvp(baseline=baseline, delta=CVPDelta())
    r2 = simulate_cvp(
        baseline=baseline, delta=CVPDelta(unit_price_delta_pct=Decimal("0.1"))
    )
    assert compute_bep_hash(r1) != compute_bep_hash(r2)


def test_target_profit_hash_varies_with_target_profit():
    """target_profit 변동 → hash 변동 (변경 감지)."""
    r1 = compute_target_profit(
        target_profit=Decimal("5000000"),
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    r2 = compute_target_profit(
        target_profit=Decimal("6000000"),  # different
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    assert compute_bep_hash(r1) != compute_bep_hash(r2)
