"""apps.api.core.capability — industry-aware capability enforcement (F-44).

Story 1.1 — F-44. Resolves the decision that backend endpoints should also
reject mismatched-industry writes (vs. frontend-only filtering). This
module provides:

- `Capability` — enum of industry-scoped capabilities (BOM, ABC, etc.).
- `INDUSTRY_CAPABILITY_MAP` — which Industry values unlock which Capability.
- `enforce_capability` — FastAPI dependency that reads the tenant's industry
  via `get_tenant_context` + `get_tenant_settings` and raises
  `IndustryCapabilityError` (403 INDUSTRY_NOT_SUPPORTED) if the tenant's
  industry does not unlock the requested capability.
- `require_capability(capability)` — helper to attach to a route.

The actual endpoints that opt into this gate live in Epic 2+ (m1_baseline
= BOM/CostPool/Inventory, m2_input = inputs, etc.). Story 1.1 only
provides the gate — wiring is deferred.

Example (Epic 2+):

    from apps.api.core.capability import require_capability, Capability

    @router.post("/api/v1/bom", dependencies=[Depends(require_capability(Capability.BOM))])
    async def create_bom(...): ...
"""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Final

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from packages.services.m0_onboarding.industry_menu import Industry


# ── Capability enum ──────────────────────────────────────────
class Capability(str, Enum):
    """Backend capabilities gated by industry.

    These map to menu items the sidebar hides for incompatible industries
    (Story 1.1 §AC #2/§AC #3). The frontend hides the menu entries;
    this module enforces that writes to the corresponding backend
    endpoints are also rejected, so a service tenant cannot bypass the
    UI filter and POST directly to /api/v1/bom.
    """

    BOM = "bom"                            # manufacturing / mfg+service / mfg+service+other
    OPENING_INVENTORY = "opening_inventory"
    INVENTORY_LEDGER = "inventory_ledger"
    COST_POOL = "cost_pool"                # service / mfg+service / mfg+service+other
    ACTIVITY = "activity"
    DRIVER = "driver"
    SEGMENT_SPLIT = "segment_split"        # mfg+service / mfg+service+other only


# ── Industry → Capability map (F-41-resolved) ────────────────
# Mirrors the visibility rules in `packages/services/m0_onboarding/industry_menu.py`.
_INDUSTRY_CAPABILITIES: Final[dict[Industry, frozenset[Capability]]] = {
    Industry.MANUFACTURING: frozenset(
        {Capability.BOM, Capability.OPENING_INVENTORY, Capability.INVENTORY_LEDGER}
    ),
    Industry.SERVICE: frozenset(
        {Capability.COST_POOL, Capability.ACTIVITY, Capability.DRIVER}
    ),
    Industry.MANUFACTURING_SERVICE: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.SEGMENT_SPLIT,
        }
    ),
    Industry.MANUFACTURING_SERVICE_OTHER: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.SEGMENT_SPLIT,
        }
    ),
}


# ── Exception (mapped to 403 INDUSTRY_NOT_SUPPORTED) ────────
class IndustryCapabilityError(Exception):
    """403 INDUSTRY_NOT_SUPPORTED — tenant's industry does not unlock capability."""

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        current_industry: Industry | None,
        capability: Capability,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"industry {current_industry!r} cannot access capability {capability.value!r}"
        )
        self.tenant_id = tenant_id
        self.current_industry = current_industry
        self.capability = capability
        self.trace_id = trace_id


# ── Public helpers ───────────────────────────────────────────
def industry_supports(industry: Industry, capability: Capability) -> bool:
    """Pure function: does this industry unlock this capability?"""
    return capability in _INDUSTRY_CAPABILITIES.get(industry, frozenset())


def require_capability(capability: Capability):
    """FastAPI dependency factory — returns a dependency that enforces the capability.

    Usage:
        @router.post("/api/v1/bom", dependencies=[Depends(require_capability(Capability.BOM))])

    Reads the tenant's industry via SettingsService.get_tenant_settings and
    raises IndustryCapabilityError (mapped to 403) if unsupported.
    """

    async def _dep(
        ctx: TenantContext = Depends(get_tenant_context),
        session: AsyncSession = Depends(get_session),
    ) -> TenantContext:
        from apps.api.modules.m0_onboarding.services.settings_service import (
            SettingsService,
            TenantSettingsNotFoundError,
        )

        trace_id = str(uuid.uuid4())
        service = SettingsService(session, trace_id=trace_id)
        try:
            row = await service.get_tenant_settings(tenant_id=ctx.tenant_id)
        except TenantSettingsNotFoundError:
            # Treat as no industry selected → no capabilities unlocked.
            raise IndustryCapabilityError(
                tenant_id=ctx.tenant_id,
                current_industry=None,
                capability=capability,
                trace_id=trace_id,
            )

        onboarding = dict(row.onboarding or {})
        industry_raw = onboarding.get("industry")
        try:
            industry = Industry(industry_raw) if industry_raw else None
        except ValueError:
            industry = None

        if not industry_supports(industry, capability):
            raise IndustryCapabilityError(
                tenant_id=ctx.tenant_id,
                current_industry=industry,
                capability=capability,
                trace_id=trace_id,
            )
        return ctx

    return _dep