"""apps.api.modules.m7_simulation.handlers — Story 7.1 HTTP routes.

2 NEW endpoints:
  - POST /api/v1/simulation/cvp/compute — fetch baseline + simulate
  - GET  /api/v1/simulation/cvp/baseline — fetch baseline only

CR 12-5 L3 3-layer defense (CVP는 read-only — audit-first no-write):
  - Route layer: `@require_capability(CVP_SIMULATION)` + 4-role allow
  - Service layer: `validate_delta_bounds` (defense-in-depth)
  - Kernel layer: `compute_bep` edge case validation (unit_price > variable_cost)

2 NEW typed exceptions → HTTP envelopes (CR 12-5 D-14 main.py handlers):
  - CVPBaselineNotFoundError  → 404 CVP_BASELINE_NOT_FOUND
  - CVPInvalidDeltaError      → 422 CVP_INVALID_DELTA
"""

from __future__ import annotations

import time
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import Capability, require_any_role, require_capability
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m7_simulation.exceptions import CVPBaselineNotFoundError
from apps.api.modules.m7_simulation.schemas import (
    CVPBaselineResponse,
    CVPBaselineSerialized,
    CVPBEPResultSerialized,
    CVPDeltaRequest,
    CVPDeltaSerialized,
    CVPResultSerialized,
    CVPSimulationRequest,
    CVPSimulationResponse,
    CVPTargetProfitResultSerialized,
)
from apps.api.modules.m7_simulation.services import CVPSimulationService
from packages.cost_engine.cvp import CVPDelta
from packages.services.m7_simulation.delta_helpers import (
    CVPInvalidDeltaError,
    validate_delta_bounds,
)

router = APIRouter(
    prefix="/api/v1/simulation/cvp",
    tags=["m7-simulation"],
)


def _resolve_trace_id(ctx: TenantContext, request: Request) -> str:
    """Resolve trace_id with 11-3 fleet-wide fallback pattern."""
    trace_id = getattr(ctx, "trace_id", None)
    if trace_id:
        return str(trace_id)
    request_trace_id = getattr(request.state, "trace_id", None)
    if request_trace_id:
        return str(request_trace_id)
    return str(uuid.uuid4())


def _delta_to_kernel(delta_req: CVPDeltaRequest) -> CVPDelta:
    """Pydantic `CVPDeltaRequest` → kernel `CVPDelta` (Decimal casting)."""
    return CVPDelta(
        unit_price_delta_pct=Decimal(delta_req.unit_price_delta_pct),
        unit_variable_cost_delta_pct=Decimal(delta_req.unit_variable_cost_delta_pct),
        fixed_cost_delta_pct=Decimal(delta_req.fixed_cost_delta_pct),
        operating_rate_delta_pct=Decimal(delta_req.operating_rate_delta_pct),
    )


def _bep_kernel_to_serialized(bep_result) -> CVPBEPResultSerialized:
    """Kernel BEPResult → Pydantic CVPBEPResultSerialized."""
    return CVPBEPResultSerialized(
        bep_quantity=str(bep_result.bep_quantity),
        bep_revenue=str(bep_result.bep_revenue),
        contribution_margin_per_unit=str(bep_result.contribution_margin_per_unit),
        contribution_margin_ratio=str(bep_result.contribution_margin_ratio),
    )


def _target_kernel_to_serialized(tp_result) -> CVPTargetProfitResultSerialized:
    """Kernel TargetProfitResult → Pydantic CVPTargetProfitResultSerialized."""
    return CVPTargetProfitResultSerialized(
        target_quantity=str(tp_result.target_quantity),
        target_revenue=str(tp_result.target_revenue),
    )


