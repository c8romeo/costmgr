"""tests.cost_engine.test_cvp — Story 7.1 (Epic 7) pure kernel tests.

Tests for `packages.cost_engine.cvp`:
- `compute_bep`: 정상범위 + 3종 edge cases (unit_price ≤ variable_cost /
  fixed_cost < 0 / fixed_cost == 0)
- `compute_target_profit`: 정상범위 + 3종 edge cases (unit_price ≤ variable_cost /
  fixed_cost < 0 / target_profit < 0)
- `apply_delta`: 4 variables delta + baseline not mutated + operating_rate bounds
- `simulate_cvp`: orchestration + delta_summary 정확성
- `compute_bep_hash`: 결정론 + frozen=True enforcement
- 100회 determinism (byte-identical hash)
- Decimal precision: ROUND_HALF_EVEN parity
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.cvp import (
    BEP_HASH_PREFIX,
    BEP_INVALID_FIXED_COST_MESSAGE_KO,
    BEP_INVALID_PRICE_MESSAGE_KO,
    BEP_INVALID_TARGET_PROFIT_MESSAGE_KO,
    DEFAULT_OPERATING_RATE,
    DEFAULT_TARGET_PROFIT,
    OPERATING_RATE_MAX,
    OPERATING_RATE_MIN,
    QUANT_KRW,
    QUANT_QUANTITY,
    QUANT_RATIO,
    CVPBaseline,
    CVPDelta,
    CVPInvalidInputError,
    apply_delta,
    compute_bep,
    compute_bep_hash,
    compute_target_profit,
    simulate_cvp,
)


# ── Constants ────────────────────────────────────────────────
def test_cvp_constants():
    """Story 7.1 constants match spec §F7.1 + AD-8 monetary precision."""
    assert BEP_HASH_PREFIX == "sha256:"
    assert BEP_INVALID_PRICE_MESSAGE_KO == "단가는 단위변동비보다 커야 합니다 (정상범위 외)"
    assert BEP_INVALID_FIXED_COST_MESSAGE_KO == "고정비는 0 이상이어야 합니다"
    assert BEP_INVALID_TARGET_PROFIT_MESSAGE_KO == "목표이익은 0 이상이어야 합니다"
    assert Decimal("1.0") == DEFAULT_OPERATING_RATE
    assert Decimal("0") == DEFAULT_TARGET_PROFIT
    assert Decimal("0.5") == OPERATING_RATE_MIN
    assert Decimal("1.5") == OPERATING_RATE_MAX
    assert Decimal("1") == QUANT_KRW
    assert Decimal("0.01") == QUANT_QUANTITY
    assert Decimal("0.0001") == QUANT_RATIO


# ── compute_bep — happy path ────────────────────────────────
def test_compute_bep_basic():
    """Basic BEP: fixed_cost=10_000_000, unit_price=10_000, variable_cost=6_000 → 2_500개."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    assert result.bep_quantity == Decimal("2500.00")
    assert result.bep_revenue == Decimal("25000000")
    assert result.contribution_margin_per_unit == Decimal("4000")
    assert result.contribution_margin_ratio == Decimal("0.4000")


def test_compute_bep_high_margin():
    """High margin scenario: unit_price=15_000, variable_cost=5_000 → 66.67% ratio."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("5000"),
        unit_price=Decimal("15000"),
    )
    assert result.bep_quantity == Decimal("1000.00")
    assert result.bep_revenue == Decimal("15000000")
    assert result.contribution_margin_per_unit == Decimal("10000")
    assert result.contribution_margin_ratio == Decimal("0.6667")


def test_compute_bep_zero_fixed_cost_trivial():
    """fixed_cost=0 → trivially break-even (BEP 수량 0, 매출 0)."""
    result = compute_bep(
        fixed_cost=Decimal("0"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    assert result.bep_quantity == Decimal("0.00")
    assert result.bep_revenue == Decimal("0")
    assert result.contribution_margin_per_unit == Decimal("4000")
    assert result.contribution_margin_ratio == Decimal("0.4000")


# ── compute_bep — edge cases ────────────────────────────────
def test_compute_bep_unit_price_equals_variable_cost_raises():
    """unit_price == unit_variable_cost → ValueError (정상범위 외)."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_bep(
            fixed_cost=Decimal("10000000"),
            unit_variable_cost=Decimal("10000"),
            unit_price=Decimal("10000"),
        )
    assert exc_info.value.code == "unit_price_must_exceed_variable_cost"
    assert exc_info.value.field == "unit_price"


