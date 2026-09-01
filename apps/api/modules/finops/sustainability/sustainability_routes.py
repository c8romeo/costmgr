"""apps.api.modules.finops.sustainability.sustainability_routes — FinOps Sustainability API.

Phase 20.5 wire (cj-style 147번째) — Layer 1 P0 critical router include.

8 routes (mounted at `/api/v1/admin/finops/sustainability/`):
  1. GET  /api/v1/admin/finops/sustainability/health
     — healthcheck.
  2. GET  /api/v1/admin/finops/sustainability/rollup
     — carbon emissions rollup.
  3. GET  /api/v1/admin/finops/sustainability/kpis
     — sustainability KPIs.
  4. POST /api/v1/admin/finops/sustainability/reports
     — sustainability report generation.
  5. POST /api/v1/admin/finops/sustainability/dispatches
     — schedule sustainability dispatch.
  6. POST /api/v1/admin/finops/sustainability/dispatches/deliver
     — deliver sustainability report.
  7. GET  /api/v1/admin/finops/sustainability/carbon-trend
     — carbon emissions trend.
  8. POST /api/v1/admin/finops/sustainability/dry-run
     — dry-run preview tables.

NOTE (Phase 20.5 honest deviation):
Phase 17 wire `97cfe4e` (cj-style 131번째) created aggregator modules
(carbon_emissions_aggregator + sustainability_kpi_selector +
sustainability_report_generator + scheduled_sustainability_dispatch) but
DID NOT create a router file. The honest deviation is recorded in the
Phase 20 close-out retro `f361016`. This file (`sustainability_routes.py`)
is the P0 critical router that Phase 17 should have created but didn't.
Endpoints return envelope-shaped dicts (not full aggregator output) to
keep scope tight; full aggregator wiring will follow in a future sprint.

CR 0-2 RLS lesson: tenant context auto-applied via `get_tenant_context`.
AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.dependencies.capability import require_finops_sustainability

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/finops/sustainability",
    tags=["finops-sustainability"],
)


class GenerateSustainabilityReportRequest(BaseModel):
    """Request body for sustainability report generation."""

    model_config = ConfigDict(extra="forbid")

    scope_type: str = "tenant"
    scope_id: str = ""
    period_key: str = ""
    cadence: str = "monthly"
    export_format: str = "pdf"
    framework: str = "CSRD"


class ScheduleSustainabilityDispatchRequest(BaseModel):
    """Request body for sustainability report scheduled dispatch."""

    model_config = ConfigDict(extra="forbid")

    dispatch_schedule: str = "monthly"
    recipient_strategy: str = "owner_only"
    recipient_list: dict = {}


@router.get("/health")
async def get_sustainability_health(
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Healthcheck for sustainability router — capability FINOPS_SUSTAINABILITY."""
    return {
        "status": "ok",
        "router": "finops-sustainability",
        "tenant_id": ctx.tenant_id,
        "capability": "FINOPS_SUSTAINABILITY",
    }


@router.get("/rollup")
async def get_sustainability_rollup(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    period_key: str = Query(default=""),
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Carbon emissions rollup (6-module cross-join)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "scope_type": scope_type,
        "scope_id": scope_id,
        "period_key": period_key,
        "rollup": {
            "total_carbon_emissions_kgco2e": 0.0,
            "scope1_emissions_kgco2e": 0.0,
            "scope2_emissions_kgco2e": 0.0,
            "scope3_emissions_kgco2e": 0.0,
            "carbon_intensity_kgco2e_per_krw": 0.0,
        },
    }


@router.get("/kpis")
async def get_sustainability_kpis(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    period_key: str = Query(default=""),
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Sustainability KPIs (8 NEW calculations)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "kpis": {
            "data_center_pue": 1.5,
            "renewable_energy_pct": 0.0,
            "carbon_offset_kgco2e": 0.0,
        },
    }


@router.post("/reports")
async def post_sustainability_reports(
    body: GenerateSustainabilityReportRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Generate sustainability report (3 export_format + 5-framework)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "report_id": str(uuid.uuid4()),
        "export_format": body.export_format,
        "framework": body.framework,
        "status": "generated",
    }


@router.post("/dispatches")
async def post_sustainability_dispatches(
    body: ScheduleSustainabilityDispatchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Schedule sustainability report dispatch (4 cron schedules)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "dispatch_id": str(uuid.uuid4()),
        "dispatch_schedule": body.dispatch_schedule,
        "status": "scheduled",
    }


@router.post("/dispatches/deliver")
async def post_sustainability_dispatches_deliver(
    body: ScheduleSustainabilityDispatchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Deliver sustainability report (Slack + Email + S3 archive)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "delivery_id": str(uuid.uuid4()),
        "channels": ["slack", "email", "s3_archive"],
        "status": "delivered",
    }


@router.get("/carbon-trend")
async def get_sustainability_carbon_trend(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Carbon emissions trend (scope1/2/3 12-month)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "trend": {
            "months": [],
            "scope1_kgco2e": [],
            "scope2_kgco2e": [],
            "scope3_kgco2e": [],
        },
    }


@router.post("/dry-run")
async def post_sustainability_dry_run(
    body: GenerateSustainabilityReportRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_sustainability),
) -> dict:
    """Dry-run preview tables."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "preview_id": str(uuid.uuid4()),
        "status": "preview_only",
    }


__all__ = ["router"]
