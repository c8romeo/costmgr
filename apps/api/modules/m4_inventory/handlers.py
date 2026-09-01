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

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass
from apps.api.core.capability import Capability, require_capability, require_role
from apps.api.core.db import get_session
from apps.api.core.db_models import AuditLog
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m4_inventory.schemas import (
    CarryChainEntry,
    CarryChainResponse,
    ClosingAuditTrailEntry,
    ClosingAuditTrailResponse,
    ClosingGuardCloseAttemptRequest,
    ClosingGuardCloseAttemptResponse,
    ClosingGuardEvaluateRequest,
    ClosingGuardEvaluateResponse,
    ClosingPeriodAuditTrailEntry,
    ClosingPeriodAuditTrailResponse,
    ClosingPeriodConfirmRequest,
    ClosingPeriodConfirmResponse,
    ClosingPeriodEvaluateResponse,
    LedgerEventCreateRequest,
    MonthlyClosingReportAuditTrailResponse,
    MonthlyClosingReportResponse,
    MonthlyClosingReportV4VerdictResponse,
    NegativeProductEntry,
    PeriodClosingResponse,
    ReversalRequestCreate,
)
from apps.api.modules.m4_inventory.services.closing_guard_service import (
    ClosingGuardService,
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
    # Walking Skeleton (2026-08-16): read industry from
    # `tenant_settings.onboarding` JSONB (canonical SSOT) — see
    # `_build_ledger_service` for the rationale.
    from sqlalchemy import text

    _industry_q = await session.execute(
        text("SELECT onboarding->>'industry' " "FROM tenant_settings WHERE tenant_id = :tid"),
        {"tid": str(ctx.tenant_id)},
    )
    industry: str | None = _industry_q.scalar_one_or_none()
    if industry is None:
        industry = ctx.industry

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
        decisions=[CarryDecisionResponse(**d) for d in result["decisions"]],
        opening_inventory=result["opening_inventory"],
        chain_depth=result["chain_depth"],
        trigger_source=result["trigger_source"],
        trace_id=result["trace_id"],
    )


# ── Story 5.2 — Ledger routes ────────────────────────────────


