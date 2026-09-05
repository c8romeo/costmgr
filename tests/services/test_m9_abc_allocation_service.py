"""Tests for Story 9.2 M9 ABC Allocation service layer.

Coverage:
  - AbcAllocationService.compute_ccr_for_department normal range
    (PRD section F9.2 verbatim CCR compute + AD-15 Korean SSOT)
  - AbcAllocationService.compute_ccr_for_department edge cases
    (zero/negative capacity, type_mismatch, empty ID)
  - AbcAllocationService.produce_unused_capacity normal range (PRD section A9)
  - AbcAllocationService.compute_allocation normal range (PRD section V7)
  - AbcAllocationService.compute_allocation V7 balance (is_balanced)
  - _to_ccr_state + _to_allocation_state ORM-to-kernel boundary
    (CR 12-1 L3 precedent)
  - validate_ccr_inputs + validate_allocation_inputs CR 12-5 L3
    3-layer defense
  - serialize_ccr_state + serialize_allocation_state JSON-safe
    serializers (AD-15 section 1 Decimal-as-string)
  - constants exposure (3 NEW constants)

CR 11-3 + CR 12-5: ~30 cases, AD-21 CCRPort.compute single ownership check.
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import pytest

from apps.api.modules.m9_abc.exceptions import (
    ABC_ALLOCATION_BALANCE_ERROR_KO,
    ABC_CCR_INVALID_CAPACITY_KO,
)
from apps.api.modules.m9_abc.services.abc_allocation_service import (
    AbcAllocationService,
    AbcAllocationState,
    AbcCcrState,
    _to_allocation_state,
    _to_ccr_state,
    validate_allocation_inputs,
    validate_ccr_inputs,
)
from packages.cost_engine.abc_engine import (
    ABC_PRECISION_KRW_TOLERANCE,
    ActivityMapping,
    CcrComputeError,
    CCRResult,
    CostObjectRow,
    compute_allocation,
    compute_ccr,
    produce_unused_capacity_row,
)
from packages.services.m9_abc.abc_allocation_serializers import (
    serialize_allocation_state,
    serialize_ccr_state,
)

# AbcAllocationService.compute_ccr_for_department normal range


@pytest.mark.engine
def test_service_compute_ccr_normal_range() -> None:
    """PRD section F9.2 verbatim - 13,200,000 / 400 = 33,000 KRW/hour."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-001",
        )
        result = await svc.compute_ccr_for_department(
            department_id="dept-001",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        assert isinstance(result, CCRResult)
        assert result.ccr_per_hour == Decimal("33000")

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_ccr_zero_capacity_raises() -> None:
    """practical_capacity_hours = 0 -> CcrComputeError."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-002",
        )
        with pytest.raises(CcrComputeError) as exc_info:
            await svc.compute_ccr_for_department(
                department_id="dept-zero",
                department_cost=Decimal("13200000"),
                practical_capacity_hours=Decimal("0"),
            )
        assert exc_info.value.reason == "invalid_capacity"

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_ccr_negative_capacity_raises() -> None:
    """practical_capacity_hours < 0 -> CcrComputeError."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-003",
        )
        with pytest.raises(CcrComputeError):
            await svc.compute_ccr_for_department(
                department_id="dept-neg",
                department_cost=Decimal("13200000"),
                practical_capacity_hours=Decimal("-50"),
            )

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_ccr_negative_cost_raises() -> None:
    """department_cost < 0 -> CcrComputeError(reason="negative_cost")."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-004",
        )
        with pytest.raises(CcrComputeError) as exc_info:
            await svc.compute_ccr_for_department(
                department_id="dept-negcost",
                department_cost=Decimal("-100"),
                practical_capacity_hours=Decimal("400"),
            )
        assert exc_info.value.reason == "negative_cost"

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_ccr_type_mismatch_raises() -> None:
    """department_cost not Decimal -> CcrComputeError."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-005",
        )
        with pytest.raises(CcrComputeError) as exc_info:
            # type: ignore[arg-type]
            await svc.compute_ccr_for_department(
                department_id="dept-typo",
                department_cost="13200000",
                practical_capacity_hours=Decimal("400"),
            )
        assert exc_info.value.reason == "type_mismatch"

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_ccr_empty_id_raises() -> None:
    """department_id empty -> CcrComputeError(reason="empty_department_id")."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-006",
        )
        with pytest.raises(CcrComputeError) as exc_info:
            await svc.compute_ccr_for_department(
                department_id="",
                department_cost=Decimal("13200000"),
                practical_capacity_hours=Decimal("400"),
            )
        assert exc_info.value.reason == "empty_department_id"

    asyncio.run(_inner())


# AbcAllocationService.produce_unused_capacity


@pytest.mark.engine
def test_service_produce_unused_capacity_normal_range() -> None:
    """PRD section A9 verbatim - unused 200h * 33,000 = 6,600,000 KRW."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-007",
        )
        ccr = compute_ccr(
            department_id="dept-001",
            department_cost=Decimal("19800000"),
            practical_capacity_hours=Decimal("600"),
        )
        row = await svc.produce_unused_capacity(ccr=ccr, used_hours=Decimal("400"))
        assert row.unused_hours == Decimal("200")
        assert row.unused_cost_krw == Decimal("6600000")

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_produce_unused_capacity_negative_raises() -> None:
    """used_hours < 0 -> CcrComputeError."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-008",
        )
        ccr = compute_ccr(
            department_id="dept-001",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        with pytest.raises(CcrComputeError) as exc_info:
            await svc.produce_unused_capacity(ccr=ccr, used_hours=Decimal("-10"))
        assert exc_info.value.reason == "negative_used_hours"

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_produce_unused_capacity_zero_used() -> None:
    """used_hours = 0 -> unused = practical_capacity_hours, normal."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-009",
        )
        ccr = compute_ccr(
            department_id="dept-zero",
            department_cost=Decimal("19800000"),
            practical_capacity_hours=Decimal("600"),
        )
        row = await svc.produce_unused_capacity(ccr=ccr, used_hours=Decimal("0"))
        assert row.unused_hours == Decimal("600")

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_produce_unused_capacity_exceeds_raises() -> None:
    """used_hours > capacity -> CcrComputeError(reason="exceeds_capacity")."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-010",
        )
        ccr = compute_ccr(
            department_id="dept-001",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        with pytest.raises(CcrComputeError) as exc_info:
            await svc.produce_unused_capacity(ccr=ccr, used_hours=Decimal("500"))
        assert exc_info.value.reason == "exceeds_capacity"

    asyncio.run(_inner())


# AbcAllocationService.compute_allocation (V7 balance)


@pytest.mark.engine
def test_service_compute_allocation_balanced() -> None:
    """PRD section V7 - sum breakdown + unused = sum department_cost -> is_balanced=True."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-011",
        )
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
        result = await svc.compute_allocation(
            ccr=ccr,
            activity_mappings=activity_mappings,
            cost_object_breakdown=cost_object_breakdown,
            used_hours=Decimal("400"),
        )
        assert result.is_balanced is True

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_allocation_unbalanced_returns_false() -> None:
    """V7 unbalanced -> is_balanced=False (no raise)."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-012",
        )
        ccr = compute_ccr(
            department_id="dept-unbalanced",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        cost_object_breakdown = [
            CostObjectRow(
                product_id="prod-A",
                activity_id="act-001",
                driver_id="drv-001",
                allocated_krw=Decimal("10000000"),
            ),
        ]
        result = await svc.compute_allocation(
            ccr=ccr,
            activity_mappings=[],
            cost_object_breakdown=cost_object_breakdown,
            used_hours=Decimal("400"),
        )
        assert result.is_balanced is False

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_allocation_default_used_hours() -> None:
    """used_hours = None -> default = practical_capacity_hours (used all)."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-013",
        )
        ccr = compute_ccr(
            department_id="dept-default",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        cost_object_breakdown = [
            CostObjectRow(
                product_id="prod-A",
                activity_id="act-001",
                driver_id="drv-001",
                allocated_krw=Decimal("13200000"),
            ),
        ]
        result = await svc.compute_allocation(
            ccr=ccr,
            activity_mappings=[],
            cost_object_breakdown=cost_object_breakdown,
            used_hours=None,
        )
        assert result.unused_capacity.unused_hours == Decimal("0")
        assert result.is_balanced is True

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_compute_allocation_empty_breakdown() -> None:
    """Empty cost_object_breakdown -> total=0, is_balanced=False."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-014",
        )
        ccr = compute_ccr(
            department_id="dept-empty",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        result = await svc.compute_allocation(
            ccr=ccr,
            activity_mappings=[],
            cost_object_breakdown=[],
            used_hours=Decimal("400"),
        )
        assert result.total_breakdown_sum == Decimal("0")
        assert result.is_balanced is False

    asyncio.run(_inner())


# V7 ABC integrity check_v7_balance


@pytest.mark.engine
def test_service_check_v7_balance_balanced() -> None:
    """V7 check - balanced -> True."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-015",
        )
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
        result = await svc.compute_allocation(
            ccr=ccr,
            activity_mappings=activity_mappings,
            cost_object_breakdown=cost_object_breakdown,
            used_hours=Decimal("400"),
        )
        balanced = await svc.check_v7_balance(allocation=result)
        assert balanced is True

    asyncio.run(_inner())


