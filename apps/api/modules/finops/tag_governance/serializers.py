"""apps.api.modules.finops.tag_governance.serializers — FinOps Tag Governance serializers.

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31 verbatim). Mirrors Phase 14
`m22_finops_optimization.optimization_serializers` namespace pattern
verbatim.

CR lessons applied:
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity verification (verifiable via apps/web/lib/finops-tag-governance/
  finops-tag-governance-client.ts).
"""
from __future__ import annotations

from typing import Any

# Module identifier (mirrors m22_finops_optimization pattern verbatim).
m23_finops_tag_governance: str = "m23_finops_tag_governance"


def tag_governance_serializers(obj: Any) -> dict[str, Any]:
    """Serialize FinOps tag governance object → JSON-safe dict.

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


def tag_governance_deserialize(payload: dict[str, Any], target_class: type) -> Any:
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
    "m23_finops_tag_governance",
    "tag_governance_serializers",
    "tag_governance_deserialize",
]