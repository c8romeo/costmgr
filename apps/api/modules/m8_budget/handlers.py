"""apps.api.modules.m8_budget.handlers — Story 8.1 + 8.2 HTTP routes.

Story 8.1 (3 NEW endpoints):
  - POST /api/v1/budget/scenarios — create scenario (owner+member, BUDGET_SCENARIO)
  - GET /api/v1/budget/scenarios — list scenarios (4-role read, BUDGET_SCENARIO)
  - GET /api/v1/budget/scenarios/{period_key} — get scenario by virtual period_key

Story 8.2 (2 NEW endpoints):
  - GET /api/v1/budget/variance/{period_key} — budget vs actual variance
    (4-role read, BUDGET_SCENARIO capability reuse — AC #2 + AD-22)
  - GET /api/v1/budget/variance/{period_key}/pdf — variance PDF envelope
    (8-3 honestly DEFER — placeholder response shape)

CR 12-5 L3 3-layer defense (scenario 생성은 destructive-write):
  - Route layer: `@require_capability(BUDGET_SCENARIO)` + `require_role("owner", "member")`
  - Service layer: `validate_scenario_uniqueness(existing_count=count_scenarios())`
  - DB layer: `UNIQUE(tenant_id, real_period_key)` constraint defense-in-depth

5 NEW typed exceptions → HTTP envelopes (CR 12-5 D-14 main.py handlers):
  - ScenarioLimitExceededError → 409 SCENARIO_LIMIT_EXCEEDED
  - InvalidVirtualBudgetPeriodKeyError → 422 INVALID_VIRTUAL_BUDGET_PERIOD_KEY
  - BudgetScenarioNotFoundError → 404 BUDGET_SCENARIO_NOT_FOUND
  - BudgetVarianceNotFoundError → 404 BUDGET_VARIANCE_NOT_FOUND
  - InvalidVariancePeriodError → 422 INVALID_VARIANCE_PERIOD
"""

from __future__ import annotations

import base64
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Path, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import Capability, require_any_role, require_capability
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m8_budget.exceptions import (
    BudgetScenarioNotFoundError,
    BudgetVarianceNotFoundError,
    InvalidVariancePeriodError,
)
from apps.api.modules.m8_budget.schemas import (
    ABCDDisabledBadgeSerialized,
    BudgetScenarioListResponse,
    BudgetScenarioResponse,
    BudgetScenarioSerialized,
    BudgetVariancePdfResponse,
    CreateBudgetScenarioRequest,
    VarianceRowSerialized,
    VarianceTableResponse,
)
from apps.api.modules.m8_budget.services import (
    BudgetScenarioService,
    BudgetVarianceService,
    validate_variance_inputs,
)
from packages.cost_engine.budget_period_key import (
    InvalidVirtualBudgetPeriodKeyError,
    ScenarioLimitExceededError,
    compute_budget_scenario_hash,
    parse_virtual_budget_period_key,
)
from packages.cost_engine.budget_variance import ABCD_DISABLED_NOTE
from packages.services.m8_budget import (
    serialize_budget_scenario,
    serialize_budget_variance_pdf_envelope,
    serialize_variance_row,
    serialize_variance_total,
)

router = APIRouter(
    prefix="/api/v1/budget/scenarios",
    tags=["m8-budget"],
)

# Story 8.2 — second router for variance endpoints (PRD §F8.2).
variance_router = APIRouter(
    prefix="/api/v1/budget/variance",
    tags=["m8-budget-variance"],
)


def _resolve_trace_id(ctx: TenantContext, request: Request) -> str:
    """Resolve trace_id with 11-3 fleet-wide fallback pattern.

    `TenantContext` does not carry `trace_id` (pre-MVP frozen dataclass).
    Falls back to `request.state.trace_id` (set by middleware) then uuid4().
    """
    trace_id = getattr(ctx, "trace_id", None)
    if trace_id:
        return str(trace_id)
    request_trace_id = getattr(request.state, "trace_id", None)
    if request_trace_id:
        return str(request_trace_id)
    return str(uuid.uuid4())


