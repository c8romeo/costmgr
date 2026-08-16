"""packages.services.m9_abc.abc_validation_serializers — Story 9.1 thin JSON serializers.

Pure-Python JSON-safe serializers for `CostPoolValidation` +
`ActivityValidation` + `DriverValidation` frozen dataclasses.
Decimal-as-string (AD-15 §1 cross-language parity with TS mirror).

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — registered in
`tests/architecture/test_api_calls_only_ports.py` (T2 wire).
"""

from __future__ import annotations

from packages.cost_engine.abc_engine import (
    ActivityValidation,
    CostPoolValidation,
    DriverValidation,
    ValidationState,
)


def _serialize_cost_pool(state: CostPoolValidation) -> dict[str, object]:
    """CostPoolValidation → JSON-safe dict (PRD §F9.1 + AD-15)."""
    return {
        "department_id": str(state.department_id),
        "sum_pct": str(state.sum_pct),
        "department_count": int(state.department_count),
        "is_valid": bool(state.is_valid),
        "hash": str(state.hash),
    }


def _serialize_activity(state: ActivityValidation) -> dict[str, object]:
    """ActivityValidation → JSON-safe dict (PRD §F9.1 + AD-15)."""
    return {
        "cost_pool_id": str(state.cost_pool_id),
        "sum_pct": str(state.sum_pct),
        "activity_count": int(state.activity_count),
        "is_valid": bool(state.is_valid),
        "hash": str(state.hash),
    }


def _serialize_driver(state: DriverValidation) -> dict[str, object]:
    """DriverValidation → JSON-safe dict (PRD §F9.1 + AD-15)."""
    return {
        "activity_id": str(state.activity_id),
        "sum_pct": str(state.sum_pct),
        "driver_count": int(state.driver_count),
        "is_valid": bool(state.is_valid),
        "hash": str(state.hash),
    }


def serialize_validation_state(
    state: ValidationState,
) -> dict[str, object]:
    """Serialize ValidationState (union) → JSON-safe dict.

    Discriminates on dataclass type via isinstance. AD-15 §1
    cross-language parity with TS mirror
    `apps/web/lib/m9-abc-validation.ts`.
    """
    if isinstance(state, CostPoolValidation):
        return _serialize_cost_pool(state)
    if isinstance(state, ActivityValidation):
        return _serialize_activity(state)
    if isinstance(state, DriverValidation):
        return _serialize_driver(state)
    raise ValueError(
        f"validation_state must be CostPoolValidation | "
        f"ActivityValidation | DriverValidation, "
        f"got {type(state).__name__}"
    )


__all__ = [
    "serialize_validation_state",
]
