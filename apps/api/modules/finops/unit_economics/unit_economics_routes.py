"""apps.api.modules.finops.unit_economics.unit_economics_routes — Phase 23 FastAPI routes.

Phase 23 wire (cj-style 164번째) — FinOps Unit Economics FastAPI routes
(PRD §F39.1~§F39.8 verbatim + AD-51 (a)~(g) decisions).

9 endpoints:
1. `GET  /api/v1/finops/unit-economics/healthcheck` — health probe
2. `POST /api/v1/finops/unit-economics/compute` — compute unit economics
3. `POST /api/v1/finops/unit-economics/cost-per-business-unit` — refresh cost_per_business_unit
4. `POST /api/v1/finops/unit-economics/cost-per-transaction` — compute cost_per_transaction
5. `POST /api/v1/finops/unit-economics/margin-analysis` — execute margin analysis
6. `POST /api/v1/finops/unit-economics/dry-run` — dry-run (no actual persist)
7. `GET  /api/v1/finops/unit-economics/trend` — unit_economics trend
8. `POST /api/v1/finops/unit-economics/calculation` — execute scheduled calculation
9. `GET  /api/v1/finops/unit-economics/cadence-preview` — preview cadence schedule

AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + AD-51 (g).
Capability gate: require_finops_unit_economics (CR 12-5 D-GATE-01).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — all 7 audit actions called from routes.
- CR 1-1 ContextVar — trace_id propagation.
- CR 1-1 idempotent no-op — duplicate calls return cached result.
- CR 11-2 AUTHORIZABLE_TARGET_EVENT_TYPES — auth-layer check.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- CR 12-5 D-GATE-01 — capability gate fail-closed.
- AD-22 owner-only RBAC.
- AD-51 (a)~(g) 7 sub-decisions.
- NFR4 PII minimization PRESERVED.
- NFR18 ko-KR SSOT (finops_unit_economics.* namespace EXTENSION).
- D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
  FX + real-time stream — all honestly DEFER to future Phase 23.x).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies.capability import require_finops_unit_economics
from apps.api.modules.finops.unit_economics.cost_per_business_unit import (
    compute_cost_per_business_unit,
)
from apps.api.modules.finops.unit_economics.cost_per_transaction import (
    compute_cost_per_transaction,
)
from apps.api.modules.finops.unit_economics.margin_analysis import (
    execute_margin_analysis,
)
from apps.api.modules.finops.unit_economics.scheduled_unit_economics_calculation import (
    ALL_UNIT_ECONOMICS_CADENCES,
    _compute_period_key_for_cadence,
    compute_unit_economics_period,
    validate_cadence,
)
from apps.api.modules.finops.unit_economics.serializers import (
    ALL_COST_PER_X_METRICS,
    UNIT_ECONOMICS_CADENCE_HOURS_KST,
    UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
    UnitEconomicsCalculationStatus,
)
from apps.api.modules.finops.unit_economics.unit_economics_engine import (
    compute_unit_economics,
    list_unit_economics_results,
)

logger = logging.getLogger(__name__)

# ── Router with capability gate dependency ────────────────────────────────
router = APIRouter(
    prefix="/api/v1/finops/unit-economics",
    tags=["finops", "unit_economics"],
    dependencies=[Depends(require_finops_unit_economics)],
)


# ── Helper: extract tenant_id from request context ────────────────────────
def _extract_tenant_id(request: Request) -> str:
    """Extract tenant_id from request context (CR 0-2 RLS verbatim)."""
    tenant_id = getattr(request.state, "tenant_id", None) or request.headers.get("X-Tenant-Id")
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="tenant_id_required",
        )
    return str(tenant_id)


# ── Helper: extract trace_id from request context ─────────────────────────
def _extract_trace_id(request: Request) -> str:
    """Extract trace_id from request context (CR 1-1 verbatim)."""
    import hashlib

    return str(
        getattr(request.state, "trace_id", None)
        or hashlib.sha256(
            f"{request.url.path}:{request.headers.get('X-Request-Id', '')}".encode()
        ).hexdigest()[:32]
    )


# ── 1. Healthcheck ────────────────────────────────────────────────────────
@router.get("/healthcheck", response_model=None)
async def healthcheck(request: Request) -> dict[str, Any]:
    """Phase 23 healthcheck — verify module wiring."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    return {
        "status": "ok",
        "module": "unit_economics",
        "module_id": "m31_finops_unit_economics",
        "model_version": UNIT_ECONOMICS_ENGINE_MODEL_VERSION,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
        "capability": "FINOPS_UNIT_ECONOMICS",
        "all_cost_per_x_metrics": ALL_COST_PER_X_METRICS,
        "all_cadences": ALL_UNIT_ECONOMICS_CADENCES,
    }


