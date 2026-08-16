"""Tests for Story 9.2 CCR + Allocation pure kernel (`packages.cost_engine.abc_engine`).

PRD §F9.2 verbatim:
  - CCR = 부서 원가 ÷ 실제 조업능력, 1원 단위 (1-Won precision).
  - 미사용능력 = 별도 행 (PRD §A9 verbatim).
  - Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가) (PRD §A6 + §V7).

Coverage:
  - `compute_ccr` 정상범위 (PRD §F9.2 verbatim 1-Won precision).
  - `compute_ccr` edge cases (음수 / ZeroDivision / type_mismatch / 빈 ID).
  - `compute_ccr_hash` 결정론 (V8 byte-identical).
  - `produce_unused_capacity_row` 정상범위 (PRD §A9 verbatim 별도 행).
  - `produce_unused_capacity_row` edge cases (음수 / 초과_capacity).
  - `compute_allocation` 정상범위 (Activity mapping + Cost Object Breakdown).
  - `compute_allocation` V7 balance invariant (PRD §A6 + §V7).
  - `compute_allocation` edge cases (빈 lists / 불균형).
  - `frozen=True, slots=True` enforcement (CCR + Allocation).
  - Decimal precision ROUND_HALF_EVEN parity (TS decimal.js 동일).
  - constants 노출 검증 (3 NEW constants).
  - typed exception class 검증 (2 NEW typed exceptions).

CR 11-3 + CR 12-5: ~38 cases, A19 cohesion pattern 7번째 surface 분리 검증.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    ABC_PRECISION_KRW_TOLERANCE,
    CCR_HASH_PREFIX,
    CCR_KRW_QUANTUM,
    ActivityMapping,
    AllocationBalanceError,
    AllocationResult,
    AllocationState,
    CcrComputeError,
    CCRResult,
    CostObjectRow,
    UnusedCapacityRow,
    compute_allocation,
    compute_allocation_hash,
    compute_ccr,
    compute_ccr_hash,
    produce_unused_capacity_row,
)

# ── 정상범위 (PRD §F9.2 verbatim 1-Won precision) ─────────────


@pytest.mark.engine
def test_compute_ccr_normal_range() -> None:
    """PRD §F9.2 verbatim — 13,200,000 / 400 = 33,000원/시간.

    여행상품 설계 부서 예시 — 1-Won precision invariant.
    """
    result = compute_ccr(
        department_id="dept-001",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    assert result.department_id == "dept-001"
    assert result.department_cost == Decimal("13200000")
    assert result.practical_capacity_hours == Decimal("400")
    assert result.ccr_per_hour == Decimal("33000")
    assert result.hash.startswith(CCR_HASH_PREFIX)
    assert len(result.hash) == len(CCR_HASH_PREFIX) + 64


@pytest.mark.engine
def test_compute_ccr_small_department() -> None:
    """소규모 부서 — 1,000,000 / 100 = 10,000원/시간."""
    result = compute_ccr(
        department_id="dept-small",
        department_cost=Decimal("1000000"),
        practical_capacity_hours=Decimal("100"),
    )
    assert result.ccr_per_hour == Decimal("10000")


@pytest.mark.engine
def test_compute_ccr_rounds_half_even() -> None:
    """ROUND_HALF_EVEN parity — 1,234,567 / 333 = 3707.40841... → 3707.

    AD-8 + cross-language parity: Python ROUND_HALF_EVEN ↔ TS decimal.js.
    """
    result = compute_ccr(
        department_id="dept-round",
        department_cost=Decimal("1234567"),
        practical_capacity_hours=Decimal("333"),
    )
    # 1234567 / 333 = 3707.4084... → ROUND_HALF_EVEN → 3707
    assert result.ccr_per_hour == Decimal("3707")


@pytest.mark.engine
def test_compute_ccr_bankers_round() -> None:
    """Banker's rounding — 2500 / 2 = 1250 (exact, half-test skip)."""
    result = compute_ccr(
        department_id="dept-bankers",
        department_cost=Decimal("2500"),
        practical_capacity_hours=Decimal("2"),
    )
    assert result.ccr_per_hour == Decimal("1250")