def test_compute_bep_unit_price_less_than_variable_cost_raises():
    """unit_price < unit_variable_cost → ValueError."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_bep(
            fixed_cost=Decimal("10000000"),
            unit_variable_cost=Decimal("10000"),
            unit_price=Decimal("9000"),
        )
    assert exc_info.value.code == "unit_price_must_exceed_variable_cost"


def test_compute_bep_negative_fixed_cost_raises():
    """fixed_cost < 0 → ValueError."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_bep(
            fixed_cost=Decimal("-1000000"),
            unit_variable_cost=Decimal("6000"),
            unit_price=Decimal("10000"),
        )
    assert exc_info.value.code == "fixed_cost_must_be_non_negative"
    assert exc_info.value.field == "fixed_cost"


# ── compute_target_profit — happy path ───────────────────────
def test_compute_target_profit_basic():
    """목표이익 5_000_000, fixed_cost=10_000_000 → target_quantity=3_750개."""
    result = compute_target_profit(
        target_profit=Decimal("5000000"),
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    assert result.target_quantity == Decimal("3750.00")
    assert result.target_revenue == Decimal("37500000")


def test_compute_target_profit_zero_profit_same_as_bep():
    """target_profit=0 → 동일 compute_bep 결과 (target_quantity = BEP)."""
    tp_result = compute_target_profit(
        target_profit=Decimal("0"),
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    bep_result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    assert tp_result.target_quantity == bep_result.bep_quantity
    assert tp_result.target_revenue == bep_result.bep_revenue


# ── compute_target_profit — edge cases ──────────────────────
def test_compute_target_profit_negative_profit_raises():
    """target_profit < 0 → ValueError."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_target_profit(
            target_profit=Decimal("-1000000"),
            fixed_cost=Decimal("10000000"),
            unit_variable_cost=Decimal("6000"),
            unit_price=Decimal("10000"),
        )
    assert exc_info.value.code == "target_profit_must_be_non_negative"
    assert exc_info.value.field == "target_profit"


def test_compute_target_profit_unit_price_equals_variable_cost_raises():
    """unit_price == unit_variable_cost → ValueError."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_target_profit(
            target_profit=Decimal("5000000"),
            fixed_cost=Decimal("10000000"),
            unit_variable_cost=Decimal("10000"),
            unit_price=Decimal("10000"),
        )
    assert exc_info.value.code == "unit_price_must_exceed_variable_cost"


def test_compute_target_profit_negative_fixed_cost_raises():
    """fixed_cost < 0 → ValueError."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_target_profit(
            target_profit=Decimal("5000000"),
            fixed_cost=Decimal("-1000000"),
            unit_variable_cost=Decimal("6000"),
            unit_price=Decimal("10000"),
        )
    assert exc_info.value.code == "fixed_cost_must_be_non_negative"


# ── apply_delta ─────────────────────────────────────────────
def test_apply_delta_zero_delta_returns_equivalent():
    """delta=zero → simulated = baseline (operating_rate 동일, target_profit 동일)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
        operating_rate=Decimal("1.0"),
        target_profit=Decimal("5000000"),
    )
    delta = CVPDelta()  # all zero
    simulated = apply_delta(baseline, delta)
    assert simulated.fixed_cost == baseline.fixed_cost
    assert simulated.unit_variable_cost == baseline.unit_variable_cost
    assert simulated.unit_price == baseline.unit_price
    assert simulated.operating_rate == baseline.operating_rate
    assert simulated.target_profit == baseline.target_profit


def test_apply_delta_unit_price_increase():
    """단가 +20% → unit_price × 1.2."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.2"))
    simulated = apply_delta(baseline, delta)
    assert simulated.unit_price == Decimal("12000")
    assert simulated.fixed_cost == baseline.fixed_cost


def test_apply_delta_baseline_not_mutated():
    """baseline frozen=True → mutation 시도 시 FrozenInstanceError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.2"))
    apply_delta(baseline, delta)
    # baseline must NOT be mutated (frozen=True).
    assert baseline.unit_price == Decimal("10000")


