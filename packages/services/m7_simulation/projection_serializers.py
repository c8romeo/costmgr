"""packages.services.m7_simulation.projection_serializers — Story 7.2 thin JSON serializers.

Pure-Python JSON-safe serializers for `ProjectionInputs` + `NextMonthProjection`
frozen dataclasses. Decimal-as-string (AD-8 monetary precision parity) +
cross-language parity with TS mirror
`apps/web/lib/m7-simulation-projection.ts`.

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m7_simulation.projection_serializers`
registered in `tests/architecture/test_api_calls_only_ports.py` (T4 wire).
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass

from packages.cost_engine.projection import (
    NextMonthProjection,
    ProjectionInputs,
)


def serialize_projection_inputs(inputs: ProjectionInputs) -> dict[str, str]:
    """Serialize `ProjectionInputs` → JSON-safe dict (Decimal-as-string).

    AD-15 §1 + AD-8 cross-language parity with TS mirror
    `apps/web/lib/m7-simulation-projection.ts:serializeProjectionInputsTS`.
    """
    return {
        "loan_amount": str(inputs.loan_amount),
        "interest_rate": str(inputs.interest_rate),
        "cost_inflation_rate": str(inputs.cost_inflation_rate),
        "corporate_tax_rate": str(inputs.corporate_tax_rate),
    }


def _serialize_dataclass(obj: object) -> dict[str, str]:
    """Serialize a frozen dataclass instance → JSON-safe dict (Decimal-as-string).

    Slots-friendly: uses `dataclasses.fields()` introspection (NOT `vars()`).
    """
    if not is_dataclass(obj):
        raise TypeError(f"expected dataclass, got {type(obj).__name__}")
    return {f.name: str(getattr(obj, f.name)) for f in fields(obj)}


def serialize_projection_result(result: NextMonthProjection) -> dict[str, str]:
    """Serialize `NextMonthProjection` → JSON-safe dict (Decimal-as-string).

    AD-15 §1 + AD-8 cross-language parity with TS mirror.
    """
    return _serialize_dataclass(result)


__all__ = [
    "serialize_projection_inputs",
    "serialize_projection_result",
]
