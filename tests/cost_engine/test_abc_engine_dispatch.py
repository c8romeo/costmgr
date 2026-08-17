"""Tests for Story 9.3 EXTENSION `packages.cost_engine.abc_engine` dispatch surface.

Coverage (9-3 wire):
  - `verify_v7_balance` V7 ABC 무결성 1-Won precision invariant (8 cases)
  - `aggregate_multi_department_ccr` D-9-2-DEFER-2 해소 (6 cases)
  - `dispatch_abc_path` AD-19 dual-route + A29 forward-lock (10 cases)
  - `validate_department_count` 1 ≤ N ≤ 50 (6 cases)
  - `compute_abc_allocation_hash` V8 determinism (5 cases)
  - 5 NEW frozen dataclasses (V7Verdict + MultiDepartmentCcrResult +
    DispatchState + DepartmentAllocation + UnusedCapacitySubRow) × 8 cases
  - 2 NEW typed exceptions (EmptyDepartmentsError + TooManyDepartmentsError) × 6 cases

Total: ~49 NEW pytest cases (T1.3) — A19 cohesion pattern 7 surface EXTENSION 검증.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    ABC_HASH_PREFIX,
    CCR_KRW_QUANTUM,
    MAX_DEPARTMENT_COUNT,
    V7_BALANCE_TOLERANCE_KRW,
    ActivityMapping,
    AllocationResult,
    CCRResult,
    CostObjectRow,
    DepartmentAllocation,
    DispatchState,
    EmptyDepartmentsError,
    MultiDepartmentCcrResult,
    TooManyDepartmentsError,
    UnusedCapacityRow,
    UnusedCapacitySubRow,
    V7Verdict,
    aggregate_multi_department_ccr,
    compute_abc_allocation_hash,
    compute_allocation,
    compute_ccr,
    dispatch_abc_path,
    produce_unused_capacity_row,
    validate_department_count,
    verify_v7_balance,
)


# ── verify_v7_balance — V7 ABC 무결성 1-Won precision verification (8 cases) ──


@pytest.mark.engine
def test_verify_v7_balance_balanced_normal_range() -> None:
    """PRD §F9.3 + §A6 + §V7 verbatim — V7 무결성 1-Won precision 통과.

    Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가) → is_balanced=True.
    """
    verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        department_cost=Decimal("19800000"),
    )
    assert verdict.is_balanced is True
    assert verdict.breakdown_sum == Decimal("13200000")
    assert verdict.unused_cost == Decimal("6600000")
    assert verdict.expected_sum == Decimal("19800000")
    assert verdict.delta_krw == Decimal("0")
    assert verdict.hash.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_verify_v7_balance_unbalanced_within_tolerance() -> None:
    """V7 무결성 — tolerance 이내 (0.01 KRW) 오차 시 is_balanced=True."""
    verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        department_cost=Decimal("19800000.01"),  # 0.01 KRW 오차
    )
    assert verdict.is_balanced is True
    assert abs(verdict.delta_krw) == Decimal("0.01")


@pytest.mark.engine
def test_verify_v7_balance_unbalanced_exceeds_tolerance() -> None:
    """V7 무결성 — tolerance 초과 (1 KRW) 오차 시 is_balanced=False."""
    verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        department_cost=Decimal("19801000"),  # 1 KRW 오차 → tolerance 초과
    )
    assert verdict.is_balanced is False
    assert abs(verdict.delta_krw) > V7_BALANCE_TOLERANCE_KRW


@pytest.mark.engine
def test_verify_v7_balance_negative_delta() -> None:
    """V7 무결성 — breakdown_sum + unused_cost < department_cost (음수 delta)."""
    verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("10000000"),
        unused_cost=Decimal("5000000"),
        department_cost=Decimal("15000000"),
    )
    assert verdict.is_balanced is True
    assert verdict.delta_krw == Decimal("0")


@pytest.mark.engine
def test_verify_v7_balance_zero_breakdown() -> None:
    """V7 무결성 — Σ breakdown = 0 일 때 unused_cost = department_cost."""
    verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("0"),
        unused_cost=Decimal("19800000"),
        department_cost=Decimal("19800000"),
    )
    assert verdict.is_balanced is True
    assert verdict.delta_krw == Decimal("0")


@pytest.mark.engine
def test_verify_v7_balance_zero_unused() -> None:
    """V7 무결성 — Σ unused = 0 일 때 breakdown_sum = department_cost."""
    verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("19800000"),
        unused_cost=Decimal("0"),
        department_cost=Decimal("19800000"),
    )
    assert verdict.is_balanced is True


@pytest.mark.engine
def test_verify_v7_balance_deterministic_hash() -> None:
    """V8 determinism — 동일 3 inputs → byte-identical verdict hash."""
    verdict1 = verify_v7_balance(
        total_breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        department_cost=Decimal("19800000"),
    )
    verdict2 = verify_v7_balance(
        total_breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        department_cost=Decimal("19800000"),
    )
    assert verdict1.hash == verdict2.hash


@pytest.mark.engine
def test_verify_v7_balance_custom_tolerance() -> None:
    """V7 무결성 — custom tolerance 지원 (1500 KRW tolerance 시 1000 KRW 오차 OK)."""
    verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        department_cost=Decimal("19801000"),  # 1000 KRW 오차
        tolerance=Decimal("1500"),  # 1500 KRW tolerance (1000 KRW 오차 absorb)
    )
    assert verdict.is_balanced is True
    assert abs(verdict.delta_krw) == Decimal("1000")


# ── aggregate_multi_department_ccr — D-9-2-DEFER-2 해소 (6 cases) ──


@pytest.mark.engine
def test_aggregate_multi_department_ccr_normal_range() -> None:
    """PRD §F9.3 + §7.2 verbatim — N개 부서 CCR 일괄 compute aggregation.

    2개 부서 CCR (33,000원/시간 × 400h + 22,000원/시간 × 600h) = 26,400,000원.
    """
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
    result = aggregate_multi_department_ccr(ccr_results=[ccr1, ccr2])
    assert result.department_count == 2
    # ccr1 = 33,000 × 400 = 13,200,000, ccr2 = 22,000 × 600 = 13,200,000
    assert result.total_ccr_sum == Decimal("26400000")
    assert len(result.per_dept_results) == 2
    assert result.aggregate_hash.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_aggregate_multi_department_ccr_single_department() -> None:
    """Single department CCR aggregation (1 ≤ N ≤ MAX_DEPARTMENT_COUNT)."""
    ccr = compute_ccr(
        department_id="dept-only",
        department_cost=Decimal("10000000"),
        practical_capacity_hours=Decimal("500"),
    )
    result = aggregate_multi_department_ccr(ccr_results=[ccr])
    assert result.department_count == 1
    assert result.total_ccr_sum == Decimal("10000000")


@pytest.mark.engine
def test_aggregate_multi_department_ccr_max_departments() -> None:
    """50개 부서 CCR aggregation (MAX_DEPARTMENT_COUNT 한도)."""
    ccr_results = [
        compute_ccr(
            department_id=f"dept-{i:03d}",
            department_cost=Decimal("1000000"),
            practical_capacity_hours=Decimal("100"),
        )
        for i in range(MAX_DEPARTMENT_COUNT)
    ]
    result = aggregate_multi_department_ccr(ccr_results=ccr_results)
    assert result.department_count == MAX_DEPARTMENT_COUNT
    # 50 × (10,000 × 100) = 50,000,000
    assert result.total_ccr_sum == Decimal("50000000")


@pytest.mark.engine
def test_aggregate_multi_department_ccr_raises_on_empty() -> None:
    """empty ccr_results → EmptyDepartmentsError (HTTP 422)."""
    with pytest.raises(EmptyDepartmentsError) as exc_info:
        aggregate_multi_department_ccr(ccr_results=[])
    assert exc_info.value.reason == "empty_departments"


@pytest.mark.engine
def test_aggregate_multi_department_ccr_raises_on_exceeds_max() -> None:
    """len > MAX_DEPARTMENT_COUNT → TooManyDepartmentsError (HTTP 422)."""
    ccr_results = [
        compute_ccr(
            department_id=f"dept-{i:03d}",
            department_cost=Decimal("1000000"),
            practical_capacity_hours=Decimal("100"),
        )
        for i in range(MAX_DEPARTMENT_COUNT + 1)
    ]
    with pytest.raises(TooManyDepartmentsError) as exc_info:
        aggregate_multi_department_ccr(ccr_results=ccr_results)
    assert exc_info.value.department_count == MAX_DEPARTMENT_COUNT + 1
    assert exc_info.value.max_count == MAX_DEPARTMENT_COUNT
    assert exc_info.value.reason == "exceeds_max"


@pytest.mark.engine
def test_aggregate_multi_department_ccr_deterministic_hash() -> None:
    """V8 determinism — 동일 ccr_results → byte-identical aggregate_hash."""
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
    result1 = aggregate_multi_department_ccr(ccr_results=[ccr1, ccr2])
    result2 = aggregate_multi_department_ccr(ccr_results=[ccr1, ccr2])
    assert result1.aggregate_hash == result2.aggregate_hash


# ── dispatch_abc_path — AD-19 dual-route + A29 forward-lock (10 cases) ──


@pytest.mark.engine
def test_dispatch_abc_path_service_industry_routes_abc() -> None:
    """PRD §F9.3 verbatim — `tenant.industry == 'service'` → M9 ABC dispatch."""
    state = dispatch_abc_path(tenant_industry="service")
    assert state.tenant_industry == "service"
    assert state.resolved_engine_type == "abc"
    assert "M9 ABC" in state.dispatch_reason
    assert state.hash.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_dispatch_abc_path_manufacturing_routes_trad() -> None:
    """`tenant.industry == 'manufacturing'` → 기존 trad path (AD-18 backward compat)."""
    state = dispatch_abc_path(tenant_industry="manufacturing")
    assert state.tenant_industry == "manufacturing"
    assert state.resolved_engine_type == "trad"
    assert "trad path" in state.dispatch_reason


@pytest.mark.engine
def test_dispatch_abc_path_mixed_industry_routes_trad() -> None:
    """`tenant.industry == 'mixed'` → trad path fallback."""
    state = dispatch_abc_path(tenant_industry="mixed")
    assert state.resolved_engine_type == "trad"


@pytest.mark.engine
def test_dispatch_abc_path_empty_industry_fallback_trad() -> None:
    """empty tenant_industry → fallback to trad (defensive)."""
    state = dispatch_abc_path(tenant_industry="")
    assert state.resolved_engine_type == "trad"


@pytest.mark.engine
def test_dispatch_abc_path_unknown_industry_routes_trad() -> None:
    """Unknown industry → trad path fallback."""
    state = dispatch_abc_path(tenant_industry="other")
    assert state.resolved_engine_type == "trad"


@pytest.mark.engine
def test_dispatch_abc_path_with_requested_engine_type_service() -> None:
    """requested_engine_type='abc' 와 tenant_industry='service' 모두 ABC."""
    state = dispatch_abc_path(
        tenant_industry="service",
        requested_engine_type="abc",
    )
    assert state.resolved_engine_type == "abc"


@pytest.mark.engine
def test_dispatch_abc_path_deterministic_hash() -> None:
    """V8 determinism — 동일 tenant_industry → byte-identical dispatch hash."""
    state1 = dispatch_abc_path(tenant_industry="service")
    state2 = dispatch_abc_path(tenant_industry="service")
    assert state1.hash == state2.hash


@pytest.mark.engine
def test_dispatch_abc_path_korean_reason_service() -> None:
    """Korean SSOT — service dispatch reason contains 'M9 ABC'.

    CR 11-4 D-002 ko-KR.json SSOT only.
    """
    state = dispatch_abc_path(tenant_industry="service")
    assert "M9 ABC" in state.dispatch_reason


@pytest.mark.engine
def test_dispatch_abc_path_korean_reason_manufacturing() -> None:
    """Korean SSOT — manufacturing dispatch reason contains 'trad'."""
    state = dispatch_abc_path(tenant_industry="manufacturing")
    assert "trad" in state.dispatch_reason


@pytest.mark.engine
def test_dispatch_abc_path_different_industry_different_hash() -> None:
    """V8 determinism — different tenant_industry → different dispatch hash."""
    state_service = dispatch_abc_path(tenant_industry="service")
    state_manufacturing = dispatch_abc_path(tenant_industry="manufacturing")
    assert state_service.hash != state_manufacturing.hash


# ── validate_department_count — 1 ≤ N ≤ 50 (6 cases) ──


@pytest.mark.engine
def test_validate_department_count_normal_range() -> None:
    """1 ≤ len(department_ids) ≤ MAX_DEPARTMENT_COUNT → 정상."""
    count = validate_department_count(
        department_ids=["dept-a", "dept-b", "dept-c"],
    )
    assert count == 3


@pytest.mark.engine
def test_validate_department_count_single_department() -> None:
    """Single department (N=1, 최소 한도)."""
    count = validate_department_count(department_ids=["dept-only"])
    assert count == 1


@pytest.mark.engine
def test_validate_department_count_max_departments() -> None:
    """MAX_DEPARTMENT_COUNT departments (N=50, 최대 한도)."""
    department_ids = [f"dept-{i:03d}" for i in range(MAX_DEPARTMENT_COUNT)]
    count = validate_department_count(department_ids=department_ids)
    assert count == MAX_DEPARTMENT_COUNT


@pytest.mark.engine
def test_validate_department_count_raises_on_empty() -> None:
    """empty department_ids → EmptyDepartmentsError."""
    with pytest.raises(EmptyDepartmentsError) as exc_info:
        validate_department_count(department_ids=[])
    assert exc_info.value.reason == "empty_departments"


@pytest.mark.engine
def test_validate_department_count_raises_on_exceeds_max() -> None:
    """51 departments → TooManyDepartmentsError."""
    department_ids = [f"dept-{i:03d}" for i in range(MAX_DEPARTMENT_COUNT + 1)]
    with pytest.raises(TooManyDepartmentsError) as exc_info:
        validate_department_count(department_ids=department_ids)
    assert exc_info.value.department_count == MAX_DEPARTMENT_COUNT + 1
    assert exc_info.value.max_count == MAX_DEPARTMENT_COUNT


@pytest.mark.engine
def test_validate_department_count_custom_max_count() -> None:
    """custom max_count (10) — 11 departments → TooManyDepartmentsError."""
    department_ids = [f"dept-{i:03d}" for i in range(11)]
    with pytest.raises(TooManyDepartmentsError) as exc_info:
        validate_department_count(department_ids=department_ids, max_count=10)
    assert exc_info.value.max_count == 10


# ── compute_abc_allocation_hash — V8 determinism (5 cases) ──


@pytest.mark.engine
def test_compute_abc_allocation_hash_normal_range() -> None:
    """V8 determinism — 정상 ABC allocation aggregate hash."""
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
    activity_mapping = ActivityMapping(
        activity_id="act-1",
        hours=Decimal("400"),
        ccr_amount_krw=Decimal("13200000"),
    )
    unused_row = UnusedCapacityRow(
        unused_hours=Decimal("0"),
        ccr_per_hour=Decimal("33000"),
        unused_cost_krw=Decimal("0"),
        hash="sha256:unused0",
    )
    allocation = compute_allocation(
        ccr=ccr1,
        activity_mappings=[activity_mapping],
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

    result_hash = compute_abc_allocation_hash(
        multi_dept_ccr=multi_dept,
        per_dept_allocations=[dept_alloc],
        unused_capacity_breakdown=[unused_sub],
    )
    assert result_hash.startswith(ABC_HASH_PREFIX)
    assert len(result_hash) == len(ABC_HASH_PREFIX) + 64


@pytest.mark.engine
def test_compute_abc_allocation_hash_deterministic() -> None:
    """V8 determinism — 동일 inputs → byte-identical hash."""
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
    activity_mapping = ActivityMapping(
        activity_id="act-1",
        hours=Decimal("400"),
        ccr_amount_krw=Decimal("13200000"),
    )
    allocation = compute_allocation(
        ccr=ccr1,
        activity_mappings=[activity_mapping],
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

    hash1 = compute_abc_allocation_hash(
        multi_dept_ccr=multi_dept,
        per_dept_allocations=[dept_alloc],
        unused_capacity_breakdown=[unused_sub],
    )
    hash2 = compute_abc_allocation_hash(
        multi_dept_ccr=multi_dept,
        per_dept_allocations=[dept_alloc],
        unused_capacity_breakdown=[unused_sub],
    )
    assert hash1 == hash2


@pytest.mark.engine
def test_compute_abc_allocation_hash_invalid_multi_dept() -> None:
    """Invalid multi_dept_ccr type → ValueError."""
    with pytest.raises(ValueError, match="multi_dept_ccr must be"):
        compute_abc_allocation_hash(
            multi_dept_ccr="not-a-multi-dept",  # type: ignore[arg-type]
            per_dept_allocations=[],
            unused_capacity_breakdown=[],
        )


@pytest.mark.engine
def test_compute_abc_allocation_hash_invalid_per_dept_allocation() -> None:
    """Invalid per_dept_allocations type → ValueError."""
    ccr1 = compute_ccr(
        department_id="dept-a",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    multi_dept = aggregate_multi_department_ccr(ccr_results=[ccr1])
    with pytest.raises(ValueError, match="per_dept_allocations must be"):
        compute_abc_allocation_hash(
            multi_dept_ccr=multi_dept,
            per_dept_allocations=["not-a-dept-alloc"],  # type: ignore[list-item]
            unused_capacity_breakdown=[],
        )


@pytest.mark.engine
def test_compute_abc_allocation_hash_invalid_unused_breakdown() -> None:
    """Invalid unused_capacity_breakdown type → ValueError."""
    ccr1 = compute_ccr(
        department_id="dept-a",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    multi_dept = aggregate_multi_department_ccr(ccr_results=[ccr1])
    with pytest.raises(ValueError, match="unused_capacity_breakdown must be"):
        compute_abc_allocation_hash(
            multi_dept_ccr=multi_dept,
            per_dept_allocations=[],
            unused_capacity_breakdown=["not-an-unused-sub"],  # type: ignore[list-item]
        )


# ── 5 NEW frozen dataclasses (8 cases) ──


@pytest.mark.engine
def test_v7_verdict_frozen_dataclass() -> None:
    """V7Verdict frozen=True, slots=True — mutation 시도 → FrozenInstanceError."""
    verdict = V7Verdict(
        is_balanced=True,
        breakdown_sum=Decimal("13200000"),
        unused_cost=Decimal("6600000"),
        expected_sum=Decimal("19800000"),
        delta_krw=Decimal("0"),
        hash="sha256:abc",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        verdict.is_balanced = False  # type: ignore[misc]


@pytest.mark.engine
def test_multi_department_ccr_result_frozen_dataclass() -> None:
    """MultiDepartmentCcrResult frozen + slots."""
    ccr = compute_ccr(
        department_id="dept-1",
        department_cost=Decimal("10000000"),
        practical_capacity_hours=Decimal("500"),
    )
    result = MultiDepartmentCcrResult(
        department_count=1,
        total_ccr_sum=Decimal("10000000"),
        per_dept_results=(ccr,),
        aggregate_hash="sha256:abc",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.department_count = 2  # type: ignore[misc]


@pytest.mark.engine
def test_dispatch_state_frozen_dataclass() -> None:
    """DispatchState frozen + slots + Literal tag discriminator."""
    state = DispatchState(
        tenant_industry="service",
        resolved_engine_type="abc",
        dispatch_reason="M9 ABC dispatch",
        hash="sha256:abc",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        state.tenant_industry = "manufacturing"  # type: ignore[misc]


@pytest.mark.engine
def test_department_allocation_frozen_dataclass() -> None:
    """DepartmentAllocation frozen + nested frozen dataclasses."""
    ccr = compute_ccr(
        department_id="dept-1",
        department_cost=Decimal("10000000"),
        practical_capacity_hours=Decimal("500"),
    )
    activity_mapping = ActivityMapping(
        activity_id="act-1",
        hours=Decimal("500"),
        ccr_amount_krw=Decimal("10000000"),
    )
    cost_row = CostObjectRow(
        product_id="prod-1",
        activity_id="act-1",
        driver_id="drv-1",
        allocated_krw=Decimal("10000000"),
    )
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=[activity_mapping],
        cost_object_breakdown=[cost_row],
        used_hours=Decimal("500"),
    )
    v7_verdict = verify_v7_balance(
        total_breakdown_sum=Decimal("10000000"),
        unused_cost=Decimal("0"),
        department_cost=Decimal("10000000"),
    )
    dept_alloc = DepartmentAllocation(
        department_id="dept-1",
        ccr=ccr,
        allocation=allocation,
        v7_verdict=v7_verdict,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        dept_alloc.department_id = "dept-2"  # type: ignore[misc]


@pytest.mark.engine
def test_unused_capacity_sub_row_frozen_dataclass() -> None:
    """UnusedCapacitySubRow frozen + slots."""
    sub_row = UnusedCapacitySubRow(
        department_id="dept-1",
        unused_hours=Decimal("200"),
        unused_cost_krw=Decimal("4000000"),
        hash="sha256:abc",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        sub_row.unused_hours = Decimal("0")  # type: ignore[misc]


@pytest.mark.engine
def test_v7_verdict_required_fields() -> None:
    """V7Verdict requires 6 fields (is_balanced, breakdown_sum, unused_cost, expected_sum, delta_krw, hash)."""
    verdict = V7Verdict(
        is_balanced=True,
        breakdown_sum=Decimal("100"),
        unused_cost=Decimal("0"),
        expected_sum=Decimal("100"),
        delta_krw=Decimal("0"),
        hash="sha256:test",
    )
    assert verdict.is_balanced is True
    assert verdict.breakdown_sum == Decimal("100")
    assert verdict.expected_sum == Decimal("100")


@pytest.mark.engine
def test_dispatch_state_tag_discriminator_types() -> None:
    """DispatchState resolved_engine_type tag discriminator = Literal['trad', 'abc']."""
    state_abc = DispatchState(
        tenant_industry="service",
        resolved_engine_type="abc",
        dispatch_reason="M9 ABC dispatch",
        hash="sha256:abc",
    )
    state_trad = DispatchState(
        tenant_industry="manufacturing",
        resolved_engine_type="trad",
        dispatch_reason="trad path",
        hash="sha256:trad",
    )
    assert state_abc.resolved_engine_type == "abc"
    assert state_trad.resolved_engine_type == "trad"


@pytest.mark.engine
def test_multi_department_ccr_result_empty_per_dept() -> None:
    """MultiDepartmentCcrResult with empty per_dept_results (frozen)."""
    result = MultiDepartmentCcrResult(
        department_count=0,
        total_ccr_sum=Decimal("0"),
        per_dept_results=(),
        aggregate_hash="sha256:empty",
    )
    assert result.department_count == 0
    assert len(result.per_dept_results) == 0


# ── 2 NEW typed exceptions (6 cases) ──


@pytest.mark.engine
def test_empty_departments_error_attributes() -> None:
    """EmptyDepartmentsError attributes (message, reason)."""
    err = EmptyDepartmentsError("empty input", reason="empty_departments")
    assert err.message == "empty input"
    assert err.reason == "empty_departments"
    assert str(err) == "empty input"


@pytest.mark.engine
def test_empty_departments_error_is_value_error() -> None:
    """EmptyDepartmentsError inherits from ValueError (HTTP 422 convention)."""
    err = EmptyDepartmentsError("empty input", reason="empty_departments")
    assert isinstance(err, ValueError)


@pytest.mark.engine
def test_too_many_departments_error_attributes() -> None:
    """TooManyDepartmentsError attributes (message, department_count, max_count, reason)."""
    err = TooManyDepartmentsError(
        "exceeds max",
        department_count=51,
        max_count=MAX_DEPARTMENT_COUNT,
        reason="exceeds_max",
    )
    assert err.message == "exceeds max"
    assert err.department_count == 51
    assert err.max_count == MAX_DEPARTMENT_COUNT
    assert err.reason == "exceeds_max"


@pytest.mark.engine
def test_too_many_departments_error_is_value_error() -> None:
    """TooManyDepartmentsError inherits from ValueError (HTTP 422 convention)."""
    err = TooManyDepartmentsError(
        "exceeds max",
        department_count=51,
        max_count=MAX_DEPARTMENT_COUNT,
        reason="exceeds_max",
    )
    assert isinstance(err, ValueError)


@pytest.mark.engine
def test_empty_departments_error_in_aggregate() -> None:
    """EmptyDepartmentsError 통합 검증 (aggregate_multi_department_ccr 호출)."""
    with pytest.raises(EmptyDepartmentsError):
        aggregate_multi_department_ccr(ccr_results=[])


@pytest.mark.engine
def test_too_many_departments_error_in_validate() -> None:
    """TooManyDepartmentsError 통합 검증 (validate_department_count 호출)."""
    with pytest.raises(TooManyDepartmentsError):
        validate_department_count(
            department_ids=[f"dept-{i:03d}" for i in range(MAX_DEPARTMENT_COUNT + 1)],
        )
