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
from apps.api.modules.m11_close.services.close_sequence_service import (
    CloseSequenceService,
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


# ────────────────────────────────────────────────────────────────────────
# Story 11.2 — 3 NEW routes for close sequence lock
# (PRD §F11.1 + AD-6 close lock + §8.M11(a) 부분 마감 불허)
# ────────────────────────────────────────────────────────────────────────
class _CloseSequenceStepBody(BaseModel):
    """POST /api/v1/close/sequence/step-complete body shape."""

    model_config = ConfigDict(extra="forbid")
    step_name: str = Field(
        ...,
        pattern=r"^(divisions|manufacturing|abc|common)$",
        description="Stage to mark complete (divisions | manufacturing | abc | common).",
    )


class _CloseSequenceInitiateBody(BaseModel):
    """POST /api/v1/close/sequence/initiate body shape (empty body)."""

    model_config = ConfigDict(extra="forbid")


def _build_close_sequence_service(
    session: AsyncSession, ctx: TenantContext, request: Request
) -> CloseSequenceService:
    """Construct `CloseSequenceService` with trace_id."""
    return CloseSequenceService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=_resolve_trace_id(ctx, request),
    )


# ── POST /api/v1/close/sequence/initiate ─────────────────────
@router.post(
    "/sequence/initiate",
    status_code=201,
    summary="Initiate the 4-stage close sequence (Story 11.2)",
)
async def initiate_close_sequence_route(
    _payload: _CloseSequenceInitiateBody | None = None,
    request: Request = None,  # type: ignore[assignment]
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.CLOSE_SEQUENCE_LOCK)
    ),
    _role: None = Depends(require_role("owner")),
) -> dict[str, Any]:
    """Initiate the 4-stage close sequence for the current period.

    Story 11.2 PRIMARY AC. INSERTs a `fiscal_periods` row with
    `close_sequence_state='divisions'` + emits audit row
    `closing_sequence_initiated` (ActionClass.MONTHLY_CLOSING).

    Raises:
        409 CLOSE_SEQUENCE_ALREADY_INITIATED — existing fiscal_periods row.
    """
    seq_svc = _build_close_sequence_service(session, ctx, request)
    result = await seq_svc.initiate_close_sequence(
        period_key=_resolve_period_key(request, ctx),
        actor_id=ctx.user_id,
    )
    await session.commit()
    return result


# ── POST /api/v1/close/sequence/step-complete ────────────────
@router.post(
    "/sequence/step-complete",
    summary="Mark a 4-stage close sequence step as complete (Story 11.2)",
)
async def step_complete_route(
    payload: _CloseSequenceStepBody,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.CLOSE_SEQUENCE_LOCK)
    ),
    _role: None = Depends(require_role("owner")),
) -> dict[str, Any]:
    """Mark `step_name` as complete in the 4-stage sequence."""
    seq_svc = _build_close_sequence_service(session, ctx, request)
    result = await seq_svc.step_complete(
        period_key=_resolve_period_key(request, ctx),
        step_name=payload.step_name,
        actor_id=ctx.user_id,
    )
    await session.commit()
    return result


# ── GET /api/v1/close/sequence/state ─────────────────────────
@router.get(
    "/sequence/state",
    summary="Read-only close sequence state (Story 11.2)",
)
async def get_close_sequence_state_route(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.CLOSE_SEQUENCE_LOCK)
    ),
) -> dict[str, Any]:
    """Read-only check of close sequence progress."""
    seq_svc = _build_close_sequence_service(session, ctx, request)
    return await seq_svc.get_close_sequence_state(
        period_key=_resolve_period_key(request, ctx),
    )