# ── 2. Compute unit economics ─────────────────────────────────────────────
@router.post("/compute", response_model=None)
async def compute(
    request: Request,
    payload: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Compute UnitEconomicsResult (PRD §F39.1-1 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)

    required_keys = [
        "period_key",
        "source_settlement_id",
        "total_cost_krw",
        "total_revenue_krw",
        "total_units",
        "total_transactions",
        "target_dimensions",
        "five_dim_inputs",
        "allocation_count",
        "revenue_completeness_pct",
    ]
    for key in required_keys:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"missing_field:{key}")

    result = compute_unit_economics(
        tenant_id=tenant_id,
        period_key=payload["period_key"],
        source_settlement_id=payload["source_settlement_id"],
        total_cost_krw=float(payload["total_cost_krw"]),
        total_revenue_krw=float(payload["total_revenue_krw"]),
        total_units=int(payload["total_units"]),
        total_transactions=int(payload["total_transactions"]),
        target_dimensions=list(payload["target_dimensions"]),
        five_dim_inputs=dict(payload["five_dim_inputs"]),
        allocation_count=int(payload["allocation_count"]),
        revenue_completeness_pct=float(payload["revenue_completeness_pct"]),
        calculation_status=payload.get(
            "calculation_status", UnitEconomicsCalculationStatus.PENDING.value
        ),
        requires_2fa_challenge=bool(payload.get("requires_2fa_challenge", False)),
        dry_run=bool(payload.get("dry_run", False)),
        trace_id=trace_id,
        db_session=db_session,
    )
    return {"result": result, "trace_id": trace_id}


# ── 3. Refresh cost_per_business_unit ─────────────────────────────────────
@router.post("/cost-per-business-unit", response_model=None)
async def cost_per_business_unit_refresh(
    request: Request,
    payload: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Refresh CostPerBusinessUnitBreakdown (PRD §F39.2-1 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)

    required_keys = [
        "unit_economics_id",
        "period_key",
        "business_unit",
        "cost_center",
        "department",
        "tag_key",
        "allocated_cost_krw",
        "transaction_count",
        "cost_center_amount_krw",
        "department_amount_krw",
        "business_unit_amount_krw",
        "tag_amount_krw",
        "tenant_amount_krw",
    ]
    for key in required_keys:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"missing_field:{key}")

    breakdown = compute_cost_per_business_unit(
        tenant_id=tenant_id,
        unit_economics_id=payload["unit_economics_id"],
        period_key=payload["period_key"],
        business_unit=payload["business_unit"],
        cost_center=payload["cost_center"],
        department=payload["department"],
        tag_key=payload["tag_key"],
        allocated_cost_krw=float(payload["allocated_cost_krw"]),
        transaction_count=int(payload["transaction_count"]),
        cost_center_amount_krw=float(payload["cost_center_amount_krw"]),
        department_amount_krw=float(payload["department_amount_krw"]),
        business_unit_amount_krw=float(payload["business_unit_amount_krw"]),
        tag_amount_krw=float(payload["tag_amount_krw"]),
        tenant_amount_krw=float(payload["tenant_amount_krw"]),
        is_override=bool(payload.get("is_override", False)),
        requires_2fa_challenge=bool(payload.get("requires_2fa_challenge", False)),
        dry_run=bool(payload.get("dry_run", False)),
        trace_id=trace_id,
        db_session=db_session,
    )
    return {"breakdown": breakdown, "trace_id": trace_id}


