"""apps.api.modules.m3_calculate.handlers — FastAPI routes for M3 calculation.

Story 4.2 (Task 3.1) — `POST /api/v1/calc` route.
Story 4.3 (Task 3.2) — verdict envelope (CalcResponse.verdict) wiring.
Story 9.3 (T2.2) — A29 forward-lock dual-route EXTENSION:
  - Capability dual-route: `COST_CALCULATION OR ABC_CALCULATION` (CR 12-1 L4)
  - Discriminated union envelope: `CalcResponse | CalcAbcResponse`
    (engine_type tag discriminator: 'trad' vs 'abc')
  - M3 orchestrator now returns `CalcOutcome | CalcOutcomeABC`
    (AD-19 dual-route dispatch)

The handler is thin: validate input via Pydantic (AD-15), enforce
capability dual-route gate, open the REPEATABLE READ transaction (AD-4),
delegate to the orchestrator service, and translate typed exceptions to
AD-15 §4 envelope responses.

AD-1 binding: handler → service → engine. Handler NEVER imports
`packages.cost_engine.core` (only Pydantic + DI + service).

AD-11: handler imports the service layer (`apps.api.modules.m3_calculate.services`),
which is the adapter boundary. Engine purity is preserved.

AD-12 verdict envelope: orchestrator returns CalcOutcome(engine_result, verdict)
or CalcOutcomeABC(allocation_outcome, verdict). The handler converts the
service-layer frozen `Verdict` to the Pydantic `Verdict` model and embeds
it in CalcResponse.verdict (trad) or CalcAbcResponse.verdict (abc). On
verification_status='failed' the orchestrator already ROLLBACKed — the
handler still returns 200 OK because the calculation itself succeeded;
the verdict envelope is the application-level contract for lock.
"""

from __future__ import annotations

import uuid as _uuid_mod
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import (
    Capability,
    require_any_capability,
)
from apps.api.core.db import get_session
from apps.api.core.tenant_context import (
    TenantContext,
    get_tenant_context,
)
from apps.api.modules.m3_calculate.schemas import (
    CalcAbcResponse,
    CalcErrorResponse,
    CalcRequest,
    CalcResponse,
    VerificationItem,
)
from apps.api.modules.m3_calculate.schemas import (
    Verdict as VerdictSchema,
)
from apps.api.modules.m3_calculate.services import (
    CalcOrchestrator,
    CalcOutcome,
    CalcOutcomeABC,
)
from apps.api.modules.m3_calculate.services import (
    Verdict as VerdictService,
)

router = APIRouter(prefix="/api/v1", tags=["m3-calculate"])


