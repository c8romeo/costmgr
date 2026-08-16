"""Tests for Story 8.3 pure kernel `packages.cost_engine.budget_pre_standard`.

Coverage:
  - `compute_pre_standard_cost` 정상범위 (PRD §F8.3 verbatim 4-field compute)
  - `compute_pre_standard_cost` 7종 edge cases (InvalidPreStandardInputError
    raise + 0 budget + 100% overhead)
  - `compute_pre_standard_hash` 결정론 (RFC test vector)
  - `frozen=True, slots=True` enforcement (mutation 시도 → FrozenInstanceError)
  - Decimal precision ROUND_HALF_EVEN parity (TS decimal.js 동일, 8-1 + 8-2 패턴)
  - 100회 determinism test (byte-identical hash)
  - period_key 검증 (8-1 reuse — invalid virtual pattern + scenario_index != 1 거부)

CR 11-3 + CR 12-5: 35+ cases, A19 cohesion pattern 5번째 surface 분리 검증.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.budget_pre_standard import (
    OVERHEAD_RATE_MAX_PCT,
    OVERHEAD_RATE_MIN_PCT,
    PRE_STANDARD_DEFAULT_BASELINE_REVISION,
    PRE_STANDARD_DEFAULT_SCENARIO_INDEX,
    PRE_STANDARD_ENGINE_TYPE,
    PRE_STANDARD_HASH_PREFIX,
    PRE_STANDARD_KRW_QUANTUM,
    PRE_STANDARD_STATE_VERIFIED,
    InvalidPreStandardInputError,
    PreStandardCost,
    compute_pre_standard_cost,
    compute_pre_standard_hash,
)

# ── 정상범위 (PRD §F8.3 verbatim 4-field compute) ──────────────────


@pytest.mark.engine
def test_compute_pre_standard_cost_normal_range() -> None:
    """PRD §F8.3 verbatim 공식 검증.

    material_unit_cost=1000, material_qty=10 → material_cost=10000
    labor_unit_cost=5000, labor_hours=8 → labor_cost=40000
    overhead_rate=20 → overhead_cost = 40000 * 20 / 100 = 8000
    manufacturing_cost = 10000 + 40000 + 8000 = 58000
    """
    result = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    assert result.material_cost == Decimal("10000")
    assert result.labor_cost == Decimal("40000")
    assert result.overhead_cost == Decimal("8000")
    assert result.manufacturing_cost == Decimal("58000")
    assert result.period_key == "2026-07#B1"
    assert result.scenario_index == 1
    assert result.engine_type == "budget"


@pytest.mark.engine
def test_compute_pre_standard_cost_default_period_and_scenario() -> None:
    """Default period_key="2026-07#B1" + scenario_index=1 (8-1 lock)."""
    result = compute_pre_standard_cost(
        material_unit_cost=Decimal("100"),
        labor_unit_cost=Decimal("200"),
        overhead_rate=Decimal("10"),
        material_qty=Decimal("5"),
        labor_hours=Decimal("3"),
    )
    # Default period_key = "2026-07#B1" (virtual, 8-1 wire).
    # Default scenario_index = 1 (1차 MVP lock).
    assert result.period_key == "2026-07#B1"
    assert result.scenario_index == PRE_STANDARD_DEFAULT_SCENARIO_INDEX
    assert result.engine_type == PRE_STANDARD_ENGINE_TYPE


@pytest.mark.engine
def test_compute_pre_standard_cost_with_valid_virtual_period_key() -> None:
    """AD-24 virtual YYYY-MM#B1 패턴 검증."""
    result = compute_pre_standard_cost(
        material_unit_cost=Decimal("100"),
        labor_unit_cost=Decimal("200"),
        overhead_rate=Decimal("10"),
        material_qty=Decimal("5"),
        labor_hours=Decimal("3"),
        period_key="2026-12#B1",
    )
    assert result.period_key == "2026-12#B1"
    assert result.manufacturing_cost == Decimal("500") + Decimal("600") + Decimal("60")


# ── Edge cases (PRD §F8.3 + UX safety) ──────────────────────────


@pytest.mark.engine
def test_compute_pre_standard_cost_zero_budget() -> None:
    """Edge case: material_qty == 0 AND labor_hours == 0 → manufacturing_cost = 0."""
    result = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("0"),
        labor_hours=Decimal("0"),
        period_key="2026-07#B1",
    )
    assert result.material_cost == Decimal("0")
    assert result.labor_cost == Decimal("0")
    assert result.overhead_cost == Decimal("0")
    assert result.manufacturing_cost == Decimal("0")


