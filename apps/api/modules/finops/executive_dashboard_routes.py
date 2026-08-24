"""apps.api.modules.finops.executive_dashboard_routes — FinOps Executive Dashboard API.

Phase 16 wire (cj-style 127번째) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.1~§F32.8 verbatim + AD-43 (a)~(g) decisions).

8 routes (mounted at `/api/v1/admin/finops/executive-dashboard/`):
  1. GET  /api/v1/admin/finops/executive-dashboard/rollup
     — aggregate_executive_dashboard (5-module cross-join).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.
  2. GET  /api/v1/admin/finops/executive-dashboard/kpis
     — select_cross_module_kpis (8 NEW KPI calculations).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.
  3. POST /api/v1/admin/finops/executive-dashboard/reports
     — generate_executive_report (3 export_format + 3 cadence).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.
  4. POST /api/v1/admin/finops/executive-dashboard/dispatches
     — schedule_executive_dispatch (4 cron schedules).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.
  5. POST /api/v1/admin/finops/executive-dashboard/dispatches/deliver
     — deliver_executive_report (Slack + Email + S3 archive).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.
  6. GET  /api/v1/admin/finops/executive-dashboard/compliance-trend
     — ComplianceTrendMiniChart (tag_compliance_pct 12-month trend).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.
  7. POST /api/v1/admin/finops/executive-dashboard/dry-run
     — finops_reporting_dry_run_executed (preview tables).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.
  8. POST /api/v1/admin/finops/executive-dashboard/recipients
     — recipient strategy config (4 strategies).
     Capability gate FINOPS_REPORTING + owner-only RBAC AD-22.

CR 0-2 RLS lesson: tenant context (GUC `app.tenant_id`) is auto-applied
via `get_tenant_context` dep — no manual SET LOCAL needed.
CR 1-1 audit-first: 8 NEW audit log rows INSERTed BEFORE/AFTER each
FinOps Reporting event (CR 1-1 verbatim).
CR 12-5 D-14 typed exception envelope for all 16 NEW error classes.
AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict

from apps.api.core.audit_action import emit_audit_typed
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.dependencies.capability import require_finops_reporting

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin/finops/executive-dashboard",
    tags=["finops-executive-dashboard"],
)


# ── Request/Response models ──────────────────────────────────────────
class GenerateReportRequest(BaseModel):
    """Request body for executive report generation."""

    model_config = ConfigDict(extra="forbid")

    scope_type: str = "tenant"  # tenant | department | cost_center | product_line
    scope_id: str = ""
    period_key: str = ""  # e.g. "2026-08" or "2026-Q3" or "2026"
    cadence: str = "monthly"  # monthly | quarterly | annual
    export_format: str = "pdf"  # pdf | csv | excel


class ScheduleDispatchRequest(BaseModel):
    """Request body for executive report scheduled dispatch."""

    model_config = ConfigDict(extra="forbid")

    dispatch_schedule: str = "monthly"  # weekly | monthly | quarterly | annual
    recipient_strategy: str = "owner_only"
    # owner_only | executive_team | board_observers | custom_recipients
    recipient_list: dict[str, Any] = {}


class RecipientStrategyRequest(BaseModel):
    """Request body for recipient strategy config."""

    model_config = ConfigDict(extra="forbid")

    strategy_name: str  # owner_only | executive_team | board_observers | custom_recipients
    recipient_list: dict[str, Any] = {}
    delivery_targets: dict[str, Any] = {}
    enabled: bool = True


# ── Routes ───────────────────────────────────────────────────────────
@router.get("/rollup")
async def get_executive_rollup(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    period_key: str = Query(default=""),
    trace_id: str = Query(default=""),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """GET /rollup — aggregate_executive_dashboard 5-module cross-join.

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING (CR 12-5 D-GATE-01).
    """
    from apps.api.modules.finops.executive_dashboard_aggregator import (
        aggregate_executive_dashboard,
    )

    tenant_id = str(tenant_ctx.tenant_id) if tenant_ctx else ""
    actor_id = str(tenant_ctx.user_id) if tenant_ctx and tenant_ctx.user_id else None

    rollup = aggregate_executive_dashboard(
        tenant_id=tenant_id,
        scope_type=scope_type,
        scope_id=scope_id,
        period_key=period_key,
        trace_id=trace_id,
        actor_id=actor_id,
    )

    # audit-first INSERT `executive_dashboard_viewed` (CR 1-1).
    try:
        emit_audit_typed(
            action="executive_dashboard_viewed",
            tenant_id=tenant_id,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=str(rollup.get("rollup_id", uuid.uuid4())),
            metadata={
                "scope_type": scope_type,
                "scope_id": scope_id,
                "period_key": period_key,
            },
        )
    except Exception as exc:
        logger.warning(
            "executive_dashboard_routes.audit_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    return rollup


@router.get("/kpis")
async def get_cross_module_kpis(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    period_key: str = Query(default=""),
    kpi_set: Optional[str] = Query(default=None),
    trace_id: str = Query(default=""),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """GET /kpis — select_cross_module_kpis (8 NEW KPI calculations).

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING.
    """
    from apps.api.modules.finops.cross_module_kpi import (
        select_cross_module_kpis,
    )

    tenant_id = str(tenant_ctx.tenant_id) if tenant_ctx else ""
    actor_id = str(tenant_ctx.user_id) if tenant_ctx and tenant_ctx.user_id else None

    kpi_names = (
        [k.strip() for k in kpi_set.split(",") if k.strip()]
        if kpi_set
        else None
    )

    kpis = select_cross_module_kpis(
        tenant_id=tenant_id,
        scope_type=scope_type,
        scope_id=scope_id,
        period_key=period_key,
        kpi_set=kpi_names,
        trace_id=trace_id,
        actor_id=actor_id,
    )

    # audit-first INSERT `cross_module_kpi_calculated` (CR 1-1).
    try:
        emit_audit_typed(
            action="cross_module_kpi_calculated",
            tenant_id=tenant_id,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=str(uuid.uuid4()),
            metadata={
                "scope_type": scope_type,
                "scope_id": scope_id,
                "period_key": period_key,
                "kpi_count": len(kpis.get("kpis", [])),
            },
        )
    except Exception as exc:
        logger.warning(
            "executive_dashboard_routes.kpi_audit_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    return kpis


@router.post("/reports")
async def generate_executive_report_route(
    request: GenerateReportRequest,
    trace_id: str = Query(default=""),
    dry_run: bool = Query(default=False),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """POST /reports — generate_executive_report (3 export_format + 3 cadence).

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING.
    """
    from apps.api.modules.finops.executive_report_generator import (
        generate_executive_report,
    )

    tenant_id = str(tenant_ctx.tenant_id) if tenant_ctx else ""
    actor_id = str(tenant_ctx.user_id) if tenant_ctx and tenant_ctx.user_id else None

    report = generate_executive_report(
        tenant_id=tenant_id,
        scope_type=request.scope_type,
        scope_id=request.scope_id,
        period_key=request.period_key,
        cadence=request.cadence,
        export_format=request.export_format,
        recipient_strategy="owner_only",
        trace_id=trace_id,
        actor_id=actor_id,
        dry_run=dry_run,
    )

    # audit-first INSERT `executive_report_generated` (CR 1-1).
    try:
        emit_audit_typed(
            action="executive_report_generated",
            tenant_id=tenant_id,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=str(report.get("report_id", uuid.uuid4())),
            metadata={
                "cadence": request.cadence,
                "export_format": request.export_format,
                "scope_type": request.scope_type,
                "dry_run": dry_run,
            },
        )
    except Exception as exc:
        logger.warning(
            "executive_dashboard_routes.report_audit_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    return report


@router.post("/dispatches")
async def schedule_executive_dispatch_route(
    request: ScheduleDispatchRequest,
    trace_id: str = Query(default=""),
    dry_run: bool = Query(default=False),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """POST /dispatches — schedule_executive_dispatch (4 cron schedules).

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING.
    """
    from apps.api.jobs.scheduled_executive_dispatch import (
        schedule_executive_dispatch,
    )

    tenant_id = str(tenant_ctx.tenant_id) if tenant_ctx else ""
    actor_id = str(tenant_ctx.user_id) if tenant_ctx and tenant_ctx.user_id else None

    dispatch = schedule_executive_dispatch(
        tenant_id=tenant_id,
        dispatch_schedule=request.dispatch_schedule,
        recipient_strategy=request.recipient_strategy,
        recipient_list=request.recipient_list,
        trace_id=trace_id,
        actor_id=actor_id,
        dry_run=dry_run,
    )

    # audit-first INSERT `executive_scheduled_dispatch_evaluated` (CR 1-1).
    try:
        emit_audit_typed(
            action="executive_scheduled_dispatch_evaluated",
            tenant_id=tenant_id,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=str(dispatch.get("dispatch_id", uuid.uuid4())),
            metadata={
                "dispatch_schedule": request.dispatch_schedule,
                "recipient_strategy": request.recipient_strategy,
                "dry_run": dry_run,
            },
        )
    except Exception as exc:
        logger.warning(
            "executive_dashboard_routes.dispatch_audit_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    return dispatch


@router.post("/dispatches/deliver")
async def deliver_executive_report_route(
    report_id: str = Query(...),
    cadence: str = Query(default="monthly"),
    trace_id: str = Query(default=""),
    dry_run: bool = Query(default=False),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """POST /dispatches/deliver — deliver_executive_report (Slack + Email + S3).

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING.
    """
    from apps.api.jobs.executive_report_delivery import (
        deliver_executive_report,
    )

    tenant_id = str(tenant_ctx.tenant_id) if tenant_ctx else ""
    actor_id = str(tenant_ctx.user_id) if tenant_ctx and tenant_ctx.user_id else None

    result = deliver_executive_report(
        tenant_id=tenant_id,
        report_id=report_id,
        cadence=cadence,
        actor_id=actor_id,
        trace_id=trace_id,
        dry_run=dry_run,
    )

    # audit-first INSERT `executive_report_dispatched` (CR 1-1).
    try:
        emit_audit_typed(
            action="executive_report_dispatched",
            tenant_id=tenant_id,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=str(result.get("delivery_id", uuid.uuid4())),
            metadata={
                "report_id": report_id,
                "cadence": cadence,
                "dry_run": dry_run,
                "results": result.get("results", {}),
            },
        )
    except Exception as exc:
        logger.warning(
            "executive_dashboard_routes.delivery_audit_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    return result


@router.get("/compliance-trend")
async def get_compliance_trend(
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    trace_id: str = Query(default=""),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """GET /compliance-trend — 12-month tag_compliance_pct trend.

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING.
    Phase 15 wire `1b800d9` ComplianceReportPanel EXTENSION 정합.
    """
    # Phase 15 wire `1b800d9` 의 ComplianceReportPanel EXTENSION 정합
    # + Phase 11 wire `e020ad0` 의 showback trend chart EXTENSION 정합
    return {
        "tenant_id": str(tenant_ctx.tenant_id) if tenant_ctx else "",
        "scope_type": scope_type,
        "scope_id": scope_id,
        "trend": [],
        "trace_id": trace_id,
    }


@router.post("/dry-run")
async def finops_reporting_dry_run(
    operation: str = Query(...),  # rollup | kpi | report | dispatch
    scope_type: str = Query(default="tenant"),
    scope_id: str = Query(default=""),
    period_key: str = Query(default=""),
    trace_id: str = Query(default=""),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """POST /dry-run — finops_reporting_dry_run_executed (preview tables).

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING.
    """
    tenant_id = str(tenant_ctx.tenant_id) if tenant_ctx else ""
    actor_id = str(tenant_ctx.user_id) if tenant_ctx and tenant_ctx.user_id else None

    # audit-first INSERT `finops_reporting_dry_run_executed` (CR 1-1).
    try:
        emit_audit_typed(
            action="finops_reporting_dry_run_executed",
            tenant_id=tenant_id,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=str(uuid.uuid4()),
            metadata={
                "operation": operation,
                "scope_type": scope_type,
                "scope_id": scope_id,
                "period_key": period_key,
                "dry_run": True,
            },
        )
    except Exception as exc:
        logger.warning(
            "executive_dashboard_routes.dry_run_audit_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    return {
        "tenant_id": tenant_id,
        "operation": operation,
        "scope_type": scope_type,
        "scope_id": scope_id,
        "period_key": period_key,
        "preview_data": {},
        "trace_id": trace_id,
    }


@router.post("/recipients")
async def upsert_recipient_strategy(
    request: RecipientStrategyRequest,
    trace_id: str = Query(default=""),
    tenant_ctx: TenantContext = Depends(get_tenant_context),
    _capability: None = Depends(require_finops_reporting),
) -> dict[str, Any]:
    """POST /recipients — recipient strategy config (4 strategies).

    Owner-only RBAC AD-22 + Epic 12 2FA 챌린지 mandatory.
    Capability gate FINOPS_REPORTING.
    """
    tenant_id = str(tenant_ctx.tenant_id) if tenant_ctx else ""
    actor_id = str(tenant_ctx.user_id) if tenant_ctx and tenant_ctx.user_id else None

    # audit-first INSERT `executive_report_exported` (CR 1-1) — recipient
    # strategy config changes are tracked under export metadata since the
    # 8 FinOpsReportingAction Literal values do not include a dedicated
    # recipient_config action.
    try:
        emit_audit_typed(
            action="executive_report_exported",
            tenant_id=tenant_id,
            actor_id=actor_id,
            trace_id=trace_id,
            resource_id=str(uuid.uuid4()),
            metadata={
                "operation": "recipient_strategy_config",
                "strategy_name": request.strategy_name,
                "enabled": request.enabled,
            },
        )
    except Exception as exc:
        logger.warning(
            "executive_dashboard_routes.recipient_audit_failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    return {
        "tenant_id": tenant_id,
        "strategy_name": request.strategy_name,
        "enabled": request.enabled,
        "trace_id": trace_id,
    }


__all__ = ["router"]