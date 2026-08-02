"""apps.api.modules.m3_calculate.handlers — FastAPI routes for M3 calculation.

Story 4.2 (Task 3.1) — `POST /api/v1/calc` route.
Story 4.3 (Task 3.2) — verdict envelope (CalcResponse.verdict) wiring.

The handler is thin: validate input via Pydantic (AD-15), enforce
capability gate (CR 2.1 + Story 4.1 AC #6), open the REPEATABLE READ
transaction (AD-4), delegate to the orchestrator service, and translate
typed exceptions to AD-15 §4 envelope responses.

AD-1 binding: handler → service → engine. Handler NEVER imports
`packages.cost_engine.core` (only Pydantic + DI + service).

AD-11: handler imports the service layer (`apps.api.modules.m3_calculate.services`),
which is the adapter boundary. Engine purity is preserved.

AD-12 verdict envelope: orchestrator returns CalcOutcome(engine_result, verdict).
The handler converts the service-layer frozen `Verdict` to the Pydantic
`Verdict` model and embeds it in CalcResponse.verdict. On
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
    require_capability,
)
from apps.api.core.db import get_session
from apps.api.core.tenant_context import (
    TenantContext,
    get_tenant_context,
)
from apps.api.modules.m3_calculate.schemas import (
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
)
from apps.api.modules.m3_calculate.services import (
    Verdict as VerdictService,
)

router = APIRouter(prefix="/api/v1", tags=["m3-calculate"])


@router.post(
    "/calc",
    response_model=CalcResponse,
    status_code=status.HTTP_200_OK,
    summary="원가 계산 (§6.1 8단계 산식 체인)",
    responses={
        200: {"model": CalcResponse, "description": "계산 성공 (verified)"},
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
    _cap: Annotated[TenantContext, Depends(require_capability(Capability.COST_CALCULATION))],
) -> CalcResponse:
    """`POST /api/v1/calc` — §6.1 원가 계산 single entry point (AD-19).

    Body: `{period_key: "YYYY-MM"}` (AD-24 typed period key).

    Returns 200 OK with the 4 KRW costs + result_hash (state="verified")
    on success. Raises typed exceptions that the main.py exception
    handlers map to AD-15 §4 envelopes.

    Industry gate (AC #6): COST_CALCULATION capability is granted to
    manufacturing / mfg+service / mfg+service+other tenants. Service
    tenants get 403 INDUSTRY_NOT_SUPPORTED (Epic 9 ABC is their path).
    """
    trace_id = getattr(request.state, "trace_id", str(_uuid_mod.uuid4()))

    # Open REPEATABLE READ transaction (AD-4). `begin()` enters the
    # transaction with the specified isolation level; commit/rollback
    # is the orchestrator's responsibility.
    await session.execute(
        # Hint: set isolation. SQLAlchemy AsyncSession doesn't expose
        # isolation_level= directly per call; we use a text-level SET.
        # Story 4.2 keeps it simple — the connection-level default is
        # REPEATABLE READ on the project's PG config (Story 0.2 setup).
        # Defensive explicit SET here for production paths.
        __import__("sqlalchemy").text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
    )

    orchestrator = CalcOrchestrator(session=session, trace_id=trace_id)
    outcome = await orchestrator.compute(
        tenant_id=ctx.tenant_id,
        period_key=body.period_key,
    )
    engine_result = outcome.engine_result
    verdict_service: VerdictService = outcome.verdict

    # Story 4.3 — AD-12 verdict envelope conversion.
    # Service-layer frozen `VerdictService` → Pydantic `Verdict` for the
    # serialized envelope. Mapping is 1:1 (frozen dataclass + Pydantic
    # model with same fields).
    verdict_schema = VerdictSchema(
        verification_status=verdict_service.verification_status,
        verifications=[
            VerificationItem(
                code=item.code,
                status=item.status,
                message_ko=item.message_ko,
                details=item.details,
            )
            for item in verdict_service.verifications
        ],
        top_failure=(
            VerificationItem(
                code=verdict_service.top_failure.code,
                status=verdict_service.top_failure.status,
                message_ko=verdict_service.top_failure.message_ko,
                details=verdict_service.top_failure.details,
            )
            if verdict_service.top_failure is not None
            else None
        ),
        trace_id=verdict_service.trace_id,
    )

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