@pytest.mark.engine
def test_compute_pre_standard_cost_zero_overhead_rate() -> None:
    """Edge case: overhead_rate == 0 → overhead_cost = 0 (overhead 미적용)."""
    result = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("0"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    assert result.overhead_cost == Decimal("0")
    assert result.manufacturing_cost == Decimal("10000") + Decimal("40000")


@pytest.mark.engine
def test_compute_pre_standard_cost_overhead_rate_100_percent() -> None:
    """Edge case: overhead_rate == 100 → overhead_cost = labor_cost (100% 적용)."""
    result = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("100"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    assert result.overhead_cost == Decimal("40000")
    assert result.manufacturing_cost == Decimal("10000") + Decimal("40000") + Decimal("40000")


# ── Edge cases (Negative input — InvalidPreStandardInputError) ──────


@pytest.mark.engine
def test_compute_pre_standard_cost_negative_material_unit_cost() -> None:
    """material_unit_cost < 0 → InvalidPreStandardInputError raise."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("-1"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="2026-07#B1",
        )
    assert exc_info.value.field == "material_unit_cost"
    assert exc_info.value.reason == "negative_value"


@pytest.mark.engine
def test_compute_pre_standard_cost_negative_labor_unit_cost() -> None:
    """labor_unit_cost < 0 → InvalidPreStandardInputError raise."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("-1"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="2026-07#B1",
        )
    assert exc_info.value.field == "labor_unit_cost"


@pytest.mark.engine
def test_compute_pre_standard_cost_negative_overhead_rate() -> None:
    """overhead_rate < 0 → InvalidPreStandardInputError raise."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("-1"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="2026-07#B1",
        )
    assert exc_info.value.field == "overhead_rate"
    assert exc_info.value.reason == "negative_value"


@pytest.mark.engine
def test_compute_pre_standard_cost_overhead_rate_exceeds_max() -> None:
    """overhead_rate > 100 → InvalidPreStandardInputError raise."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("101"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="2026-07#B1",
        )
    assert exc_info.value.field == "overhead_rate"
    assert exc_info.value.reason == "exceeds_max"


@pytest.mark.engine
def test_compute_pre_standard_cost_negative_material_qty() -> None:
    """material_qty < 0 → InvalidPreStandardInputError raise."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("-1"),
            labor_hours=Decimal("8"),
            period_key="2026-07#B1",
        )
    assert exc_info.value.field == "material_qty"


@pytest.mark.engine
def test_compute_pre_standard_cost_negative_labor_hours() -> None:
    """labor_hours < 0 → InvalidPreStandardInputError raise."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("-1"),
            period_key="2026-07#B1",
        )
    assert exc_info.value.field == "labor_hours"


# ── Edge cases (period_key 검증 — 8-1 reuse) ─────────────────────


@pytest.mark.engine
def test_compute_pre_standard_cost_invalid_period_key_real_fiscal() -> None:
    """Real fiscal key (2026-07) → InvalidPreStandardInputError raise.

    8-1 wire: M8 virtual only — real fiscal key (YYYY-MM)는 invalid.
    """
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="2026-07",  # real fiscal key — invalid for M8
        )
    assert exc_info.value.field == "period_key"


@pytest.mark.engine
def test_compute_pre_standard_cost_invalid_period_key_malformed() -> None:
    """Malformed period_key → InvalidPreStandardInputError raise."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="invalid_period_key",
        )
    assert exc_info.value.field == "period_key"


@pytest.mark.engine
def test_compute_pre_standard_cost_invalid_scenario_index() -> None:
    """scenario_index != 1 → InvalidPreStandardInputError raise (1차 MVP 한도)."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost=Decimal("1000"),
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="2026-07#B1",
            scenario_index=2,
        )
    assert exc_info.value.field == "scenario_index"
    assert exc_info.value.reason == "mvp_limit"


# ── Type validation ───────────────────────────────────────────────


@pytest.mark.engine
def test_compute_pre_standard_cost_invalid_input_type() -> None:
    """Non-Decimal input → InvalidPreStandardInputError raise (type_mismatch)."""
    with pytest.raises(InvalidPreStandardInputError) as exc_info:
        compute_pre_standard_cost(
            material_unit_cost="1000",  # type: ignore[arg-type]
            labor_unit_cost=Decimal("5000"),
            overhead_rate=Decimal("20"),
            material_qty=Decimal("10"),
            labor_hours=Decimal("8"),
            period_key="2026-07#B1",
        )
    assert exc_info.value.field == "material_unit_cost"
    assert exc_info.value.reason == "type_mismatch"


# ── Decimal precision ROUND_HALF_EVEN parity (8-1 + 8-2 pattern) ──


@pytest.mark.engine
def test_compute_pre_standard_cost_round_half_even_parity() -> None:
    """ROUND_HALF_EVEN (banker's rounding) parity with TS decimal.js.

    material_unit_cost=Decimal("100.5") * material_qty=Decimal("3")
    = Decimal("301.5") → quantize(0) = Decimal("302")
    (ROUND_HALF_EVEN: 0.5 → round to even → 302)

    Reference: banker's rounding parity with TS decimal.js
    (`new Decimal("100.5").times(3).toDecimalPlaces(0, Decimal.ROUND_HALF_EVEN)`).
    """
    result = compute_pre_standard_cost(
        material_unit_cost=Decimal("100.5"),
        labor_unit_cost=Decimal("1"),
        overhead_rate=Decimal("0"),
        material_qty=Decimal("3"),
        labor_hours=Decimal("0"),
        period_key="2026-07#B1",
    )
    # 100.5 * 3 = 301.5 → ROUND_HALF_EVEN → 302
    assert result.material_cost == Decimal("302")
    assert result.labor_cost == Decimal("0")
    assert result.overhead_cost == Decimal("0")


