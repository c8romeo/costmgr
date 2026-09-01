"""apps.api.modules.finops.serializers — FinOps serializers (CR 12-5 D-PARITY-01).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29 verbatim).

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30 verbatim).

This module is the BACKFILL for the Phase 11 stub that `__init__.py`
references in its docstring but never had a real implementation.

Mirrors Phase 12 `m20_finops_anomaly.finops_anomaly_serializers`
namespace pattern verbatim.

CR lessons applied:
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity verification (verifiable via apps/web/lib/finops-forecast/
  finops-forecast-client.ts).
"""

from __future__ import annotations

from typing import Any

# Module identifier (mirrors m20_finops_anomaly pattern verbatim).
m21_finops_forecast: str = "m21_finops_forecast"

# Module identifier for Phase 14 wire — FinOps Optimization & Rightsizing
# (mirrors m21_finops_forecast pattern verbatim).
m22_finops_optimization: str = "m22_finops_optimization"


def finops_forecast_serializers(obj: Any) -> dict[str, Any]:
    """Serialize FinOps forecast object → JSON-safe dict.

    Pure validator pattern (CR 11-4 P-015 verbatim). Service-layer uses
    this to convert TypedDict → JSONB for PostgreSQL persistence.

    Args:
        obj: TypedDict or Pydantic model.

    Returns:
        dict[str, Any] — JSON-safe representation.
    """
    if hasattr(obj, "model_dump"):
        return obj.model_dump()  # Pydantic v2
    if hasattr(obj, "dict"):
        return obj.dict()  # Pydantic v1
    if isinstance(obj, dict):
        return dict(obj)
    raise TypeError(f"Cannot serialize object of type {type(obj).__name__}")


def finops_forecast_deserialize(payload: dict[str, Any], target_class: type) -> Any:
    """Deserialize JSONB payload → typed object.

    Pure validator pattern (CR 11-4 P-015 verbatim).

    Args:
        payload: JSON-safe dict.
        target_class: TypedDict class or Pydantic model.

    Returns:
        Instantiated object of target_class.
    """
    if hasattr(target_class, "model_validate"):
        return target_class.model_validate(payload)  # Pydantic v2
    if hasattr(target_class, "parse_obj"):
        return target_class.parse_obj(payload)  # Pydantic v1
    return payload


__all__ = [
    "m21_finops_forecast",
    "m22_finops_optimization",
    "finops_forecast_serializers",
    "finops_forecast_deserialize",
]
