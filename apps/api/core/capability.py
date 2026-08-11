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

from fastapi import Depends
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

    BOM = "bom"  # manufacturing / mfg+service / mfg+service+other
    OPENING_INVENTORY = "opening_inventory"
    INVENTORY_LEDGER = "inventory_ledger"
    COST_POOL = "cost_pool"  # service / mfg+service / mfg+service+other
    ACTIVITY = "activity"
    DRIVER = "driver"
    SEGMENT_SPLIT = "segment_split"  # mfg+service / mfg+service+other only
    # Story 5.3 — closing-guard capability (PRD §F4.2 + §V3). Granted to
    # manufacturing-kind industries (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have inventory
    # so the closing-guard gate has nothing to check (industry skip matrix
    # in `ClosingGuardService`).
    INVENTORY_CLOSING_GUARD = "inventory_closing_guard"
    # Story 1.3 — AI document extraction (Task 3.6). Granted to every
    # Industry per the ARCHITECTURE-SPINE capability map (all four
    # industries can use AI extraction). This is a defense-in-depth gate
    # on the M10 routes, not a tenant-kind filter.
    AI_EXTRACT = "ai_extract"
    # Story 2.1 — product catalog. Every industry has SOME product type
    # (service tenants register `service` products even without a BOM).
    # The PRODUCT capability gates the catalog CRUD itself.
    PRODUCT = "product"
    # Story 2.1 — gated subset: only industries that own a physical
    # bill-of-materials can register `material` / `semi_product` types.
    # Service tenants cannot (no BOM menu → no material entries).
    # R6: service tenants STILL register `product` + `goods` — finished
    # products and trade goods are BOM-independent catalog rows.
    PRODUCT_MATERIAL = "product_material"
    # Story 3.1 — Monthly input production stream. Service tenants have
    # no manufacturing capability → the [생산] tab is hidden. The other
    # 5 streams (orders/sales/purchases/expenses/labor) are ungated;
    # the gate here only protects the production-stream writes. PRD §8.M2(b).
    MONTHLY_INPUT_PRODUCTION = "monthly_input_production"
    # Story 4.1 — Periodic cost calculation. Granted to all industries
    # with a manufacturing footprint (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have a [계산] tab
    # — they will have Epic 9 ABC costing instead. The engine itself
    # (packages.cost_engine.core.period_cost) is industry-agnostic and
    # always returns `state="draft"` (AD-22 — service layer owns state
    # transitions). The capability gate here only checks that the
    # caller MAY run CalcPort.compute_period_cost at all.
    COST_CALCULATION = "cost_calculation"
    # Story 6.1 — Monthly Closing Report capability (PRD §F4.3 + §F5).
    # Granted to manufacturing-kind industries (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have a [마감] tab
    # because they have no inventory ledger to snapshot.
    MONTHLY_CLOSING_REPORT = "monthly_closing_report"
    # Story 11.1 (Epic 11) — Reversal request capability (PRD §F11.3).
    # Granted to manufacturing-kind industries (manufacturing / mfg+service /
    # mfg+service+other). Service-only tenants do NOT have inventory ledger
    # so the reversal entrypoint is denied at the capability gate (PRISM).
    # Wired through `m11_close` module authority (M11) for AD-22 reversal
    # sequence + AD-25 cache invalidation publisher.
    REVERSAL_REQUEST = "reversal_request"
    # Story 11.2 (Epic 11) — 4-stage close sequence lock capability
    # (PRD §F11.1 + §8.M11(a)). Granted to manufacturing-kind
    # industries (manufacturing / mfg+service / mfg+service+other).
    # Service-only tenants do NOT have a close sequence (no inventory
    # ledger → no fiscal_periods row to lock down).
    CLOSE_SEQUENCE_LOCK = "close_sequence_lock"
    # Story 11.3 (Epic 11) — Snapshot persistence capability (PRD §F11.2 +
    # AD-20 state machine). Gates the POST /close/snapshots/commit +
    # GET /close/snapshots/{period_key} routes. Granted to manufacturing-
    # kind industries; service-only tenants have no fiscal_period_snapshots.
    SNAPSHOT_PERSISTENCE = "snapshot_persistence"
    # Story 11.3 (Epic 11) — Reversal execute capability (PRD §F11.3 +
    # AD-22 reversal 영구화). Gates the POST /close/snapshots/reverse
    # route. Distinct from REVERSAL_REQUEST (which gates AD-22 reversal
    # REQUEST 11-1 wire); this gates the EXECUTE step (3-tier guard
    # against fiscal_period_snapshots.state='committed'). Granted to
    # manufacturing-kind industries.
    REVERSAL_EXECUTE = "reversal_execute"
    # Story 11.3 (Epic 11) — Reopen operator capability (W2 reopen flow).
    # Gates the POST /close/sequence/reopen route. AD-10 owner-only
    # is enforced at the require_role layer; this capability gate is
    # the industry-aware front. Granted to manufacturing-kind industries;
    # service-only tenants do NOT have fiscal_periods to reopen.
    REOPEN_OPERATOR = "reopen_operator"


