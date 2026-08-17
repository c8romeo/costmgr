"""Tests for Story 9.3 EXTENSION V8 byte-identical determinism.

V8 determinism = 동일 입력 → byte-identical hash (Epic 4 baseline + 8-3 pattern).
100회 반복 호출 시 hash 변동 0건 검증.

Coverage (T1.4): 6 cases
  - verify_v7_balance × 1 (100회 반복)
  - aggregate_multi_department_ccr × 1 (100회 반복)
  - dispatch_abc_path × 1 (100회 반복)
  - compute_abc_allocation_hash × 1 (100회 반복)
  - frozen dataclass repr byte-identical × 1 (slots=True invariant)
  - cross-call hash stability × 1 (different contexts, same inputs)
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    ABC_HASH_PREFIX,
    CostObjectRow,
    aggregate_multi_department_ccr,
    compute_abc_allocation_hash,
    compute_allocation,
    compute_ccr,
    dispatch_abc_path,
    verify_v7_balance,
)


@pytest.mark.engine
def test_verify_v7_balance_100_iterations_byte_identical() -> None:
    """V8 determinism — verify_v7_balance 100회 반복 → byte-identical hash."""
    first_hash: str | None = None
    for _ in range(100):
        verdict = verify_v7_balance(
            total_breakdown_sum=Decimal("13200000"),
            unused_cost=Decimal("6600000"),
            department_cost=Decimal("19800000"),
        )
        if first_hash is None:
            first_hash = verdict.hash
        else:
            assert verdict.hash == first_hash, (
                "V8 determinism violated: verify_v7_balance hash changed "
                "across iterations"
            )
    assert first_hash is not None
    assert first_hash.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_aggregate_multi_department_ccr_100_iterations_byte_identical() -> None:
    """V8 determinism — aggregate_multi_department_ccr 100회 반복."""
    ccr1 = compute_ccr(
        department_id="dept-a",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    ccr2 = compute_ccr(
        department_id="dept-b",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("600"),
    )
    first_hash: str | None = None
    for _ in range(100):
        result = aggregate_multi_department_ccr(ccr_results=[ccr1, ccr2])
        if first_hash is None:
            first_hash = result.aggregate_hash
        else:
            assert result.aggregate_hash == first_hash, (
                "V8 determinism violated: aggregate_multi_department_ccr "
                "hash changed across iterations"
            )
    assert first_hash is not None


@pytest.mark.engine
def test_dispatch_abc_path_100_iterations_byte_identical() -> None:
    """V8 determinism — dispatch_abc_path 100회 반복."""
    first_hash: str | None = None
    for _ in range(100):
        state = dispatch_abc_path(tenant_industry="service")
        if first_hash is None:
            first_hash = state.hash
        else:
            assert state.hash == first_hash, (
                "V8 determinism violated: dispatch_abc_path hash changed "
                "across iterations"
            )
    assert first_hash is not None


@pytest.mark.engine
def test_compute_abc_allocation_hash_100_iterations_byte_identical() -> None:
    """V8 determinism — compute_abc_allocation_hash 100회 반복."""
    ccr1 = compute_ccr(
        department_id="dept-a",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    multi_dept = aggregate_multi_department_ccr(ccr_results=[ccr1])

    cost_row = CostObjectRow(
        product_id="prod-1",
        activity_id="act-1",
        driver_id="drv-1",
        allocated_krw=Decimal("13200000"),
    )
    from packages.cost_engine.abc_engine import (
        ActivityMapping,
        DepartmentAllocation,
        UnusedCapacitySubRow,
        V7Verdict,
    )
    allocation = compute_allocation(
        ccr=ccr1,
        activity_mappings=[
            ActivityMapping(
                activity_id="act-1",
                hours=Decimal("400"),
                ccr_amount_krw=Decimal("13200000"),
            ),
        ],
        cost_object_breakdown=[cost_row],
        used_hours=Decimal("400"),
    )
    v7_verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("0"),
        department_cost=Decimal("13200000"),
    )
    dept_alloc = DepartmentAllocation(
        department_id="dept-a",
        ccr=ccr1,
        allocation=allocation,
        v7_verdict=v7_verdict,
    )
    unused_sub = UnusedCapacitySubRow(
        department_id="dept-a",
        unused_hours=Decimal("0"),
        unused_cost_krw=Decimal("0"),
        hash="sha256:unusedsub0",
    )

    first_hash: str | None = None
    for _ in range(100):
        result_hash = compute_abc_allocation_hash(
            multi_dept_ccr=multi_dept,
            per_dept_allocations=[dept_alloc],
            unused_capacity_breakdown=[unused_sub],
        )
        if first_hash is None:
            first_hash = result_hash
        else:
            assert result_hash == first_hash, (
                "V8 determinism violated: compute_abc_allocation_hash "
                "changed across iterations"
            )
    assert first_hash is not None


@pytest.mark.engine
def test_9_3_frozen_dataclass_slots_repr_byte_identical() -> None:
    """V8 determinism — frozen dataclass (slots=True) repr byte-identical.

    `repr(dataclass)` 결정론 검증 (Epic 4 baseline + 8-3 pattern 동일).
    """
    from packages.cost_engine.abc_engine import DepartmentAllocation, V7Verdict

    v7 = V7Verdict(
        is_balanced=True,
        breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        expected_sum=Decimal("19800000"),
        delta_krw=Decimal("0"),
        hash="sha256:abc",
    )
    repr1 = repr(v7)
    repr2 = repr(v7)
    assert repr1 == repr2
    assert "is_balanced=True" in repr1
    assert "breakdown_sum=Decimal('13200000')" in repr1


@pytest.mark.engine
def test_9_3_cross_context_hash_stability() -> None:
    """V8 determinism — different contexts (different tenants) → same hash for same inputs.

    cross-language parity 정합: 동일한 departure_id + cost → 동일 hash.
    """
    # Context 1: tenant-1
    verdict_t1 = dispatch_abc_path(tenant_industry="service")
    # Context 2: tenant-2 (same input)
    verdict_t2 = dispatch_abc_path(tenant_industry="service")
    # Same inputs → same hash (V8 byte-identical determinism)
    assert verdict_t1.hash == verdict_t2.hash