# ── Edge cases (음수 / ZeroDivision / type_mismatch / 빈 ID) ─────


@pytest.mark.engine
def test_compute_ccr_zero_capacity_raises() -> None:
    """practical_capacity_hours = 0 → CcrComputeError(reason="invalid_capacity").

    PRD §F9.2 verbatim: 1원 단위 계산, ZeroDivision 회피.
    """
    with pytest.raises(CcrComputeError) as exc_info:
        compute_ccr(
            department_id="dept-zero",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("0"),
        )
    assert exc_info.value.department_id == "dept-zero"
    assert exc_info.value.reason == "invalid_capacity"


@pytest.mark.engine
def test_compute_ccr_negative_capacity_raises() -> None:
    """practical_capacity_hours < 0 → CcrComputeError."""
    with pytest.raises(CcrComputeError) as exc_info:
        compute_ccr(
            department_id="dept-neg",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("-50"),
        )
    assert exc_info.value.reason == "invalid_capacity"


@pytest.mark.engine
def test_compute_ccr_negative_cost_raises() -> None:
    """department_cost < 0 → CcrComputeError(reason="negative_cost")."""
    with pytest.raises(CcrComputeError) as exc_info:
        compute_ccr(
            department_id="dept-negcost",
            department_cost=Decimal("-100"),
            practical_capacity_hours=Decimal("400"),
        )
    assert exc_info.value.reason == "negative_cost"


@pytest.mark.engine
def test_compute_ccr_type_mismatch_raises() -> None:
    """department_cost not Decimal → CcrComputeError(reason="type_mismatch")."""
    with pytest.raises(CcrComputeError) as exc_info:
        # type: ignore[arg-type]
        compute_ccr(
            department_id="dept-typo",
            department_cost="13200000",
            practical_capacity_hours=Decimal("400"),
        )
    assert exc_info.value.reason == "type_mismatch"