def _to_serialized(kernel) -> BudgetScenarioSerialized:
    """Kernel `BudgetScenario` → Pydantic `BudgetScenarioSerialized`.

    AD-15 §1 + AD-8 monetary precision parity.
    """
    data = serialize_budget_scenario(kernel)
    digest = compute_budget_scenario_hash(scenario=kernel)
    return BudgetScenarioSerialized(
        id=data["id"],  # type: ignore[arg-type]
        tenant_id=data["tenant_id"],  # type: ignore[arg-type]
        period_key=data["period_key"],  # type: ignore[arg-type]
        real_period_key=data["real_period_key"],  # type: ignore[arg-type]
        scenario_index=data["scenario_index"],  # type: ignore[arg-type]
        scenario_hash=digest,
        created_by=data["created_by"],  # type: ignore[arg-type]
        created_at_kst=data["created_at_kst"],  # type: ignore[arg-type]
    )


@router.post(
    "",
    response_model=BudgetScenarioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_capability(Capability.BUDGET_SCENARIO)),
        Depends(require_any_role("owner", "member")),
    ],
    responses={
        409: {"description": "Scenario limit exceeded (1차 MVP = 1 only)"},
        422: {"description": "Invalid real period key"},
        403: {"description": "Capability or role denied"},
    },
)
async def create_budget_scenario(
    request_body: CreateBudgetScenarioRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> BudgetScenarioResponse:
    """POST /api/v1/budget/scenarios — create new budget scenario.

    Owner + member only (viewer forbidden). Service layer enforces
    1차 MVP scenario 1개 잠금 + DB UNIQUE 제약 defense-in-depth.
    """
    service = BudgetScenarioService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    kernel = await service.create_scenario(real_period_key=request_body.real_period_key)
    return BudgetScenarioResponse(scenario=_to_serialized(kernel))


@router.get(
    "",
    response_model=BudgetScenarioListResponse,
    dependencies=[
        Depends(require_capability(Capability.BUDGET_SCENARIO)),
        Depends(require_any_role("owner", "member", "viewer", "consultant_proxy")),
    ],
)
async def list_budget_scenarios(
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> BudgetScenarioListResponse:
    """GET /api/v1/budget/scenarios — list scenarios (4-role read)."""
    service = BudgetScenarioService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    kernels = await service.list_scenarios()
    return BudgetScenarioListResponse(
        scenarios=[_to_serialized(k) for k in kernels],
        total_count=len(kernels),
        trace_id=service.trace_id,
    )


@router.get(
    "/{period_key}",
    response_model=BudgetScenarioResponse,
    dependencies=[
        Depends(require_capability(Capability.BUDGET_SCENARIO)),
        Depends(require_any_role("owner", "member", "viewer", "consultant_proxy")),
    ],
    responses={
        404: {"description": "Budget scenario not found"},
        422: {"description": "Invalid virtual budget period key"},
    },
)
async def get_budget_scenario(
    period_key: str = Path(..., description="AD-24 virtual YYYY-MM#B<n>"),
    request: Request = ...,  # FastAPI Request injection
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> BudgetScenarioResponse:
    """GET /api/v1/budget/scenarios/{period_key} — get scenario by virtual key."""
    service = BudgetScenarioService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    kernel = await service.get_scenario(period_key=period_key)
    return BudgetScenarioResponse(scenario=_to_serialized(kernel))


# ── Story 8.2 — Variance table endpoint (PRD §F8.2) ────────────────
@variance_router.get(
    "/{period_key}",
    response_model=VarianceTableResponse,
    dependencies=[
        Depends(require_capability(Capability.BUDGET_SCENARIO)),
        Depends(require_any_role(
            "owner", "member", "viewer", "consultant_proxy"
        )),
    ],
    responses={
        404: {"description": "Budget variance not found"},
        422: {"description": "Invalid virtual budget period key"},
    },
)
async def get_budget_variance_table(
    period_key: str = Path(
        ..., description="AD-24 virtual YYYY-MM#B<n> (8-1 wire)"
    ),
    request: Request = ...,  # FastAPI Request injection
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> VarianceTableResponse:
    """GET /api/v1/budget/variance/{period_key} — budget vs actual variance table.

    AC #1 ~ #6 + PRD §F8.2 verbatim.
    Capability reuse: BUDGET_SCENARIO (8-1 wire — 산업 agnostic).
    """
    service = BudgetVarianceService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )

    # CR 12-5 L3 3-layer defense — period_key validation.
    validate_variance_inputs(period_key=period_key)

    # 8-2 atomic wire: fetch_variance_table returns empty list
    # (production JOIN query is honestly DEFER to 8-3 follow-up).
    kernel_rows = await service.fetch_variance_table(period_key=period_key)
    total_row = await service.compute_variance_total(rows=kernel_rows)
    badge_payload = await service.fetch_abcd_disabled_badge(variant="variance")

    parts = parse_virtual_budget_period_key(period_key=period_key)

    return VarianceTableResponse(
        period_key=period_key,
        scenario_index=parts.scenario_index,
        rows=[VarianceRowSerialized(**serialize_variance_row(r)) for r in kernel_rows],
        total_row=VarianceRowSerialized(**serialize_variance_total(total_row)),
        abcd_disabled_badge=ABCDDisabledBadgeSerialized(**badge_payload),
        abcd_disabled_note=ABCD_DISABLED_NOTE,
        trace_id=service.trace_id,
    )


# ── Story 8.2 — Variance PDF endpoint (8-3 honestly DEFER) ─────────
@variance_router.get(
    "/{period_key}/pdf",
    response_model=BudgetVariancePdfResponse,
    dependencies=[
        Depends(require_capability(Capability.BUDGET_SCENARIO)),
        Depends(require_any_role(
            "owner", "member", "viewer", "consultant_proxy"
        )),
    ],
    responses={
        404: {"description": "Budget variance not found"},
        422: {"description": "Invalid virtual budget period key"},
    },
)
async def get_budget_variance_pdf(
    period_key: str = Path(
        ..., description="AD-24 virtual YYYY-MM#B<n> (8-1 wire)"
    ),
    request: Request = ...,  # FastAPI Request injection
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> BudgetVariancePdfResponse:
    """GET /api/v1/budget/variance/{period_key}/pdf — variance PDF (8-3 DEFER).

    8-2 atomic wire: returns envelope shape with empty pdf_bytes_b64 (placeholder).
    8-3 follow-up sprint: wire to packages.services.m6_reports.pdf_helpers
    (Epic 6 M5 PDF generator reuse, READ-ONLY pattern).
    """
    service = BudgetVarianceService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )

    validate_variance_inputs(period_key=period_key)
    kernel_rows = await service.fetch_variance_table(period_key=period_key)
    total_row = await service.compute_variance_total(rows=kernel_rows)
    await service.generate_budget_variance_pdf(period_key=period_key, scenario_index=1)

    parts = parse_virtual_budget_period_key(period_key=period_key)

    envelope = serialize_budget_variance_pdf_envelope(
        period_key=period_key,
        scenario_index=parts.scenario_index,
        rows=kernel_rows,
        total_row=total_row,
        generated_at_kst=datetime.now().isoformat(),
    )

    return BudgetVariancePdfResponse(
        period_key=period_key,
        scenario_index=parts.scenario_index,
        pdf_bytes_b64=base64.b64encode(b"").decode("ascii"),
        envelope=envelope,
        trace_id=service.trace_id,
    )


__all__ = [
    "router",
    "variance_router",
    "create_budget_scenario",
    "list_budget_scenarios",
    "get_budget_scenario",
    "get_budget_variance_table",
    "get_budget_variance_pdf",
    # Re-export typed exceptions for main.py envelope handler 등록 (CR 12-5 D-14).
    "ScenarioLimitExceededError",
    "InvalidVirtualBudgetPeriodKeyError",
    "BudgetScenarioNotFoundError",
    "BudgetVarianceNotFoundError",
    "InvalidVariancePeriodError",
]