@pytest.mark.engine
def test_service_check_v7_balance_unbalanced() -> None:
    """V7 check - unbalanced -> False."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-016",
        )
        ccr = compute_ccr(
            department_id="dept-unbalanced",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
        cost_object_breakdown = [
            CostObjectRow(
                product_id="prod-A",
                activity_id="act-001",
                driver_id="drv-001",
                allocated_krw=Decimal("10000000"),
            ),
        ]
        result = await svc.compute_allocation(
            ccr=ccr,
            activity_mappings=[],
            cost_object_breakdown=cost_object_breakdown,
            used_hours=Decimal("400"),
        )
        balanced = await svc.check_v7_balance(allocation=result)
        assert balanced is False

    asyncio.run(_inner())


# ORM-to-kernel boundary helpers (CR 12-1 L3)


def test_to_ccr_state_normal_range() -> None:
    """_to_ccr_state - CCRResult + AllocationResult -> AbcCcrState DTO."""
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
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=activity_mappings,
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    state = _to_ccr_state(ccr, allocation, department_id="dept-001")
    assert isinstance(state, AbcCcrState)
    assert state.ccr == ccr
    assert state.is_balanced is True
    assert state.unused_capacity is not None


def test_to_allocation_state_normal_range() -> None:
    """_to_allocation_state - AllocationResult -> AbcAllocationState."""
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
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=activity_mappings,
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    state = _to_allocation_state(
        allocation, ccr, department_id="dept-001"
    )
    assert isinstance(state, AbcAllocationState)
    assert state.is_balanced is True


def test_to_allocation_state_unbalanced_message() -> None:
    """_to_allocation_state - unbalanced -> Korean envelope message."""
    ccr = compute_ccr(
        department_id="dept-unbalanced",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    cost_object_breakdown = [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-001",
            driver_id="drv-001",
            allocated_krw=Decimal("10000000"),
        ),
    ]
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=[],
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    state = _to_allocation_state(
        allocation, ccr, department_id="dept-unbalanced"
    )
    assert state.is_balanced is False
    assert state.unbalanced_message_ko is not None
    assert ABC_ALLOCATION_BALANCE_ERROR_KO in state.unbalanced_message_ko


# CR 12-5 L3 pre-validation


def test_validate_ccr_inputs_zero_capacity_raises() -> None:
    """validate_ccr_inputs - 0 capacity -> CcrComputeError."""
    with pytest.raises(CcrComputeError) as exc_info:
        validate_ccr_inputs(
            department_id="dept-001",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("0"),
        )
    assert exc_info.value.reason == "invalid_capacity"


def test_validate_ccr_inputs_empty_id_raises() -> None:
    """validate_ccr_inputs - empty department_id -> CcrComputeError."""
    with pytest.raises(CcrComputeError) as exc_info:
        validate_ccr_inputs(
            department_id="",
            department_cost=Decimal("13200000"),
            practical_capacity_hours=Decimal("400"),
        )
    assert exc_info.value.reason == "empty_department_id"


def test_validate_ccr_inputs_negative_cost_raises() -> None:
    """validate_ccr_inputs - negative cost -> CcrComputeError."""
    with pytest.raises(CcrComputeError) as exc_info:
        validate_ccr_inputs(
            department_id="dept-001",
            department_cost=Decimal("-100"),
            practical_capacity_hours=Decimal("400"),
        )
    assert exc_info.value.reason == "negative_cost"


def test_validate_allocation_inputs_normal_passes() -> None:
    """validate_allocation_inputs - normal input (no raise)."""
    validate_allocation_inputs(
        activity_mappings=[
            ActivityMapping(
                activity_id="act-001",
                hours=Decimal("100"),
                ccr_amount_krw=Decimal("3300000"),
            )
        ],
        cost_object_breakdown=[
            CostObjectRow(
                product_id="prod-A",
                activity_id="act-001",
                driver_id="drv-001",
                allocated_krw=Decimal("3300000"),
            )
        ],
    )
    # 9-2 wire = empty allowed, no raise
    validate_allocation_inputs(
        activity_mappings=[],
        cost_object_breakdown=[],
    )


# Serializers (AD-15 section 1 Decimal-as-string)


def test_serialize_ccr_state_normal_range() -> None:
    """serialize_ccr_state - Decimal-as-string + UUID-as-string."""
    ccr = compute_ccr(
        department_id="dept-001",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
    )
    serialized = serialize_ccr_state(state=ccr)
    assert serialized["department_id"] == "dept-001"
    assert serialized["department_cost"] == "13200000"
    assert serialized["practical_capacity_hours"] == "400"
    assert serialized["ccr_per_hour"] == "33000"
    assert serialized["hash"].startswith("sha256:")


def test_serialize_ccr_state_type_mismatch_raises() -> None:
    """serialize_ccr_state - not CCRResult -> ValueError."""
    with pytest.raises(ValueError, match="state must be CCRResult"):
        # type: ignore[arg-type]
        serialize_ccr_state(state="not a CCRResult")


def test_serialize_allocation_state_normal_range() -> None:
    """serialize_allocation_state - AllocationResult -> full dict."""
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
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=activity_mappings,
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )
    serialized = serialize_allocation_state(state=allocation)
    assert serialized["ccr"]["ccr_per_hour"] == "33000"
    assert serialized["total_breakdown_sum"] == "13200000"
    assert serialized["is_balanced"] is True


def test_serialize_allocation_state_union_coverage() -> None:
    """serialize_allocation_state - 5 NEW frozen dataclasses all supported."""
    ccr = compute_ccr(
        department_id="dept-001",
        department_cost=Decimal("13200000"),
        practical_capacity_hours=Decimal("400"),
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
    unused = produce_unused_capacity_row(
        ccr=ccr,
        used_hours=Decimal("0"),
    )
    for state in (ccr, mapping, cost_row, unused):
        s = serialize_allocation_state(state=state)
        assert isinstance(s, dict)


def test_serialize_allocation_state_type_mismatch_raises() -> None:
    """serialize_allocation_state - invalid type -> ValueError."""
    with pytest.raises(ValueError, match="state must be"):
        # type: ignore[arg-type]
        serialize_allocation_state(state=42)


# Constants (AD-15 section 1 Decimal-as-string exposure)


def test_constants_exposed_in_services_layer() -> None:
    """3 NEW constants exposure (ABC_PRECISION_KRW_TOLERANCE 0.01 KRW)."""
    assert Decimal("0.01") == ABC_PRECISION_KRW_TOLERANCE
    assert ABC_CCR_INVALID_CAPACITY_KO == "CCR 계산: 실제 조업능력은 0보다 커야 합니다"
    assert (
        ABC_ALLOCATION_BALANCE_ERROR_KO
        == "ABC 배부액 합계가 부서 원가와 일치하지 않습니다"
    )


# Service-layer pre-validation boundary tests


@pytest.mark.engine
def test_service_compute_hash_for_state() -> None:
    """compute_ccr_hash_for_state + compute_allocation_hash_for_state."""
    import asyncio
    svc = AbcAllocationService(
        session=None,  # type: ignore[arg-type]
        tenant_id=uuid.uuid4(),
        actor_id=uuid.uuid4(),
        trace_id="trace-hash",
    )
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
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=activity_mappings,
        cost_object_breakdown=cost_object_breakdown,
        used_hours=Decimal("400"),
    )

    async def _check() -> None:
        h1 = await svc.compute_ccr_hash_for_state(ccr_result=ccr)
        h2 = await svc.compute_allocation_hash_for_state(allocation=allocation)
        assert h1.startswith("sha256:")
        assert h2.startswith("sha256:")

    asyncio.run(_check())


@pytest.mark.engine
def test_service_fetch_tenant_abc_allocation_empty() -> None:
    """9-2 wire - fetch_tenant_abc_allocation returns empty dict placeholder."""
    async def _inner() -> None:
        svc = AbcAllocationService(
            session=None,  # type: ignore[arg-type]
            tenant_id=uuid.uuid4(),
            actor_id=uuid.uuid4(),
            trace_id="trace-fetch",
        )
        result = await svc.fetch_tenant_abc_allocation()
        assert result == {}

    asyncio.run(_inner())