# ── POST /api/v1/close/sequence/confirm ──────────────────────
@router.post(
    "/sequence/confirm",
    status_code=200,
    summary=(
        "Confirm the 4-stage close sequence (Story 11.2) — "
        "PRD §F11.1 PRIMARY + AC#4(b) AD-6 INSERT 거부 wire"
    ),
)
async def confirm_close_sequence_route(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.CLOSE_SEQUENCE_LOCK)
    ),
    _role: None = Depends(require_role("owner")),
) -> dict[str, Any]:
    """Confirm the 4-stage close sequence.

    Story 11.2 PRIMARY AC. PRD §F11.1 + AD-6 close lock:
      1. SELECT FOR UPDATE on fiscal_periods.
      2. partial_close_guard → 4단계 모두 완료 검증.
      3. AD-6 INSERT 거부 sanity check (NEW 3rd-sweep D3 wire).
      4. UPDATE fiscal_periods.status='closed' +
         close_sequence_state='confirmed' + closed_at=now().
      5. Audit-first emit `closing_sequence_confirmed`.

    Story 11.2 3rd-sweep cross-module orchestration note: this
    handler is intentionally scoped to the M11 fiscal_periods
    dimension. The 6-1 wire `ClosingPeriodService.confirm_closing_period`
    (monthly_input_periods.status UPDATE + closing_snapshot ledger
    INSERT + V4 verifier) runs FIRST as the orchestrator's preceding
    step. The M11 confirm ONLY runs after 6-1 has confirmed monthly
    inputs are sealed.

    Raises:
        409 PARTIAL_CLOSE_BLOCKED — 4단계 미완료.
        409 ALREADY_CONFIRMED — fiscal_periods.status='closed'.
        409 CLOSE_SEQUENCE_NOT_INITIATED — no fiscal_periods row.
    """
    seq_svc = _build_close_sequence_service(session, ctx, request)
    result = await seq_svc.confirm_close_sequence(
        period_key=_resolve_period_key(request, ctx),
        actor_id=ctx.user_id,
    )
    await session.commit()
    return result


def _resolve_period_key(request: Request, ctx: TenantContext) -> str:
    """Extract period_key from query or fall back to current month.

    Reads `?period_key=YYYY-MM` from the URL query string; falls back to
    the current UTC month if absent (system cron default).
    """
    period_key = request.query_params.get("period_key")
    if period_key:
        return period_key
    now = datetime.now(tz=UTC)
    return now.strftime("%Y-%m")


# ────────────────────────────────────────────────────────────────────────
# Story 11.3 — 4 NEW routes for snapshot persistence + reversal + reopen
# (PRD §F11.2 + AD-20 state machine + AD-22 reversal 영구화 + W2 reopen)
# ────────────────────────────────────────────────────────────────────────
#
# Note: These 4 routes delegate to services created in T3/T4/T5. The
# route shells are wired here so that the URL contract is stable
# (T3/T4/T5 implement the service bodies + tests).
#
# 4 routes (singular resource naming per spec AC #1-4):
#   POST /api/v1/close/snapshot/commit       → AD-20 state='verified'→'committed'
#                                              → SnapshotPersistenceService (T3)
#   POST /api/v1/close/snapshot/reverse      → AD-22 state='committed'→'reversed'
#                                              → ReversalExecuteService (T4)
#   POST /api/v1/close/reopen                → W2 reopen flow
#                                              → ReopenService (T5)
#   GET  /api/v1/close/snapshot/{period_key} → read snapshot state
#                                              → SnapshotPersistenceService.get (T3)


# ── Request/response schemas for the 4 NEW routes ──────────
class SnapshotCommitRequest(BaseModel):
    """POST /api/v1/close/snapshot/commit body shape."""

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Period key in 'YYYY-MM' format (AD-24 typed).",
    )
    snapshot_id: uuid.UUID = Field(
        ...,
        description="fiscal_period_snapshots.snapshot_id to commit (state='verified').",
    )


class SnapshotCommitResponse(BaseModel):
    """POST /api/v1/close/snapshot/commit response envelope."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    period_key: str
    state: str
    cache_invalidation_receipts: list[dict[str, str]]
    trace_id: str


class SnapshotReverseRequest(BaseModel):
    """POST /api/v1/close/snapshot/reverse body shape (AD-22 영구화)."""

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Period key in 'YYYY-MM' format (AD-24 typed).",
    )
    snapshot_id: uuid.UUID = Field(
        ...,
        description="fiscal_period_snapshots.snapshot_id to reverse (state='committed').",
    )
    reversal_reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Free-text justification (Korean SSOT OK).",
    )


class SnapshotReverseResponse(BaseModel):
    """POST /api/v1/close/snapshot/reverse response envelope."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: str
    period_key: str
    state: str
    correction_group_id: str
    cache_invalidation_receipts: list[dict[str, str]]
    trace_id: str


class ReopenRequest(BaseModel):
    """POST /api/v1/close/reopen body shape (W2)."""

    model_config = ConfigDict(extra="forbid")

    period_key: str = Field(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Period key in 'YYYY-MM' format (AD-24 typed).",
    )
    operator_action: str = Field(
        ...,
        description=(
            "One of REOPEN_OPERATOR_ACTIONS = "
            "{operator_reopen, audit_finding, legal_compliance, data_correction}. "
            "AD-10 owner-only + reason length 20-500."
        ),
    )
    reason: str = Field(
        ...,
        min_length=20,
        max_length=500,
        description="Operator justification (min 20 chars, AD-15 audit-justification).",
    )