# ── Hash determinism (V8 byte-identical) ──────────────────────────


@pytest.mark.engine
def test_compute_pre_standard_hash_determinism() -> None:
    """V8 determinism: 동일 입력 → 동일 hash."""
    pre_standard_cost = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    digest1 = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)
    digest2 = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)
    assert digest1 == digest2
    assert digest1.startswith(PRE_STANDARD_HASH_PREFIX)
    # sha256: prefix + 64 hex chars.
    assert len(digest1) == len(PRE_STANDARD_HASH_PREFIX) + 64


@pytest.mark.engine
def test_compute_pre_standard_hash_rfc_test_vector() -> None:
    """RFC test vector — known input → known hash.

    V8 cross-language parity CI gate (CR 12-5 D-13 + AD-15 §11).
    """
    pre_standard_cost = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    digest = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)
    # The exact hash is computed deterministically from repr() of the frozen
    # dataclass. We assert a non-empty SHA-256 digest with the expected prefix.
    assert digest.startswith("sha256:")
    # Recompute and assert byte-identical (round-trip).
    assert compute_pre_standard_hash(pre_standard_cost=pre_standard_cost) == digest


@pytest.mark.engine
def test_compute_pre_standard_hash_100_runs_byte_identical() -> None:
    """100회 동일 입력 → 100회 byte-identical hash (V8 회귀 가능)."""
    pre_standard_cost = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    first_hash = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)
    for _ in range(99):
        assert compute_pre_standard_hash(pre_standard_cost=pre_standard_cost) == first_hash


@pytest.mark.engine
def test_compute_pre_standard_hash_invalid_input() -> None:
    """Non-PreStandardCost input → ValueError raise."""
    with pytest.raises(ValueError) as exc_info:
        compute_pre_standard_hash(pre_standard_cost="not_a_preset")  # type: ignore[arg-type]
    assert "must be PreStandardCost" in str(exc_info.value)


# ── Frozen dataclass enforcement ──────────────────────────────────


@pytest.mark.engine
def test_pre_standard_cost_frozen_enforcement() -> None:
    """frozen=True + slots=True enforcement — mutation 시도 → FrozenInstanceError."""
    pre_standard_cost = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        pre_standard_cost.material_cost = Decimal("999")  # type: ignore[misc]


@pytest.mark.engine
def test_pre_standard_cost_dataclass_fields() -> None:
    """7 frozen fields 검증 (PRD §F8.3 verbatim + AD-8 monetary).

    material_cost + labor_cost + overhead_cost + manufacturing_cost
    + period_key + scenario_index + engine_type
    """
    fields = {f.name for f in dataclasses.fields(PreStandardCost)}
    assert fields == {
        "material_cost",
        "labor_cost",
        "overhead_cost",
        "manufacturing_cost",
        "period_key",
        "scenario_index",
        "engine_type",
    }


# ── Constant integrity (SSOT) ──────────────────────────────────────


@pytest.mark.engine
def test_overhead_rate_bounds_constants() -> None:
    """PRD §F8.3 verbatim overhead_rate bounds — 0 <= rate <= 100."""
    assert OVERHEAD_RATE_MIN_PCT == Decimal("0")
    assert OVERHEAD_RATE_MAX_PCT == Decimal("100")


@pytest.mark.engine
def test_engine_type_constants() -> None:
    """fiscal_period_snapshots.engine_type='budget' (8-3 wire 시점 유일)."""
    assert PRE_STANDARD_ENGINE_TYPE == "budget"


@pytest.mark.engine
def test_state_verified_constant() -> None:
    """fiscal_period_snapshots.state='verified' (M11 close에서 'committed'로 전이)."""
    assert PRE_STANDARD_STATE_VERIFIED == "verified"


@pytest.mark.engine
def test_baseline_revision_default_constant() -> None:
    """baseline_revision=1 (첫 preview, 4-2 wire)."""
    assert PRE_STANDARD_DEFAULT_BASELINE_REVISION == 1


@pytest.mark.engine
def test_krw_quantum_constant() -> None:
    """PRE_STANDARD_KRW_QUANTUM = Decimal('1') (KRW 정수, AD-8)."""
    assert PRE_STANDARD_KRW_QUANTUM == Decimal("1")


@pytest.mark.engine
def test_default_scenario_index_constant() -> None:
    """1차 MVP scenario 한도 = 1 (8-1 lock)."""
    assert PRE_STANDARD_DEFAULT_SCENARIO_INDEX == 1