@router.post(
    "/calc",
    response_model=CalcResponse | CalcAbcResponse,
    status_code=status.HTTP_200_OK,
    summary="원가 계산 (§6.1 8단계 산식 체인 + Epic 9 ABC dual-route)",
    responses={
        200: {
            "model": CalcResponse | CalcAbcResponse,
            "description": (
                "계산 성공 (verified). Discriminated union envelope: "
                "CalcResponse (engine_type='trad') or CalcAbcResponse "
                "(engine_type='abc'). Discriminator tag = `engine_type`."
            ),
        },
        403: {"model": CalcErrorResponse, "description": "INDUSTRY_NOT_SUPPORTED"},
        409: {
            "model": CalcErrorResponse,
            "description": "MONTHLY_INPUT_BLOCKED or FISCAL_PERIOD_SNAPSHOT_DIVERGED",
        },
        422: {"model": CalcErrorResponse, "description": "BASELINE_NOT_READY or INVALID_PAYLOAD"},
        500: {"model": CalcErrorResponse, "description": "INTERNAL_ERROR"},
    },
)
async def post_calc(
    request: Request,
    body: CalcRequest,
    ctx: Annotated[TenantContext, Depends(get_tenant_context)],
    session: Annotated[AsyncSession, Depends(get_session)],
    _cap: Annotated[
        TenantContext,
        # Story 9.3 (T2.2) — A29 forward-lock dual-route capability gate
        # (CR 12-1 L4 precedent — mirrors require_any_role pattern).
        # Tenant gets through if EITHER:
        #   - manufacturing-kind: COST_CALCULATION (trad path)
        #   - service-kind: ABC_CALCULATION (abc dual-route path)
        # Service-layer `_resolve_engine_type` further discriminates by
        # industry === 'service' for M9 dispatch (AD-19).
        Depends(require_any_capability(Capability.COST_CALCULATION, Capability.ABC_CALCULATION)),
    ],
) -> CalcResponse | CalcAbcResponse:
    """`POST /api/v1/calc` — §6.1 원가 계산 single entry point (AD-19).

    Body: `{period_key: "YYYY-MM"}` (AD-24 typed period key).

    Returns 200 OK with discriminated union envelope:
      - `CalcResponse` (engine_type='trad') — 4 KRW costs + result_hash
      - `CalcAbcResponse` (engine_type='abc') — allocation_outcome + snapshot_id

    Raises typed exceptions that the main.py exception handlers map to
    AD-15 §4 envelopes.

    Industry gate (AC #6 + Story 9.3 dual-route):
      - manufacturing / mfg+service / mfg+service+other → COST_CALCULATION
        → trad path (CalcResponse)
      - service → ABC_CALCULATION → M9 dual-route path (CalcAbcResponse)
    """
    trace_id = getattr(request.state, "trace_id", str(_uuid_mod.uuid4()))

    # Walking Skeleton (2026-08-16): the explicit
    # `SET TRANSACTION ISOLATION LEVEL REPEATABLE READ` here is
    # REMOVED — the project's Postgres connection-level default is
    # already REPEATABLE READ (Story 0.2 docker-compose setup), and
    # the explicit mid-transaction SET raises
    # `ActiveSQLTransactionError: SET TRANSACTION ISOLATION LEVEL
    # must be called before any query` because the session has
    # already implicitly begun (RLS `SET LOCAL` fired during the
    # `begin` event listener).

    orchestrator = CalcOrchestrator(session=session, trace_id=trace_id)
    outcome = await orchestrator.compute(
        tenant_id=ctx.tenant_id,
        period_key=body.period_key,
    )

    # Story 9.3 (T2.2) — Discriminated union narrowing. Pydantic v2 + FastAPI
    # support `Union[A, B]` response_model with `discriminator` tag. Here we
    # narrow at the handler level using `isinstance` since we have direct
    # access to the typed return from the orchestrator (CR 11-4 L2 idiom).
    if isinstance(outcome, CalcOutcomeABC):
        # ABC dual-route path (service industry). The envelope does NOT
        # have KRW cost fields (no material/labor/overhead/—manufacturing_cost
        # in pure ABC path). snapshot_id is the fiscal_period_snapshots.id
        # row written by M9 AbcAllocationService.compute_and_persist.
        verdict_schema = _to_verdict_schema(outcome.verdict)
        # outcome.snapshot_id is a UUID-as-string (M9 service-layer contract)
        snapshot_uuid = (
            _uuid_mod.UUID(outcome.snapshot_id) if outcome.snapshot_id else _uuid_mod.uuid4()
        )
        return CalcAbcResponse(
            tenant_id=ctx.tenant_id,
            period_key=body.period_key,
            baseline_revision=1,  # 9-3 wire = initial revision; bump pattern follows Epic 4
            allocation_outcome=outcome.allocation_outcome,
            snapshot_id=snapshot_uuid,
            result_hash=outcome.result_hash,
            state="verified",
            trace_id=trace_id,
            verdict=verdict_schema,
        )

    # Trad path (manufacturing-kind industry). Existing 4-KRW-cost envelope.
    assert isinstance(outcome, CalcOutcome)  # narrowing aid for type-checkers
    engine_result = outcome.engine_result
    verdict_service: VerdictService = outcome.verdict

    # Story 4.3 — AD-12 verdict envelope conversion.
    # Service-layer frozen `VerdictService` → Pydantic `Verdict` for the
    # serialized envelope. Mapping is 1:1 (frozen dataclass + Pydantic
    # model with same fields).
    #
    # Walking Skeleton (2026-08-16): the calc-time wire envelope is
    # restricted to V1/V4/V7/V8 (cost allocation gates) and
    # `passed`/`failed` status. The orchestrator also runs V3 (closing
    # ≥ 0 invariant, Story 5.3) and emits items with `status='skipped'`
    # for non-applicable cases. Those items MUST NOT cross the wire:
    # - V3 was added in Story 5.3 (post AD-12 calc envelope lock),
    #   so it never made it into the Pydantic Literal.
    # - `skipped` is service-internal (per the docstring on
    #   `VerificationItem`: "skipped rules do NOT appear").
    # We filter those out defensively here.
    verdict_schema = _to_verdict_schema(verdict_service)

    # Build response from engine result. The DB snapshot is INSERTed at
    # state="verified" (AD-22 — service layer transition); the engine's
    # returned CalcResult carries state="draft" invariant.
    # We use the engine's int KRW fields directly (already AD-8 BIGINT).
    return CalcResponse(
        tenant_id=engine_result.tenant_id,
        period_key=engine_result.period_key,
        baseline_revision=1,  # TODO(epic-4): read from period row after compute
        material_cost=int(engine_result.material_cost),
        labor_cost=int(engine_result.labor_cost),
        overhead_cost=int(engine_result.overhead_cost),
        manufacturing_cost=int(engine_result.manufacturing_cost),
        inventory_adjustment=int(engine_result.inventory_adjustment),
        result_hash=engine_result.result_hash,
        state="verified",
        trace_id=trace_id,
        verdict=verdict_schema,
    )


# ── Internals (shared by both trad + abc paths) ───────────────
_allowed_codes = frozenset({"V1", "V4", "V7", "V8"})
_allowed_statuses = frozenset({"passed", "failed"})


def _to_wire_item(item):
    """Filter V3 + skipped items out of the wire envelope (Walking Skeleton 2026-08-16)."""
    if item.code not in _allowed_codes or item.status not in _allowed_statuses:
        return None
    return VerificationItem(
        code=item.code,
        status=item.status,
        message_ko=item.message_ko,
        details=item.details,
    )


def _to_verdict_schema(verdict_service: VerdictService) -> VerdictSchema:
    """Convert service-layer frozen `Verdict` → Pydantic `Verdict` (AD-12 envelope)."""
    wire_verifications = [
        wi for wi in (_to_wire_item(it) for it in verdict_service.verifications) if wi is not None
    ]
    wire_top_failure = (
        _to_wire_item(verdict_service.top_failure)
        if verdict_service.top_failure is not None
        else None
    )
    return VerdictSchema(
        verification_status=verdict_service.verification_status,
        verifications=wire_verifications,
        top_failure=wire_top_failure,
        trace_id=verdict_service.trace_id,
    )