class ReopenResponse(BaseModel):
    """POST /api/v1/close/reopen response envelope."""

    model_config = ConfigDict(extra="forbid")

    fiscal_period_id: str
    period_key: str
    status: str
    reopen_audit_id: str
    trace_id: str


class SnapshotStateResponse(BaseModel):
    """GET /api/v1/close/snapshot/{period_key} response envelope."""

    model_config = ConfigDict(extra="forbid")

    period_key: str
    snapshot_id: str | None
    state: str | None
    committed_at: str | None
    trace_id: str


# ── Service stub references (filled in by T3/T4/T5) ─────────
def _build_snapshot_persistence_service(
    session: AsyncSession, ctx: TenantContext, request: Request
):
    """Construct `SnapshotPersistenceService` (T3 wire)."""
    from apps.api.modules.m11_close.services.snapshot_persistence_service import (
        SnapshotPersistenceService,
    )

    return SnapshotPersistenceService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=_resolve_trace_id(ctx, request),
    )


def _build_reversal_execute_service(
    session: AsyncSession, ctx: TenantContext, request: Request
):
    """Construct `ReversalExecuteService` (T4 wire)."""
    from apps.api.modules.m11_close.services.reversal_execute_service import (
        ReversalExecuteService,
    )

    return ReversalExecuteService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=_resolve_trace_id(ctx, request),
    )


def _build_reopen_service(
    session: AsyncSession, ctx: TenantContext, request: Request
):
    """Construct `ReopenService` (T5 wire)."""
    from apps.api.modules.m11_close.services.reopen_service import ReopenService

    return ReopenService(
        session,
        tenant_id=ctx.tenant_id,
        trace_id=_resolve_trace_id(ctx, request),
    )


