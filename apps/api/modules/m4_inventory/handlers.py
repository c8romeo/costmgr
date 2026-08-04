"""apps.api.modules.m4_inventory.handlers — M4 inventory FastAPI routes.

Story 5.1 — opening inventory auto-carry chain manual trigger.
Story 5.2 — append-only inventory_ledger event routes.

Routes (5-1):
- POST /api/v1/inventory/opening-carry/{period_id}
    → Manual carry chain trigger (PRD §F4.1 backup path when
      INVENTORY_PERIOD_CHAIN_LIMIT depth exceeded or when operator
      wants to force a fresh carry after data fix).

Routes (5-2 — 4 NEW):
- POST /api/v1/inventory/ledger/events
    → Operator manual INSERT (recovery / backfill entry).
      AD-22 reversal fields MUST NOT be set in 5-2 (Epic 11 owns).
- GET /api/v1/inventory/ledger/period-closing?period_key=...
    → Read-only SUM(qty) closing projection per product (PRD §6.2).
      Replaces Epic 3.3 inline projection as single source of truth
      (AC #5 swap).
- GET /api/v1/inventory/ledger/carry-chain?period_key=...&depth=N
    → Read-only recursive CTE walk of `opening_carried` events
      (Story 5.1 + 5.2 consumers). Depth bounded at 12.
- POST /api/v1/inventory/ledger/reversal-requests
    → M4 reversal entrypoint forward-fill (AD-22). Epic 11 module
      authority owns the actual reversal sequence INSERT; this
      endpoint emits the audit marker + 501 forward-fill until M11
      ships.

Defense in depth:
- require_capability(Capability.INVENTORY_LEDGER) — all 4 NEW routes
  (manufacturing 3종 ✅ / service-only ❌ per PRD §F4.1 + §6.2).
- require_role("owner") — AD-10 owner-only mutations (POST routes).
- Audit-first wire (CR 1.1): LedgerService.append_event emits
  `inventory_ledger_event_appended` audit row BEFORE the data write.
  request_reversal emits `inventory_ledger_reversal_requested` audit
  marker only (no inventory_ledger INSERT — Epic 11 ownership).

Error contract (AD-15 §4 envelope):
- 200 — success with response envelope
- 400 INVALID_PAYLOAD — service-side shape validation failure
- 403 FORBIDDEN_ROLE — non-owner caller
- 403 INDUSTRY_NOT_SUPPORTED — service-only tenant attempted
  inventory_ledger write (capability gate)
- 404 MONTHLY_INPUT_NOT_FOUND — period_id missing for tenant (5-1 route)
- 422 INVENTORY_LEDGER_INVALID_EVENT_TYPE — event_type not in 11-value
  whitelist
- 422 INVENTORY_LEDGER_PERIOD_KEY_FORMAT — period_key not 'YYYY-MM'
- 422 MONTHLY_INPUT_CARRY_PREV_PERIOD_NOT_FOUND — 5-1 carry prev missing
- 422 MONTHLY_INPUT_CARRY_CHAIN_LIMIT — depth > 12 (manual trigger)
- 500 APPEND_ONLY_LEDGER_VIOLATION — DB trigger raised on
  UPDATE/DELETE attempt (AC #3 1st axis)
- 501 INVENTORY_LEDGER_REVERSAL_NOT_YET_WIRED — Epic 11 forward-fill
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import Capability, require_capability, require_role
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
    TenantSettingsNotFoundError,
)
from apps.api.modules.m4_inventory.schemas import (
    CarryChainEntry,
    CarryChainResponse,
    LedgerEventCreateRequest,
    PeriodClosingResponse,
    ReversalRequestCreate,
)
from apps.api.modules.m4_inventory.services.ledger_service import LedgerService
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


# ── Manual trigger route (Story 5.1) ─────────────────────────
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
    _capability: None = Depends(require_capability(Capability.OPENING_INVENTORY)),
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


# ── Story 5.2 — Ledger routes ────────────────────────────────


async def _build_ledger_service(
    session: AsyncSession, ctx: TenantContext
) -> LedgerService:
    """Construct `LedgerService` with tenant industry loaded.

    Helper: identical to the pattern used by the 5-1 carry route
    (industry loaded from tenant_settings; None for service tenants).
    """
    settings_svc = SettingsService(session, tenant_id=ctx.tenant_id)
    try:
        settings = await settings_svc.get_or_create_settings()
        industry = settings.industry
    except TenantSettingsNotFoundError:
        industry = None
    return LedgerService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=ctx.trace_id,
    )


@router.post(
    "/ledger/events",
    response_model=PeriodClosingResponse,
    status_code=200,
    summary="Operator manual INSERT — append-only inventory_ledger event (Story 5.2)",
)
async def create_ledger_event(
    payload: LedgerEventCreateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.INVENTORY_LEDGER)
    ),
    _role: None = Depends(require_role("owner")),
) -> PeriodClosingResponse:
    """Operator manual INSERT entry (recovery / backfill).

    AD-2 append-only invariant: this endpoint appends ONE row to
    `inventory_ledger` (no UPDATE/DELETE possible — DB trigger fires).

    The body MUST NOT set `reverses_event_id` or `correction_group_id`
    — those are reserved for Epic 11 module authority INSERTs. The
    pure kernel `build_event_payload` accepts them as optional kwargs,
    but the handler does NOT pass them.

    Returns the closing projection for the affected (product, period)
    so the operator can immediately verify the append result.
    """
    ledger_svc = await _build_ledger_service(session, ctx)

    # payload.trace_id is honored by LedgerService.append_event internally
    # (the service mints UUIDv7 if None) — the explicit trace_id_for_emit
    # local was a remnant of an earlier wire shape. The append_event call
    # below uses payload fields directly; no local capture needed.
    await ledger_svc.append_event(
        product_id=payload.product_id,
        period_key=payload.period_key,
        event_type=payload.event_type,
        qty=payload.qty,
        source="manual_backfill",
        reverses_event_id=None,  # Epic 11 forward-fill only
        correction_group_id=None,  # Epic 11 forward-fill only
        metadata=payload.metadata,
        actor_id=ctx.user_id,
    )

    # Echo back the updated closing projection for the affected
    # (product, period) — single product is the operator's working set.
    closing_qty = await ledger_svc.query_period_closing(
        product_id=payload.product_id,
        period_key=payload.period_key,
    )
    return PeriodClosingResponse(
        period_key=payload.period_key,
        closing={str(payload.product_id): str(closing_qty)},
        trace_id=ctx.trace_id,
    )


@router.get(
    "/ledger/period-closing",
    response_model=PeriodClosingResponse,
    status_code=200,
    summary="Read-only SUM(qty) closing projection per product (Story 5.2 AC #1 + AC #5)",
)
async def get_period_closing(
    period_key: str = Query(..., description="AD-24 typed 'YYYY-MM' fiscal key"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.INVENTORY_LEDGER)
    ),
) -> PeriodClosingResponse:
    """Read-only closing projection (multi-product).

    AC #5 wire: this endpoint replaces the Epic 3.3 inline projection
    as the canonical read path. The same SQL fragment powers both
    `MonthlyInputService._compute_inventory_projection_for_state`
    warnings aggregator (T8 swap) and this HTTP route.

    Single query — `LedgerService.query_period_closing_all` aggregates
    SUM(qty) per product for the period in one round-trip.
    """
    ledger_svc = await _build_ledger_service(session, ctx)
    closing_map = await ledger_svc.query_period_closing_all(
        period_key=period_key,
    )
    closing = {str(pid): str(qty) for pid, qty in closing_map.items()}
    return PeriodClosingResponse(
        period_key=period_key,
        closing=closing,
        trace_id=ctx.trace_id,
    )


@router.get(
    "/ledger/carry-chain",
    response_model=CarryChainResponse,
    status_code=200,
    summary="Read-only recursive CTE walk of opening_carried events (Story 5.2 AC #1)",
)
async def get_carry_chain(
    product_id: uuid.UUID = Query(...),
    period_key: str = Query(..., description="Upper bound (exclusive)"),
    depth: int = Query(
        default=12,
        ge=1,
        le=12,
        description="Max recursion depth (≤ INVENTORY_PERIOD_CHAIN_LIMIT=12)",
    ),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.INVENTORY_LEDGER)
    ),
) -> CarryChainResponse:
    """Read-only carry-chain walk (recursive CTE).

    Returns `opening_carried` events ordered chronologically
    (ascending period_key) up to `depth` periods.
    """
    ledger_svc = await _build_ledger_service(session, ctx)

    raw = await ledger_svc.query_carry_chain(
        product_id=product_id,
        period_key=period_key,
    )
    # `depth` is the upper bound; actual walked depth = len(raw)
    actual_depth = min(depth, len(raw))

    entries = [
        CarryChainEntry(
            event_id=r["event_id"],
            period_key=r["period_key"],
            qty=r["qty"],
            inserted_at=r["inserted_at"],
        )
        for r in raw
    ]
    return CarryChainResponse(
        product_id=str(product_id),
        period_key=period_key,
        depth=actual_depth,
        chain=entries,
        trace_id=ctx.trace_id,
    )


@router.post(
    "/ledger/reversal-requests",
    status_code=501,  # 501 Not Implemented — Epic 11 forward-fill
    summary="M4 reversal entrypoint forward-fill (Story 5.2 AC #6; Epic 11 ships actual write)",
)
async def request_reversal(
    payload: ReversalRequestCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.INVENTORY_LEDGER)
    ),
    _role: None = Depends(require_role("owner")),
) -> dict[str, str]:
    """M4 reversal entrypoint stub.

    AC #6 + OQ5 cj-style default: this endpoint emits the audit marker
    `inventory_ledger_reversal_requested` and verifies the target event
    exists for the tenant. The actual reversal sequence INSERT
    (negating row + optional corrected row) is owned by Epic 11 module
    authority. Until M11 ships, the endpoint returns 501.

    The 501 envelope is mapped from
    `InventoryLedgerReversalNotYetWiredError` in `apps/api/main.py`.
    """
    ledger_svc = await _build_ledger_service(session, ctx)
    # request_reversal emits `inventory_ledger_reversal_requested`
    # audit marker; on success it raises 501 InventoryLedgerReversalNotYetWiredError.
    # We pass `actor_id=ctx.user_id` so the audit row carries the actor.
    await ledger_svc.request_reversal(
        event_id=payload.event_id,
        reason=payload.reason,
        actor_id=ctx.user_id,
    )
    # Unreachable: request_reversal always raises. Defensive return for
    # type-checker satisfaction (FastAPI will never serialize this).
    return {"trace_id": ctx.trace_id}