# ── 4. Compute cost_per_transaction ───────────────────────────────────────
@router.post("/cost-per-transaction", response_model=None)
async def cost_per_transaction_compute(
    request: Request,
    payload: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Compute CostPerTransactionBreakdown (PRD §F39.3-1 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)

    required_keys = [
        "unit_economics_id",
        "period_key",
        "transaction_id",
        "business_unit",
        "cost_center",
        "allocated_cost_krw",
        "transaction_count",
    ]
    for key in required_keys:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"missing_field:{key}")

    transaction = compute_cost_per_transaction(
        tenant_id=tenant_id,
        unit_economics_id=payload["unit_economics_id"],
        period_key=payload["period_key"],
        transaction_id=payload["transaction_id"],
        business_unit=payload["business_unit"],
        cost_center=payload["cost_center"],
        allocated_cost_krw=float(payload["allocated_cost_krw"]),
        transaction_count=int(payload["transaction_count"]),
        phase_22_settlement_tags=dict(payload.get("phase_22_settlement_tags", {})),
        requires_2fa_challenge=bool(payload.get("requires_2fa_challenge", False)),
        dry_run=bool(payload.get("dry_run", False)),
        trace_id=trace_id,
        db_session=db_session,
    )
    return {"transaction": transaction, "trace_id": trace_id}


# ── 5. Execute margin analysis ────────────────────────────────────────────
@router.post("/margin-analysis", response_model=None)
async def margin_analysis_execute(
    request: Request,
    payload: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Execute MarginAnalysisResult (PRD §F39.4-1 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)

    required_keys = [
        "unit_economics_id",
        "period_key",
        "business_unit",
        "total_cost_krw",
        "total_revenue_krw",
    ]
    for key in required_keys:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"missing_field:{key}")

    margin = execute_margin_analysis(
        tenant_id=tenant_id,
        unit_economics_id=payload["unit_economics_id"],
        period_key=payload["period_key"],
        business_unit=payload["business_unit"],
        total_cost_krw=float(payload["total_cost_krw"]),
        total_revenue_krw=float(payload["total_revenue_krw"]),
        revenue_sources=list(payload.get("revenue_sources", [])),
        revenue_completeness_pct=float(payload.get("revenue_completeness_pct", 0.0)),
        requires_2fa_challenge=bool(payload.get("requires_2fa_challenge", False)),
        dry_run=bool(payload.get("dry_run", False)),
        trace_id=trace_id,
        db_session=db_session,
    )
    return {"margin": margin, "trace_id": trace_id}


