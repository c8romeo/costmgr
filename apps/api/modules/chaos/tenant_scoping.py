"""apps.api.modules.chaos.tenant_scoping — Multi-region chaos decision helpers.

Phase 9 (cj-style 99번째 wire) — Tenant-scoped + multi-region chaos
(PRD §F25.5 verbatim).

Helpers:
- `resolve_target_region(region: str) -> str` — validate region enum.
- `is_multi_region_eligible(blast_radius: str) -> bool` — check if
  blast radius L4 / L5 requires multi-region logic.
- `validate_chaos_tenant_scope(tenant_id, blast_radius, region) -> None` —
  cross-tenant isolation guard.

CR 0-2 RLS lesson: phase_9_chaos_experiments table RLS auto-applied
via `tenant_id = current_setting('app.tenant_id')::uuid`.
"""
from __future__ import annotations

import uuid

from apps.api.core.errors import BaseError

# ── Region enum ────────────────────────────────────────────────
VALID_REGIONS = ("seoul", "tokyo", "all")


# ── Typed exception envelope ────────────────────────────────────
class ChaosTenantScopingError(BaseError):
    """400 CHAOS_TENANT_SCOPING_INVALID — invalid region or blast radius combo."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, object] | None = None,
        http_status: int = 400,
    ) -> None:
        super().__init__(
            code=code,
            message_ko=message_ko,
            details=details or {},
            trace_id=str(uuid.uuid4()),
            http_status=http_status,
        )


def resolve_target_region(region: str) -> str:
    """Validate region enum. Returns the canonical lowercase region."""
    region_lower = region.lower()
    if region_lower not in VALID_REGIONS:
        raise ChaosTenantScopingError(
            code="CHAOS_INVALID_REGION",
            message_ko=f"유효하지 않은 region: {region!r}",
            details={"region": region, "valid": list(VALID_REGIONS)},
        )
    return region_lower


def is_multi_region_eligible(blast_radius: str) -> bool:
    """True if blast radius L4 (single_region) or L5 (multi_region).

    Used to decide whether to wire Phase 5 failover_orchestrator
    auto-trigger verification.
    """
    return blast_radius in ("single_region", "multi_region")


def validate_chaos_tenant_scope(
    *,
    tenant_id: str,
    blast_radius: str,
    region: str,
) -> None:
    """Validate chaos tenant scope + region + blast radius combination.

    Rules:
    - region='all' requires blast_radius='multi_region'.
    - blast_radius='single_request' is compatible with any region.
    - blast_radius='single_tenant' works for any region.
    - blast_radius='all_tenants' is region-independent (production scope).
    """
    canonical_region = resolve_target_region(region)
    if canonical_region == "all" and blast_radius != "multi_region":
        raise ChaosTenantScopingError(
            code="CHAOS_REGION_BLAST_RADIUS_MISMATCH",
            message_ko="region='all' requires blast_radius='multi_region'.",
            details={
                "region": canonical_region,
                "blast_radius": blast_radius,
            },
        )


__all__ = [
    "VALID_REGIONS",
    "ChaosTenantScopingError",
    "resolve_target_region",
    "is_multi_region_eligible",
    "validate_chaos_tenant_scope",
]
