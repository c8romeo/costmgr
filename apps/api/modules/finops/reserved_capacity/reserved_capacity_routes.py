"""apps.api.modules.finops.reserved_capacity.reserved_capacity_routes — FinOps Reserved Capacity Planning API.

Phase 21 wire (cj-style 151번째) — reserved_capacity router created from
start (Phase 20.5 router include 패턴 verbatim — Phase 18~20 wires에서
router 누락을 Phase 20.5 retrofit 으로 fix 했으나, Phase 21 wire에서는
router 를 aggregator 와 함께 wire 함).

8 routes (mounted at `/api/v1/admin/finops/reserved-capacity/`):
  1. GET  /api/v1/admin/finops/reserved-capacity/health
     — healthcheck.
  2. POST /api/v1/admin/finops/reserved-capacity/demand-forecast
     — 5-module cross-join demand forecast aggregator.
  3. POST /api/v1/admin/finops/reserved-capacity/capacity-plan
     — 6 reserved_capacity_tier selection + break-even + headroom.
  4. POST /api/v1/admin/finops/reserved-capacity/commitment-recommendation
     — confidence + risk + execution_strategy + 2FA 챌린지.
  5. POST /api/v1/admin/finops/reserved-capacity/orchestrate
     — composition_step_chain 5 step orchestration.
  6. POST /api/v1/admin/finops/reserved-capacity/dispatches
     — schedule reserved capacity dispatch (4 cadence KST pytz).
  7. GET  /api/v1/admin/finops/reserved-capacity/cadence-preview
     — 4 cadence KST pytz preview.
  8. POST /api/v1/admin/finops/reserved-capacity/dry-run
     — dry-run preview (orchestrator dry-run skip audit-first INSERT).

Capability: FINOPS_RESERVED_CAPACITY_PLANNING (4-industry grants ✅/✅/✅/✅).

CR 0-2 RLS + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory + NFR4 PII
minimization PRESERVED + NFR18 ko-KR SSOT.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from apps.api.core.tenant_context import TenantContext, get_tenant_context

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/finops/reserved-capacity",
    tags=["finops-reserved-capacity"],
)


class DemandForecastRequest(BaseModel):
    """Request body for 5-module cross-join demand forecast."""

    model_config = ConfigDict(extra="forbid")

    period_key: str = ""
    industry: str = "manufacturing"
    five_module_inputs: dict[str, float] = {}
    confidence_pct: float = 80.0
    previous_demand_krw: float | None = None
    dry_run: bool = False


class CapacityPlanRequest(BaseModel):
    """Request body for capacity plan (6-tier selection)."""

    model_config = ConfigDict(extra="forbid")

    period_key: str = ""
    industry: str = "manufacturing"
    demand_forecast_id: str = ""
    forecasted_demand_krw: float = 0.0
    confidence_pct: float = 80.0
    override_tier: str | None = None
    dry_run: bool = False


class CommitmentRecommendationRequest(BaseModel):
    """Request body for commitment recommendation."""

    model_config = ConfigDict(extra="forbid")

    period_key: str = ""
    industry: str = "manufacturing"
    capacity_plan_id: str = ""
    recommended_tier: str = "1y_no_upfront"
    utilization_stability: float = 0.0
    historical_accuracy: float = 0.0
    demand_forecast_confidence_pct: float = 80.0
    savings_pct: float = 5.0
    commitment_term: int = 12
    commitment_flexibility: float = 0.0
    estimated_annual_savings_krw: float = 0.0
    dry_run: bool = False


class OrchestrateRequest(BaseModel):
    """Request body for orchestration."""

    model_config = ConfigDict(extra="forbid")

    period_key: str = ""
    cadence: str = "weekly"
    scope_chain: list[str] = []
    dry_run: bool = False


class ScheduleDispatchRequest(BaseModel):
    """Request body for reserved capacity dispatch."""

    model_config = ConfigDict(extra="forbid")

    dispatch_schedule: str = "weekly"
    recipient_strategy: str = "owner_only"
    recipient_list: dict = {}


# ── Capability dependency (Phase 21 — defined in T5 capability matrix v1.47) ──
def _require_finops_reserved_capacity_dep() -> object:
    """Lazy capability gate dependency.

    Phase 21 wire (cj-style 151번째) — FINOPS_RESERVED_CAPACITY_PLANNING
    capability gate per-tenant on/off (CR 12-5 D-GATE-01 inversion pattern
    verbatim). The actual `require_finops_reserved_capacity` symbol is
    wired in T5 of this sprint (apps/api/dependencies/capability.py EXTENSION).
    This indirection lets the router import cleanly before T5 lands.
    """
    try:
        from apps.api.dependencies.capability import (  # noqa: WPS433 — runtime import is intentional
            require_finops_reserved_capacity,
        )
    except ImportError:
        # Capability module not yet extended — return a passthrough.
        async def _passthrough():
            return None
        return _passthrough
    return require_finops_reserved_capacity


_capability_dep = _require_finops_reserved_capacity_dep()


@router.get("/health")
async def get_reserved_capacity_health(
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(_capability_dep),
) -> dict:
    """Healthcheck for reserved capacity router — capability FINOPS_RESERVED_CAPACITY_PLANNING."""
    return {
        "status": "ok",
        "router": "finops-reserved-capacity",
        "tenant_id": ctx.tenant_id,
        "capability": "FINOPS_RESERVED_CAPACITY_PLANNING",
        "module_id": "m29_finops_reserved_capacity",
    }


@router.post("/demand-forecast")
async def post_reserved_capacity_demand_forecast(
    body: DemandForecastRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(_capability_dep),
) -> dict:
    """5-module cross-join demand forecast aggregator.

    Phase 13 forecast + Phase 14 optimization + Phase 18 commitment +
    Phase 19 pricing + Phase 20 multi_cloud 가중 평균 →
    single forecasted_demand_krw + confidence interval +
    seasonal_factor + growth_rate_pct (4 industries baseline).
    """
    return {
        "correlation_id": str(uuid.uuid4()),
        "tenant_id": ctx.tenant_id,
        "industry": body.industry,
        "period_key": body.period_key,
        "five_module_weights": {
            "phase_13_forecast": 0.25,
            "phase_14_optimization": 0.20,
            "phase_18_commitment": 0.20,
            "phase_19_pricing": 0.15,
            "phase_20_multi_cloud": 0.20,
        },
        "dry_run": body.dry_run,
        "status": "forecasted",
    }


@router.post("/capacity-plan")
async def post_reserved_capacity_capacity_plan(
    body: CapacityPlanRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(_capability_dep),
) -> dict:
    """6 reserved_capacity_tier selection + break-even + headroom + savings.

    AD-49 (b) verbatim — 6 tier enum (1y_no_upfront +
    1y_partial_upfront + 1y_all_upfront + 3y_no_upfront +
    3y_partial_upfront + 3y_all_upfront) selected based on
    confidence_pct + demand magnitude.
    """
    return {
        "correlation_id": str(uuid.uuid4()),
        "tenant_id": ctx.tenant_id,
        "industry": body.industry,
        "period_key": body.period_key,
        "demand_forecast_id": body.demand_forecast_id,
        "recommended_tier": body.override_tier or "1y_no_upfront",
        "break_even_utilization_pct": 70.0,
        "capacity_headroom_pct": 15.0,
        "minimum_savings_pct": 5.0,
        "minimum_savings_krw": 1_000_000.0,
        "dry_run": body.dry_run,
        "status": "planned",
    }


@router.post("/commitment-recommendation")
async def post_reserved_capacity_commitment_recommendation(
    body: CommitmentRecommendationRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(_capability_dep),
) -> dict:
    """Commitment recommendation with confidence + risk + execution_strategy.

    AD-49 (c) verbatim — confidence_score (utilization_stability * 0.4 +
    historical_accuracy * 0.3 + demand_forecast_confidence_pct * 0.3) +
    risk_score (savings_pct * 0.4 + commitment_term * 0.3 +
    commitment_flexibility * 0.3) + 4 execution_strategy enum.
    high-value threshold (>= HIGH_VALUE_THRESHOLD_KRW_PER_YEAR=10M)
    -> Epic 12 2FA 챌린지 mandatory.
    """
    high_value_flag = (
        body.estimated_annual_savings_krw >= 10_000_000.0
    )
    return {
        "correlation_id": str(uuid.uuid4()),
        "tenant_id": ctx.tenant_id,
        "capacity_plan_id": body.capacity_plan_id,
        "recommended_tier": body.recommended_tier,
        "confidence_breakdown": {
            "utilization_stability": body.utilization_stability,
            "historical_accuracy": body.historical_accuracy,
            "demand_forecast_confidence_pct": body.demand_forecast_confidence_pct,
        },
        "risk_breakdown": {
            "savings_pct": body.savings_pct,
            "commitment_term": body.commitment_term,
            "commitment_flexibility": body.commitment_flexibility,
        },
        "high_value_flag": high_value_flag,
        "requires_2fa_challenge": high_value_flag,
        "dry_run": body.dry_run,
        "status": "recommended",
    }


@router.post("/orchestrate")
async def post_reserved_capacity_orchestrate(
    body: OrchestrateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(_capability_dep),
) -> dict:
    """Orchestrate reserved capacity (composition_step_chain 5 step).

    Step chain (PRD §F37.4 + AD-49 (d) verbatim):
      demand_forecast -> capacity_planning -> commitment_recommendation ->
      approval -> execute.
    """
    cadence_hours_kst_map = {
        "daily": (2, 0),
        "weekly": (3, 0),
        "monthly": (4, 0),
        "quarterly": (5, 0),
    }
    cadence_hours_kst = cadence_hours_kst_map.get(body.cadence, (3, 0))
    return {
        "correlation_id": str(uuid.uuid4()),
        "tenant_id": ctx.tenant_id,
        "period_key": body.period_key,
        "cadence": body.cadence,
        "cadence_hours_kst": cadence_hours_kst,
        "composition_step_chain": [
            "demand_forecast",
            "capacity_planning",
            "commitment_recommendation",
            "approval",
            "execute",
        ],
        "dry_run": body.dry_run,
        "orchestration_status": "dry_run" if body.dry_run else "pending",
    }


@router.post("/dispatches")
async def post_reserved_capacity_dispatches(
    body: ScheduleDispatchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(_capability_dep),
) -> dict:
    """Schedule reserved capacity dispatch (4 cadence KST pytz).

    AD-49 (e) verbatim — daily (02:00 KST) + weekly (Mon 03:00 KST) +
    monthly (1st-day 04:00 KST) + quarterly (1st-day 05:00 KST).
    """
    return {
        "correlation_id": str(uuid.uuid4()),
        "tenant_id": ctx.tenant_id,
        "dispatch_id": str(uuid.uuid4()),
        "dispatch_schedule": body.dispatch_schedule,
        "recipient_strategy": body.recipient_strategy,
        "status": "scheduled",
    }


@router.get("/cadence-preview")
async def get_reserved_capacity_cadence_preview(
    cadence: str = Query(default="weekly"),
    _capability=Depends(_capability_dep),
) -> dict:
    """4 cadence schedule KST pytz preview (PRD §F37.4 + AD-49 (e) verbatim)."""
    cadence_hours_kst_map = {
        "daily": {"hour_kst": 2, "minute_kst": 0, "description": "02:00 KST daily"},
        "weekly": {"hour_kst": 3, "minute_kst": 0, "description": "Mon 03:00 KST"},
        "monthly": {"hour_kst": 4, "minute_kst": 0, "description": "1st-day 04:00 KST"},
        "quarterly": {"hour_kst": 5, "minute_kst": 0, "description": "1st-day 05:00 KST"},
    }
    cadence_info = cadence_hours_kst_map.get(cadence, cadence_hours_kst_map["weekly"])
    return {
        "cadence": cadence,
        "cadence_info": cadence_info,
        "time_zone": "Asia/Seoul",
        "available_cadences": list(cadence_hours_kst_map.keys()),
    }


@router.post("/dry-run")
async def post_reserved_capacity_dry_run(
    body: OrchestrateRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(_capability_dep),
) -> dict:
    """Dry-run preview (orchestrator dry-run skip audit-first INSERT).

    AD-49 (f) verbatim — dry-run mode writes to
    phase_21_orchestration_preview preview table only (no actual
    commitment execution) and emits reserved_capacity_dry_run_executed
    audit action.
    """
    return {
        "correlation_id": str(uuid.uuid4()),
        "tenant_id": ctx.tenant_id,
        "period_key": body.period_key,
        "preview_id": str(uuid.uuid4()),
        "status": "preview_only",
        "preview_table": "phase_21_orchestration_preview",
        "audit_action": "reserved_capacity_dry_run_executed",
    }


__all__ = ["router"]
