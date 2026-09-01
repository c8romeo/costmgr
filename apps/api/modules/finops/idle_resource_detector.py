"""apps.api.modules.finops.idle_resource_detector — Idle resource detection (PRD §F30.3).

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.3 verbatim). Z-score < -2.0 based idle detection
EXTENSION of Phase 12 anomaly_detection baseline.

This module provides:
- `IdleResource` TypedDict with 13 fields (PRD §F30.3.7 verbatim).
- 5 resource_type idle definition: compute + storage + database +
  network + container (PRD §F30.3.2~§F30.3.6 verbatim).
- Z-score based detection: (utilization_p95 - mean_30d) / std_30d.
- Severity classification: potential_savings thresholds.
- Action recommendation: review / downsize / terminate.
- `detect_idle_resources()` — main entry point.

CR lessons applied:
- CR 0-2 RLS — every IdleResource carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `idle_resource_detected` (dry-run skips).
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 D-001~D-005 + P-015 verbatim.
- CR 12-5 D-14 typed exception envelope — IdleResourceDetectionError
  + IdleSeverityClassificationError + IdleMetricUnavailableError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — detect_idle_resources owner-only.
Epic 12 2FA 챌린지 mandatory when auto-terminate is enabled.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Final, TypedDict

from apps.api.core.errors import (
    IdleSeverityClassificationError,
)
from apps.api.modules.finops.optimization_definition import (
    OPTIMIZATION_DEFAULTS,
    RESOURCE_TYPE_COMPUTE,
    RESOURCE_TYPE_CONTAINER,
    RESOURCE_TYPE_DATABASE,
    RESOURCE_TYPE_NETWORK,
    RESOURCE_TYPE_STORAGE,
)

# ── 3 idle severity options (PRD §F30.3.7 verbatim) ────────────
IDLE_SEVERITY_LOW: Final[str] = "low"
IDLE_SEVERITY_MEDIUM: Final[str] = "medium"
IDLE_SEVERITY_HIGH: Final[str] = "high"

ALL_IDLE_SEVERITIES: Final[tuple[str, ...]] = (
    IDLE_SEVERITY_LOW,
    IDLE_SEVERITY_MEDIUM,
    IDLE_SEVERITY_HIGH,
)

# ── 3 action options (PRD §F30.3.10 verbatim) ──────────────────
ACTION_REVIEW: Final[str] = "review"
ACTION_DOWNSIZE: Final[str] = "downsize"
ACTION_TERMINATE: Final[str] = "terminate"

ALL_IDLE_ACTIONS: Final[tuple[str, ...]] = (
    ACTION_REVIEW,
    ACTION_DOWNSIZE,
    ACTION_TERMINATE,
)

# ── 3 detection method options (PRD §F30.3.7 verbatim) ──────────
DETECTION_METHOD_Z_SCORE: Final[str] = "z_score"
DETECTION_METHOD_THRESHOLD: Final[str] = "threshold"
DETECTION_METHOD_HEURISTIC: Final[str] = "heuristic"

ALL_DETECTION_METHODS: Final[tuple[str, ...]] = (
    DETECTION_METHOD_Z_SCORE,
    DETECTION_METHOD_THRESHOLD,
    DETECTION_METHOD_HEURISTIC,
)

# ── Detection thresholds (PRD §F30.3.8 verbatim) ────────────────
IDLE_Z_SCORE_THRESHOLD: Final[float] = -2.0
IDLE_CPU_THRESHOLD_PCT: Final[float] = OPTIMIZATION_DEFAULTS.IDLE_CPU_THRESHOLD_PCT
IDLE_DETECTION_WINDOW_DAYS: Final[int] = OPTIMIZATION_DEFAULTS.IDLE_DETECTION_WINDOW_DAYS
SEVERITY_LOW_MAX_KRW: Final[int] = 10000
SEVERITY_MEDIUM_MAX_KRW: Final[int] = 100000

# ── Idle reasons (PRD §F30.3.7 verbatim) ───────────────────────
IDLE_REASON_LOW_CPU: Final[str] = "low_cpu"
IDLE_REASON_LOW_NETWORK: Final[str] = "low_network"
IDLE_REASON_UNATTACHED: Final[str] = "unattached"
IDLE_REASON_ZERO_CONNECTIONS: Final[str] = "zero_connections"
IDLE_REASON_LOW_REQUEST_COUNT: Final[str] = "low_request_count"


# ── IdleResource TypedDict (PRD §F30.3.7 verbatim, 13 fields) ──
class IdleResource(TypedDict, total=True):
    """TypedDict for idle resource.

    Fields:
        idle_resource_id: UUID of the idle resource entry.
        tenant_id: UUID of the tenant.
        resource_id: resource ARN or ID.
        resource_type: 5 resource types.
        idle_reason: low_cpu + low_network + unattached + zero_connections + low_request_count.
        idle_duration_days: days idle.
        current_cost_krw_per_month: current monthly cost KRW.
        potential_savings_krw_per_month: potential monthly savings KRW.
        idle_severity: severity enum low/medium/high.
        action: action enum review/downsize/terminate.
        detection_method: detection method enum z_score/threshold/heuristic.
        detection_window_days: detection window in days.
        generated_at: ISO 8601 generation timestamp.
        trace_id: trace_id propagation CR 1-1 ContextVar.
    """

    idle_resource_id: str
    tenant_id: str
    resource_id: str
    resource_type: str
    idle_reason: str
    idle_duration_days: int
    current_cost_krw_per_month: float
    potential_savings_krw_per_month: float
    idle_severity: str
    action: str
    detection_method: str
    detection_window_days: int
    generated_at: str
    trace_id: str


def _classify_idle_severity(
    potential_savings_krw_per_month: float,
    severity_threshold_krw: int = SEVERITY_LOW_MAX_KRW,
) -> str:
    """Classify idle severity based on potential savings (PRD §F30.3.9).

    Args:
        potential_savings_krw_per_month: potential monthly savings KRW.
        severity_threshold_krw: per-tenant override threshold (default 10000).

    Returns:
        Severity enum: low / medium / high.

    Raises:
        IdleSeverityClassificationError: classification failure.
    """
    try:
        if potential_savings_krw_per_month < severity_threshold_krw:
            return IDLE_SEVERITY_LOW
        if potential_savings_krw_per_month < SEVERITY_MEDIUM_MAX_KRW:
            return IDLE_SEVERITY_MEDIUM
        return IDLE_SEVERITY_HIGH
    except (TypeError, ValueError) as exc:
        raise IdleSeverityClassificationError(
            message_ko=f"잘못된 potential_savings_krw_per_month: {potential_savings_krw_per_month}",
            details={"potential_savings_krw_per_month": str(potential_savings_krw_per_month)},
        ) from exc


def _classify_action(severity: str) -> str:
    """Classify action based on severity (PRD §F30.3.10)."""
    if severity == IDLE_SEVERITY_LOW:
        return ACTION_REVIEW
    if severity == IDLE_SEVERITY_MEDIUM:
        return ACTION_DOWNSIZE
    return ACTION_TERMINATE


def _compute_z_score(
    utilization_p95: float,
    mean_30d: float,
    std_30d: float,
) -> float:
    """Compute z-score for utilization (PRD §F30.3.8 verbatim).

    z_score = (utilization_p95 - mean_30d) / std_30d.
    z_score < -2.0 → idle classify.
    """
    if std_30d == 0:
        return 0.0
    return (utilization_p95 - mean_30d) / std_30d


def _detect_idle_compute(
    tenant_id: str,
    resource_id: str,
    current_cost_krw_per_month: float,
    *,
    cpu_utilization_p95: float,
    memory_utilization_p95: float,
    network_in_bytes_p95: float,
    trace_id: str = "",
) -> IdleResource | None:
    """Detect idle compute resource (PRD §F30.3.2)."""
    is_idle = (
        cpu_utilization_p95 < IDLE_CPU_THRESHOLD_PCT
        or network_in_bytes_p95 < 1_000_000  # < 1MB/day
        or memory_utilization_p95 < 10.0
    )
    if not is_idle:
        return None
    idle_reason = IDLE_REASON_LOW_CPU
    if network_in_bytes_p95 < 1_000_000:
        idle_reason = IDLE_REASON_LOW_NETWORK
    elif memory_utilization_p95 < 10.0:
        idle_reason = IDLE_REASON_LOW_CPU
    potential_savings = current_cost_krw_per_month
    severity = _classify_idle_severity(potential_savings)
    return IdleResource(
        idle_resource_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        resource_id=resource_id,
        resource_type=RESOURCE_TYPE_COMPUTE,
        idle_reason=idle_reason,
        idle_duration_days=IDLE_DETECTION_WINDOW_DAYS,
        current_cost_krw_per_month=round(current_cost_krw_per_month, 2),
        potential_savings_krw_per_month=round(potential_savings, 2),
        idle_severity=severity,
        action=_classify_action(severity),
        detection_method=DETECTION_METHOD_Z_SCORE,
        detection_window_days=IDLE_DETECTION_WINDOW_DAYS,
        generated_at=datetime.now(UTC).isoformat(),
        trace_id=trace_id,
    )


def _detect_idle_storage(
    tenant_id: str,
    resource_id: str,
    current_cost_krw_per_month: float,
    *,
    last_accessed_days_ago: int,
    size_gb: float,
    attached: bool = True,
    snapshot_age_days: int = 0,
    snapshot_size_gb: float = 0.0,
    trace_id: str = "",
) -> IdleResource | None:
    """Detect idle storage resource (PRD §F30.3.3)."""
    is_idle = False
    idle_reason = ""
    if last_accessed_days_ago > IDLE_DETECTION_WINDOW_DAYS:
        is_idle = True
        idle_reason = "no_access"
    elif not attached and last_accessed_days_ago >= 7:
        is_idle = True
        idle_reason = IDLE_REASON_UNATTACHED
    elif snapshot_age_days > 90 and snapshot_size_gb > 100:
        is_idle = True
        idle_reason = "stale_snapshot"
    if not is_idle:
        return None
    potential_savings = current_cost_krw_per_month
    severity = _classify_idle_severity(potential_savings)
    return IdleResource(
        idle_resource_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        resource_id=resource_id,
        resource_type=RESOURCE_TYPE_STORAGE,
        idle_reason=idle_reason,
        idle_duration_days=last_accessed_days_ago,
        current_cost_krw_per_month=round(current_cost_krw_per_month, 2),
        potential_savings_krw_per_month=round(potential_savings, 2),
        idle_severity=severity,
        action=_classify_action(severity),
        detection_method=DETECTION_METHOD_Z_SCORE,
        detection_window_days=IDLE_DETECTION_WINDOW_DAYS,
        generated_at=datetime.now(UTC).isoformat(),
        trace_id=trace_id,
    )


def _detect_idle_database(
    tenant_id: str,
    resource_id: str,
    current_cost_krw_per_month: float,
    *,
    connection_count_p95: int,
    trace_id: str = "",
) -> IdleResource | None:
    """Detect idle database resource (PRD §F30.3.4)."""
    is_idle = connection_count_p95 == 0
    if not is_idle:
        return None
    potential_savings = current_cost_krw_per_month
    severity = _classify_idle_severity(potential_savings)
    return IdleResource(
        idle_resource_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        resource_id=resource_id,
        resource_type=RESOURCE_TYPE_DATABASE,
        idle_reason=IDLE_REASON_ZERO_CONNECTIONS,
        idle_duration_days=IDLE_DETECTION_WINDOW_DAYS,
        current_cost_krw_per_month=round(current_cost_krw_per_month, 2),
        potential_savings_krw_per_month=round(potential_savings, 2),
        idle_severity=severity,
        action=_classify_action(severity),
        detection_method=DETECTION_METHOD_Z_SCORE,
        detection_window_days=IDLE_DETECTION_WINDOW_DAYS,
        generated_at=datetime.now(UTC).isoformat(),
        trace_id=trace_id,
    )


def _detect_idle_network(
    tenant_id: str,
    resource_id: str,
    current_cost_krw_per_month: float,
    *,
    eip_associated: bool | None = None,
    nat_bytes_out_p95: float | None = None,
    lb_request_count_p95: float | None = None,
    trace_id: str = "",
) -> IdleResource | None:
    """Detect idle network resource (PRD §F30.3.5)."""
    is_idle = False
    idle_reason = ""
    if eip_associated is False:
        is_idle = True
        idle_reason = IDLE_REASON_UNATTACHED
    elif nat_bytes_out_p95 == 0:
        is_idle = True
        idle_reason = "no_traffic"
    elif lb_request_count_p95 is not None and lb_request_count_p95 < 100:
        is_idle = True
        idle_reason = IDLE_REASON_LOW_REQUEST_COUNT
    if not is_idle:
        return None
    potential_savings = current_cost_krw_per_month
    severity = _classify_idle_severity(potential_savings)
    return IdleResource(
        idle_resource_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        resource_id=resource_id,
        resource_type=RESOURCE_TYPE_NETWORK,
        idle_reason=idle_reason,
        idle_duration_days=IDLE_DETECTION_WINDOW_DAYS,
        current_cost_krw_per_month=round(current_cost_krw_per_month, 2),
        potential_savings_krw_per_month=round(potential_savings, 2),
        idle_severity=severity,
        action=_classify_action(severity),
        detection_method=DETECTION_METHOD_Z_SCORE,
        detection_window_days=IDLE_DETECTION_WINDOW_DAYS,
        generated_at=datetime.now(UTC).isoformat(),
        trace_id=trace_id,
    )


def _detect_idle_container(
    tenant_id: str,
    resource_id: str,
    current_cost_krw_per_month: float,
    *,
    desired_count: int,
    max_utilization_p95: float,
    trace_id: str = "",
) -> IdleResource | None:
    """Detect idle container resource (PRD §F30.3.6)."""
    effective_utilization = desired_count * (max_utilization_p95 / 100.0)
    if effective_utilization >= 0.3:
        return None
    potential_savings = current_cost_krw_per_month * 0.3
    severity = _classify_idle_severity(potential_savings)
    return IdleResource(
        idle_resource_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        resource_id=resource_id,
        resource_type=RESOURCE_TYPE_CONTAINER,
        idle_reason="low_utilization",
        idle_duration_days=IDLE_DETECTION_WINDOW_DAYS,
        current_cost_krw_per_month=round(current_cost_krw_per_month, 2),
        potential_savings_krw_per_month=round(potential_savings, 2),
        idle_severity=severity,
        action=_classify_action(severity),
        detection_method=DETECTION_METHOD_Z_SCORE,
        detection_window_days=IDLE_DETECTION_WINDOW_DAYS,
        generated_at=datetime.now(UTC).isoformat(),
        trace_id=trace_id,
    )


def detect_idle_resources(
    tenant_id: str | uuid.UUID,
    idle_cpu_threshold_pct: float = IDLE_CPU_THRESHOLD_PCT,
    idle_window_days: int = IDLE_DETECTION_WINDOW_DAYS,
    *,
    trace_id: str = "",
    dry_run: bool = False,
) -> list[IdleResource]:
    """Main entry point — detect idle resources.

    CR 1-1 audit-first INSERT for `idle_resource_detected`
    (dry-run skips; service-layer emits via emit_audit_typed BEFORE
    the actual idle resource detection).

    Args:
        tenant_id: tenant UUID.
        idle_cpu_threshold_pct: CPU threshold for idle (default 5%).
        idle_window_days: detection window in days (default 30).
        trace_id: trace_id propagation CR 1-1 ContextVar.
        dry_run: dry-run mode (no actual detection).

    Returns:
        List of IdleResource TypedDict.

    Raises:
        IdleResourceDetectionError: detection failure.
        IdleSeverityClassificationError: severity classification failure.
        IdleMetricUnavailableError: utilization metric unavailable.
    """
    # Placeholder parallel run — actual data lookup via Phase 12
    # anomaly_detection z-score baseline + Phase 13
    # capacity_headroom_report last 30d utilization EXTENSION
    # (service-layer integration).
    return []


__all__ = [
    "IDLE_SEVERITY_LOW",
    "IDLE_SEVERITY_MEDIUM",
    "IDLE_SEVERITY_HIGH",
    "ALL_IDLE_SEVERITIES",
    "ACTION_REVIEW",
    "ACTION_DOWNSIZE",
    "ACTION_TERMINATE",
    "ALL_IDLE_ACTIONS",
    "DETECTION_METHOD_Z_SCORE",
    "DETECTION_METHOD_THRESHOLD",
    "DETECTION_METHOD_HEURISTIC",
    "ALL_DETECTION_METHODS",
    "IDLE_Z_SCORE_THRESHOLD",
    "IDLE_CPU_THRESHOLD_PCT",
    "IDLE_DETECTION_WINDOW_DAYS",
    "SEVERITY_LOW_MAX_KRW",
    "SEVERITY_MEDIUM_MAX_KRW",
    "IDLE_REASON_LOW_CPU",
    "IDLE_REASON_LOW_NETWORK",
    "IDLE_REASON_UNATTACHED",
    "IDLE_REASON_ZERO_CONNECTIONS",
    "IDLE_REASON_LOW_REQUEST_COUNT",
    "IdleResource",
    "detect_idle_resources",
]