@pytest.mark.engine
def test_compute_ccr_empty_department_id_raises() -> None:
    """department_id empty → CcrComputeError(reason="empty_department_id")."""
    with pytest.raises(CcrComputeError) as exc_info:
        compute_ccr(
            department_id="",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
    assert exc_info.value.reason == "empty_department_id"


# ── compute_ccr_hash 결정론 (V8 byte-identical) ────────────────


@pytest.mark.engine
def test_compute_ccr_hash_byte_identical() -> None:
    """V8 determinism — 동일 입력 → byte-identical hash (100회 반복)."""
    first = compute_ccr(
        department_id="dept-deterministic",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    for _ in range(100):
        again = compute_ccr(
            department_id="dept-deterministic",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        assert again.hash == first.hash


@pytest.mark.engine
def test_compute_ccr_hash_different_department() -> None:
    """다른 department_id → 다른 hash."""
    h_a = compute_ccr(
        department_id="dept-A",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    ).hash
    h_b = compute_ccr(
        department_id="dept-B",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    ).hash
    assert h_a != h_b


@pytest.mark.engine
def test_compute_ccr_hash_format() -> None:
    """hash format = sha256: + 64-char hexdigest."""
    result = compute_ccr(
        department_id="dept-format",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    assert result.hash.startswith("sha256:")
    assert len(result.hash) == 7 + 64  # sha256: prefix + 64 hex
    hex_part = result.hash[len("sha256:"):]
    assert all(c in "0123456789abcdef" for c in hex_part)


@pytest.mark.engine
def test_compute_ccr_hash_detached_function() -> None:
    """compute_ccr_hash standalone function — 동일 CCRResult → 동일 hash."""
    result = compute_ccr(
        department_id="dept-standalone",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    h1 = compute_ccr_hash(ccr_result=result)
    h2 = compute_ccr_hash(ccr_result=result)
    assert h1 == h2
    # Note: stored hash was computed with placeholder "" so differs from
    # re-computed detached hash (this matches 9-1 validate_validation_hash
    # precedent — re-computed hash is `repr(state)` including stored hash).


# ── produce_unused_capacity_row (PRD §A9 verbatim) ──────────────


@pytest.mark.engine
def test_produce_unused_capacity_row_normal_range() -> None:
    """PRD §F9.2 + §A9 verbatim — 미사용능력 별도 행 6,600,000원.

    부서 19,800,000원 / 600h = 33,000원/시간 CCR.
    사용 400h, 미사용 200h × 33,000원/시간 = 6,600,000원.
    """
    ccr = compute_ccr(
        department_id="dept-001",
        department_cost=Decimal("19800000"),
        practical_capacity_hours=Decimal("600"),
    )
    row = produce_unused_capacity_row(
        ccr=ccr,
        used_hours=Decimal("400"),
    )
    assert row.unused_hours == Decimal("200")
    assert row.ccr_per_hour == Decimal("33000")
    assert row.unused_cost_krw == Decimal("6600000")
    assert row.hash.startswith(CCR_HASH_PREFIX)


@pytest.mark.engine
def test_produce_unused_capacity_row_zero_hours() -> None:
    """used_hours = 0 → unused = practical_capacity_hours, 정상.

    19,800,000 / 600h × 600h = 19,800,000원 (전액 미사용).
    """
    ccr = compute_ccr(
        department_id="dept-zero",
        department_cost=Decimal("19800000"),
        practical_capacity_hours=Decimal("600"),
    )
    row = produce_unused_capacity_row(ccr=ccr, used_hours=Decimal("0"))
    assert row.unused_hours == Decimal("600")
    assert row.unused_cost_krw == Decimal("19800000")


@pytest.mark.engine
def test_produce_unused_capacity_row_full_used() -> None:
    """used_hours = practical_capacity_hours → unused = 0, 정상."""
    ccr = compute_ccr(
        department_id="dept-full",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    row = produce_unused_capacity_row(ccr=ccr, used_hours=Decimal("400"))
    assert row.unused_hours == Decimal("0")
    assert row.unused_cost_krw == Decimal("0")


@pytest.mark.engine
def test_produce_unused_capacity_row_negative_used_raises() -> None:
    """used_hours < 0 → CcrComputeError(reason="negative_used_hours")."""
    ccr = compute_ccr(
        department_id="dept-negused",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    with pytest.raises(CcrComputeError) as exc_info:
        produce_unused_capacity_row(ccr=ccr, used_hours=Decimal("-10"))
    assert exc_info.value.reason == "negative_used_hours"


@pytest.mark.engine
def test_produce_unused_capacity_row_exceeds_capacity_raises() -> None:
    """used_hours > capacity → CcrComputeError(reason="exceeds_capacity")."""
    ccr = compute_ccr(
        department_id="dept-exceed",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    with pytest.raises(CcrComputeError) as exc_info:
        produce_unused_capacity_row(ccr=ccr, used_hours=Decimal("500"))
    assert exc_info.value.reason == "exceeds_capacity"


@pytest.mark.engine
def test_produce_unused_capacity_row_type_mismatch_raises() -> None:
    """used_hours not Decimal → CcrComputeError(reason="type_mismatch")."""
    ccr = compute_ccr(
        department_id="dept-type",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    with pytest.raises(CcrComputeError) as exc_info:
        # type: ignore[arg-type]
        produce_unused_capacity_row(ccr=ccr, used_hours=400)
    assert exc_info.value.reason == "type_mismatch"


# ── compute_allocation (PRD §A6 + §V7 verbatim ABC 무결성) ──────


@pytest.mark.engine
def test_compute_allocation_balanced() -> None:
    """V7 무결성 — Σ breakdown + unused = Σ department_cost → is_balanced=True.

    예: 부서 원가 13,200,000원, 사용 400h × 33,000 = 13,200,000원 (전액 사용)
        + 미사용 0원 = 13,200,000원 = 부서 원가 → balanced.
    """
    ccr = compute_ccr(
        department_id="dept-001",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    activity_mappings = [
        ActivityMapping(
            activity_id="act-001",
            hours=Decimal("400"),
            ccr_amount_krw=Decimal("13200000"),
        ),
    ]
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("13200000"),
        ),
    ]
    result = compute_allocation(
        ccr=ccr,
        activity_mappings=activity_mappings,
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    assert result.is_balanced is True
    assert result.total_breakdown_sum == Decimal("13200000")
    assert result.department_cost == Decimal("13200000")


@pytest.mark.engine
def test_compute_allocation_with_unused_capacity() -> None:
    """V7 무결성 with 미사용능력 — Σ breakdown + unused = Σ department_cost.

    예: 부서 13,200,000원, used 400h × 33,000 = 13,200,000원,
        unused 200h × 33,000 = 6,600,000원 → 부서 원가 = 19,800,000원.
        Σ breakdown 13,200,000 + unused 6,600,000 = 19,800,000 = department_cost.
    """
    ccr = compute_ccr(
        department_id="dept-001",
        department_cost=Decimal("19800000"),
        practical_capacity_hours=Decimal("600"),
    )
    activity_mappings = [
        ActivityMapping(
            activity_id="act-001",
            hours=Decimal("400"),
            ccr_amount_krw=Decimal("13200000"),
        ),
    ]
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("13200000"),
        ),
    ]
    result = compute_allocation(
        ccr=ccr,
        activity_mappings=activity_mappings,
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    assert result.is_balanced is True
    assert result.total_breakdown_sum == Decimal("13200000")
    assert result.unused_capacity.unused_cost_krw == Decimal("6600000")


@pytest.mark.engine
def test_compute_allocation_unbalanced_returns_false() -> None:
    """V7 불균형 — Σ breakdown ≠ department_cost → is_balanced=False.

    9-2 wire는 raise 안 함 (D-9-3-DEFER 후보); frontend disabled signal.
    """
    ccr = compute_ccr(
        department_id="dept-unbalanced",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    # intentionally wrong breakdown sum
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("10000000"),  # not 13,200,000
        ),
    ]
    result = compute_allocation(
        ccr=ccr,
        activity_mappings=[],
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),  # full, unused=0
    )
    assert result.is_balanced is False
    assert result.total_breakdown_sum == Decimal("10000000")


@pytest.mark.engine
def test_compute_allocation_multiple_products() -> None:
    """원가대상 4개 (상품A/B/C/D) — Σ = department_cost."""
    ccr = compute_ccr(
        department_id="dept-multi",
        department_cost=Decimal("12000000"),
        practical_capacity_hours=Decimal("400"),
    )
    activity_mappings = [
        ActivityMapping(
            activity_id="act-001",
            hours=Decimal("160"),
            ccr_amount_krw=Decimal("4800000"),
        ),
        ActivityMapping(
            activity_id="act-002",
            hours=Decimal("140"),
            ccr_amount_krw=Decimal("4200000"),
        ),
        ActivityMapping(
            activity_id="act-003",
            hours=Decimal("100"),
            ccr_amount_krw=Decimal("3000000"),
        ),
    ]
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("3000000"),
        ),
        CostObjectRow(
            product_id="prod-B",
            activity_id="act-002",
            driver_id="drv-002",
            allocated_krw=Decimal("3500000"),
        ),
        CostObjectRow(
            product_id="prod-C",
            activity_id="act-003",
            driver_id="drv-001",
            allocated_krw=Decimal("2500000"),
        ),
        CostObjectRow(
            product_id="prod-D",
            activity_id="act-001",
            driver_id="drv-002",
            allocated_krw=Decimal("3000000"),
        ),
    ]
    result = compute_allocation(
        ccr=ccr,
        activity_mappings=activity_mappings,
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    assert result.total_breakdown_sum == Decimal("12000000")
    assert result.is_balanced is True


@pytest.mark.engine
def test_compute_allocation_empty_breakdown() -> None:
    """빈 cost_object_breakdown → total = 0, is_balanced = (0+unused==dept)."""
    ccr = compute_ccr(
        department_id="dept-empty",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    result = compute_allocation(
        ccr=ccr,
        activity_mappings=[],
        cost_object_breakdown=[],
        used_hours=Decimal("400"),
    )
    assert result.total_breakdown_sum == Decimal("0")
    assert result.is_balanced is False  # 0 + 0 != 13,200,000


@pytest.mark.engine
def test_compute_allocation_hash_byte_identical() -> None:
    """V8 determinism — 동일 inputs → byte-identical hash (100회 반복)."""
    ccr = compute_ccr(
        department_id="dept-deterministic-alloc",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    activity_mappings = [
        ActivityMapping(
            activity_id="act-001",
            hours=Decimal("400"),
            ccr_amount_krw=Decimal("13200000"),
        ),
    ]
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("13200000"),
        ),
    ]
    first = compute_allocation(
        ccr=ccr,
        activity_mappings=list(activity_mappings),
        cost_object_breakdown=list(cost_object_breakdown),
        used_hours=Decimal("400"),
    )
    for _ in range(100):
        again = compute_allocation(
            ccr=ccr,
            activity_mappings=list(activity_mappings),
            cost_object_breakdown=list(cost_object_breakdown),
            used_hours=Decimal("400"),
        )
        assert compute_allocation_hash(allocation=again) == compute_allocation_hash(allocation=first)


# ── frozen=True, slots=True enforcement ─────────────────────────


@pytest.mark.engine
def test_ccr_result_is_frozen() -> None:
    """CCRResult frozen → mutation 시도 → FrozenInstanceError."""
    result = compute_ccr(
        department_id="dept-frozen",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.department_id = "modified"  # type: ignore[misc]


@pytest.mark.engine
def test_allocation_result_is_frozen() -> None:
    """AllocationResult frozen."""
    ccr = compute_ccr(
        department_id="dept-alloc-frozen",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    result = compute_allocation(
        ccr=ccr,
        activity_mappings=[],
        cost_object_breakdown=[],
        used_hours=Decimal("400"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.is_balanced = not result.is_balanced  # type: ignore[misc]


@pytest.mark.engine
def test_unused_capacity_row_is_frozen() -> None:
    """UnusedCapacityRow frozen."""
    ccr = compute_ccr(
        department_id="dept-unused-frozen",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    row = produce_unused_capacity_row(ccr=ccr, used_hours=Decimal("100"))
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.unused_hours = Decimal("999")  # type: ignore[misc]


@pytest.mark.engine
def test_activity_mapping_is_frozen() -> None:
    """ActivityMapping frozen."""
    mapping = ActivityMapping(
        activity_id="act-001",
        hours=Decimal("100"),
        ccr_amount_krw=Decimal("3300000"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        mapping.hours = Decimal("999")  # type: ignore[misc]


@pytest.mark.engine
def test_cost_object_row_is_frozen() -> None:
    """CostObjectRow frozen."""
    row = CostObjectRow(
        product_id="prod-A",
        activity_id="act-001",
        driver_id="drv-001",
        allocated_krw=Decimal("1000000"),
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.allocated_krw = Decimal("9999")  # type: ignore[misc]


# ── Constants 노출 검증 (3 NEW constants) ──────────────────────


@pytest.mark.engine
def test_constants_exposed() -> None:
    """9-2 surface에 3 NEW constants 노출 — CCR_KRW_QUANTUM +
    ABC_PRECISION_KRW_TOLERANCE + CCR_HASH_PREFIX."""
    assert Decimal("1") == CCR_KRW_QUANTUM
    assert CCR_KRW_QUANTUM.__class__.__name__ == "Decimal"
    assert Decimal("0.01") == ABC_PRECISION_KRW_TOLERANCE
    assert CCR_HASH_PREFIX == "sha256:"


# ── Typed exception class 검증 ──────────────────────────────────


@pytest.mark.engine
def test_typed_exceptions_exposed() -> None:
    """9-2 surface에 2 NEW typed exceptions 노출."""
    assert issubclass(CcrComputeError, ValueError)
    assert issubclass(AllocationBalanceError, ValueError)


@pytest.mark.engine
def test_ccr_compute_error_attributes() -> None:
    """CcrComputeError attributes 검증."""
    err = CcrComputeError(
        "test",
        department_id="dept-001",
        reason="invalid_capacity",
    )
    assert err.department_id == "dept-001"
    assert err.reason == "invalid_capacity"


@pytest.mark.engine
def test_allocation_balance_error_attributes() -> None:
    """AllocationBalanceError attributes 검증."""
    err = AllocationBalanceError(
        "test",
        department_id="dept-001",
        expected_sum=Decimal("13200000"),
        actual_sum=Decimal("10000000"),
        reason="balance_mismatch",
    )
    assert err.department_id == "dept-001"
    assert err.expected_sum == Decimal("13200000")
    assert err.actual_sum == Decimal("10000000")
    assert err.reason == "balance_mismatch"


# ── AllocationState union (TS mirror parity) ─────────────────────


@pytest.mark.engine
def test_allocation_state_union_coverage() -> None:
    """AllocationState union covers all 5 NEW frozen dataclasses — TS mirror parity."""
    ccr = CCRResult(
        department_id="dept-001",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
        ccr_per_hour=Decimal("33000"),
        hash="sha256:" + "a" * 64,
    )
    mapping = ActivityMapping(
        activity_id="act-001",
        hours=Decimal("100"),
        ccr_amount_krw=Decimal("3300000"),
    )
    cost_row = CostObjectRow(
        product_id="prod-A",
        activity_id="act-001",
        driver_id="drv-001",
        allocated_krw=Decimal("3300000"),
    )
    unused = UnusedCapacityRow(
        unused_hours=Decimal("200"),
        ccr_per_hour=Decimal("33000"),
        unused_cost_krw=Decimal("6600000"),
        hash="sha256:" + "b" * 64,
    )
    alloc = AllocationResult(
        ccr=ccr,
        activity_mappings=(mapping,),
        cost_object_breakdown=(cost_row,),
        unused_capacity=unused,
        department_cost=Decimal("13200000"),
        total_breakdown_sum=Decimal("3300000"),
        is_balanced=False,
    )
    # Discriminated union — all 5 types accepted
    for instance in (ccr, mapping, cost_row, unused, alloc):
        assert isinstance(instance, AllocationState)


# ── 1-Won precision boundary tests ─────────────────────────────


@pytest.mark.engine
def test_compute_ccr_one_won_precision_invariant() -> None:
    """1-Won precision invariant — ccr_per_hour is always KRW integer."""
    for cost, hours in [
        (Decimal("1000000"), Decimal("333")),  # 3003.003...
        (Decimal("9999999"), Decimal("7")),  # 1428571.28... → 1428571
        (Decimal("1"), Decimal("3")),  # 0.333... → 0
        (Decimal("10000000"), Decimal("100")),  # 100,000 (exact)
    ]:
        result = compute_ccr(
            department_id="dept-precision",
            department_cost=cost,
            practical_capacity_hours=hours,
        )
        assert result.ccr_per_hour == result.ccr_per_hour.quantize(CCR_KRW_QUANTUM)


@pytest.mark.engine
def test_v7_abc_integrity_invariant_within_tolerance() -> None:
    """V7 ABC 무결성 — tolerance ±0.01 KRW 적용."""
    ccr = compute_ccr(
        department_id="dept-tolerance",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    # Use within ±0.01 tolerance
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("13199999.99"),  # within tolerance
        ),
    ]
    result = compute_allocation(
        ccr=ccr,
        activity_mappings=[],
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    # 13199999.99 + 0 = 13199999.99, abs diff = 0.01 == ABC_PRECISION_KRW_TOLERANCE
    assert result.is_balanced is True
    assert Decimal("0.01") == ABC_PRECISION_KRW_TOLERANCE