# ── Industry → Capability map (F-41-resolved) ────────────────
# Mirrors the visibility rules in `packages/services/m0_onboarding/industry_menu.py`.
_INDUSTRY_CAPABILITIES: Final[dict[Industry, frozenset[Capability]]] = {
    Industry.MANUFACTURING: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            # Story 5.3 — manufacturing tenants get closing-guard gate
            # (PRD §F4.2 + §V3).
            Capability.INVENTORY_CLOSING_GUARD,
            Capability.AI_EXTRACT,  # Story 1.3 — all industries can use AI extraction
            # Story 2.1 — manufacturing tenants can register all 5 product types.
            Capability.PRODUCT,
            Capability.PRODUCT_MATERIAL,
            # Story 3.1 — manufacturing tenants get the [생산] tab.
            Capability.MONTHLY_INPUT_PRODUCTION,
            # Story 4.1 — manufacturing tenants can run §6.1 원가 계산.
            Capability.COST_CALCULATION,
            # Story 6.1 — manufacturing tenants get Monthly Closing Report.
            Capability.MONTHLY_CLOSING_REPORT,
            # Story 11.1 — manufacturing tenants get REVERSAL_REQUEST
            # (PRD §F11.3 — AD-22 reversal sequence + AD-25 publisher).
            Capability.REVERSAL_REQUEST,
            # Story 11.2 — manufacturing tenants get the 4-stage
            # close sequence lock (PRD §F11.1 + §8.M11(a)).
            Capability.CLOSE_SEQUENCE_LOCK,
            # Story 11.3 — manufacturing tenants get SNAPSHOT_PERSISTENCE
            # (AD-20 state machine), REVERSAL_EXECUTE (AD-22 영구화),
            # and REOPEN_OPERATOR (W2 reopen flow).
            Capability.SNAPSHOT_PERSISTENCE,
            Capability.REVERSAL_EXECUTE,
            Capability.REOPEN_OPERATOR,
        }
    ),
    Industry.SERVICE: frozenset(
        {
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.AI_EXTRACT,
            # Story 2.1 — service tenants get PRODUCT (catalog CRUD) but
            # NOT PRODUCT_MATERIAL (no BOM → no physical raw/semi entries).
            Capability.PRODUCT,
            # Story 3.1 — service tenants have NO production capability
            # → the [생산] tab is hidden. The other 5 streams
            # (orders/sales/purchases/expenses/labor) are ungated.
            # Story 4.1 — service tenants do NOT have COST_CALCULATION
            # (no manufacturing footprint → no [계산] tab; they will
            # use Epic 9 ABC costing instead — gate owner: m9_abc).
        }
    ),
    Industry.MANUFACTURING_SERVICE: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            # Story 5.3 — 겸영 tenants get closing-guard gate
            # (PRD §F4.2 + §V3).
            Capability.INVENTORY_CLOSING_GUARD,
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.SEGMENT_SPLIT,
            Capability.AI_EXTRACT,
            # Story 2.1 — both engines → full product catalog.
            Capability.PRODUCT,
            Capability.PRODUCT_MATERIAL,
            # Story 3.1 — 겸영 tenants get the [생산] tab.
            Capability.MONTHLY_INPUT_PRODUCTION,
            # Story 4.1 — 겸영 tenants get BOTH §6.1 traditional costing
            # AND Epic 9 ABC costing (rows above). m3_calculate service
            # routes only check COST_CALCULATION; M9 routes check
            # COST_POOL/ACTIVITY/DRIVER.
            Capability.COST_CALCULATION,
            # Story 6.1 — 겸영 tenants get Monthly Closing Report.
            Capability.MONTHLY_CLOSING_REPORT,
            # Story 11.1 — 겸영 tenants get REVERSAL_REQUEST.
            Capability.REVERSAL_REQUEST,
            # Story 11.2 — 겸영 tenants get the 4-stage close
            # sequence lock (manufacturing footprint present).
            Capability.CLOSE_SEQUENCE_LOCK,
            # Story 11.3 — 겸영 tenants get SNAPSHOT_PERSISTENCE +
            # REVERSAL_EXECUTE + REOPEN_OPERATOR.
            Capability.SNAPSHOT_PERSISTENCE,
            Capability.REVERSAL_EXECUTE,
            Capability.REOPEN_OPERATOR,
        }
    ),
    Industry.MANUFACTURING_SERVICE_OTHER: frozenset(
        {
            Capability.BOM,
            Capability.OPENING_INVENTORY,
            Capability.INVENTORY_LEDGER,
            # Story 5.3 — 겸영 + other tenants get closing-guard gate
            # (PRD §F4.2 + §V3).
            Capability.INVENTORY_CLOSING_GUARD,
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.SEGMENT_SPLIT,
            Capability.AI_EXTRACT,
            # Story 2.1 — full catalog + 격리 버킷.
            Capability.PRODUCT,
            Capability.PRODUCT_MATERIAL,
            # Story 3.1 — full matrix.
            Capability.MONTHLY_INPUT_PRODUCTION,
            # Story 4.1 — full matrix + 격리 버킷.
            Capability.COST_CALCULATION,
            # Story 6.1 — full matrix tenants get Monthly Closing Report.
            Capability.MONTHLY_CLOSING_REPORT,
            # Story 11.1 — full matrix tenants get REVERSAL_REQUEST.
            Capability.REVERSAL_REQUEST,
            # Story 11.2 — full matrix tenants get the 4-stage close
            # sequence lock (manufacturing footprint present).
            Capability.CLOSE_SEQUENCE_LOCK,
            # Story 11.3 — full matrix tenants get SNAPSHOT_PERSISTENCE +
            # REVERSAL_EXECUTE + REOPEN_OPERATOR.
            Capability.SNAPSHOT_PERSISTENCE,
            Capability.REVERSAL_EXECUTE,
            Capability.REOPEN_OPERATOR,
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
        except TenantSettingsNotFoundError as err:
            # Treat as no industry selected → no capabilities unlocked.
            raise IndustryCapabilityError(
                tenant_id=ctx.tenant_id,
                current_industry=None,
                capability=capability,
                trace_id=trace_id,
            ) from err

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


# ── Role gate (AD-10) — owner-only mutations ─────────────────
class ForbiddenRoleError(Exception):
    """403 FORBIDDEN_ROLE — caller's role does not allow this mutation.

    AD-10 + T4.2: only `owner` may run POST/PATCH. member/viewer are
    read-only on product catalog. Mapped to HTTP 403 by main.py global
    handler.
    """

    def __init__(
        self,
        *,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
        role: str,
        required_role: str,
        trace_id: str,
    ) -> None:
        super().__init__(f"role {role!r} forbidden; required {required_role!r}")
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.role = role
        self.required_role = required_role
        self.trace_id = trace_id


def require_role(required_role: str):
    """FastAPI dependency factory — enforce a minimum role on the route.

    H3 / AD-10 / T4.2 — owner-only mutations. The `role` is read from
    `TenantContext.role` (set by JWT decoding in `get_tenant_context`).

    Usage:
        @router.post(
            "/products",
            dependencies=[Depends(require_role("owner"))],
        )
    """

    async def _dep(
        ctx: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        trace_id = str(uuid.uuid4())
        if ctx.role != required_role:
            raise ForbiddenRoleError(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                role=ctx.role,
                required_role=required_role,
                trace_id=trace_id,
            )
        return ctx

    return _dep


def require_any_role(*allowed_roles: str):
    """FastAPI dependency factory — enforce role ∈ {allowed_roles} on the route.

    Story 12.4 review P-10: M2 entry gates (consume_challenge_token, etc.)
    need to allow owner OR member (NOT viewer/consultant_proxy). This
    helper is the multi-role complement of `require_role`.

    Usage:
        @router.post(
            "/account/2fa/challenge-tokens/consume",
            dependencies=[Depends(require_any_role("owner", "member"))],
        )
    """
    allowed = frozenset(allowed_roles)

    async def _dep(
        ctx: TenantContext = Depends(get_tenant_context),
    ) -> TenantContext:
        trace_id = str(uuid.uuid4())
        if ctx.role not in allowed:
            raise ForbiddenRoleError(
                tenant_id=ctx.tenant_id,
                user_id=ctx.user_id,
                role=ctx.role,
                required_role="|".join(sorted(allowed)),
                trace_id=trace_id,
            )
        return ctx

    return _dep
