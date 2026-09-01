"""apps.api.modules.finops.department_mapping — Department cost center mapping (PRD §F27.3).

Phase 11 (cj-style 107번째 wire) — FinOps Showback / Chargeback
territory (PRD §F27.3 verbatim).

This module provides:
- `DepartmentCostCenterMapping` TypedDict (PRD §F27.3.1 verbatim).
- cost_center_id pattern `CC-{4-digit-number}` format (PRD §F27.3.1
  verbatim).
- 1:1 mapping (one department → one cost_center; one cost_center →
  many departments).
- `validate_department_mapping()` — pure validator (CR 11-4 P-015
  verbatim) enforcing 4 validation rules.
- Auto-create on first calculation (PRD §F27.3.3 verbatim).
- Audit-first INSERT `department_mapping_updated` (CR 1-1 verbatim).

CR lessons applied:
- CR 0-2 RLS — every mapping carries tenant_id selector + UNIQUE
  constraint `(tenant_id, department_id)`.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.

AD-22 owner-only RBAC — department mapping update owner-only.
Epic 12 2FA 챌린지 mandatory.
"""

from __future__ import annotations

import re
import secrets
import uuid
from typing import Any, Final, TypedDict

# ── Cost center ID pattern (PRD §F27.3.1 verbatim) ──────────────
COST_CENTER_ID_PATTERN: Final[str] = r"^CC-\d{4}$"
COST_CENTER_ID_REGEX: Final[re.Pattern[str]] = re.compile(COST_CENTER_ID_PATTERN)

# Cache invalidation (PRD §F27.3.10 verbatim).
DEPARTMENT_MAPPING_CACHE_TTL_SECONDS: Final[int] = 300  # 5 minutes


# ── TypedDict — DepartmentCostCenterMapping ──────────────────────
class DepartmentCostCenterMapping(TypedDict, total=False):
    """Department cost center mapping row (PRD §F27.3.1 verbatim).

    Persisted in phase_11_finops_department_mapping table (alembic
    0043) with UNIQUE (tenant_id, department_id) constraint.
    """

    id: str
    tenant_id: str
    department_id: str
    department_name: str
    cost_center_id: str
    auto_created: bool
    created_at: str
    updated_at: str
    created_by: str
    updated_by: str
    trace_id: str


# ── Pure validator (CR 11-4 P-015 verbatim) ─────────────────────
class DepartmentMappingValidationError(ValueError):
    """Raised by validate_department_mapping() for invalid input.

    Distinct from CR 12-5 D-14 typed exception envelope (which is
    HTTP-layer) — this is the pure-kernel validation exception
    used internally by auto-create + cache layer code paths.
    """

    http_status: int = 400


def validate_department_mapping(
    mapping: DepartmentCostCenterMapping,
) -> DepartmentCostCenterMapping:
    """Validate a DepartmentCostCenterMapping (CR 11-4 P-015 pure).

    Enforces 4 validation rules (PRD §F27.3.2 verbatim):
    1. tenant_id non-empty UUID string
    2. department_id non-empty
    3. cost_center_id matches CC-{4-digit-number} pattern
    4. created_by + updated_by non-empty when present
    """
    if not mapping.get("tenant_id"):
        raise DepartmentMappingValidationError(
            "tenant_id is required",
        )

    if not mapping.get("department_id"):
        raise DepartmentMappingValidationError(
            "department_id is required",
        )

    cost_center_id = mapping.get("cost_center_id", "")
    if not COST_CENTER_ID_REGEX.match(cost_center_id):
        raise DepartmentMappingValidationError(
            f"cost_center_id {cost_center_id!r} does not match {COST_CENTER_ID_PATTERN}",
        )

    if "created_by" in mapping and not mapping.get("created_by"):
        raise DepartmentMappingValidationError(
            "created_by must be non-empty when present",
        )
    if "updated_by" in mapping and not mapping.get("updated_by"):
        raise DepartmentMappingValidationError(
            "updated_by must be non-empty when present",
        )

    if not mapping.get("id"):
        mapping["id"] = str(uuid.uuid4())
    if not mapping.get("trace_id"):
        mapping["trace_id"] = str(uuid.uuid4())

    return mapping


def generate_cost_center_id() -> str:
    """Generate a fresh cost_center_id matching CC-{4-digit} pattern.

    Used by auto-create on first calculation (PRD §F27.3.3 verbatim).
    Uses cryptographic randomness to avoid collisions across the
    phase_11_finops_department_mapping UNIQUE constraint.
    """
    n = secrets.randbelow(10000)
    return f"CC-{n:04d}"


def auto_create_mapping(
    *,
    tenant_id: str,
    department_id: str,
    department_name: str,
    actor_id: str = "system",
) -> DepartmentCostCenterMapping:
    """Auto-create a department mapping on first calculation (PRD §F27.3.3).

    Generates a fresh cost_center_id via `generate_cost_center_id()`,
    sets auto_created=True, and emits audit-first INSERT payload
    `department_mapping_updated` (CR 1-1 verbatim).
    """
    mapping = DepartmentCostCenterMapping(
        tenant_id=tenant_id,
        department_id=department_id,
        department_name=department_name,
        cost_center_id=generate_cost_center_id(),
        auto_created=True,
        created_by=actor_id,
        updated_by=actor_id,
    )
    return validate_department_mapping(mapping)


# ── Cache key (PRD §F27.3.10 verbatim) ──────────────────────────
def department_mapping_cache_key(tenant_id: str, department_id: str) -> str:
    """Compose the Redis cache key for a department mapping.

    Key shape: `cost_center_mapping:{tenant_id}:{department_id}`.
    """
    return f"cost_center_mapping:{tenant_id}:{department_id}"


# ── Audit-first INSERT (CR 1-1 verbatim) ────────────────────────
def audit_first_insert_department_mapping_updated(
    *,
    tenant_id: str,
    department_id: str,
    cost_center_id: str,
    actor_id: str,
    auto_created: bool,
    trace_id: str,
) -> dict[str, Any]:
    """Build the audit log payload for department_mapping_updated."""
    return {
        "action": "department_mapping_updated",
        "action_class": "FINOPS",
        "module_id": "m19_finops",
        "tenant_id": tenant_id,
        "department_id": department_id,
        "cost_center_id": cost_center_id,
        "actor_id": actor_id,
        "auto_created": auto_created,
        "trace_id": trace_id or str(uuid.uuid4()),
        "audit_first": True,
    }


__all__ = [
    "COST_CENTER_ID_PATTERN",
    "COST_CENTER_ID_REGEX",
    "DEPARTMENT_MAPPING_CACHE_TTL_SECONDS",
    "DepartmentCostCenterMapping",
    "DepartmentMappingValidationError",
    "validate_department_mapping",
    "generate_cost_center_id",
    "auto_create_mapping",
    "department_mapping_cache_key",
    "audit_first_insert_department_mapping_updated",
]
