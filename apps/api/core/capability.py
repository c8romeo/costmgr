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
    # Story 10.1 (Epic 10) — AI insight capability (PRD §F10.1 + §8.1 M10).
    # Industry-agnostic per CR 12-1 L4 precedent (mirrors TWO_FACTOR_AUTH /
    # BACKUP_EXPORT / BUDGET_SCENARIO / CVP_SIMULATION / ABC_CALCULATION).
    # Granted to all 4 industries. Gates POST /api/v1/ai/extract-monthly.
    # Drift detector: tests/integration/test_capability_matrix_v1_21_drift.py
    # (matrix row already declared; backend enum was the missing half).
    AI_INSIGHT = "ai_insight"
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
    # Story 12.2 (Epic 12) — Daily backup export + JSON self-download
    # capability (PRD §F12.2 + §M12-b). Industry-agnostic security baseline
    # (CR 12-1 L4 precedent — 2FA pattern). Granted to all 4 industries
    # because backup is operational infrastructure, not industry-specific.
    # NOT enforced as a route gate (mirrors TWO_FACTOR_AUTH): owner-only
    # via AD-10 `require_role("owner")`. Documented in capability-matrix
    # v1.14 for industry-parity auditability.
    BACKUP_EXPORT = "backup_export"
    # Story 12.1 + 12.4 (Epic 12) — 2FA mandatory gate capability
    # (PRD §F12.1 + §M12-a). Industry-agnostic security baseline — 2FA
    # is operational infrastructure, not industry-specific. Granted to
    # all 4 industries. NOT enforced as a route gate (CR 12-1 L4):
    # 2FA allowlist is owner+member at the `require_any_role` layer.
    # Originally documented in capability-matrix v1.13 (12-1) but the
    # enum entry was missed — 12-2 carry-over fix (drift detector
    # `tests/integration/test_capability_matrix_v1_14_drift.py` surfaces it).
    TWO_FACTOR_AUTH = "two_factor_auth"
    # Story 12.3 (Epic 12) — Account deletion + retention consent
    # capability (PRD §F12.3 + NFR4 2절 5년 audit 보존 + 30일 hard
    # delete + NFR7 2FA 강제). Industry-agnostic security baseline
    # (CR 12-1 L4 precedent — mirrors TWO_FACTOR_AUTH + BACKUP_EXPORT
    # patterns). Granted to all 4 industries because deletion is
    # operational infrastructure (data subject right / GDPR Art.17),
    # not industry-specific. Enforced ONLY on the destructive endpoint
    # POST /account/deletion/request (the 3-layer TOTP defense target).
    # Other endpoints (challenge-token / cancel / status) gate ONLY on
    # `require_role("owner")` per AD-10.
    ACCOUNT_DELETION = "account_deletion"
    # Story 8.1 (Epic 8) — Virtual budget period key + scenario lock
    # capability (PRD §F8.1 + AD-24 period key typed pattern).
    # Industry-agnostic baseline — "budget scenario는 tenant-level 재무
    # baseline" — 모든 industry 동일 적용 (CR 12-1 L4 precedent +
    # 7-1/7-2 industry-agnostic 동일 적용). Granted to all 4 industries
    # because budget scenarios are financial planning infrastructure,
    # not industry-specific. Reused by Story 8-2 (variance table) +
    # Story 8-3 (pre-standard cost preview) — 신규 capability 추가 0건
    # (CR 11-3 즉시 sweep 회피). Documented in capability-matrix v1.17.
    BUDGET_SCENARIO = "budget_scenario"
    # Story 7.1 (Epic 7) — CVP/BEP slider simulation capability
    # (PRD §F7.1 + AD-5 engine purity). Industry-agnostic baseline
    # (CR 12-1 L4 precedent — manufacturing 3종 ✅ + service-only ✅).
    # Granted to all 4 industries because CVP/BEP is financial
    # planning infrastructure, not industry-specific. Used as the
    # capability gate for both POST /simulation/cvp/compute and
    # GET /simulation/cvp/baseline routes. Documented in
    # capability-matrix v1.17.
    CVP_SIMULATION = "cvp_simulation"
    # Story 9.1 (Epic 9) — ABC 100% validation guard capability
    # (PRD §F9.1 + AD-5 engine purity + A19 cohesion pattern 6번째 surface).
    # Industry-agnostic baseline (CR 12-1 L4 precedent — manufacturing 3종 ✅
    # + service-only ✅). Granted to all 4 industries because ABC validation
    # is a precursor guard before CCR allocation (9-2 / 9-3 / 9-4 follow-up).
    # Used as the capability gate for POST /api/v1/abc/{cost-pools,activities,
    # drivers/validate,validate} routes. Documented in capability-matrix v1.18.
    # 9-2 / 9-3 / 9-4 동일 capability 재사용 (CR 11-3 즉시 sweep 회피).
    ABC_CALCULATION = "abc_calculation"


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
            # Story 10.1 (Epic 10) — manufacturing tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4 + 7-1/7-2/8-1
            # /8-2/8-3 precedent). Gates POST /api/v1/ai/extract-monthly.
            Capability.AI_INSIGHT,
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
            # Story 12.2 — manufacturing tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — manufacturing tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — manufacturing tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — manufacturing tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — manufacturing tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — manufacturing tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4 + 7-1/7-2/8-1/8-2/8-3 precedent).
            Capability.ABC_CALCULATION,
        }
    ),
    Industry.SERVICE: frozenset(
        {
            Capability.COST_POOL,
            Capability.ACTIVITY,
            Capability.DRIVER,
            Capability.AI_EXTRACT,
            # Story 10.1 (Epic 10) — service tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.AI_INSIGHT,
            # Story 2.1 — service tenants get PRODUCT (catalog CRUD) but
            # NOT PRODUCT_MATERIAL (no BOM → no physical raw/semi entries).
            Capability.PRODUCT,
            # Story 3.1 — service tenants have NO production capability
            # → the [생산] tab is hidden. The other 5 streams
            # (orders/sales/purchases/expenses/labor) are ungated.
            # Story 4.1 — service tenants do NOT have COST_CALCULATION
            # (no manufacturing footprint → no [계산] tab; they will
            # use Epic 9 ABC costing instead — gate owner: m9_abc).
            # Story 12.2 — service tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — service tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — service tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — service tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — service tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — service tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.ABC_CALCULATION,
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
            # Story 10.1 (Epic 10) — 겸영 tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.AI_INSIGHT,
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
            # Story 12.2 — 겸영 tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — 겸영 tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — 겸영 tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — 겸영 tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — 겸영 tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — 겸영 tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.ABC_CALCULATION,
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
            # Story 10.1 (Epic 10) — full matrix tenants get AI_INSIGHT
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.AI_INSIGHT,
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
            # Story 12.2 — full matrix tenants get BACKUP_EXPORT
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.BACKUP_EXPORT,
            # Story 12.1 — full matrix tenants get TWO_FACTOR_AUTH
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.TWO_FACTOR_AUTH,
            # Story 12.3 — full matrix tenants get ACCOUNT_DELETION
            # (industry-agnostic, security baseline CR 12-1 L4).
            Capability.ACCOUNT_DELETION,
            # Story 8.1 — full matrix tenants get BUDGET_SCENARIO
            # (industry-agnostic, financial baseline CR 12-1 L4 +
            # 7-1/7-2 L4 precedent — all industries grant).
            Capability.BUDGET_SCENARIO,
            # Story 7.1 — full matrix tenants get CVP_SIMULATION
            # (industry-agnostic, financial baseline CR 12-1 L4).
            Capability.CVP_SIMULATION,
            # Story 9.1 — full matrix tenants get ABC_CALCULATION
            # (industry-agnostic, validation guard CR 12-1 L4).
            Capability.ABC_CALCULATION,
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


def require_any_capability(*allowed_capabilities: Capability):
    """FastAPI dependency factory — enforce ANY of the listed capabilities on the route.

    Story 9.3 (T2 prep + T6 capability-matrix v1.19) — A29 forward-lock
    dual-route gate. M3 orchestrator's POST /api/v1/calc route accepts
    EITHER COST_CALCULATION (manufacturing-kind) OR ABC_CALCULATION
    (service-kind) — service-layer `_resolve_engine_type` further
    discriminates by `tenant.industry == 'service'` for M9 dispatch
    (AD-19 dual-route).

    CR 12-1 L4 precedent — mirrors `require_any_role` multi-role pattern.

    Usage:
        @router.post(
            "/api/v1/calc",
            dependencies=[Depends(
                require_any_capability(
                    Capability.COST_CALCULATION, Capability.ABC_CALCULATION
                )
            )],
        )

    Raises:
        IndustryCapabilityError: 403 INDUSTRY_NOT_SUPPORTED if NONE of the
            allowed capabilities are unlocked by the tenant's industry.
            Mapped to HTTP 403 by main.py global handler.
    """
    allowed = frozenset(allowed_capabilities)

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
        except TenantSettingsNotFoundError as settings_err:
            # Treat as no industry selected → no capabilities unlocked.
            # Raise the FIRST capability as the canonical error.
            raise IndustryCapabilityError(
                tenant_id=ctx.tenant_id,
                current_industry=None,
                capability=next(iter(allowed)),
                trace_id=trace_id,
            ) from settings_err

        onboarding = dict(row.onboarding or {})
        industry_raw = onboarding.get("industry")
        try:
            industry = Industry(industry_raw) if industry_raw else None
        except ValueError:
            industry = None

        # ANY-OF semantics: pass if at least one allowed capability is
        # unlocked by the tenant's industry. Otherwise raise the FIRST
        # capability as the canonical 403 error.
        for cap in allowed:
            if industry_supports(industry, cap):
                return ctx
        raise IndustryCapabilityError(
            tenant_id=ctx.tenant_id,
            current_industry=industry,
            capability=next(iter(allowed)),
            trace_id=trace_id,
        )

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