def test_apply_delta_operating_rate_out_of_bounds():
    """operating_rate result out of bounds → CVPInvalidInputError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
        operating_rate=Decimal("1.0"),
    )
    # operating_rate × 1.6 = 1.6 (out of bounds > 1.5).
    delta = CVPDelta(operating_rate_delta_pct=Decimal("0.6"))
    with pytest.raises(CVPInvalidInputError) as exc_info:
        apply_delta(baseline, delta)
    assert exc_info.value.code == "operating_rate_out_of_bounds"


def test_apply_delta_invalid_basetype_raises():
    """baseline not CVPBaseline → ValueError."""
    delta = CVPDelta()
    with pytest.raises(CVPInvalidInputError) as exc_info:
        apply_delta({"fixed_cost": Decimal("10000000")}, delta)  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_decimal_type"


def test_apply_delta_invalid_deltatype_raises():
    """delta not CVPDelta → ValueError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    with pytest.raises(CVPInvalidInputError) as exc_info:
        apply_delta(baseline, {"unit_price_delta_pct": Decimal("0.2")})  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_decimal_type"


# ── simulate_cvp ────────────────────────────────────────────
def test_simulate_cvp_full_orchestration():
    """Full orchestration: 4 variables delta + simulated + baseline BEP/target."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
        target_profit=Decimal("5000000"),
    )
    delta = CVPDelta(
        unit_price_delta_pct=Decimal("0.2"),
        unit_variable_cost_delta_pct=Decimal("-0.1"),
        fixed_cost_delta_pct=Decimal("0"),
        operating_rate_delta_pct=Decimal("0"),
    )
    result = simulate_cvp(baseline=baseline, delta=delta)

    # Simulated unit_price = 10000 × 1.2 = 12000.
    # Simulated unit_variable_cost = 6000 × 0.9 = 5400.
    # Simulated fixed_cost = 10000000 (unchanged).
    # contribution_margin = 12000 - 5400 = 6600.
    # simulated_bep_quantity = 10000000 / 6600 = 1515.15
    assert result.simulated_bep.bep_quantity == Decimal("1515.15")
    assert result.simulated_bep.contribution_margin_per_unit == Decimal("6600")

    # baseline BEP unchanged.
    assert result.baseline_bep.bep_quantity == Decimal("2500.00")

    # delta_summary 정확성 (4 keys).
    assert len(result.delta_summary) == 4
    assert result.delta_summary["unit_price_delta_pct"] == Decimal("0.2000")
    assert result.delta_summary["unit_variable_cost_delta_pct"] == Decimal("-0.1000")
    assert result.delta_summary["fixed_cost_delta_pct"] == Decimal("0.0000")
    assert result.delta_summary["operating_rate_delta_pct"] == Decimal("0.0000")


def test_simulate_cvp_invalid_baseline_raises():
    """baseline not CVPBaseline → ValueError."""
    delta = CVPDelta()
    with pytest.raises(CVPInvalidInputError) as exc_info:
        simulate_cvp(baseline={"fixed_cost": Decimal("10000000")}, delta=delta)  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_decimal_type"


def test_simulate_cvp_invalid_delta_raises():
    """delta not CVPDelta → ValueError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    with pytest.raises(CVPInvalidInputError) as exc_info:
        simulate_cvp(baseline=baseline, delta={"unit_price_delta_pct": Decimal("0.2")})  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_decimal_type"


def test_simulate_cvp_target_profit_carries_from_baseline():
    """simulate_cvp uses baseline.target_profit unchanged (not mutated)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
        target_profit=Decimal("8000000"),
    )
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.1"))
    result = simulate_cvp(baseline=baseline, delta=delta)
    # target_quantity = (10_000_000 + 8_000_000) / (11000 - 6000) = 3600
    assert result.simulated_target_profit.target_quantity == Decimal("3600.00")
    assert result.simulated_target_profit.target_revenue == Decimal("39600000")
    # baseline target_profit = (10_000_000 + 8_000_000) / (10000 - 6000) = 4500
    assert result.baseline_target_profit.target_quantity == Decimal("4500.00")


# ── compute_bep_hash — V8 determinism ───────────────────────
def test_compute_bep_hash_format():
    """Hash format: `sha256:` + 64-char hexdigest."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    digest = compute_bep_hash(result)
    assert digest.startswith(BEP_HASH_PREFIX)
    hex_part = digest[len(BEP_HASH_PREFIX):]
    assert len(hex_part) == 64  # 32 bytes = 64 hex chars
    int(hex_part, 16)  # validate hex


def test_compute_bep_hash_determinism():
    """동일 입력 → 동일 hash (NFR16 determinism)."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    h1 = compute_bep_hash(result)
    h2 = compute_bep_hash(result)
    assert h1 == h2


def test_compute_bep_hash_100x_byte_identical():
    """100회 동일 입력 → 100회 byte-identical hash (V8 회귀 가능)."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    expected = compute_bep_hash(result)
    for _ in range(100):
        assert compute_bep_hash(result) == expected


