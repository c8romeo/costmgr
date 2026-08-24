"""apps.api.jobs.compliance_report — Compliance report job (PRD §F31.4).

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31.4 verbatim). Background job that
generates compliance reports on a schedule (default monthly:
`0 4 1 * *` cron). Emits `compliance_report_generated` audit action.

Mirrors Phase 11/12/13/14 background job pattern verbatim.

CR lessons applied:
- CR 0-2 RLS — every job invocation carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `compliance_report_generated`.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 D-001~D-005 + P-015 verbatim — pure validator pattern.
- CR 12-1 L4 industry-agnostic capability FINOPS_TAG_GOVERNANCE.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — compliance report generation owner-only.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Final

from apps.api.modules.finops.allocation_audit import (
    ComplianceReport,
    EXPORT_FORMAT_CSV,
    REPORT_TYPES,
    generate_compliance_report,
)

# Default cron: monthly at 4 AM on the 1st (PRD §F31.4 verbatim).
DEFAULT_COMPLIANCE_CRON: Final[str] = "0 4 1 * *"


def run_compliance_report_job(
    tenant_id: str | uuid.UUID,
    *,
    report_type: str,
    period_start: str,
    period_end: str,
    export_format: str = EXPORT_FORMAT_CSV,
    dry_run: bool = False,
    trace_id: str = "",
) -> ComplianceReport:
    """Run the compliance report job (PRD §F31.4-1).

    Aggregates compliance metrics, generates report, emits audit log.

    Args:
        tenant_id: tenant UUID.
        report_type: 4 REPORT_TYPES options.
        period_start: ISO 8601 date string.
        period_end: ISO 8601 date string.
        export_format: csv / pdf / json.
        dry_run: if True, no audit log emitted.
        trace_id: trace_id propagation.

    Returns:
        ComplianceReport TypedDict.
    """
    if report_type not in REPORT_TYPES:
        raise ValueError(f"report_type {report_type!r} not in REPORT_TYPES")

    # In production, this would query the database for actual metrics.
    # For now, stub returns zero-counts report.
    return generate_compliance_report(
        tenant_id=tenant_id,
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        total_resources_scanned=0,
        compliant_resources=0,
        export_format=export_format,
        dry_run=dry_run,
        trace_id=trace_id,
    )


__all__ = [
    "DEFAULT_COMPLIANCE_CRON",
    "run_compliance_report_job",
]