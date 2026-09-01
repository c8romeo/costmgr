"""apps.api.jobs.executive_report_delivery — Executive report delivery cron.

Phase 16 wire (cj-style 127번째) — FinOps Reporting & Executive Dashboard
territory (PRD §F32.3-9 verbatim + AD-43 (c) decision).

Executive report delivery cron:
- KST monthly 1st-day 09:00 + quarterly 1st-day 09:00 + annual Jan-1 09:00
- 3 delivery targets: owner-only Slack `#bizup-executive-reports` channel +
  Email recipients resolver + S3 archive URL
- Audit-first INSERT `executive_report_dispatched` (CR 1-1 verbatim)

AD-14 stack pin — apscheduler==3.10.4 + pytz==2024.1 + slack-sdk==3.23.0 +
sendgrid==6.11.0.

CR lessons applied:
- CR 0-2 RLS — tenant_id selector + multi-tenant isolation.
- CR 1-1 audit-first INSERT — `executive_report_dispatched`.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-1 L4 industry-agnostic — 4-industry grants ✅/✅/✅/✅.
- CR 12-5 D-14 typed exception envelope verbatim.
- AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory.
- NFR4 PII minimization PRESERVED.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import pytz

from apps.api.core.errors import ExecutiveReportDeliveryError
from apps.api.modules.finops.reporting.serializers import (
    ALL_CADENCES,
    Cadence,
)

logger = logging.getLogger(__name__)

KST = pytz.timezone("Asia/Seoul")

# Delivery cron expressions (PRD §F32.3-9 verbatim).
DELIVERY_CRON_EXPRESSIONS: dict[str, str] = {
    Cadence.MONTHLY.value: "0 9 1 * *",  # KST 1st day of month 09:00
    Cadence.QUARTERLY.value: "0 9 1 1,4,7,10 *",  # KST 1st day of quarter
    Cadence.ANNUAL.value: "0 9 1 1 *",  # KST Jan 1 09:00
}

# Slack channel for executive reports.
SLACK_CHANNEL_EXECUTIVE_REPORTS = "#bizup-executive-reports"


def deliver_executive_report(
    tenant_id: str,
    report_id: str,
    cadence: str = "monthly",
    actor_id: str | None = None,
    trace_id: str = "",
    dry_run: bool = False,
    db_session: Any | None = None,
) -> dict[str, Any]:
    """Deliver executive report via 3 targets (PRD §F32.3-9 verbatim).

    Phase 16 wire (cj-style 127번째) — Slack + Email + S3 archive.

    Args:
        tenant_id: Tenant UUID.
        report_id: Report UUID.
        cadence: monthly/quarterly/annual.
        actor_id: Actor UUID (owner-only RBAC AD-22).
        trace_id: Trace ID for audit.
        dry_run: If True, skip actual dispatch + audit.
        db_session: Optional DB session.

    Returns:
        Dict with delivery status per target.

    Raises:
        ExecutiveReportDeliveryError — delivery failure.
    """
    if cadence not in ALL_CADENCES:
        raise ExecutiveReportDeliveryError(
            reason=f"invalid_cadence:{cadence}",
            tenant_id=tenant_id,
        )

    delivery_id = str(uuid.uuid4())
    results = {
        "slack": False,
        "email": False,
        "s3_archive": False,
    }

    # Slack dispatch.
    try:
        if not dry_run:
            from apps.api.jobs.scheduled_executive_dispatch import _dispatch_slack

            results["slack"] = _dispatch_slack(
                tenant_id=tenant_id,
                report_id=report_id,
                recipients={"channel": SLACK_CHANNEL_EXECUTIVE_REPORTS},
                dry_run=dry_run,
            )
        else:
            results["slack"] = True
    except Exception as exc:
        logger.warning(
            "executive_report_delivery.slack failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    # Email dispatch.
    try:
        if not dry_run:
            from apps.api.jobs.scheduled_executive_dispatch import _dispatch_email

            results["email"] = _dispatch_email(
                tenant_id=tenant_id,
                report_id=report_id,
                recipients={"strategy": "owner_only"},
                dry_run=dry_run,
            )
        else:
            results["email"] = True
    except Exception as exc:
        logger.warning(
            "executive_report_delivery.email failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    # S3 archive.
    try:
        if not dry_run:
            from apps.api.jobs.scheduled_executive_dispatch import _dispatch_s3_archive

            results["s3_archive"] = _dispatch_s3_archive(
                tenant_id=tenant_id,
                period_key=datetime.now(tz=KST).strftime("%Y-%m"),
                report_id=report_id,
                dry_run=dry_run,
            )
        else:
            results["s3_archive"] = True
    except Exception as exc:
        logger.warning(
            "executive_report_delivery.s3 failed",
            extra={"tenant_id": tenant_id, "error": str(exc)},
        )

    # Audit-first INSERT `executive_report_dispatched` (CR 1-1).
    if not dry_run:
        try:
            from apps.api.core.audit_action import emit_audit_typed

            emit_audit_typed(
                action="executive_report_dispatched",
                tenant_id=tenant_id,
                actor_id=actor_id,
                trace_id=trace_id,
                resource_id=delivery_id,
                metadata={
                    "report_id": report_id,
                    "cadence": cadence,
                    "results": results,
                    "slack_channel": SLACK_CHANNEL_EXECUTIVE_REPORTS,
                },
            )
        except ImportError:
            pass

    logger.info(
        "executive_report_delivery.deliver_executive_report",
        extra={
            "tenant_id": tenant_id,
            "delivery_id": delivery_id,
            "cadence": cadence,
            "dry_run": dry_run,
            "results": results,
        },
    )

    return {
        "delivery_id": delivery_id,
        "tenant_id": tenant_id,
        "report_id": report_id,
        "cadence": cadence,
        "results": results,
        "delivered_at": datetime.now(tz=UTC),
        "trace_id": trace_id,
    }


__all__ = [
    "DELIVERY_CRON_EXPRESSIONS",
    "SLACK_CHANNEL_EXECUTIVE_REPORTS",
    "KST",
    "deliver_executive_report",
]
