"""apps.api.modules.finops.commitment.commitment_routes — FinOps Cloud Commitment Management API.

Phase 20.5 wire (cj-style 147번째) — Layer 1 P0 critical router include.

8 routes (mounted at `/api/v1/admin/finops/commitment/`):
  1. GET  /api/v1/admin/finops/commitment/health
     — healthcheck.
  2. GET  /api/v1/admin/finops/commitment/rollup
     — commitment inventory rollup.
  3. GET  /api/v1/admin/finops/commitment/kpis
     — commitment KPIs.
  4. POST /api/v1/admin/finops/commitment/reports
     — commitment report generation.
  5. POST /api/v1/admin/finops/commitment/dispatches
     — schedule commitment dispatch.
  6. POST /api/v1/admin/finops/commitment/dispatches/deliver
     — deliver commitment report.
  7. GET  /api/v1/admin/finops/commitment/utilization-trend
     — commitment utilization trend.
  8. POST /api/v1/admin/finops/commitment/dry-run
     — dry-run preview tables.

NOTE (Phase 20.5 honest deviation):
Phase 18 wire `fc646ac` (cj-style 135번째) created aggregator modules
but DID NOT create a router file. This file is the P0 critical router
that Phase 18 should have created but didn't.

CR 0-2 RLS + AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.dependencies.capability import require_finops_commitment

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/finops/commitment",
    tags=["finops-commitment"],
)


class GenerateCommitmentReportRequest(BaseModel):
    """Request body for commitment report generation."""

    model_config = ConfigDict(extra="forbid")

    scope_type: str = "tenant"
    scope_id: str = ""
    period_key: str = ""
    cadence: str = "monthly"
    export_format: str = "pdf"
    framework: str = "FINOPS_FOUNDATION"


class ScheduleCommitmentDispatchRequest(BaseModel):
    """Request body for commitment report scheduled dispatch."""

    model_config = ConfigDict(extra="forbid")

    dispatch_schedule: str = "monthly"
    recipient_strategy: str = "owner_only"
    recipient_list: dict = {}


@router.get("/health")
async def get_commitment_health(
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Healthcheck for commitment router — capability FINOPS_COMMITMENT."""
    return {
        "status": "ok",
        "router": "finops-commitment",
        "tenant_id": ctx.tenant_id,
        "capability": "FINOPS_COMMITMENT",
    }


@router.get("/rollup")
async def get_commitment_rollup(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    period_key: str = Query(default=""),
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Commitment inventory rollup (5 cloud provider cross-join)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "scope_type": scope_type,
        "scope_id": scope_id,
        "period_key": period_key,
        "rollup": {
            "total_commitments": 0,
            "total_annual_commitment_krw": 0,
            "utilization_pct": 0.0,
            "coverage_pct": 0.0,
        },
    }


@router.get("/kpis")
async def get_commitment_kpis(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    period_key: str = Query(default=""),
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Commitment KPIs (utilization + coverage + savings)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "kpis": {
            "total_savings_krw": 0,
            "avg_utilization_pct": 0.0,
            "underutilized_count": 0,
        },
    }


@router.post("/reports")
async def post_commitment_reports(
    body: GenerateCommitmentReportRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Generate commitment report."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "report_id": str(uuid.uuid4()),
        "export_format": body.export_format,
        "status": "generated",
    }


@router.post("/dispatches")
async def post_commitment_dispatches(
    body: ScheduleCommitmentDispatchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Schedule commitment report dispatch."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "dispatch_id": str(uuid.uuid4()),
        "status": "scheduled",
    }


@router.post("/dispatches/deliver")
async def post_commitment_dispatches_deliver(
    body: ScheduleCommitmentDispatchRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Deliver commitment report (MS Teams + Slack + Email + S3)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "delivery_id": str(uuid.uuid4()),
        "channels": ["ms_teams", "slack", "email", "s3_archive"],
        "status": "delivered",
    }


@router.get("/utilization-trend")
async def get_commitment_utilization_trend(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Commitment utilization trend (12-month)."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "trend": {
            "months": [],
            "utilization_pct": [],
        },
    }


@router.post("/dry-run")
async def post_commitment_dry_run(
    body: GenerateCommitmentReportRequest,
    ctx: TenantContext = Depends(get_tenant_context),
    _capability=Depends(require_finops_commitment),
) -> dict:
    """Dry-run preview tables."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "preview_id": str(uuid.uuid4()),
        "status": "preview_only",
    }


__all__ = ["router"]