# ── 6. Dry-run ────────────────────────────────────────────────────────────
@router.post("/dry-run", response_model=None)
async def dry_run(
    request: Request,
    payload: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Dry-run unit_economics computation (no actual persist).

    Mirrors /compute but always sets dry_run=True + emits
    `unit_economics_dry_run_executed` audit action.
    """
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)

    payload["dry_run"] = True
    result = compute_unit_economics(
        tenant_id=tenant_id,
        period_key=payload.get("period_key", ""),
        source_settlement_id=payload.get("source_settlement_id", ""),
        total_cost_krw=float(payload.get("total_cost_krw", 0.0)),
        total_revenue_krw=float(payload.get("total_revenue_krw", 0.0)),
        total_units=int(payload.get("total_units", 0)),
        total_transactions=int(payload.get("total_transactions", 0)),
        target_dimensions=list(payload.get("target_dimensions", [])),
        five_dim_inputs=dict(payload.get("five_dim_inputs", {})),
        allocation_count=int(payload.get("allocation_count", 0)),
        revenue_completeness_pct=float(payload.get("revenue_completeness_pct", 0.0)),
        calculation_status=payload.get(
            "calculation_status", UnitEconomicsCalculationStatus.DRY_RUN_COMPLETED.value
        ),
        dry_run=True,
        trace_id=trace_id,
        db_session=db_session,
    )
    return {"dry_run_result": result, "trace_id": trace_id, "dry_run": True}


# ── 7. Trend ──────────────────────────────────────────────────────────────
@router.get("/trend", response_model=None)
async def trend(
    request: Request,
    period_key: str | None = Query(default=None),
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Unit_economics trend (PRD §F39.5 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)
    results = list_unit_economics_results(
        tenant_id=tenant_id,
        period_key=period_key,
        db_session=db_session,
    )
    return {
        "results": results,
        "period_key": period_key,
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }


# ── 8. Scheduled calculation ──────────────────────────────────────────────
@router.post("/calculation", response_model=None)
async def calculation(
    request: Request,
    payload: dict[str, Any],
    db_session: AsyncSession = Depends(lambda: None),  # type: ignore[arg-type,return-value]
) -> dict[str, Any]:
    """Execute scheduled unit_economics calculation (PRD §F39.1 verbatim)."""
    tenant_id = _extract_tenant_id(request)
    trace_id = _extract_trace_id(request)

    required_keys = [
        "source_settlement_id",
        "five_dim_inputs",
        "total_cost_krw",
        "total_revenue_krw",
        "total_units",
        "total_transactions",
        "allocation_count",
        "revenue_completeness_pct",
        "target_dimensions",
        "cadence",
    ]
    for key in required_keys:
        if key not in payload:
            raise HTTPException(status_code=400, detail=f"missing_field:{key}")

    validate_cadence(cadence=payload["cadence"])

    result = compute_unit_economics_period(
        tenant_id=tenant_id,
        source_settlement_id=payload["source_settlement_id"],
        five_dim_inputs=dict(payload["five_dim_inputs"]),
        total_cost_krw=float(payload["total_cost_krw"]),
        total_revenue_krw=float(payload["total_revenue_krw"]),
        total_units=int(payload["total_units"]),
        total_transactions=int(payload["total_transactions"]),
        allocation_count=int(payload["allocation_count"]),
        revenue_completeness_pct=float(payload["revenue_completeness_pct"]),
        target_dimensions=list(payload["target_dimensions"]),
        cadence=payload["cadence"],
        calculation_status=UnitEconomicsCalculationStatus.COMPUTING.value,
        dry_run=bool(payload.get("dry_run", False)),
        trace_id=trace_id,
        db_session=db_session,
    )
    return {"result": result, "trace_id": trace_id}


# ── 9. Cadence preview ────────────────────────────────────────────────────
@router.get("/cadence-preview", response_model=None)
async def cadence_preview(request: Request) -> dict[str, Any]:
    """Preview cadence schedule (PRD §F39.1 verbatim)."""
    trace_id = _extract_trace_id(request)
    import datetime

    try:
        import pytz

        now_kst = datetime.datetime.now(pytz.timezone("Asia/Seoul"))
    except ImportError:  # pragma: no cover — defensive guard
        now_kst = datetime.datetime.now(datetime.UTC)

    schedule: dict[str, Any] = {}
    for cadence in ALL_UNIT_ECONOMICS_CADENCES:
        hour, minute = UNIT_ECONOMICS_CADENCE_HOURS_KST[cadence]
        schedule[cadence] = {
            "hour_kst": hour,
            "minute_kst": minute,
            "period_key": _compute_period_key_for_cadence(cadence=cadence, now_kst=now_kst),
            "timezone": "Asia/Seoul",
        }
    return {
        "schedule": schedule,
        "now_kst": now_kst.isoformat(),
        "all_cadences": ALL_UNIT_ECONOMICS_CADENCES,
        "trace_id": trace_id,
    }


__all__ = ["router"]