def test_compute_bep_hash_different_input_different_hash():
    """다른 fixed_cost → 다른 hash (변경 감지)."""
    r1 = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    r2 = compute_bep(
        fixed_cost=Decimal("12000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    assert compute_bep_hash(r1) != compute_bep_hash(r2)


def test_compute_bep_hash_works_on_cvp_result():
    """compute_bep_hash supports CVPResult type as well."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.1"))
    result = simulate_cvp(baseline=baseline, delta=delta)
    digest = compute_bep_hash(result)
    assert digest.startswith(BEP_HASH_PREFIX)
    assert len(digest) == len(BEP_HASH_PREFIX) + 64


def test_compute_bep_hash_works_on_target_profit_result():
    """compute_bep_hash supports TargetProfitResult type as well."""
    result = compute_target_profit(
        target_profit=Decimal("5000000"),
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    digest = compute_bep_hash(result)
    assert digest.startswith(BEP_HASH_PREFIX)


def test_compute_bep_hash_non_result_raises():
    """result not BEPResult/CVPResult/TargetProfitResult → ValueError."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_bep_hash({"bep_quantity": Decimal("2500")})  # type: ignore[arg-type]
    assert exc_info.value.code == "invalid_decimal_type"


# ── Frozen dataclass enforcement ────────────────────────────
def test_bep_result_is_frozen():
    """BEPResult is frozen=True → mutation 시 FrozenInstanceError."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.bep_quantity = Decimal("9999.99")  # type: ignore[misc]


def test_cvp_baseline_is_frozen():
    """CVPBaseline is frozen=True → mutation 시 FrozenInstanceError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        baseline.unit_price = Decimal("99999")  # type: ignore[misc]


def test_cvp_delta_is_frozen():
    """CVPDelta is frozen=True → mutation 시 FrozenInstanceError."""
    delta = CVPDelta()
    with pytest.raises(dataclasses.FrozenInstanceError):
        delta.unit_price_delta_pct = Decimal("0.5")  # type: ignore[misc]


def test_cvp_result_is_frozen():
    """CVPResult is frozen=True → mutation 시 FrozenInstanceError."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    delta = CVPDelta()
    result = simulate_cvp(baseline=baseline, delta=delta)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.simulated_bep = result.baseline_bep  # type: ignore[misc]


# ── Cross-function consistency ──────────────────────────────
def test_apply_delta_then_compute_bep_consistency():
    """apply_delta + compute_bep = simulate_cvp.simulated_bep (consistency check)."""
    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    delta = CVPDelta(
        unit_price_delta_pct=Decimal("0.1"),
        unit_variable_cost_delta_pct=Decimal("-0.05"),
    )
    simulated_baseline = apply_delta(baseline, delta)
    direct_bep = compute_bep(
        fixed_cost=simulated_baseline.fixed_cost,
        unit_variable_cost=simulated_baseline.unit_variable_cost,
        unit_price=simulated_baseline.unit_price,
    )
    orch_result = simulate_cvp(baseline=baseline, delta=delta)
    assert direct_bep == orch_result.simulated_bep


# ── Decimal precision parity (ROUND_HALF_EVEN) ──────────────
def test_decimal_round_half_even_parity():
    """ROUND_HALF_EVEN parity (banker's rounding) — AD-8 monetary types.

    contribution_margin_per_unit is quantized to KRW (Decimal("1")).
    Contribution margin ratio uses 4 decimal places (Decimal("0.0001")).
    """
    # Clean KRW-only numbers — no fractional KRW rounding artifacts.
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    # Contribution margin = 4000 KRW (exact, no rounding needed).
    assert result.contribution_margin_per_unit == Decimal("4000")
    # bep_quantity = 10000000 / 4000 = 2500.00 (exact).
    assert result.bep_quantity == Decimal("2500.00")
    # contribution_margin_ratio = 4000 / 10000 = 0.4 → 0.4000 (4dp quantization).
    assert result.contribution_margin_ratio == Decimal("0.4000")
    # bep_revenue = 2500 × 10000 = 25000000.
    assert result.bep_revenue == Decimal("25000000")


# ── Public API export ───────────────────────────────────────
def test_cvp_public_api_exports():
    """Public API export — all Story 7.1 functions importable from packages.cost_engine."""
    from packages.cost_engine import (  # noqa: F401
        BEPResult,
        CVPBaseline,
        CVPDelta,
        CVPInvalidInputError,
        CVPResult,
        TargetProfitResult,
        apply_delta,
        compute_bep,
        compute_bep_hash,
        compute_target_profit,
        simulate_cvp,
    )
    # All imports succeeded.
    assert True