def _result_kernel_to_serialized(result) -> CVPResultSerialized:
    """Kernel CVPResult → Pydantic CVPResultSerialized (4 nested results)."""
    return CVPResultSerialized(
        simulated_bep=_bep_kernel_to_serialized(result.simulated_bep),
        simulated_target_profit=_target_kernel_to_serialized(
            result.simulated_target_profit
        ),
        baseline_bep=_bep_kernel_to_serialized(result.baseline_bep),
        baseline_target_profit=_target_kernel_to_serialized(
            result.baseline_target_profit
        ),
        delta_summary={k: str(v) for k, v in result.delta_summary.items()},
    )


def _baseline_kernel_to_serialized(baseline) -> CVPBaselineSerialized:
    """Kernel CVPBaseline → Pydantic CVPBaselineSerialized."""
    return CVPBaselineSerialized(
        fixed_cost=str(baseline.fixed_cost),
        unit_variable_cost=str(baseline.unit_variable_cost),
        unit_price=str(baseline.unit_price),
        operating_rate=str(baseline.operating_rate),
        target_profit=str(baseline.target_profit),
    )


@router.post(
    "/compute",
    response_model=CVPSimulationResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_capability(Capability.CVP_SIMULATION)),
        Depends(require_any_role("owner", "member", "viewer", "consultant_proxy")),
    ],
    responses={
        404: {"description": "CVP baseline not found"},
        422: {"description": "Invalid period_key or delta out of bounds"},
        403: {"description": "Capability or role denied"},
    },
)
async def compute_cvp_simulation(
    request_body: CVPSimulationRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> CVPSimulationResponse:
    """POST /api/v1/simulation/cvp/compute — fetch baseline + simulate.

    Owner+member+viewer+consultant_proxy allowed (AD-10 4-role — CVP는
    read-only 시뮬레이션). Service layer enforces delta bounds validation.
    """
    delta = _delta_to_kernel(request_body.delta)
    # Defense-in-depth: validate delta bounds before engine call.
    validate_delta_bounds(delta)

    started = time.perf_counter()
    service = CVPSimulationService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    baseline, result, _source_period_key = await service.compute(
        period_key=request_body.period_key,
        delta=delta,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    return CVPSimulationResponse(
        baseline=_baseline_kernel_to_serialized(baseline),
        delta=CVPDeltaSerialized(
            unit_price_delta_pct=str(delta.unit_price_delta_pct),
            unit_variable_cost_delta_pct=str(delta.unit_variable_cost_delta_pct),
            fixed_cost_delta_pct=str(delta.fixed_cost_delta_pct),
            operating_rate_delta_pct=str(delta.operating_rate_delta_pct),
        ),
        result=_result_kernel_to_serialized(result),
        latency_ms=latency_ms,
        trace_id=service.trace_id,
    )


@router.get(
    "/baseline",
    response_model=CVPBaselineResponse,
    dependencies=[
        Depends(require_capability(Capability.CVP_SIMULATION)),
        Depends(require_any_role("owner", "member", "viewer", "consultant_proxy")),
    ],
    responses={
        404: {"description": "CVP baseline not found"},
        422: {"description": "Invalid period_key"},
        403: {"description": "Capability or role denied"},
    },
)
async def get_cvp_baseline(
    period_key: str = Query(
        ...,
        min_length=7,
        max_length=7,
        description="AD-24 fiscal period key — YYYY-MM",
    ),
    request: Request = ...,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> CVPBaselineResponse:
    """GET /api/v1/simulation/cvp/baseline?period_key=YYYY-MM — fetch baseline."""
    service = CVPSimulationService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    baseline, source_period_key, fiscal_period_state = await service.fetch_cvp_baseline(
        period_key=period_key
    )
    return CVPBaselineResponse(
        baseline=_baseline_kernel_to_serialized(baseline),
        period_key=period_key,
        source_period_key=source_period_key,
        fiscal_period_state=fiscal_period_state,
        trace_id=service.trace_id,
    )


__all__ = [
    "router",
    "compute_cvp_simulation",
    "get_cvp_baseline",
    # Re-export typed exceptions for main.py envelope handler 등록 (CR 12-5 D-14).
    "CVPBaselineNotFoundError",
    "CVPInvalidDeltaError",
]
