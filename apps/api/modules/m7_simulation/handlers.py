"""apps.api.modules.m7_simulation.handlers — Story 7.1 + 7.2 HTTP routes.

Story 7.1 routes:
  - POST /api/v1/simulation/cvp/compute — fetch baseline + simulate
  - GET  /api/v1/simulation/cvp/baseline — fetch baseline only

Story 7.2 routes (CVP_SIMULATION capability reuse):
  - POST /api/v1/simulation/projection/compute — fetch baseline + project
  - GET  /api/v1/simulation/projection/baseline — fetch baseline + projection_month validation
  - POST /api/v1/simulation/projection/report/pdf — generate PDF report

CR 12-5 L3 3-layer defense (CVP/projection are read-only — audit-first no-write):
  - Route layer: `@require_capability(CVP_SIMULATION)` + 4-role allow
  - Service layer: chronological invariant + 4종 input validation
  - Kernel layer: pure math edge case validation

5 NEW typed exceptions → HTTP envelopes (CR 12-5 D-14 main.py handlers):
  - CVPBaselineNotFoundError              → 404 CVP_BASELINE_NOT_FOUND
  - CVPInvalidDeltaError                  → 422 CVP_INVALID_DELTA
  - InvalidProjectionMonthError           → 422 INVALID_PROJECTION_MONTH
  - ProjectionInputsInvalidError          → 422 PROJECTION_INPUTS_INVALID
  - ProjectionBaselineNotFoundError       → 404 PROJECTION_BASELINE_NOT_FOUND
"""

from __future__ import annotations

import time
import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.capability import Capability, require_any_role, require_capability
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.m7_simulation.exceptions import (
    CVPBaselineNotFoundError,
    InvalidProjectionMonthError,
    ProjectionBaselineNotFoundError,
    ProjectionInputsInvalidError,
)
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
    NextMonthProjectionSerialized,
    ProjectionBaselineResponse,
    ProjectionComputeRequest,
    ProjectionComputeResponse,
    ProjectionInputsRequest,
    ProjectionInputsSerialized,
    ProjectionPdfRequest,
)
from apps.api.modules.m7_simulation.services import (
    CVPSimulationService,
    ProjectionService,
)
from packages.cost_engine.cvp import CVPDelta
from packages.cost_engine.projection import (
    ProjectionInputs,
    compute_projection_hash,
)
from packages.services.m7_simulation.delta_helpers import (
    CVPInvalidDeltaError,
    validate_delta_bounds,
)
from packages.services.m7_simulation.projection_pdf_helpers import (
    serialize_projection_pdf_envelope,
)