# ── POST /api/v1/close/snapshots/commit (AD-20) ─────────────
@router.post(
    "/snapshot/commit",
    response_model=SnapshotCommitResponse,
    status_code=200,
    summary=(
        "AD-20 commit_snapshot_persistence (state='verified'→'committed') — "
        "Story 11.3 PRIMARY"
    ),
)
async def commit_snapshot_route(
    payload: SnapshotCommitRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.SNAPSHOT_PERSISTENCE)
    ),
    _role: None = Depends(require_role("owner")),
) -> SnapshotCommitResponse:
    """AD-20 commit_snapshot_persistence — state machine transition.

    Story 11.3 PRIMARY AC. Accepts a snapshot_id (state='verified') and
    transitions it to state='committed' via SnapshotPersistenceService
    (wired in T3). Emits audit row + AD-25 multi-channel publish
    (closing_snapshot_cache + fiscal_period_cache + cost_engine_cache +
    ai_cache).

    Raises (T3 wire):
    - 409 SNAPSHOT_ALREADY_COMMITTED — state != 'verified'
    - 403 SNAPSHOT_PERSISTENCE_INDUSTRY_DENIED — service-only tenant
    """
    svc = _build_snapshot_persistence_service(session, ctx, request)
    result = await svc.commit_snapshot(
        period_key=payload.period_key,
        snapshot_id=payload.snapshot_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    await session.commit()
    return SnapshotCommitResponse(
        snapshot_id=str(result.snapshot_id),
        period_key=result.period_key,
        state=result.state,
        cache_invalidation_receipts=result.cache_invalidation_receipts,
        trace_id=result.trace_id,
    )


# ── POST /api/v1/close/snapshots/reverse (AD-22 영구화) ──────
@router.post(
    "/snapshot/reverse",
    response_model=SnapshotReverseResponse,
    status_code=200,
    summary=(
        "AD-22 reversal 영구화 (state='committed'→'reversed') — "
        "Story 11.3 PRIMARY"
    ),
)
async def reverse_snapshot_route(
    payload: SnapshotReverseRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.REVERSAL_EXECUTE)
    ),
    _role: None = Depends(require_role("owner")),
) -> SnapshotReverseResponse:
    """AD-22 reversal 영구화 — committed snapshot → reversed state.

    Story 11.3 PRIMARY AC. Requires the underlying snapshot_id to be
    in state='committed' (3-tier guard from T4). Delegates to
    ReversalExecuteService (wired in T4) which:
    1. SELECT FOR UPDATE on fiscal_period_snapshots.
    2. State guard (must be 'committed').
    3. Persists AD-22 reversal pair (sign-negating + corrected row).
    4. UPDATE fiscal_period_snapshots.state = 'reversed'.
    5. Audit-first emit `snapshot_persistence_reversed`.
    6. AD-25 multi-channel publish (4 channels).

    Raises (T4 wire):
    - 422 REVERSAL_SNAPSHOT_MISMATCH — state != 'committed'
    - 422 LOCKED_PERIOD_REVERSAL_REJECTED — period_status='locked'
    - 409 REVERSAL_DUPLICATE — (tenant_id, reverses_event_id) UNIQUE
    """
    svc = _build_reversal_execute_service(session, ctx, request)
    result = await svc.execute_reversal(
        period_key=payload.period_key,
        snapshot_id=payload.snapshot_id,
        reversal_reason=payload.reversal_reason,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    await session.commit()
    return SnapshotReverseResponse(
        snapshot_id=str(result.snapshot_id),
        period_key=result.period_key,
        state=result.state,
        correction_group_id=str(result.correction_group_id),
        cache_invalidation_receipts=result.cache_invalidation_receipts,
        trace_id=result.trace_id,
    )


# ── POST /api/v1/close/sequence/reopen (W2) ─────────────────
@router.post(
    "/reopen",
    response_model=ReopenResponse,
    status_code=200,
    summary=(
        "W2 reopen flow (operator_action 4-value enum + reason length 20-500) — "
        "Story 11.3 PRIMARY"
    ),
)
async def reopen_close_sequence_route(
    payload: ReopenRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.REOPEN_OPERATOR)
    ),
    _role: None = Depends(require_role("owner")),
) -> ReopenResponse:
    """W2 reopen flow — owner-only operator reopen.

    Story 11.3 PRIMARY AC. Requires:
    - operator_action ∈ {operator_reopen, audit_finding, legal_compliance, data_correction}
    - reason length 20-500 chars
    - AD-10 owner-only role

    Delegates to ReopenService (wired in T5) which:
    1. SELECT FOR UPDATE on fiscal_periods.
    2. Validate operator_action enum + reason length.
    3. Audit-first emit `reopen_completed`.
    4. AD-25 multi-channel publish (fiscal_period_cache + closing_snapshot_cache).

    Raises (T5 wire):
    - 422 REOPEN_OPERATOR_ACTION_INVALID — operator_action or reason length
    - 409 FISCAL_PERIOD_NOT_CLOSED — fiscal_periods.status != 'closed'
    - 500 REOPEN_AUDIT_EMIT_FAILED — audit-first failed
    """
    svc = _build_reopen_service(session, ctx, request)
    result = await svc.execute_reopen(
        period_key=payload.period_key,
        operator_action=payload.operator_action,
        reason=payload.reason,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    await session.commit()
    return ReopenResponse(
        fiscal_period_id=str(result.fiscal_period_id),
        period_key=result.period_key,
        status=result.status,
        reopen_audit_id=str(result.reopen_audit_id),
        trace_id=result.trace_id,
    )


# ── GET /api/v1/close/snapshots/{period_key} ────────────────
@router.get(
    "/snapshot/{period_key}",
    response_model=SnapshotStateResponse,
    status_code=200,
    summary="Read fiscal_period_snapshots state for a period_key — Story 11.3",
)
async def get_snapshot_state_route(
    request: Request,
    period_key: str = Path(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="Period key in 'YYYY-MM' format (AD-24 typed).",
    ),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
    _capability: None = Depends(
        require_capability(Capability.SNAPSHOT_PERSISTENCE)
    ),
) -> SnapshotStateResponse:
    """Read fiscal_period_snapshots state for the given period_key.

    Story 11.3 observability read. Delegates to
    SnapshotPersistenceService.get_snapshot (wired in T3).

    Returns:
    - snapshot_id: UUID of the snapshot (None if no snapshot exists)
    - state: 'verified' | 'committed' | 'reversed' (None if no snapshot)
    - committed_at: ISO-8601 timestamp of commit transition (None if not committed)
    """
    svc = _build_snapshot_persistence_service(session, ctx, request)
    result = await svc.get_snapshot(
        period_key=period_key,
        trace_id=_resolve_trace_id(ctx, request),
    )
    return SnapshotStateResponse(
        period_key=result.period_key,
        snapshot_id=str(result.snapshot_id) if result.snapshot_id else None,
        state=result.state,
        committed_at=result.committed_at,
        trace_id=result.trace_id,
    )


__all__ = [
    "ALLOWED_CHANNELS",
    "CacheInvalidationPublishRequest",
    "CacheInvalidationPublishResponse",
    "ReopenRequest",
    "ReopenResponse",
    "ReversalCreateRequest",
    "ReversalCreateResponse",
    "ReversalHistoryEntry",
    "ReversalHistoryResponse",
    "SnapshotCommitRequest",
    "SnapshotCommitResponse",
    "SnapshotReverseRequest",
    "SnapshotReverseResponse",
    "SnapshotStateResponse",
    "router",
]
