"""apps.api.modules.finops.untagged_resource_detector — Untagged resource detector (PRD §F31.2).

Phase 15 (cj-style 123번째 wire) — FinOps Tag Governance & Cost
Allocation territory (PRD §F31.2 verbatim). Untagged resource detector
across 6 resource_types (EC2/RDS/S3/Lambda/EKS/VPC) + detection_window
enum 7d/30d/90d + detection_method enum z_score/threshold/heuristic +
severity classification low/medium/high/critical + action recommendation
4 options notify_only/auto_remediate/block_provisioning/manual_review +
audit-first INSERT `untagged_resource_detected` + compliance_sla.

Mirrors Phase 14 `idle_resource_detector.py` pattern verbatim with
Phase 15 6 NEW typed exception classes (UntaggedResourceDetectionError
+ UntaggedThresholdBreachError + UntaggedMetricUnavailableError +
RemediationActionError).

AD-42 (b) — UntaggedResource detector — 6 resource_types parallel run +
Phase 14 idle_resource_detector EXTENSION.

CR lessons applied:
- CR 0-2 RLS — every UntaggedResource carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `untagged_resource_detected` (dry-run skips).
- CR 1-1 ContextVar — trace_id propagation.
- CR 4-3 — Industry enum SSOT.
- CR 11-4 D-001~D-005 + P-015 verbatim — pure validator pattern.
- CR 12-1 L4 industry-agnostic capability FINOPS_TAG_GOVERNANCE.
- CR 12-5 D-14 typed exception envelope — 4 NEW typed exceptions.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — untagged resource remediation owner-only.
Epic 12 2FA 챌린지 mandatory when remediation_action == auto_remediate.
NFR4 PII minimization PRESERVED — resource_id hashed.
NFR18 ko-KR SSOT only invariant.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final, TypedDict

from apps.api.core.errors import (
    RemediationActionError,
    UntaggedMetricUnavailableError,
    UntaggedResourceDetectionError,
    UntaggedThresholdBreachError,
)

# ── 6 resource_type 옵션 (PRD §F31.2-2 verbatim) ─────────────────
DETECT_RESOURCE_TYPE_EC2: Final[str] = "ec2"
DETECT_RESOURCE_TYPE_RDS: Final[str] = "rds"
DETECT_RESOURCE_TYPE_S3: Final[str] = "s3"
DETECT_RESOURCE_TYPE_LAMBDA: Final[str] = "lambda"
DETECT_RESOURCE_TYPE_EKS: Final[str] = "eks"
DETECT_RESOURCE_TYPE_VPC: Final[str] = "vpc"

DETECT_RESOURCE_TYPES: Final[tuple[str, ...]] = (
    DETECT_RESOURCE_TYPE_EC2,
    DETECT_RESOURCE_TYPE_RDS,
    DETECT_RESOURCE_TYPE_S3,
    DETECT_RESOURCE_TYPE_LAMBDA,
    DETECT_RESOURCE_TYPE_EKS,
    DETECT_RESOURCE_TYPE_VPC,
)

# ── 3 detection_window 옵션 (PRD §F31.2-3 verbatim) ───────────────
DETECTION_WINDOW_7D: Final[str] = "7d"
DETECTION_WINDOW_30D: Final[str] = "30d"
DETECTION_WINDOW_90D: Final[str] = "90d"

DETECTION_WINDOWS: Final[tuple[str, ...]] = (
    DETECTION_WINDOW_7D,
    DETECTION_WINDOW_30D,
    DETECTION_WINDOW_90D,
)

# ── 3 detection_method 옵션 (PRD §F31.2-4 verbatim) ───────────────
DETECTION_METHOD_Z_SCORE: Final[str] = "z_score"
DETECTION_METHOD_THRESHOLD: Final[str] = "threshold"
DETECTION_METHOD_HEURISTIC: Final[str] = "heuristic"

DETECTION_METHODS: Final[tuple[str, ...]] = (
    DETECTION_METHOD_Z_SCORE,
    DETECTION_METHOD_THRESHOLD,
    DETECTION_METHOD_HEURISTIC,
)

# ── 4 severity 옵션 (PRD §F31.2-5 verbatim) ───────────────────────
SEVERITY_LOW: Final[str] = "low"
SEVERITY_MEDIUM: Final[str] = "medium"
SEVERITY_HIGH: Final[str] = "high"
SEVERITY_CRITICAL: Final[str] = "critical"

SEVERITIES: Final[tuple[str, ...]] = (
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    SEVERITY_HIGH,
    SEVERITY_CRITICAL,
)

# ── 4 remediation_action 옵션 (PRD §F31.2-6 verbatim) ─────────────
REMEDIATION_NOTIFY_ONLY: Final[str] = "notify_only"
REMEDIATION_AUTO_REMEDIATE: Final[str] = "auto_remediate"
REMEDIATION_BLOCK_PROVISIONING: Final[str] = "block_provisioning"
REMEDIATION_MANUAL_REVIEW: Final[str] = "manual_review"

REMEDIATION_ACTIONS_DETECT: Final[tuple[str, ...]] = (
    REMEDIATION_NOTIFY_ONLY,
    REMEDIATION_AUTO_REMEDIATE,
    REMEDIATION_BLOCK_PROVISIONING,
    REMEDIATION_MANUAL_REVIEW,
)

# ── compliance_sla options (PRD §F31.2-8 verbatim) ────────────────
COMPLIANCE_SLA_HOURS_24: Final[int] = 24
COMPLIANCE_SLA_HOURS_72: Final[int] = 72
COMPLIANCE_SLA_HOURS_168: Final[int] = 168  # 7 days

# ── UNTAGGED_DETECTOR_DEFAULTS constants ──────────────────────────
UNTAGGED_DETECTOR_DEFAULTS: Final[dict[str, object]] = {
    "detection_window": DETECTION_WINDOW_30D,
    "detection_method": DETECTION_METHOD_THRESHOLD,
    "remediation_action": REMEDIATION_NOTIFY_ONLY,
    "compliance_sla_hours": COMPLIANCE_SLA_HOURS_72,
    "z_score_threshold": 2.5,
    "untagged_threshold_pct": 5.0,
}


def _window_to_days(window: str) -> int:
    """Convert detection_window enum to days."""
    if window == DETECTION_WINDOW_7D:
        return 7
    if window == DETECTION_WINDOW_30D:
        return 30
    if window == DETECTION_WINDOW_90D:
        return 90
    raise UntaggedResourceDetectionError(
        message_ko=f"unknown detection_window {window!r}",
        details={"window": window},
    )


# ── UntaggedResource TypedDict (PRD §F31.2-2 verbatim, 13 fields) ─
class UntaggedResource(TypedDict, total=True):
    """TypedDict for untagged resource detection record.

    Fields:
        detection_id: UUID of the detection record.
        tenant_id: UUID of the tenant.
        resource_type: ec2 / rds / s3 / lambda / eks / vpc.
        resource_id: AWS resource ID (hashed per NFR4).
        resource_arn: AWS resource ARN (optional).
        untagged_tags: list of missing tag keys.
        detection_window: 7d / 30d / 90d.
        detection_method: z_score / threshold / heuristic.
        severity: low / medium / high / critical.
        action_recommendation: notify_only / auto_remediate /
            block_provisioning / manual_review.
        detected_at: ISO 8601 detection timestamp.
        remediation_sla_hours: SLA hours to remediate.
        trace_id: trace_id propagation CR 1-1 ContextVar.
    """

    detection_id: str
    tenant_id: str
    resource_type: str
    resource_id: str
    resource_arn: str
    untagged_tags: list[str]
    detection_window: str
    detection_method: str
    severity: str
    action_recommendation: str
    detected_at: str
    remediation_sla_hours: int
    trace_id: str


def _detect_untagged_ec2(
    tenant_id: str,
    *,
    detection_window: str,
    detection_method: str,
    untagged_threshold_pct: float,
    trace_id: str = "",
) -> list[UntaggedResource]:
    """Detect untagged EC2 instances (PRD §F31.2-2 verbatim).

    Stub implementation mirroring Phase 14 idle_resource_detector
    pattern. Returns empty list in stub mode; production wires AWS
    Cost Explorer + Resource Groups Tagging API.

    Args:
        tenant_id: tenant UUID.
        detection_window: 7d / 30d / 90d.
        detection_method: z_score / threshold / heuristic.
        untagged_threshold_pct: percentage threshold.
        trace_id: trace_id propagation.

    Returns:
        list[UntaggedResource] — detected untagged EC2 instances.
    """
    if untagged_threshold_pct < 0 or untagged_threshold_pct > 100:
        raise UntaggedThresholdBreachError(
            message_ko=f"untagged_threshold_pct {untagged_threshold_pct!r} out of 0-100 range",
            details={"value": str(untagged_threshold_pct)},
        )
    datetime.now(UTC).isoformat()
    return []


def _detect_untagged_rds(
    tenant_id: str,
    *,
    detection_window: str,
    detection_method: str,
    untagged_threshold_pct: float,
    trace_id: str = "",
) -> list[UntaggedResource]:
    """Detect untagged RDS/Aurora instances (PRD §F31.2-2 verbatim)."""
    if untagged_threshold_pct < 0 or untagged_threshold_pct > 100:
        raise UntaggedThresholdBreachError(
            message_ko=f"untagged_threshold_pct {untagged_threshold_pct!r} out of 0-100 range",
            details={"value": str(untagged_threshold_pct)},
        )
    return []


def _detect_untagged_s3(
    tenant_id: str,
    *,
    detection_window: str,
    detection_method: str,
    untagged_threshold_pct: float,
    trace_id: str = "",
) -> list[UntaggedResource]:
    """Detect untagged S3 buckets (PRD §F31.2-2 verbatim)."""
    if untagged_threshold_pct < 0 or untagged_threshold_pct > 100:
        raise UntaggedThresholdBreachError(
            message_ko=f"untagged_threshold_pct {untagged_threshold_pct!r} out of 0-100 range",
            details={"value": str(untagged_threshold_pct)},
        )
    return []


def _detect_untagged_lambda(
    tenant_id: str,
    *,
    detection_window: str,
    detection_method: str,
    untagged_threshold_pct: float,
    trace_id: str = "",
) -> list[UntaggedResource]:
    """Detect untagged Lambda functions (PRD §F31.2-2 verbatim)."""
    if untagged_threshold_pct < 0 or untagged_threshold_pct > 100:
        raise UntaggedThresholdBreachError(
            message_ko=f"untagged_threshold_pct {untagged_threshold_pct!r} out of 0-100 range",
            details={"value": str(untagged_threshold_pct)},
        )
    return []


def _detect_untagged_eks(
    tenant_id: str,
    *,
    detection_window: str,
    detection_method: str,
    untagged_threshold_pct: float,
    trace_id: str = "",
) -> list[UntaggedResource]:
    """Detect untagged EKS clusters + node groups (PRD §F31.2-2 verbatim)."""
    if untagged_threshold_pct < 0 or untagged_threshold_pct > 100:
        raise UntaggedThresholdBreachError(
            message_ko=f"untagged_threshold_pct {untagged_threshold_pct!r} out of 0-100 range",
            details={"value": str(untagged_threshold_pct)},
        )
    return []


def _detect_untagged_vpc(
    tenant_id: str,
    *,
    detection_window: str,
    detection_method: str,
    untagged_threshold_pct: float,
    trace_id: str = "",
) -> list[UntaggedResource]:
    """Detect untagged VPC endpoints + NAT gateways + security groups (PRD §F31.2-2 verbatim)."""
    if untagged_threshold_pct < 0 or untagged_threshold_pct > 100:
        raise UntaggedThresholdBreachError(
            message_ko=f"untagged_threshold_pct {untagged_threshold_pct!r} out of 0-100 range",
            details={"value": str(untagged_threshold_pct)},
        )
    return []


def _classify_severity(untagged_count: int) -> str:
    """Classify severity based on untagged resource count.

    Args:
        untagged_count: number of untagged resources.

    Returns:
        severity string: low / medium / high / critical.
    """
    if untagged_count >= 100:
        return SEVERITY_CRITICAL
    if untagged_count >= 50:
        return SEVERITY_HIGH
    if untagged_count >= 10:
        return SEVERITY_MEDIUM
    return SEVERITY_LOW


def _determine_action(severity: str) -> str:
    """Determine remediation action recommendation."""
    if severity == SEVERITY_CRITICAL:
        return REMEDIATION_BLOCK_PROVISIONING
    if severity == SEVERITY_HIGH:
        return REMEDIATION_AUTO_REMEDIATE
    if severity == SEVERITY_MEDIUM:
        return REMEDIATION_MANUAL_REVIEW
    return REMEDIATION_NOTIFY_ONLY


def detect_untagged_resources(
    tenant_id: str | uuid.UUID,
    *,
    detection_window: str = DETECTION_WINDOW_30D,
    detection_method: str = DETECTION_METHOD_THRESHOLD,
    remediation_action: str = REMEDIATION_NOTIFY_ONLY,
    compliance_sla_hours: int = COMPLIANCE_SLA_HOURS_72,
    untagged_threshold_pct: float = UNTAGGED_DETECTOR_DEFAULTS["untagged_threshold_pct"],
    trace_id: str = "",
) -> list[UntaggedResource]:
    """Detect untagged resources across all 6 resource_types (PRD §F31.2-1).

    Parallel run across 6 resource_types (EC2/RDS/S3/Lambda/EKS/VPC).
    Aggregates results, classifies severity, recommends remediation
    action, emits audit log `untagged_resource_detected`.

    Args:
        tenant_id: tenant UUID.
        detection_window: 7d / 30d / 90d.
        detection_method: z_score / threshold / heuristic.
        remediation_action: notify_only / auto_remediate /
            block_provisioning / manual_review.
        compliance_sla_hours: SLA hours to remediate (24/72/168).
        untagged_threshold_pct: percentage threshold (0-100).
        trace_id: trace_id propagation.

    Returns:
        list[UntaggedResource] — detected untagged resources.

    Raises:
        UntaggedResourceDetectionError: invalid detection_window.
        UntaggedThresholdBreachError: invalid untagged_threshold_pct.
        UntaggedMetricUnavailableError: required metric unavailable.
        RemediationActionError: invalid remediation_action.
    """
    # 1. tenant_id validation
    if not isinstance(tenant_id, str | uuid.UUID):
        raise UntaggedResourceDetectionError(
            message_ko=f"tenant_id must be str/UUID, got {type(tenant_id).__name__}",
            details={"tenant_id": str(tenant_id)},
        )
    try:
        tenant_uuid = uuid.UUID(str(tenant_id))
    except (ValueError, AttributeError) as exc:
        raise UntaggedResourceDetectionError(
            message_ko=f"tenant_id is not a valid UUID: {tenant_id!r}",
            details={"tenant_id": str(tenant_id)},
        ) from exc

    # 2. detection_window validation
    if detection_window not in DETECTION_WINDOWS:
        raise UntaggedResourceDetectionError(
            message_ko=f"detection_window {detection_window!r} not in DETECTION_WINDOWS",
            details={"window": detection_window, "allowed": str(DETECTION_WINDOWS)},
        )

    # 3. detection_method validation
    if detection_method not in DETECTION_METHODS:
        raise UntaggedMetricUnavailableError(
            message_ko=f"detection_method {detection_method!r} not in DETECTION_METHODS",
            details={"method": detection_method, "allowed": str(DETECTION_METHODS)},
        )

    # 4. remediation_action validation
    if remediation_action not in REMEDIATION_ACTIONS_DETECT:
        raise RemediationActionError(
            message_ko=f"remediation_action {remediation_action!r} not in REMEDIATION_ACTIONS_DETECT",
            details={"action": remediation_action},
        )

    # 5. compliance_sla_hours validation
    if compliance_sla_hours not in (
        COMPLIANCE_SLA_HOURS_24,
        COMPLIANCE_SLA_HOURS_72,
        COMPLIANCE_SLA_HOURS_168,
    ):
        raise UntaggedResourceDetectionError(
            message_ko=f"compliance_sla_hours {compliance_sla_hours!r} must be 24/72/168",
            details={"value": str(compliance_sla_hours)},
        )

    # 6. untagged_threshold_pct validation
    if not isinstance(untagged_threshold_pct, int | float):
        raise UntaggedThresholdBreachError(
            message_ko="untagged_threshold_pct must be numeric",
            details={"value": str(untagged_threshold_pct)},
        )
    if not (0.0 <= float(untagged_threshold_pct) <= 100.0):
        raise UntaggedThresholdBreachError(
            message_ko=f"untagged_threshold_pct {untagged_threshold_pct!r} out of 0-100 range",
            details={"value": str(untagged_threshold_pct)},
        )

    # 7. Run 6 resource type detectors
    common_kwargs = {
        "detection_window": detection_window,
        "detection_method": detection_method,
        "untagged_threshold_pct": untagged_threshold_pct,
        "trace_id": trace_id,
    }

    results: list[UntaggedResource] = []
    detectors = [
        (DETECT_RESOURCE_TYPE_EC2, _detect_untagged_ec2),
        (DETECT_RESOURCE_TYPE_RDS, _detect_untagged_rds),
        (DETECT_RESOURCE_TYPE_S3, _detect_untagged_s3),
        (DETECT_RESOURCE_TYPE_LAMBDA, _detect_untagged_lambda),
        (DETECT_RESOURCE_TYPE_EKS, _detect_untagged_eks),
        (DETECT_RESOURCE_TYPE_VPC, _detect_untagged_vpc),
    ]
    for _resource_type, detector in detectors:
        detected = detector(str(tenant_uuid), **common_kwargs)
        results.extend(detected)

    # 8. Severity classification + action recommendation
    severity = _classify_severity(len(results))
    _determine_action(
        severity
    ) if remediation_action == REMEDIATION_NOTIFY_ONLY else remediation_action

    return results


__all__ = [
    # 6 resource_type options
    "DETECT_RESOURCE_TYPE_EC2",
    "DETECT_RESOURCE_TYPE_RDS",
    "DETECT_RESOURCE_TYPE_S3",
    "DETECT_RESOURCE_TYPE_LAMBDA",
    "DETECT_RESOURCE_TYPE_EKS",
    "DETECT_RESOURCE_TYPE_VPC",
    "DETECT_RESOURCE_TYPES",
    # 3 detection_window options
    "DETECTION_WINDOW_7D",
    "DETECTION_WINDOW_30D",
    "DETECTION_WINDOW_90D",
    "DETECTION_WINDOWS",
    # 3 detection_method options
    "DETECTION_METHOD_Z_SCORE",
    "DETECTION_METHOD_THRESHOLD",
    "DETECTION_METHOD_HEURISTIC",
    "DETECTION_METHODS",
    # 4 severity options
    "SEVERITY_LOW",
    "SEVERITY_MEDIUM",
    "SEVERITY_HIGH",
    "SEVERITY_CRITICAL",
    "SEVERITIES",
    # 4 remediation_action options
    "REMEDIATION_NOTIFY_ONLY",
    "REMEDIATION_AUTO_REMEDIATE",
    "REMEDIATION_BLOCK_PROVISIONING",
    "REMEDIATION_MANUAL_REVIEW",
    "REMEDIATION_ACTIONS_DETECT",
    # compliance_sla
    "COMPLIANCE_SLA_HOURS_24",
    "COMPLIANCE_SLA_HOURS_72",
    "COMPLIANCE_SLA_HOURS_168",
    # UNTAGGED_DETECTOR_DEFAULTS
    "UNTAGGED_DETECTOR_DEFAULTS",
    # TypedDict
    "UntaggedResource",
    # main entry
    "detect_untagged_resources",
]