async def _build_ledger_service(session: AsyncSession, ctx: TenantContext) -> LedgerService:
    """Construct `LedgerService` with tenant industry loaded.

    Walking Skeleton (2026-08-16): the original implementation routed
    through `SettingsService.get_or_create_settings()` which doesn't
    exist (the real method is `get_tenant_settings(tenant_id=...)`),
    and `SettingsService` doesn't accept `tenant_id` (it's stateless
    — RLS via `SET LOCAL app.current_tenant_id`). Read industry
    directly from `tenant_settings` via the session; fall back to
    `ctx.industry` (JWT app_metadata) when the row is absent.
    """
    from sqlalchemy import text

    # Walking Skeleton (2026-08-16): read industry directly from the
    # `tenant_settings.onboarding` JSONB (matches `m0_onboarding`'s
    # canonical storage). TenantSettings has no `.industry` column —
    # that lives on `tenants.industry`, which is the WRONG SSOT for
    # tenant-side onboarding wizard state.
    result = await session.execute(
        text("SELECT onboarding->>'industry' " "FROM tenant_settings WHERE tenant_id = :tid"),
        {"tid": str(ctx.tenant_id)},
    )
    industry: str | None = result.scalar_one_or_none()
    if industry is None:
        industry = ctx.industry
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
    _capability: None = Depends(require_capability(Capability.INVENTORY_LEDGER)),
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
    _capability: None = Depends(require_capability(Capability.INVENTORY_LEDGER)),
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
    _capability: None = Depends(require_capability(Capability.INVENTORY_LEDGER)),
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
    summary="DEPRECATED — use /api/v1/close/reversal-requests. M11 actual write route is SSOT.",
    deprecated=True,
    description=(
        "DEPRECATED since Story 11.1 (Epic 11). The M11 actual write route is "
        "`POST /api/v1/close/reversal-requests` (see `apps/api/modules/m11_close/handlers.py`). "
        "This endpoint remains as a 501 forward-fill for backward compatibility "
        "with Story 5.2 AC #6 clients until the deprecation is fully retired in "
        "a follow-up sprint. The `Deprecation` header is set so clients can "
        "discover the replacement route."
    ),
)
async def request_reversal(
    payload: ReversalRequestCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.INVENTORY_LEDGER)),
    _role: None = Depends(require_role("owner")),
) -> dict[str, str]:
    """M4 reversal entrypoint stub (DEPRECATED since Story 11.1).

    AC #6 + OQ5 cj-style default: this endpoint emits the audit marker
    `inventory_ledger_reversal_requested` and verifies the target event
    exists for the tenant. The actual reversal sequence INSERT
    (negating row + optional corrected row) is owned by Epic 11 module
    authority at `POST /api/v1/close/reversal-requests` (M11 module).
    Until M11 ships, the endpoint returns 501.

    Deprecation: this route is the M4 forward-fill; the M11 SSOT is
    `POST /api/v1/close/reversal-requests`. The `Deprecation: true`
    header is emitted so clients can discover the replacement.

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


# ── Story 5.3 — Closing guard routes (T6.1 + T6.2) ────────────


async def _build_closing_guard_service(
    session: AsyncSession, ctx: TenantContext
) -> ClosingGuardService:
    """Construct `ClosingGuardService` with tenant industry loaded.

    Walking Skeleton (2026-08-16): same fix as
    `_build_ledger_service` — read industry from
    `tenant_settings.onboarding` JSONB (canonical SSOT) instead of a
    mis-named `SettingsService.get_or_create_settings().industry`
    (tenant_settings has no `industry` column — that lives on
    `tenants.industry`, which is the WRONG SSOT for wizard state).
    """
    from sqlalchemy import text

    result = await session.execute(
        text("SELECT onboarding->>'industry' " "FROM tenant_settings WHERE tenant_id = :tid"),
        {"tid": str(ctx.tenant_id)},
    )
    industry_raw: str | None = result.scalar_one_or_none()
    if industry_raw is None:
        industry_raw = ctx.industry

    from packages.services.m0_onboarding.industry_menu import Industry

    industry_enum: Industry | None = None
    if industry_raw is not None:
        try:
            industry_enum = Industry(industry_raw)
        except (ValueError, KeyError):
            industry_enum = None

    return ClosingGuardService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry_enum,
        trace_id=ctx.trace_id,
    )


@router.post(
    "/closing-guard/evaluate",
    response_model=ClosingGuardEvaluateResponse,
    status_code=200,
    summary="Closing invariant read-only check (Story 5.3 AC #2 + AC #4)",
)
async def evaluate_closing_guard(
    payload: ClosingGuardEvaluateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.INVENTORY_LEDGER)),
) -> ClosingGuardEvaluateResponse:
    """Read-only closing ≥ 0 invariant check (PRD §F4.2 + §V3).

    Returns the ClosingInvariant NamedTuple fields in wire format.
    UI uses this for the [수불부] tab red banner + manual edit reject
    gate (Story 5.3 T9 frontend wire).

    For service-only tenants: guard_enabled=False, code='EMPTY_PERIOD'.
    """
    guard_svc = await _build_closing_guard_service(session, ctx)
    invariant = await guard_svc.evaluate_closing_guard(period_key=payload.period_key)

    closing_wire = {str(pid): f"{qty:f}" for pid, qty in invariant.closing_per_product.items()}
    negative_products = [
        NegativeProductEntry(
            product_id=str(pid),
            closing_qty=f"{qty:f}",
        )
        for pid, qty in invariant.negative_products.items()
    ]
    banner_ko = ""
    if invariant.code == "NEGATIVE_CLOSING":
        banner_ko = _format_banner_ko(invariant)

    return ClosingGuardEvaluateResponse(
        period_key=payload.period_key,
        code=invariant.code,
        closing_per_product=closing_wire,
        negative_products=negative_products,
        guard_enabled=invariant.guard_enabled,
        banner_ko=banner_ko,
        trace_id=ctx.trace_id,
    )


@router.post(
    "/closing-guard/close-attempt",
    response_model=ClosingGuardCloseAttemptResponse,
    status_code=200,
    summary="Close-time gate wire — additive over 4-2 is_blocked (Story 5.3 AC #5)",
)
async def request_close_attempt(
    payload: ClosingGuardCloseAttemptRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.INVENTORY_CLOSING_GUARD)),
    _role: None = Depends(require_role("owner")),
) -> ClosingGuardCloseAttemptResponse:
    """Close-time gate wire (PRD §F4.2 + §V3 — Story 5.3 AC #5).

    Additive over Story 4-2 is_blocked → 409 MONTHLY_INPUT_BLOCKED.
    When invariant.code='NEGATIVE_CLOSING', raises 409
    ClosingGuardNegativeInventoryError → 409 NEGATIVE_CLOSING_INVENTORY.
    """
    guard_svc = await _build_closing_guard_service(session, ctx)
    result = await guard_svc.request_close_attempt(
        period_key=payload.period_key,
        actor_id=ctx.user_id,
    )
    return ClosingGuardCloseAttemptResponse(
        allowed=result["allowed"],
        period_key=result["period_key"],
        closing_per_product=result["closing_per_product"],
        invariant_code=result["invariant_code"],
        trace_id=ctx.trace_id,
    )


@router.get(
    "/closing-guard/audit-trail",
    response_model=ClosingAuditTrailResponse,
    status_code=200,
    summary="Closing-guard audit log emission trace (Story 5.3 P1 review patch — observability)",
)
async def get_closing_guard_audit_trail(
    period_key: str = Query(..., description="AD-24 typed 'YYYY-MM' fiscal key"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.INVENTORY_LEDGER)),
) -> ClosingAuditTrailResponse:
    """Closing-guard audit log query (CR 1.1 observability).

    Returns `audit_logs` entries filtered by:
    - `tenant_id` (RLS predicate — current tenant only)
    - `payload->>'period_key' = period_key` (JSONB extraction)
    - `action IN ('closing_guard_violated', 'closing_guard_passed',
                  'v3_closing_invariant_verified')`

    Read-only query — NO owner role required per P1 spec.
    Capability gate: INVENTORY_LEDGER (manufacturing-kind industries).

    The query uses the `idx_closing_guard_audit` index added by Alembic
    0016 (Alembic Story 5.3 P3 review patch) for tenant-scoped
    period_key lookups.
    """
    rows = (
        (
            await session.execute(
                select(AuditLog)
                .where(
                    AuditLog.tenant_id == ctx.tenant_id,
                    AuditLog.target_table == ActionClass.CLOSING_GUARD.value,
                    AuditLog.action.in_(
                        [
                            "closing_guard_violated",
                            "closing_guard_passed",
                            "v3_closing_invariant_verified",
                        ]
                    ),
                    AuditLog.payload["period_key"].astext == period_key,
                )
                .order_by(AuditLog.occurred_at.desc())
            )
        )
        .scalars()
        .all()
    )

    entries = [
        ClosingAuditTrailEntry(
            id=str(r.id),
            tenant_id=str(r.tenant_id) if r.tenant_id is not None else None,
            actor_id=str(r.actor_id) if r.actor_id is not None else None,
            action=r.action,
            target_table=r.target_table,
            target_id=str(r.target_id) if r.target_id is not None else None,
            reason=r.reason,
            payload=dict(r.payload or {}),
            occurred_at=r.occurred_at.isoformat() if r.occurred_at else "",
        )
        for r in rows
    ]
    return ClosingAuditTrailResponse(
        period_key=period_key,
        entries=entries,
        trace_id=ctx.trace_id,
    )


def _format_banner_ko(invariant) -> str:
    """Format the Korean red banner from a ClosingInvariant NamedTuple.

    Lazy import — avoid circular dependency on
    packages.services.m4_inventory.closing_guard.
    """
    from packages.services.m4_inventory.closing_guard import (
        format_negative_closing_banner_ko,
    )

    return format_negative_closing_banner_ko(invariant)


# ─────────────────────────────────────────────────────────────
# Story 6.1 — Closing Period Service routes (3 NEW)
# ─────────────────────────────────────────────────────────────


@router.get(
    "/closing-period/status",
    response_model=ClosingPeriodEvaluateResponse,
    status_code=200,
    summary="Read-only closing-period status check (Story 6.1 T5.1)",
)
async def get_closing_period_status(
    period_key: str = Query(..., description="AD-24 typed 'YYYY-MM' fiscal key"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT)),
) -> ClosingPeriodEvaluateResponse:
    """Closing-period status check (PRD §F4.3 + §V4 — read-only).

    Returns `ClosingPeriodResult` NamedTuple wrapped in response envelope
    with status + allowed + closing_per_product + closing_snapshot_count +
    ledger_event_count + period_key.
    """
    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodService,
    )

    cp_svc = ClosingPeriodService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=ctx.trace_id,
        industry=ctx.industry,
    )
    result = await cp_svc.evaluate_closing_period(period_key)
    return ClosingPeriodEvaluateResponse(
        status=result.status,
        allowed=result.allowed,
        closing_per_product={
            str(pid): f"{qty:f}" for pid, qty in result.closing_per_product.items()
        },
        closing_snapshot_count=result.closing_snapshot_count,
        ledger_event_count=result.ledger_event_count,
        period_key=result.period_key,
        trace_id=ctx.trace_id,
    )


@router.post(
    "/closing-period/confirm",
    response_model=ClosingPeriodConfirmResponse,
    status_code=200,
    summary="Close-time hook — confirm closing period (Story 6.1 T5.2)",
)
async def post_closing_period_confirm(
    payload: ClosingPeriodConfirmRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT)),
    _role: None = Depends(require_role("owner")),
) -> ClosingPeriodConfirmResponse:
    """Confirm closing period (PRD §F4.3 + AD-6 fiscal-period close lock).

    Atomicity:
    - SELECT FOR UPDATE on monthly_input_periods (CR 5.3 P4 patch)
    - Idempotent no-op skip on already-closed (CR 1.1 lesson)
    - Audit-first emit (closing_period_confirmed) before commit
    """
    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodService,
    )

    cp_svc = ClosingPeriodService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=ctx.trace_id,
        industry=ctx.industry,
    )
    result = await cp_svc.confirm_closing_period(
        payload.period_key,
        actor_id=ctx.user_id,
    )
    return ClosingPeriodConfirmResponse(
        confirmed=result["confirmed"],
        closing_snapshot_count=result["closing_snapshot_count"],
        period_key=result["period_key"],
        finalized_at=result["finalized_at"],
        trace_id=ctx.trace_id,
    )


@router.get(
    "/closing-period/audit-trail",
    response_model=ClosingPeriodAuditTrailResponse,
    status_code=200,
    summary="Closing-period audit log query (Story 6.1 T5.3 — observability)",
)
async def get_closing_period_audit_trail(
    period_key: str = Query(..., description="AD-24 typed 'YYYY-MM' fiscal key"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT)),
) -> ClosingPeriodAuditTrailResponse:
    """Closing-period audit log query (CR 1.1 observability).

    Returns `audit_logs` entries where target_table='closing_period' for
    the current period_key, ordered by occurred_at DESC, capped at 10.
    """
    from apps.api.modules.m4_inventory.services.closing_period_service import (
        ClosingPeriodService,
    )

    cp_svc = ClosingPeriodService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=ctx.trace_id,
        industry=ctx.industry,
    )
    rows = await cp_svc.get_closing_period_audit_trail(period_key)
    return ClosingPeriodAuditTrailResponse(
        period_key=period_key,
        entries=[
            ClosingPeriodAuditTrailEntry(
                action=r["action"],
                payload=r["payload"],
                occurred_at=r["occurred_at"],
            )
            for r in rows
        ],
        trace_id=ctx.trace_id,
    )


# ─────────────────────────────────────────────────────────────
# Story 6.2 — Monthly Closing Report routes (3 NEW)
# ─────────────────────────────────────────────────────────────


@router.get(
    "/monthly-closing-report",
    response_model=MonthlyClosingReportResponse,
    status_code=200,
    summary="Read-only monthly closing report aggregator (Story 6.2 AC #1)",
)
async def get_monthly_closing_report(
    period_key: str = Query(..., description="AD-24 typed 'YYYY-MM' fiscal key"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT)),
) -> MonthlyClosingReportResponse:
    """Monthly Closing Report aggregator (PRD §F5 + §F5.2).

    Read-only 3-source join (D1 결정, 2026-08-08):
    1. closing_snapshot ledger events (6-1 wire).
    2. inventory_ledger 전체 events (5-2 wire).
    3. monthly_input_periods.opening_inventory JSONB (5-1 wire).
    + 환율 source from `tenant_settings.baseline.currency_pair`.

    NOTE (bmad-code-review H7 결정, 2026-08-08): response_model wire
    shape 가 FastAPI boundary 에서 enforce.
    """
    from apps.api.modules.m4_inventory.services.monthly_closing_report_service import (
        MonthlyClosingReportService,
    )

    mcr_svc = MonthlyClosingReportService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=ctx.trace_id,
        industry=ctx.industry,
    )
    return await mcr_svc.get_monthly_closing_report(
        period_key,
        actor_id=ctx.user_id,
    )


@router.get(
    "/monthly-closing-report/audit-trail",
    response_model=MonthlyClosingReportAuditTrailResponse,
    status_code=200,
    summary="Monthly closing report audit log query (Story 6.2 T3.2 — observability)",
)
async def get_monthly_closing_report_audit_trail(
    period_key: str = Query(..., description="AD-24 typed 'YYYY-MM' fiscal key"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT)),
) -> MonthlyClosingReportAuditTrailResponse:
    """Monthly closing report audit log query (CR 1.1 observability).

    Returns `audit_logs` entries where:
    - `target_table IN ('monthly_closing_report', 'closing_period')` OR
    - `target_table = 'verification_log'` AND
      `payload->>'action_name' = 'verify_v4_closing_period_consistency'`
    for the current period_key, ordered by occurred_at DESC, capped at 10.

    NOTE (bmad-code-review H3 결정, 2026-08-08): SQL 컬럼은
    `MonthlyClosingReportAuditEntry { id, action, actor_id, created_at,
    payload }` mirror 와 정렬 (bmad-code-review 결정).
    """
    from apps.api.modules.m4_inventory.services.monthly_closing_report_service import (
        MonthlyClosingReportService,
    )

    mcr_svc = MonthlyClosingReportService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=ctx.trace_id,
        industry=ctx.industry,
    )
    rows = await mcr_svc.get_monthly_closing_report_audit_trail(period_key)
    return {
        "period_key": period_key,
        "entries": rows,
        "trace_id": ctx.trace_id,
    }


@router.get(
    "/monthly-closing-report/v4-verdict",
    response_model=MonthlyClosingReportV4VerdictResponse,
    status_code=200,
    summary="V4 closing-period-consistency verdict read-only (Story 6.2 T3.3)",
)
async def get_monthly_closing_report_v4_verdict(
    period_key: str = Query(..., description="AD-24 typed 'YYYY-MM' fiscal key"),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT)),
) -> MonthlyClosingReportV4VerdictResponse:
    """V4 closing-period-consistency verdict read-only (PRD §V4).

    3-source aggregate verification (D1 결정, 2026-08-08):
    ledger + closing_snapshot + product_whitelist. V4 contract 에서
    fiscal_period_snapshots 제외 (PRD §6.1 산식 체인이 KRW 임).

    NOTE (bmad-code-review H2 결정, 2026-08-08): 응답 envelope 는
    `{period_key, verdict, trace_id}` wrapper. Panel 이
    `response.verdict.status` discriminator 검사.
    """
    from apps.api.modules.m4_inventory.services.monthly_closing_report_service import (
        MonthlyClosingReportService,
    )

    mcr_svc = MonthlyClosingReportService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=ctx.trace_id,
        industry=ctx.industry,
    )
    verdict = await mcr_svc.verify_monthly_closing_report_v4(
        period_key,
        actor_id=ctx.user_id,
    )
    return {
        "period_key": period_key,
        "verdict": dict(verdict),
        "trace_id": ctx.trace_id,
    }


# ─────────────────────────────────────────────────────────────
# Story 6.3 — Closing PDF Export routes (1 NEW POST)
# ─────────────────────────────────────────────────────────────

# B9: canonical AD-24 period_key pattern.
_PERIOD_KEY_PATTERN: str = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.post(
    "/monthly-closing-report/export-pdf",
    response_model=None,
    status_code=200,
    summary="Export monthly closing period as PDF/A4 (Story 6.3 AC #1)",
    responses={
        200: {"description": "PDF byte stream (application/pdf)"},
        422: {"description": "CLOSING_PDF_EXPORT_INVALID_INDUSTRY"},
        409: {"description": "CLOSING_PDF_EXPORT_SIZE_EXCEEDED"},
        500: {"description": "CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR"},
    },
)
async def export_closing_pdf(
    period_key: str = Query(
        ...,
        pattern=_PERIOD_KEY_PATTERN,
        description="AD-24 typed 'YYYY-MM' fiscal key (B9 Pydantic regex)",
    ),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(require_capability(Capability.MONTHLY_CLOSING_REPORT)),
) -> Response:
    """Closing PDF Export — PDF/A4 byte stream (PRD §F6.3).

    B8: industry is no longer a query parameter. Service layer
    resolves industry from `tenant_settings.baseline.industry` so
    caller cannot spoof a different industry. `TenantContext`
    exposes the resolved industry for the service to consume.

    B3: period_key is sanitized for Content-Disposition `filename=`
    via the pure kernel `escape_content_disposition_filename`
    helper, and CRLF/quote/backslash are stripped.

    Returns:
        Response with Content-Type: application/pdf + Content-Disposition:
        attachment; filename="closing-{period_key}.pdf".
    """
    from apps.api.modules.m4_inventory.services.closing_pdf_export_service import (
        ClosingPdfExportService,
    )
    from packages.services.m4_inventory.closing_pdf_export import (
        escape_content_disposition_filename,
    )

    # B8: resolve industry from tenant context (server-side).
    # If TenantContext does not yet expose `industry`, fall back to
    # reading tenant_settings via a helper; for now we accept it as
    # a required field on the context and return 422 if absent.
    industry = getattr(ctx, "industry", None)
    if industry is None:
        # Defense-in-depth: re-raise as 422 via the typed envelope.
        from apps.api.modules.m4_inventory.services.closing_pdf_export_service import (
            ClosingPdfExportInvalidIndustryError,
        )

        raise ClosingPdfExportInvalidIndustryError(
            tenant_id=ctx.tenant_id,
            period_key=period_key,
            industry="",
            trace_id=ctx.trace_id,
        )

    svc = ClosingPdfExportService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=ctx.trace_id,
        actor_id=ctx.user_id,
    )
    result = await svc.export_closing_pdf(period_key, industry=industry)
    safe_name = escape_content_disposition_filename(period_key)
    return Response(
        content=result["pdf_bytes"],
        media_type="application/pdf",
        headers={
            "Content-Disposition": (f'attachment; filename="closing-{safe_name}.pdf"'),
            "X-Closing-Pdf-Export-Size": str(result["pdf_size_bytes"]),
            "X-Closing-Pdf-Export-Is-Empty": str(result["is_empty"]).lower(),
            "X-Closing-Pdf-Export-Industry": industry,
        },
    )
