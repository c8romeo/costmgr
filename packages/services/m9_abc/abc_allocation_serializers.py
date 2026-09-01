"""packages.services.m9_abc.abc_allocation_serializers — Story 9.2 thin JSON serializers.

Pure-Python JSON-safe serializers for `CCRResult` + `AllocationResult` +
`UnusedCapacityRow` + `ActivityMapping` + `CostObjectRow` frozen dataclasses.
Decimal-as-string (AD-15 §1 cross-language parity with TS mirror
`apps/web/lib/m9-abc-allocation.ts`).

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — registered in
`tests/architecture/test_api_calls_only_ports.py` (T2 wire).
"""

from __future__ import annotations

from packages.cost_engine.abc_engine import (
    ActivityMapping,
    AllocationResult,
    AllocationState,
    CCRResult,
    CostObjectRow,
    UnusedCapacityRow,
)


def _serialize_ccr(state: CCRResult) -> dict[str, object]:
    """CCRResult → JSON-safe dict (PRD §F9.2 + AD-15)."""
    return {
        "department_id": str(state.department_id),
        "department_cost": str(state.department_cost),
        "practical_capacity_hours": str(state.practical_capacity_hours),
        "ccr_per_hour": str(state.ccr_per_hour),
        "hash": str(state.hash),
    }


def _serialize_unused(state: UnusedCapacityRow) -> dict[str, object]:
    """UnusedCapacityRow → JSON-safe dict (PRD §A9 + AD-15)."""
    return {
        "unused_hours": str(state.unused_hours),
        "ccr_per_hour": str(state.ccr_per_hour),
        "unused_cost_krw": str(state.unused_cost_krw),
        "hash": str(state.hash),
    }


def _serialize_activity(state: ActivityMapping) -> dict[str, object]:
    """ActivityMapping → JSON-safe dict (PRD §F9.2 + AD-15)."""
    return {
        "activity_id": str(state.activity_id),
        "hours": str(state.hours),
        "ccr_amount_krw": str(state.ccr_amount_krw),
    }


def _serialize_cost_object(state: CostObjectRow) -> dict[str, object]:
    """CostObjectRow → JSON-safe dict (PRD §9 #21 + AD-15)."""
    return {
        "product_id": str(state.product_id),
        "activity_id": str(state.activity_id),
        "driver_id": str(state.driver_id),
        "allocated_krw": str(state.allocated_krw),
    }


def _serialize_allocation(state: AllocationResult) -> dict[str, object]:
    """AllocationResult → JSON-safe dict (PRD §V7 + AD-15)."""
    return {
        "ccr": _serialize_ccr(state.ccr),
        "activity_mappings": [_serialize_activity(m) for m in state.activity_mappings],
        "cost_object_breakdown": [_serialize_cost_object(r) for r in state.cost_object_breakdown],
        "unused_capacity": _serialize_unused(state.unused_capacity),
        "department_cost": str(state.department_cost),
        "total_breakdown_sum": str(state.total_breakdown_sum),
        "is_balanced": bool(state.is_balanced),
    }


def serialize_ccr_state(state: CCRResult) -> dict[str, object]:
    """Serialize CCRResult → JSON-safe dict.

    Discriminates on dataclass type. AD-15 §1 cross-language parity with
    TS mirror `apps/web/lib/m9-abc-allocation.ts`.
    """
    if not isinstance(state, CCRResult):
        raise ValueError(f"state must be CCRResult, got {type(state).__name__}")
    return _serialize_ccr(state)


def serialize_allocation_state(state: AllocationState) -> dict[str, object]:
    """Serialize AllocationState (union) → JSON-safe dict.

    Discriminates on dataclass type via isinstance. AD-15 §1 cross-language
    parity with TS mirror `apps/web/lib/m9-abc-allocation.ts`.

    Supports:
      - `CCRResult` → CCR subset dict
      - `AllocationResult` → full allocation dict
      - `UnusedCapacityRow` → unused row dict
      - `ActivityMapping` → activity mapping dict
      - `CostObjectRow` → cost object row dict
    """
    if isinstance(state, AllocationResult):
        return _serialize_allocation(state)
    if isinstance(state, CCRResult):
        return _serialize_ccr(state)
    if isinstance(state, UnusedCapacityRow):
        return _serialize_unused(state)
    if isinstance(state, ActivityMapping):
        return _serialize_activity(state)
    if isinstance(state, CostObjectRow):
        return _serialize_cost_object(state)
    raise ValueError(
        f"state must be AllocationResult | CCRResult | UnusedCapacityRow | "
        f"ActivityMapping | CostObjectRow, got {type(state).__name__}"
    )


__all__ = [
    "serialize_ccr_state",
    "serialize_allocation_state",
]
