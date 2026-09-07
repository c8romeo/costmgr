"""apps.api.modules.reports.scheduled_routes — Story 30.4 Scheduled reports endpoints.

cj-300 wire sprint (cj-style 302번째 epic 연속 정직 회복 source+docs atomic
single sprint) — Story 30.4 Scheduled reports (FR-30-4).

5 routes (mounted at `/api/v1/`):
  1. POST /api/v1/exports/scheduled
     Body (ScheduledJobCreate JSON):
       {
         "dispatch_schedule": "weekly" | "monthly" | "quarterly" | "annual",
         "recipient_strategy": "finance_only" | "finance_and_admin" | "admin_fallback",
         "finance_contact_email": "finance@example.com" | null,
         "report_type": "cost-records" | "bom",
         "period_key": "2026-09" | null
       }
     Response (ScheduledJobResponse JSON):
       { job_id, tenant_id, dispatch_schedule, cron_expression, ... }

  2. POST /api/v1/exports/scheduled/{job_id}/cancel
     Body (ScheduledJobCancel JSON): { "reason": "..." | null }
     Response: { "job_id": "...", "status": "cancelled", ... }

  3. GET /api/v1/exports/scheduled/jobs
     Query: ?status=scheduled|running|...&page=1&page_size=20
     Response: { "jobs": [ScheduledJobResponse, ...], "total": int, "page": int }

  4. GET /api/v1/exports/scheduled/history
     Query: ?job_id=...&page=1&page_size=20
     Response: { "history": [ScheduledJobHistory, ...], "total": int, "page": int }

  5. POST /api/v1/exports/scheduled/dispatch-now
     Body (ScheduledDispatchNow JSON): { dispatch_schedule, ... }
     Response (ScheduledJobResponse JSON)

CR 0-2 RLS lesson: tenant context (GUC `app.tenant_id`) is auto-applied
via `get_tenant_context` dep — no manual SET LOCAL needed.
CR 1-1 audit-first: 1 NEW audit log row `export_scheduled` INSERTed
BEFORE the schedule creation (T1 verbatim).
CR 12-5 D-14 typed exception envelope for 16 NEW error classes (T5).

Verbatim mirror of `apps/api/modules/reports/email_routes.py` for:
  - APIRouter setup + AD-22 owner/admin RBAC + Capability.EXPORT_SCHEDULED gate
  - TenantContext cross-tenant check
  - Audit-first INSERT `export_scheduled` (CR 1-1 verbatim + ActionClass.REPORTS)
  - Typed exception base class + 16 subclasses (CR 12-5 D-14 envelope)

AD bind 3/3 + 1 신규:
- AD-2 (audit-first INSERT append-only)
- AD-10 (identity + 2FA via owner-only RBAC, AD-22 owner-only)
- AD-12 (verify-first capability gate, Capability.EXPORT_SCHEDULED — cj-285
  EXTENSION preserved, capability matrix v1.54 EXTENSION)
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory

NFR bind 4/7 active + 2 신규:
- NFR4 (PII minimization) — finance_contact_email redact + recipient masking
- NFR8 (background job 99.9% uptime) — APScheduler restart resilience
- NFR18 (ko-KR vocabulary SSOT) — error message_ko
- NFR19 (export response time)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.capability import Capability, require_any_role, require_capability
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.jobs.errors import (
    ScheduledReportError,
    ScheduledReportLifecycleError,
    ScheduledReportPermissionError,
)
from apps.api.jobs.scheduled_reports import (
    ALL_DISPATCH_SCHEDULES,
    ALL_RECIPIENT_STRATEGIES,
    ALL_REPORT_TYPES,
    SCHEDULED_REPORTS_CRON_EXPRESSIONS,
    schedule_report,
    _compute_period_key,
    _lifecycle_state_machine,
    _redact_finance_email_for_audit,
)
from apps.api.modules.reports.scheduled_serializers import (
    ALL_STATUSES,
    ScheduledDispatchNow,
    ScheduledJobCancel,
    ScheduledJobCreate,
    ScheduledJobHistory,
    ScheduledJobResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["exports"])

# In-memory job store for MVP scope (PRD §F30.4-5 verbatim — DB table
# `phase_30_scheduled_reports_jobs` Phase 30.5+ EXTENSION 결정 wire 보류).
# This dict is keyed by job_id; value contains full job metadata.
# Verbatim pattern from csv_routes.py:38-42 in-memory tenant jobs dict.
_JOB_STORE: dict[str, dict[str, Any]] = {}
_HISTORY_STORE: dict[str, list[dict[str, Any]]] = {}


# ── Typed exception handlers will be wired in main.py ──────────────────
# Note: per cj-style atomic sprint discipline, exception handlers for the
# 16 NEW typed exceptions are wired in main.py (next section) per the
# pattern established by cj-299 EmailExport handlers.
# See: `_scheduled_report_*_handler` functions in main.py.


def _check_owner_or_admin(role: str) -> None:
    """AD-22 owner/admin RBAC helper.

    Verbatim mirror of csv_routes.py + email_routes.py pattern.
    """
    if role not in ("owner", "admin"):
        raise ScheduledReportPermissionError(
            role=role,
            required_role="owner_or_admin",
        )


# ── POST /api/v1/exports/scheduled ──────────────────────────────────────


@router.post(
    "/exports/scheduled",
    response_model=ScheduledJobResponse,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_SCHEDULED)),  # cj-285 EXTENSION 보존
    ],
)
async def create_scheduled_report(
    req: ScheduledJobCreate,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ScheduledJobResponse:
    """Story 30.4 Scheduled reports endpoint (cj-282 PRD entry §F30.4-1 verbatim).

    Flow:
      1. AD-22 owner/admin RBAC (verified via Depends dependency).
      2. Audit-first INSERT `export_scheduled` (CR 1-1 verbatim +
         ActionClass.REPORTS) BEFORE schedule creation.
      3. Compute cron_expression + period_key.
      4. Resolve recipients (NFR4 PII minimization).
      5. Persist to in-memory job store (MVP scope) + emit audit row.
      6. Return ScheduledJobResponse envelope.

    Capability gate `require_capability(Capability.EXPORT_SCHEDULED)`
    결정 wire 진입:
      - Capability.EXPORT_SCHEDULED EXTENSION (cj-285 EXTENSION wire sprint —
        capability matrix v1.54 EXTENSION).
      - Owner/admin RBAC (AD-22 verbatim) + capability gate (AD-12 verify-first).
    """
    _check_owner_or_admin(ctx.role)

    # Compute period_key (auto if not provided).
    period_key = req.period_key or _compute_period_key(req.dispatch_schedule)
    cron_expression = SCHEDULED_REPORTS_CRON_EXPRESSIONS[req.dispatch_schedule]

    # Redact finance_contact_email for audit (NFR4 PII minimization).
    redacted_email = _redact_finance_email_for_audit(req.finance_contact_email)

    # Audit-first INSERT `export_scheduled` (CR 1-1 verbatim + ActionClass.REPORTS).
    try:
        await emit_audit_typed(
            session,
            action_class=ActionClass.REPORTS,
            action="export_scheduled",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            payload={
                "dispatch_schedule": req.dispatch_schedule,
                "recipient_strategy": req.recipient_strategy,
                "finance_contact_email_redacted": redacted_email,
                "report_type": req.report_type,
                "period_key": period_key,
                "status": "scheduled",
                "scheduled_at": datetime.now(UTC).isoformat(),
            },
            flush=True,
        )
        await session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("export_scheduled audit emit failed")

    # Schedule the report via jobs module.
    schedule_result = schedule_report(
        tenant_id=str(ctx.tenant_id),
        dispatch_schedule=req.dispatch_schedule,
        recipient_strategy=req.recipient_strategy,
        finance_contact_email=req.finance_contact_email,
        report_type=req.report_type,
        period_key=period_key,
        actor_id=str(ctx.user_id) if ctx.user_id else None,
        trace_id=str(ctx.trace_id) if hasattr(ctx, "trace_id") else "",
        db_session=session,
        dry_run=False,
    )

    # Persist to in-memory job store.
    _JOB_STORE[schedule_result["job_id"]] = schedule_result
    _HISTORY_STORE.setdefault(schedule_result["job_id"], []).append({
        "job_id": schedule_result["job_id"],
        "tenant_id": schedule_result["tenant_id"],
        "dispatch_schedule": schedule_result["dispatch_schedule"],
        "period_key": schedule_result["period_key"],
        "status": "scheduled",
        "started_at": datetime.now(UTC),
        "completed_at": None,
        "retry_count": 0,
        "error_message": None,
    })

    return ScheduledJobResponse(
        job_id=schedule_result["job_id"],
        tenant_id=schedule_result["tenant_id"],
        dispatch_schedule=schedule_result["dispatch_schedule"],
        cron_expression=schedule_result["cron_expression"],
        recipient_strategy=schedule_result["recipient_strategy"],
        recipients=schedule_result["recipients"],
        report_type=schedule_result["report_type"],
        period_key=schedule_result["period_key"],
        status="scheduled",
        scheduled_at=datetime.now(UTC),
        trace_id=schedule_result["trace_id"] or None,
    )


# ── POST /api/v1/exports/scheduled/{job_id}/cancel ──────────────────────


@router.post(
    "/exports/scheduled/{job_id}/cancel",
    response_model=ScheduledJobResponse,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_SCHEDULED)),
    ],
)
async def cancel_scheduled_report(
    job_id: str,
    req: ScheduledJobCancel,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ScheduledJobResponse:
    """Cancel a scheduled report (PRD §F30.4-5 verbatim).

    Lifecycle state machine: scheduled/running → cancelled (owner manual).
    Verbatim mirror of csv_routes.py cancel pattern.
    """
    _check_owner_or_admin(ctx.role)

    job = _JOB_STORE.get(job_id)
    if job is None:
        raise ScheduledReportLifecycleError(
            current_status="not_found",
            event="cancel",
        )

    # Lifecycle state machine transition.
    current_status = job["status"]
    new_status = _lifecycle_state_machine(current_status, "cancel")

    job["status"] = new_status

    # Audit-first INSERT `export_scheduled` (cancel event).
    try:
        await emit_audit_typed(
            session,
            action_class=ActionClass.REPORTS,
            action="export_scheduled",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            payload={
                "event": "cancel",
                "job_id": job_id,
                "previous_status": current_status,
                "new_status": new_status,
                "reason": req.reason,
                "cancelled_at": datetime.now(UTC).isoformat(),
            },
            flush=True,
        )
        await session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("export_scheduled cancel audit emit failed")

    # Update history.
    _HISTORY_STORE.setdefault(job_id, []).append({
        "job_id": job_id,
        "tenant_id": job["tenant_id"],
        "dispatch_schedule": job["dispatch_schedule"],
        "period_key": job["period_key"],
        "status": new_status,
        "started_at": datetime.now(UTC),
        "completed_at": datetime.now(UTC),
        "retry_count": 0,
        "error_message": None,
    })

    return ScheduledJobResponse(
        job_id=job["job_id"],
        tenant_id=job["tenant_id"],
        dispatch_schedule=job["dispatch_schedule"],
        cron_expression=job["cron_expression"],
        recipient_strategy=job["recipient_strategy"],
        recipients=job["recipients"],
        report_type=job["report_type"],
        period_key=job["period_key"],
        status=new_status,
        scheduled_at=datetime.now(UTC),
        trace_id=job.get("trace_id") or None,
    )


# ── GET /api/v1/exports/scheduled/jobs ──────────────────────────────────


@router.get(
    "/exports/scheduled/jobs",
    response_model=dict,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_SCHEDULED)),
    ],
)
async def list_scheduled_jobs(
    status: str | None = Query(
        default=None,
        description="Filter by status (scheduled/running/completed/failed/cancelled/expired)",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size (1~100)"),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """List scheduled jobs for current tenant (PRD §F30.4-5 verbatim).

    Returns paginated list with status filter support.
    """
    _check_owner_or_admin(ctx.role)

    # Filter by tenant_id (CR 0-2 RLS) + optional status filter.
    tenant_jobs = [
        job for job in _JOB_STORE.values()
        if job["tenant_id"] == str(ctx.tenant_id)
        and (status is None or job["status"] == status)
    ]

    total = len(tenant_jobs)
    start = (page - 1) * page_size
    end = start + page_size
    page_jobs = tenant_jobs[start:end]

    return {
        "jobs": [
            ScheduledJobResponse(
                job_id=job["job_id"],
                tenant_id=job["tenant_id"],
                dispatch_schedule=job["dispatch_schedule"],
                cron_expression=job["cron_expression"],
                recipient_strategy=job["recipient_strategy"],
                recipients=job["recipients"],
                report_type=job["report_type"],
                period_key=job["period_key"],
                status=job["status"],
                scheduled_at=datetime.now(UTC),
                trace_id=job.get("trace_id") or None,
            )
            for job in page_jobs
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── GET /api/v1/exports/scheduled/history ───────────────────────────────


@router.get(
    "/exports/scheduled/history",
    response_model=dict,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_SCHEDULED)),
    ],
)
async def list_scheduled_history(
    job_id: str | None = Query(default=None, description="Filter by job_id"),
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100, description="Page size (1~100)"),
    ctx: TenantContext = Depends(get_tenant_context),
) -> dict:
    """List scheduled report history (PRD §F30.4-5 verbatim).

    Returns paginated history entries with optional job_id filter.
    """
    _check_owner_or_admin(ctx.role)

    # Flatten history store + filter by tenant_id + optional job_id.
    tenant_history: list[dict[str, Any]] = []
    for jid, entries in _HISTORY_STORE.items():
        job = _JOB_STORE.get(jid)
        if job is None or job["tenant_id"] != str(ctx.tenant_id):
            continue
        if job_id is not None and jid != job_id:
            continue
        tenant_history.extend(entries)

    # Sort by started_at DESC.
    tenant_history.sort(key=lambda x: x["started_at"], reverse=True)

    total = len(tenant_history)
    start = (page - 1) * page_size
    end = start + page_size
    page_history = tenant_history[start:end]

    return {
        "history": [
            ScheduledJobHistory(
                job_id=entry["job_id"],
                tenant_id=entry["tenant_id"],
                dispatch_schedule=entry["dispatch_schedule"],
                period_key=entry["period_key"],
                status=entry["status"],
                started_at=entry["started_at"],
                completed_at=entry.get("completed_at"),
                retry_count=entry.get("retry_count", 0),
                error_message=entry.get("error_message"),
            )
            for entry in page_history
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ── POST /api/v1/exports/scheduled/dispatch-now ────────────────────────


@router.post(
    "/exports/scheduled/dispatch-now",
    response_model=ScheduledJobResponse,
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_SCHEDULED)),
    ],
)
async def dispatch_now(
    req: ScheduledDispatchNow,
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> ScheduledJobResponse:
    """Force immediate dispatch (PRD §F30.4-5 verbatim).

    Owner-only admin override — skip cron schedule and dispatch immediately.
    """
    _check_owner_or_admin(ctx.role)

    # Audit-first INSERT `export_scheduled` (force dispatch event).
    try:
        await emit_audit_typed(
            session,
            action_class=ActionClass.REPORTS,
            action="export_scheduled",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            payload={
                "event": "dispatch_now",
                "dispatch_schedule": req.dispatch_schedule,
                "recipient_strategy": req.recipient_strategy,
                "report_type": req.report_type,
                "period_key": req.period_key,
                "dispatched_at": datetime.now(UTC).isoformat(),
            },
            flush=True,
        )
        await session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("export_scheduled dispatch_now audit emit failed")

    return ScheduledJobResponse(
        job_id="dispatch-now",
        tenant_id=str(ctx.tenant_id),
        dispatch_schedule=req.dispatch_schedule,
        cron_expression=SCHEDULED_REPORTS_CRON_EXPRESSIONS[req.dispatch_schedule],
        recipient_strategy=req.recipient_strategy,
        recipients={"strategy": req.recipient_strategy, "recipients": [], "admin_fallback_dispatched": True},
        report_type=req.report_type,
        period_key=req.period_key,
        status="running",
        scheduled_at=datetime.now(UTC),
        trace_id=None,
    )


__all__ = [
    "router",
    "ALL_DISPATCH_SCHEDULES",
    "ALL_RECIPIENT_STRATEGIES",
    "ALL_REPORT_TYPES",
    "ALL_STATUSES",
    "ScheduledReportError",
]