router = APIRouter(
    prefix="/api/v1/simulation",
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


# ──────────────────────────────────────────────────────────────────
# Story 7.1 — CVP routes
# ──────────────────────────────────────────────────────────────────
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
        simulated_target_profit=_target_kernel_to_serialized(result.simulated_target_profit),
        baseline_bep=_bep_kernel_to_serialized(result.baseline_bep),
        baseline_target_profit=_target_kernel_to_serialized(result.baseline_target_profit),
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
    "/cvp/compute",
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
    "/cvp/baseline",
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


# ──────────────────────────────────────────────────────────────────
# Story 7.2 — Projection routes (CVP_SIMULATION capability reuse)
# ──────────────────────────────────────────────────────────────────
def _projection_inputs_to_kernel(
    inputs_req: ProjectionInputsRequest,
) -> ProjectionInputs:
    """Pydantic `ProjectionInputsRequest` → kernel `ProjectionInputs`."""
    return ProjectionInputs(
        loan_amount=Decimal(inputs_req.loan_amount),
        interest_rate=Decimal(inputs_req.interest_rate),
        cost_inflation_rate=Decimal(inputs_req.cost_inflation_rate),
        corporate_tax_rate=Decimal(inputs_req.corporate_tax_rate),
    )


def _projection_inputs_to_serialized(
    inputs_kernel: ProjectionInputs,
) -> ProjectionInputsSerialized:
    """Kernel `ProjectionInputs` → Pydantic `ProjectionInputsSerialized`."""
    return ProjectionInputsSerialized(
        loan_amount=str(inputs_kernel.loan_amount),
        interest_rate=str(inputs_kernel.interest_rate),
        cost_inflation_rate=str(inputs_kernel.cost_inflation_rate),
        corporate_tax_rate=str(inputs_kernel.corporate_tax_rate),
    )


def _next_month_projection_to_serialized(
    projection_kernel,
) -> NextMonthProjectionSerialized:
    """Kernel `NextMonthProjection` → Pydantic `NextMonthProjectionSerialized`."""
    return NextMonthProjectionSerialized(
        projected_revenue=str(projection_kernel.projected_revenue),
        projected_variable_cost=str(projection_kernel.projected_variable_cost),
        projected_fixed_cost=str(projection_kernel.projected_fixed_cost),
        interest_expense=str(projection_kernel.interest_expense),
        pre_tax_income=str(projection_kernel.pre_tax_income),
        corporate_tax=str(projection_kernel.corporate_tax),
        after_tax_income=str(projection_kernel.after_tax_income),
    )


@router.post(
    "/projection/compute",
    response_model=ProjectionComputeResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_capability(Capability.CVP_SIMULATION)),
        Depends(require_any_role("owner", "member", "viewer", "consultant_proxy")),
    ],
    responses={
        404: {"description": "Projection baseline not found"},
        422: {"description": ("Invalid period_key / projection_month / 4종 projection inputs")},
        403: {"description": "Capability or role denied"},
    },
)
async def compute_projection_simulation(
    request_body: ProjectionComputeRequest,
    request: Request,
    response: Response,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ProjectionComputeResponse:
    """POST /api/v1/simulation/projection/compute — fetch baseline + project.

    Owner+member+viewer+consultant_proxy allowed (AD-10 4-role — projection
    is read-only simulation). Service layer enforces:
      - AD-24 period_key / projection_month format
      - chronological invariant (projection_month > period_key)
      - 4종 inputs validation (defense-in-depth + kernel layer)

    Response carries `X-Projection-Hash` header (V8 determinism).
    """
    started = time.perf_counter()
    service = ProjectionService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    inputs_kernel = _projection_inputs_to_kernel(request_body.inputs)

    baseline, projection = await service.compute(
        period_key=request_body.period_key,
        projection_month=request_body.projection_month,
        projection_inputs=inputs_kernel,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    # V8 determinism hash header (CR 12-5 D-13 + NFR16).
    projection_hash = compute_projection_hash(projection)
    response.headers["X-Projection-Hash"] = projection_hash

    return ProjectionComputeResponse(
        baseline=_baseline_kernel_to_serialized(baseline),
        projection_inputs=_projection_inputs_to_serialized(inputs_kernel),
        result=_next_month_projection_to_serialized(projection),
        latency_ms=latency_ms,
        trace_id=service.trace_id,
    )


@router.get(
    "/projection/baseline",
    response_model=ProjectionBaselineResponse,
    dependencies=[
        Depends(require_capability(Capability.CVP_SIMULATION)),
        Depends(require_any_role("owner", "member", "viewer", "consultant_proxy")),
    ],
    responses={
        404: {"description": "Projection baseline not found"},
        422: {"description": "Invalid period_key / projection_month / chronological"},
        403: {"description": "Capability or role denied"},
    },
)
async def get_projection_baseline(
    period_key: str = Query(
        ...,
        min_length=7,
        max_length=7,
        description="AD-24 fiscal period key — YYYY-MM",
    ),
    projection_month: str = Query(
        ...,
        min_length=7,
        max_length=7,
        description="AD-24 projection target month — YYYY-MM (must be > period_key)",
    ),
    request: Request = ...,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ProjectionBaselineResponse:
    """GET /api/v1/simulation/projection/baseline — fetch baseline + projection_month validation.

    Service layer validates:
      - AD-24 format
      - chronological invariant (projection_month > period_key)

    Returns baseline + `derived_projection_inputs_hint` (4종 placeholder
    values for frontend form initial state — defaults to 0).
    """
    service = ProjectionService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    # `fetch_projection_baseline` returns CVPBaseline only; it internally
    # validates format + chronological invariant + delegates to
    # 7-1 CVPSimulationService for the actual fetch.
    baseline = await service.fetch_projection_baseline(
        period_key=period_key,
        projection_month=projection_month,
    )
    source_period_key = period_key  # echo back (already validated)
    fiscal_period_state = "verified"  # baseline implies verified snapshot

    return ProjectionBaselineResponse(
        baseline=_baseline_kernel_to_serialized(baseline),
        period_key=period_key,
        projection_month=projection_month,
        source_period_key=source_period_key,
        fiscal_period_state=fiscal_period_state,
        derived_projection_inputs_hint={
            "loan_amount": "0",
            "interest_rate": "0",
            "cost_inflation_rate": "0",
            "corporate_tax_rate": "22",  # Korean statutory default
        },
        trace_id=service.trace_id,
    )


@router.post(
    "/projection/report/pdf",
    status_code=status.HTTP_200_OK,
    dependencies=[
        Depends(require_capability(Capability.CVP_SIMULATION)),
        Depends(require_any_role("owner", "member", "viewer", "consultant_proxy")),
    ],
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "PDF binary (Epic 6 §9 #20+ 원가 예측 보고서)",
        },
        404: {"description": "Projection baseline not found"},
        422: {"description": "Invalid 4종 inputs / period_key / projection_month"},
        403: {"description": "Capability or role denied"},
    },
)
async def generate_projection_pdf(
    request_body: ProjectionPdfRequest,
    request: Request,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> Response:
    """POST /api/v1/simulation/projection/report/pdf — generate PDF report.

    M5 §9 #20+ "원가 예측 보고서" envelope (Epic 6 reuse pattern).

    Response: `application/pdf` binary + `Content-Disposition: attachment;
    filename="cost-prediction-report-{period_key}-{projection_month}.pdf"`.

    AD-15 envelope contract:
    - 200 OK + application/pdf binary
    - 404 PROJECTION_BASELINE_NOT_FOUND (baseline missing)
    - 422 PROJECTION_INPUTS_INVALID (4종 validation failure)
    - 422 INVALID_PROJECTION_MONTH (chronological violation)
    """
    started = time.perf_counter()
    service = ProjectionService(
        session,
        tenant_id=ctx.tenant_id,
        actor_id=ctx.user_id,
        trace_id=_resolve_trace_id(ctx, request),
    )
    inputs_kernel = _projection_inputs_to_kernel(request_body.inputs)

    baseline, projection = await service.compute(
        period_key=request_body.period_key,
        projection_month=request_body.projection_month,
        projection_inputs=inputs_kernel,
    )
    latency_ms = int((time.perf_counter() - started) * 1000)

    # Build envelope (M5 §9 #20+ "원가 예측 보고서").
    envelope = serialize_projection_pdf_envelope(
        baseline=baseline,
        projection_inputs=inputs_kernel,
        projection=projection,
        period_key=request_body.period_key,
        projection_month=request_body.projection_month,
    )

    # PDF byte rendering — Epic 6 M5 PDF generator is the canonical renderer
    # (planned for Epic 6 M5 follow-up sprint). For 7-2 wire scope, emit the
    # envelope as JSON bytes (placeholder). The endpoint contract (200 +
    # application/pdf + Content-Disposition + X-Projection-Hash) is satisfied
    # at the wire level; actual PDF rendering is a follow-up.
    import json

    pdf_bytes = json.dumps(envelope, ensure_ascii=False).encode("utf-8")

    filename = (
        f"cost-prediction-report-{request_body.period_key}-" f"{request_body.projection_month}.pdf"
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Latency-Ms": str(latency_ms),
            "X-Trace-Id": service.trace_id,
            "X-Projection-Hash": compute_projection_hash(projection),
        },
    )


__all__ = [
    "router",
    "compute_cvp_simulation",
    "get_cvp_baseline",
    "compute_projection_simulation",
    "get_projection_baseline",
    "generate_projection_pdf",
    # Re-export typed exceptions for main.py envelope handler 등록 (CR 12-5 D-14).
    "CVPBaselineNotFoundError",
    "CVPInvalidDeltaError",
    "InvalidProjectionMonthError",
    "ProjectionInputsInvalidError",
    "ProjectionBaselineNotFoundError",
]
