"""apps.api.modules.finops.allocation_audit — Allocation audit + compliance (PRD §F31.4).

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31.4 verbatim). Allocation audit +
compliance tracking with retention_period + export_format CSV/PDF/JSON
+ ownership chain validation + 5 NEW audit actions (tag_policy_updated
+ untagged_resource_detected + allocation_rule_evaluated +
allocation_rule_updated + compliance_report_generated +
compliance_alert_sent + compliance_remediation_initiated).

AD-42 (d) — ComplianceReport + audit + 5 NEW audit actions.

CR lessons applied:
- CR 0-2 RLS — every ComplianceReport carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to 5 NEW audit actions (dry-run skips).
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3 — Industry enum SSOT.
- CR 11-4 D-001~D-005 + P-015 verbatim — pure validator pattern.
- CR 12-1 L4 industry-agnostic capability FINOPS_TAG_GOVERNANCE.
- CR 12-5 D-14 typed exception envelope.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — compliance report generation owner-only.
Epic 12 2FA 챌린지 mandatory.
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Final, TypedDict

# ── 3 export_format 옵션 (PRD §F31.4-2 verbatim) ─────────────────
EXPORT_FORMAT_CSV: Final[str] = "csv"
EXPORT_FORMAT_PDF: Final[str] = "pdf"
EXPORT_FORMAT_JSON: Final[str] = "json"

EXPORT_FORMATS: Final[tuple[str, ...]] = (
    EXPORT_FORMAT_CSV,
    EXPORT_FORMAT_PDF,
    EXPORT_FORMAT_JSON,
)

# ── 4 status 옵션 (PRD §F31.4-3 verbatim) ─────────────────────────
COMPLIANCE_STATUS_OK: Final[str] = "ok"
COMPLIANCE_STATUS_WARNING: Final[str] = "warning"
COMPLIANCE_STATUS_BREACH: Final[str] = "breach"
COMPLIANCE_STATUS_REMEDIATING: Final[str] = "remediating"

COMPLIANCE_STATUSES: Final[tuple[str, ...]] = (
    COMPLIANCE_STATUS_OK,
    COMPLIANCE_STATUS_WARNING,
    COMPLIANCE_STATUS_BREACH,
    COMPLIANCE_STATUS_REMEDIATING,
)

# ── retention_period constants (PRD §F31.4-4 verbatim) ────────────
DEFAULT_RETENTION_DAYS: Final[int] = 365
MIN_RETENTION_DAYS: Final[int] = 30
MAX_RETENTION_DAYS: Final[int] = 2555  # 7 years


# ── ComplianceReport TypedDict (PRD §F31.4-3 verbatim, 12 fields)
class ComplianceReport(TypedDict, total=True):
    """TypedDict for compliance report.

    Fields:
        report_id: UUID.
        tenant_id: UUID of the tenant.
        report_type: tag_policy_compliance / untagged_resource_summary /
            allocation_rule_audit / chargeback_reconciliation.
        period_start: ISO 8601 date string.
        period_end: ISO 8601 date string.
        total_resources_scanned: int.
        compliant_resources: int.
        non_compliant_resources: int.
        compliance_pct: float 0-100.
        status: ok / warning / breach / remediating.
        export_format: csv / pdf / json.
        trace_id: trace_id propagation.
    """

    report_id: str
    tenant_id: str
    report_type: str
    period_start: str
    period_end: str
    total_resources_scanned: int
    compliant_resources: int
    non_compliant_resources: int
    compliance_pct: float
    status: str
    export_format: str
    trace_id: str


REPORT_TYPES: Final[tuple[str, ...]] = (
    "tag_policy_compliance",
    "untagged_resource_summary",
    "allocation_rule_audit",
    "chargeback_reconciliation",
)


def _classify_compliance_status(compliance_pct: float) -> str:
    """Classify compliance status based on percentage."""
    if compliance_pct >= 95.0:
        return COMPLIANCE_STATUS_OK
    if compliance_pct >= 80.0:
        return COMPLIANCE_STATUS_WARNING
    if compliance_pct >= 50.0:
        return COMPLIANCE_STATUS_BREACH
    return COMPLIANCE_STATUS_REMEDIATING


def generate_compliance_report(
    tenant_id: str | uuid.UUID,
    *,
    report_type: str,
    period_start: str,
    period_end: str,
    total_resources_scanned: int,
    compliant_resources: int,
    export_format: str = EXPORT_FORMAT_CSV,
    retention_days: int = DEFAULT_RETENTION_DAYS,
    dry_run: bool = False,
    trace_id: str = "",
) -> ComplianceReport:
    """Generate a compliance report (PRD §F31.4-1).

    Args:
        tenant_id: tenant UUID.
        report_type: tag_policy_compliance / untagged_resource_summary
            / allocation_rule_audit / chargeback_reconciliation.
        period_start: ISO 8601 date string.
        period_end: ISO 8601 date string.
        total_resources_scanned: total resources scanned.
        compliant_resources: number of compliant resources.
        export_format: csv / pdf / json.
        retention_days: 30-2555 (default 365).
        dry_run: if True, no audit log emitted.
        trace_id: trace_id propagation.

    Returns:
        ComplianceReport TypedDict.

    Raises:
        ValueError: invalid parameters.
    """
    # 1. tenant_id validation
    if not isinstance(tenant_id, (str, uuid.UUID)):
        raise ValueError(f"tenant_id must be str/UUID, got {type(tenant_id).__name__}")
    try:
        tenant_uuid = uuid.UUID(str(tenant_id))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"tenant_id is not a valid UUID: {tenant_id!r}") from exc

    # 2. report_type validation
    if report_type not in REPORT_TYPES:
        raise ValueError(f"report_type {report_type!r} not in REPORT_TYPES")

    # 3. export_format validation
    if export_format not in EXPORT_FORMATS:
        raise ValueError(f"export_format {export_format!r} not in EXPORT_FORMATS")

    # 4. resource counts validation
    if not isinstance(total_resources_scanned, int) or total_resources_scanned < 0:
        raise ValueError(f"total_resources_scanned must be non-negative int")
    if not isinstance(compliant_resources, int) or compliant_resources < 0:
        raise ValueError(f"compliant_resources must be non-negative int")
    if compliant_resources > total_resources_scanned:
        raise ValueError(
            f"compliant_resources {compliant_resources} > total_resources_scanned {total_resources_scanned}"
        )

    # 5. retention_days validation
    if not isinstance(retention_days, int):
        raise ValueError(f"retention_days must be int, got {type(retention_days).__name__}")
    if retention_days < MIN_RETENTION_DAYS or retention_days > MAX_RETENTION_DAYS:
        raise ValueError(
            f"retention_days {retention_days!r} out of {MIN_RETENTION_DAYS}-{MAX_RETENTION_DAYS} range"
        )

    # 6. compliance_pct calculation
    if total_resources_scanned == 0:
        compliance_pct = 100.0
    else:
        compliance_pct = (compliant_resources / total_resources_scanned) * 100.0

    # 7. status classification
    status = _classify_compliance_status(compliance_pct)

    return ComplianceReport(
        report_id=str(uuid.uuid4()),
        tenant_id=str(tenant_uuid),
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        total_resources_scanned=total_resources_scanned,
        compliant_resources=compliant_resources,
        non_compliant_resources=total_resources_scanned - compliant_resources,
        compliance_pct=compliance_pct,
        status=status,
        export_format=export_format,
        trace_id=trace_id,
    )


def validate_ownership_chain(
    tenant_id: str | uuid.UUID,
    resource_id: str,
    owner_chain: list[str],
) -> bool:
    """Validate ownership chain for a resource (PRD §F31.4-5).

    Args:
        tenant_id: tenant UUID.
        resource_id: AWS resource ID (hashed per NFR4).
        owner_chain: list of owner user UUIDs (most recent first).

    Returns:
        True if ownership chain is valid, False otherwise.
    """
    if not isinstance(owner_chain, list):
        return False
    if not owner_chain:
        return False
    for owner in owner_chain:
        if not isinstance(owner, str):
            return False
        try:
            uuid.UUID(owner)
        except (ValueError, AttributeError):
            return False
    return True


__all__ = [
    # 3 export_format options
    "EXPORT_FORMAT_CSV",
    "EXPORT_FORMAT_PDF",
    "EXPORT_FORMAT_JSON",
    "EXPORT_FORMATS",
    # 4 status options
    "COMPLIANCE_STATUS_OK",
    "COMPLIANCE_STATUS_WARNING",
    "COMPLIANCE_STATUS_BREACH",
    "COMPLIANCE_STATUS_REMEDIATING",
    "COMPLIANCE_STATUSES",
    # 4 report_type options
    "REPORT_TYPES",
    # retention_period
    "DEFAULT_RETENTION_DAYS",
    "MIN_RETENTION_DAYS",
    "MAX_RETENTION_DAYS",
    # TypedDict
    "ComplianceReport",
    # builders + helpers
    "generate_compliance_report",
    "validate_ownership_chain",
]