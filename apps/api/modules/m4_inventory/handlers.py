"""apps.api.modules.m4_inventory.handlers — M4 inventory FastAPI routes.

Story 5.1 — opening inventory auto-carry chain manual trigger.

Route:
- POST /api/v1/inventory/opening-carry/{period_id}
    → Manual carry chain trigger (PRD §F4.1 backup path when
      INVENTORY_PERIOD_CHAIN_LIMIT depth exceeded or when operator
      wants to force a fresh carry after data fix).

Defense in depth:
- require_role("owner") — AD-10.
- Audit-first wire: OpeningCarryService.trigger_carry_chain_for_period
  emits audit_logs row BEFORE the data write (CR 1.1 lesson).

Error contract (AD-15 §4 envelope):
- 200 — carry chain applied, returns CarryChainResultResponse
- 400 INVALID_PAYLOAD — service-side shape validation failure
- 403 FORBIDDEN_ROLE — non-owner caller
- 404 MONTHLY_INPUT_NOT_FOUND — period_id missing for tenant
- 422 MONTHLY_INPUT_CARRY_PREV_PERIOD_NOT_FOUND — prev_period_key missing
- 422 MONTHLY_INPUT_CARRY_CHAIN_LIMIT — depth > 12 (manual trigger
  still applies — but the carry itself is rejected because the chain
  cannot resolve a fresh prev without walking beyond limit)
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import require_role
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
    TenantSettingsNotFoundError,
)
from apps.api.modules.m4_inventory.services.opening_carry_service import (
    OpeningCarryService,
)

router = APIRouter(prefix="/api/v1/inventory", tags=["m4-inventory"])


# ── Response ─────────────────────────────────────────────────
class CarryDecisionResponse(BaseModel):
    """Single carry decision in the result envelope."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    opening_qty: str
    is_stale: bool
    recompute: bool


class CarryChainResultResponse(BaseModel):
    """Manual trigger result envelope.

    Mirrors the dict returned by
    `OpeningCarryService.trigger_carry_chain_for_period`.
    """

    model_config = ConfigDict(extra="forbid")

    period_id: str
    period_key: str
    prev_period_key: str | None
    decisions: list[CarryDecisionResponse]
    opening_inventory: dict[str, str]
    chain_depth: int
    trigger_source: str
    trace_id: str


# ── Manual trigger route ─────────────────────────────────────
@router.post(
    "/opening-carry/{period_id}",
    response_model=CarryChainResultResponse,
    status_code=200,
    summary="Trigger opening inventory carry chain manually (Story 5.1)",
)
async def trigger_opening_carry(
    period_id: uuid.UUID,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _role: None = Depends(require_role("owner")),
) -> CarryChainResultResponse:
    """Manual carry chain trigger.

    Use cases:
    - Initial bootstrap when 5-1 backend first lands (migrate from
      3.3 MVP default 0 → auto-carry).
    - Operator data fix: re-trigger after prev period row mutation.
    - Beyond 12-period chain (depth guard rejects automatic, operator
      can manually invoke per-period to extend).
    """
    # Load industry from tenant_settings (m2_input_service uses this pattern)
    settings_svc = SettingsService(session, tenant_id=ctx.tenant_id)
    try:
        settings = await settings_svc.get_or_create_settings()
        industry = settings.industry
    except TenantSettingsNotFoundError:
        industry = None

    carry_svc = OpeningCarryService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=ctx.trace_id,
    )
    result = await carry_svc.trigger_carry_chain_for_period(
        period_id,
        actor_id=ctx.user_id,
    )

    return CarryChainResultResponse(
        period_id=result["period_id"],
        period_key=result["period_key"],
        prev_period_key=result["prev_period_key"],
        decisions=[
            CarryDecisionResponse(**d) for d in result["decisions"]
        ],
        opening_inventory=result["opening_inventory"],
        chain_depth=result["chain_depth"],
        trigger_source=result["trigger_source"],
        trace_id=result["trace_id"],
    )
