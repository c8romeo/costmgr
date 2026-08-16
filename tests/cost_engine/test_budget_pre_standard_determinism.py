"""V8 byte-identical CI gate for Story 8.3 budget_pre_standard.py.

CR 12-5 D-13 + AD-15 §11 cross-language parity.

8-1 `test_budget_scenario_determinism.py` + 8-2 `test_budget_variance_determinism.py`
패턴 미러 (5+ cases).

Validates:
  - 100회 동일 입력 → 100회 byte-identical `pre_standard_hash`
  - hash는 sha256 prefix + 64 hex chars
  - Decimal precision 유지 (전체 자릿수 보존)
  - Order-independent hash (dataclass frozen slots)
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.cost_engine.budget_pre_standard import (
    PRE_STANDARD_HASH_PREFIX,
    InvalidPreStandardInputError,
    compute_pre_standard_cost,
    compute_pre_standard_hash,
)


@pytest.mark.engine
def test_determinism_100_runs_byte_identical() -> None:
    """V8 byte-identical CI gate — 100회 동일 입력 → 동일 hash."""
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
def test_determinism_hash_format() -> None:
    """Hash format: sha256: prefix + 64 hex chars."""
    pre_standard_cost = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    digest = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)
    assert digest.startswith(PRE_STANDARD_HASH_PREFIX)
    hex_part = digest.removeprefix(PRE_STANDARD_HASH_PREFIX)
    assert len(hex_part) == 64
    # Hex chars only.
    int(hex_part, 16)


@pytest.mark.engine
def test_determinism_different_inputs_different_hash() -> None:
    """다른 입력 → 다른 hash (collision 방지)."""
    pre_standard_cost_a = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    pre_standard_cost_b = compute_pre_standard_cost(
        material_unit_cost=Decimal("1001"),  # 1원 차이
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    hash_a = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost_a)
    hash_b = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost_b)
    assert hash_a != hash_b


@pytest.mark.engine
def test_determinism_decimal_precision_preserved() -> None:
    """Decimal 정밀도 보존 — repr() full precision (dataclass auto).

    QUANTIZE 후에도 KRW integer 결과값이 repr()에 결정론으로 보존됨.
    동일 입력 → 동일 quantized result → 동일 hash.
    """
    pre_standard_cost = compute_pre_standard_cost(
        material_unit_cost=Decimal("1234.5678"),
        labor_unit_cost=Decimal("9876.5432"),
        overhead_rate=Decimal("15.5"),
        material_qty=Decimal("100"),
        labor_hours=Decimal("80"),
        period_key="2026-07#B1",
    )
    # After quantize to PRE_STANDARD_KRW_QUANTUM=Decimal('1'), result is KRW integer.
    # repr() preserves the quantized Decimal values.
    repr_str = repr(pre_standard_cost)
    assert "123457" in repr_str  # 1234.5678 * 100 = 123456.78 → 123457 (ROUND_HALF_EVEN)
    assert "790123" in repr_str  # 9876.5432 * 80 = 790123.456 → 790123 (ROUND_HALF_EVEN)
    # Hash must be byte-identical regardless of quantize rounding.
    hash1 = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)
    hash2 = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost)
    assert hash1 == hash2


@pytest.mark.engine
def test_determinism_independent_recompute_byte_identical() -> None:
    """독립 recompute → byte-identical hash (AD-5 purity invariant)."""
    # Two independent compute_pre_standard_cost calls with same inputs.
    pre_standard_cost_a = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    pre_standard_cost_b = compute_pre_standard_cost(
        material_unit_cost=Decimal("1000"),
        labor_unit_cost=Decimal("5000"),
        overhead_rate=Decimal("20"),
        material_qty=Decimal("10"),
        labor_hours=Decimal("8"),
        period_key="2026-07#B1",
    )
    hash_a = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost_a)
    hash_b = compute_pre_standard_hash(pre_standard_cost=pre_standard_cost_b)
    assert hash_a == hash_b


@pytest.mark.engine
def test_determinism_error_path_byte_identical() -> None:
    """에러 경로에서도 동일 입력 → 동일 exception (determinism 검증)."""
    for _ in range(10):
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