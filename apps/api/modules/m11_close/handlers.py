"""apps.api.modules.m11_close.handlers — M11 closure module FastAPI routes.

Story 11.1 — M11 module authority reverse-direction service owner.
Wires the AD-22 reversal sequence (sign-negating + corrected row) +
AD-25 cache invalidation publisher.

Routes (3 NEW):
- POST /api/v1/close/reversal-requests
    → Owner-only AD-22 reversal sequence (sign-negating + optional
      corrected row + AD-25 publish + audit-first emit).
      201 REVERSAL_COMPLETED on success.
- GET /api/v1/close/reversal-requests/{correction_group_id}
    → Observability read of the reversal pair (sign-negating + corrected
      rows) sharing correction_group_id.
- POST /api/v1/close/cache-invalidation
    → AD-25 cache invalidation publish endpoint (1-channel: ai_cache).
      M11 reversal sequence wires this internally; this endpoint is
      available for the M10 AI cache consumer to flush on demand.

Defense in depth:
- require_capability(Capability.REVERSAL_REQUEST) — manufacturing 3종 ✅
  / service-only ❌ (PRD §F11.3 PRISM gate).
- require_role("owner") — AD-10 owner-only mutations.
- Audit-first wire (CR 1.1): ReversalService emits
  `m11_reversal_handler_invoked` → `inventory_ledger_reversal_logged` →
  `cache_invalidation_published` audit rows BEFORE the data writes.
- AD-25 1-channel wire: channel FROZENSET = `{'ai_cache'}`.

Error contract (AD-15 §4 envelope):
- 201 REVERSAL_COMPLETED — success with correction_group_id + history
- 400 INVALID_PAYLOAD — service-side shape validation failure
- 403 FORBIDDEN_ROLE — non-owner caller
- 403 INDUSTRY_NOT_SUPPORTED — service-only tenant attempted reversal
  (capability gate)
- 403 REVERSAL_REJECTED — capability / actor / target_reversibility gate
- 403 REVERSAL_UNAUTHORIZED — caller role mismatch
- 404 REVERSAL_TARGET_NOT_FOUND — target_event_id not in tenant
- 422 INVALID_CACHE_INVALIDATION_CHANNEL — channel not in
  ALLOWED_CHANNELS (POST /cache-invalidation)
- 422 REVERSAL_DUPLICATE — (tenant_id, reverses_event_id) UNIQUE
  constraint violation (re-reversal)
- 422 LOCKED_PERIOD_REVERSAL_REJECTED — period_status='locked'
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Path, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.cache_invalidation_publisher import (
    ALLOWED_CHANNELS,
    CacheInvalidationPublisher,
)
from apps.api.core.capability import Capability, require_capability, require_role
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m0_onboarding.services.settings_service import (
    SettingsService,
    TenantSettingsNotFoundError,
)
from apps.api.modules.m11_close.services.reversal_service import (
    ReversalService,
)

router = APIRouter(prefix="/api/v1/close", tags=["m11-close"])


def _resolve_trace_id(ctx: TenantContext, request: Request) -> str:
    """Resolve trace_id with fallback for fleet-wide TenantContext.trace_id bug.

    W11 defer — `TenantContext` does NOT carry `trace_id` (it's a pre-mvp
    frozen dataclass). The m4_inventory module uses `ctx.trace_id` directly
    which is a latent bug fixed in 11-3 fleet-wide. For 11-1, we add a
    per-route fallback here that:
    1. Tries `ctx.trace_id` if the attribute exists (forward-compat).
    2. Falls back to `request.state.trace_id` if set by middleware.
    3. Generates a fresh `uuid4()` as last resort.

    This keeps the m11_close routes consistent with the existing pattern
    (m4_inventory) while suppressing the AttributeError that would
    otherwise fire at request time.
    """
    trace_id = getattr(ctx, "trace_id", None)
    if trace_id:
        return str(trace_id)
    request_trace_id = getattr(request.state, "trace_id", None)
    if request_trace_id:
        return str(request_trace_id)
    return str(uuid.uuid4())


# ── Request schemas ──────────────────────────────────────────
class ReversalCreateRequest(BaseModel):
    """POST /api/v1/close/reversal-requests body shape."""

    model_config = ConfigDict(extra="forbid")

    target_event_id: uuid.UUID = Field(
        ...,
        description="inventory_ledger.event_id to reverse (AD-22 sign-negating target)",
    )
    reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Free-text user-provided justification (Korean SSOT OK)",
    )
    corrected_qty: Decimal | None = Field(
        default=None,
        ge=Decimal("0"),
        decimal_places=4,
        max_digits=18,
        description="Optional corrected qty (AD-22 sequence step 2). "
        "Requires corrected_period_key when set. "
        "Banker's rounding (ROUND_HALF_EVEN) at QTY_QUANTUM = NUMERIC(18,4) "
        "to keep parity with the TS mirror (CR 0-4).",
    )
    corrected_period_key: str | None = Field(
        None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Optional corrected period key (AD-24 typed 'YYYY-MM'). "
        "Requires corrected_qty when set.",
    )


class CacheInvalidationPublishRequest(BaseModel):
    """POST /api/v1/close/cache-invalidation body shape (AD-25 1-channel)."""

    model_config = ConfigDict(extra="forbid")

    channel: str = Field(
        default="ai_cache",
        description="Cache invalidation channel. Must be in ALLOWED_CHANNELS "
        "(`frozenset({'ai_cache'})` for Story 11.1 wire).",
    )
    event_id: uuid.UUID = Field(
        ...,
        description="invalidation trigger event_id (typically inventory_ledger.event_id)",
    )
    correction_group_id: uuid.UUID = Field(
        ...,
        description="correction_group_id linking the reversal pair",
    )


# ── Response schemas ─────────────────────────────────────────
class ReversalHistoryEntry(BaseModel):
    """Single row in the reversal_history list."""

    model_config = ConfigDict(extra="forbid")

    event_id: str
    tenant_id: str
    product_id: str
    period_key: str
    event_type: str
    qty: str | None
    reverses_event_id: str | None
    correction_group_id: str | None
    reversal_of_period_key: str | None
    trace_id: str


class ReversalCreateResponse(BaseModel):
    """POST /api/v1/close/reversal-requests response envelope."""

    model_config = ConfigDict(extra="forbid")

    correction_group_id: str
    negating_event_id: str
    corrected_event_id: str | None
    target_event_id: str
    reversal_history: list[ReversalHistoryEntry]
    trace_id: str
    cache_invalidation_receipt: dict[str, str]


class ReversalHistoryResponse(BaseModel):
    """GET /api/v1/close/reversal-requests/{correction_group_id} response."""

    model_config = ConfigDict(extra="forbid")

    correction_group_id: str
    reversal_history: list[ReversalHistoryEntry]
    trace_id: str


class CacheInvalidationPublishResponse(BaseModel):
    """POST /api/v1/close/cache-invalidation response envelope."""

    model_config = ConfigDict(extra="forbid")

    channel: str
    tenant_id: str
    event_id: str
    correction_group_id: str
    published_at: str
    trace_id: str


# ── Helpers ──────────────────────────────────────────────────
async def _build_reversal_service(
    session: AsyncSession, ctx: TenantContext, request: Request
) -> ReversalService:
    """Construct `ReversalService` with tenant industry loaded.

    Mirrors the 5-2 ledger handler pattern (industry loaded from
    tenant_settings; None for service-only tenants). Uses
    `_resolve_trace_id(ctx, request)` for the W11 fleet-wide
    `TenantContext.trace_id` fallback.
    """
    settings_svc = SettingsService(session, tenant_id=ctx.tenant_id)
    try:
        settings = await settings_svc.get_or_create_settings()
        industry = settings.industry
    except TenantSettingsNotFoundError:
        industry = None
    return ReversalService(
        session,
        tenant_id=ctx.tenant_id,
        industry=industry,
        trace_id=_resolve_trace_id(ctx, request),
    )


def _capability_granted_for_industry(industry: Any | None) -> bool:
    """PRISM gate — REVERSAL_REQUEST is manufacturing 3종 ✅ only.

    PRD §F11.3 + capability matrix v1.10: REVERSAL_REQUEST is granted
    to the 3 Industry values that have a manufacturing footprint
    (manufacturing / manufacturing_service / manufacturing_service_other).
    service-only tenants are denied.

    Returns:
        True if the industry is in the manufacturing 3종 whitelist.
    """
    if industry is None:
        return False
    industry_value = getattr(industry, "value", None) or str(industry)
    return industry_value in {
        "manufacturing",
        "manufacturing_service",
        "manufacturing_service_other",
    }


# ── POST /api/v1/close/reversal-requests (AD-22 wire) ────────
@router.post(
    "/reversal-requests",
    response_model=ReversalCreateResponse,
    status_code=201,
    summary="AD-22 reversal sequence (sign-negating + optional corrected row) — Story 11.1",
)
async def create_reversal_request(
    payload: ReversalCreateRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.REVERSAL_REQUEST)
    ),
    _role: None = Depends(require_role("owner")),
) -> ReversalCreateResponse:
    """Execute AD-22 9-step reversal sequence.

    Returns 201 REVERSAL_COMPLETED with:
    - correction_group_id (links sign-negating + corrected rows)
    - negating_event_id (new row, qty = -target.qty)
    - corrected_event_id (new row, when corrected_qty/period_key are set)
    - reversal_history: list of all rows sharing correction_group_id
    - cache_invalidation_receipt: AD-25 publisher receipt (channel='ai_cache')

    Raises (handler-level envelope exceptions dispatched via main.py):
    - 403 REVERSAL_REJECTED — capability / authorization gate
    - 422 LOCKED_PERIOD_REVERSAL_REJECTED — period_status='locked'
    - 422 REVERSAL_DUPLICATE — (tenant_id, reverses_event_id) UNIQUE violation
    - 404 REVERSAL_TARGET_NOT_FOUND — target_event_id missing
    """
    reversal_svc = await _build_reversal_service(session, ctx, request)

    # PRISM gate (manufacturing 3종 ✅ / service-only ❌).
    capability_granted = _capability_granted_for_industry(reversal_svc.industry)

    response = await reversal_svc.execute_reversal(
        target_event_id=payload.target_event_id,
        reason=payload.reason,
        actor_id=ctx.user_id,
        capability_granted=capability_granted,
        corrected_qty=payload.corrected_qty,
        corrected_period_key=payload.corrected_period_key,
    )

    await session.commit()

    return ReversalCreateResponse(
        correction_group_id=str(response.correction_group_id),
        negating_event_id=str(response.negating_event_id),
        corrected_event_id=(
            str(response.corrected_event_id)
            if response.corrected_event_id
            else None
        ),
        target_event_id=str(response.target_event_id),
        reversal_history=[
            ReversalHistoryEntry(**entry) for entry in response.reversal_history
        ],
        trace_id=response.trace_id,
        cache_invalidation_receipt=response.cache_invalidation_receipt,
    )


# ── GET /api/v1/close/reversal-requests/{correction_group_id} ─
@router.get(
    "/reversal-requests/{correction_group_id}",
    response_model=ReversalHistoryResponse,
    status_code=200,
    summary="Read reversal pair (sign-negating + corrected) by correction_group_id",
)
async def get_reversal_history(
    request: Request,
    correction_group_id: uuid.UUID = Path(
        ...,
        description="correction_group_id linking the reversal pair",
    ),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.REVERSAL_REQUEST)
    ),
) -> ReversalHistoryResponse:
    """Observability read of the reversal pair.

    Returns 200 with correction_group_id + list of all rows sharing
    the correction_group_id (sign-negating + corrected).
    """
    reversal_svc = await _build_reversal_service(session, ctx, request)
    history = await reversal_svc.get_reversal_history(
        correction_group_id=correction_group_id,
    )
    return ReversalHistoryResponse(
        correction_group_id=str(correction_group_id),
        reversal_history=[
            ReversalHistoryEntry(**entry) for entry in history
        ],
        trace_id=_resolve_trace_id(ctx, request),
    )


# ── POST /api/v1/close/cache-invalidation (AD-25 PRIMARY) ────
@router.post(
    "/cache-invalidation",
    response_model=CacheInvalidationPublishResponse,
    status_code=200,
    summary="AD-25 cache invalidation publish (1-channel: ai_cache) — Story 11.1",
)
async def publish_cache_invalidation(
    payload: CacheInvalidationPublishRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.REVERSAL_REQUEST)
    ),
    _role: None = Depends(require_role("owner")),
) -> CacheInvalidationPublishResponse:
    """AD-25 cache invalidation publish endpoint.

    Wire 1-channel: `channel='ai_cache'` (M10 AI cache invalidation target).
    M11 reversal sequence wires this internally; this endpoint is also
    available for the M10 AI cache consumer to flush on demand.

    Returns 200 with the receipt envelope (channel, tenant_id, event_id,
    correction_group_id, published_at, trace_id).

    Raises (handled in main.py):
    - 422 INVALID_CACHE_INVALIDATION_CHANNEL — channel not in ALLOWED_CHANNELS
    """
    publisher = CacheInvalidationPublisher()
    receipt = publisher.publish(
        channel=payload.channel,
        tenant_id=ctx.tenant_id,
        event_id=payload.event_id,
        correction_group_id=payload.correction_group_id,
        trace_id=_resolve_trace_id(ctx, request),
        published_at=datetime.now(tz=UTC).isoformat(),
    )
    await session.commit()

    return CacheInvalidationPublishResponse(
        channel=receipt.channel,
        tenant_id=str(receipt.tenant_id),
        event_id=str(receipt.target_event_id),
        correction_group_id=str(receipt.correction_group_id),
        published_at=receipt.published_at,
        trace_id=receipt.trace_id,
    )


__all__ = [
    "ALLOWED_CHANNELS",
    "CacheInvalidationPublishRequest",
    "CacheInvalidationPublishResponse",
    "ReversalCreateRequest",
    "ReversalCreateResponse",
    "ReversalHistoryEntry",
    "ReversalHistoryResponse",
    "router",
]
