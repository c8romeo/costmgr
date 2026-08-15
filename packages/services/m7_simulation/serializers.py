"""packages.services.m7_simulation.serializers — Story 7.1 thin JSON serializers.

Pure-Python JSON-safe serializers for `CVPBaseline` + `CVPDelta` + `CVPResult`
frozen dataclasses. Decimal-as-string (AD-8 monetary precision parity) +
cross-language parity with TS mirror `apps/web/lib/m7-simulation-cvp.ts`.

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m7_simulation` registered
in `tests/architecture/test_api_calls_only_ports.py` (T4 wire).
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass

from packages.cost_engine.cvp import (
    CVPBaseline,
    CVPDelta,
    CVPResult,
)


def serialize_cvp_baseline(baseline: CVPBaseline) -> dict[str, str]:
    """Serialize `CVPBaseline` → JSON-safe dict (Decimal-as-string).

    AD-15 §1 + AD-8 cross-language parity with TS mirror
    `apps/web/lib/m7-simulation-cvp.ts:serializeCvpBaselineTS`.
    """
    return {
        "fixed_cost": str(baseline.fixed_cost),
        "unit_variable_cost": str(baseline.unit_variable_cost),
        "unit_price": str(baseline.unit_price),
        "operating_rate": str(baseline.operating_rate),
        "target_profit": str(baseline.target_profit),
    }


def serialize_cvp_delta(delta: CVPDelta) -> dict[str, str]:
    """Serialize `CVPDelta` → JSON-safe dict (Decimal-as-string).

    AD-15 §1 + AD-8 cross-language parity with TS mirror.
    """
    return {
        "unit_price_delta_pct": str(delta.unit_price_delta_pct),
        "unit_variable_cost_delta_pct": str(delta.unit_variable_cost_delta_pct),
        "fixed_cost_delta_pct": str(delta.fixed_cost_delta_pct),
        "operating_rate_delta_pct": str(delta.operating_rate_delta_pct),
    }


def _serialize_dataclass(obj: object) -> dict[str, str]:
    """Serialize a frozen dataclass instance → JSON-safe dict (Decimal-as-string).

    Slots-friendly: uses `dataclasses.fields()` introspection (NOT `vars()`).
    """
    if not is_dataclass(obj):
        raise TypeError(
            f"expected dataclass, got {type(obj).__name__}"
        )
    return {f.name: str(getattr(obj, f.name)) for f in fields(obj)}


def serialize_cvp_result(result: CVPResult) -> dict[str, object]:
    """Serialize `CVPResult` → JSON-safe dict (Decimal-as-string).

    AD-15 §1 + AD-8 cross-language parity with TS mirror.
    """
    return {
        "simulated_bep": _serialize_dataclass(result.simulated_bep),
        "simulated_target_profit": _serialize_dataclass(
            result.simulated_target_profit
        ),
        "baseline_bep": _serialize_dataclass(result.baseline_bep),
        "baseline_target_profit": _serialize_dataclass(
            result.baseline_target_profit
        ),
        "delta_summary": {k: str(v) for k, v in result.delta_summary.items()},
    }


__all__ = [
    "serialize_cvp_baseline",
    "serialize_cvp_delta",
    "serialize_cvp_result",
]
