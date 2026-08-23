"""apps.api.modules.chaos.chaos_experiment — Chaos experiment TypedDict + validation.

Phase 9 (cj-style 99번째 wire) — Chaos Engineering / Game Day territory
(PRD §F25.1 + AD-36 (a)(b)(g) sub-decisions).

This module provides:
- `ChaosExperiment` TypedDict with 13 fields (PRD §F25.1 verbatim).
- `AbortCondition` TypedDict with 5 fields (PRD §F25.1.6 verbatim).
- 5 blast radius constants + 10 fault type constants + 3 intensity
  constants + 4 rollback strategy constants (single source of truth
  shared with frontend chaos dashboard via CR 12-5 D-PARITY-01).
- 4 NEW CR 12-5 D-14 typed exception classes (ChaosExperimentInvalid
  BlastRadiusError + ChaosExperimentOwnerOnlyForbiddenError +
  ChaosRollbackTriggerFailedError + ContinuousChaosProductionUnsafe
  Error).
- `validate_chaos_experiment()` — pydantic v2 model_validator-equivalent
  enforcing blast_radius / intensity / abort_conditions / duration.

CR lessons applied:
- CR 0-2 RLS — every ChaosExperiment carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim.
- CR 4-3/4-4 — chaos_experiment baseline freeze pattern verbatim
  미러 (steady_state_metric baseline 30d rolling).

AD-22 owner-only RBAC — L3~L5 blast radius + manual abort + 2FA 챌린지
Epic 12 정합.

Industry-agnostic per CR 12-1 L4 precedent (mirrors PERFORMANCE_TESTING
Phase 8 wire + OBSERVABILITY_* Phase 7 wire pattern verbatim). All 4
industries get CHAOS_ENGINEERING capability.
"""
from __future__ import annotations

import uuid
from typing import Any, Final, Literal, TypedDict

from apps.api.core.errors import BaseError

# ── Constants — single source of truth for blast radius levels ──
# PRD §F25.1.4 verbatim — 5 blast radius levels.
BLAST_RADIUS_L1: Final[str] = "single_request"
BLAST_RADIUS_L2: Final[str] = "single_tenant"
BLAST_RADIUS_L3: Final[str] = "all_tenants"
BLAST_RADIUS_L4: Final[str] = "single_region"
BLAST_RADIUS_L5: Final[str] = "multi_region"

VALID_BLAST_RADII: Final[tuple[str, ...]] = (
    BLAST_RADIUS_L1,
    BLAST_RADIUS_L2,
    BLAST_RADIUS_L3,
    BLAST_RADIUS_L4,
    BLAST_RADIUS_L5,
)


# ── Constants — 10 fault injection types (PRD §F25.2 verbatim) ──
FAULT_TYPE_LATENCY: Final[str] = "latency"
FAULT_TYPE_ERROR: Final[str] = "error"
FAULT_TYPE_RESOURCE: Final[str] = "resource"
FAULT_TYPE_NETWORK: Final[str] = "network_partition"
FAULT_TYPE_DISK_IO: Final[str] = "disk_io"
FAULT_TYPE_DB_POOL: Final[str] = "db_connection_pool"
FAULT_TYPE_CACHE: Final[str] = "cache_failure"
FAULT_TYPE_DNS: Final[str] = "dns_failure"
FAULT_TYPE_PROCESS: Final[str] = "process_kill"
FAULT_TYPE_CLOCK_SKEW: Final[str] = "clock_skew"

VALID_FAULT_TYPES: Final[tuple[str, ...]] = (
    FAULT_TYPE_LATENCY,
    FAULT_TYPE_ERROR,
    FAULT_TYPE_RESOURCE,
    FAULT_TYPE_NETWORK,
    FAULT_TYPE_DISK_IO,
    FAULT_TYPE_DB_POOL,
    FAULT_TYPE_CACHE,
    FAULT_TYPE_DNS,
    FAULT_TYPE_PROCESS,
    FAULT_TYPE_CLOCK_SKEW,
)


# ── Constants — 3 intensity levels ──────────────────────────────
INTENSITY_LOW: Final[str] = "low"
INTENSITY_MEDIUM: Final[str] = "medium"
INTENSITY_HIGH: Final[str] = "high"

VALID_INTENSITIES: Final[tuple[str, ...]] = (
    INTENSITY_LOW,
    INTENSITY_MEDIUM,
    INTENSITY_HIGH,
)


# ── Constants — 4 rollback strategies (PRD §F25.6.2 verbatim) ───
ROLLBACK_AUTOMATIC: Final[str] = "automatic"
ROLLBACK_MANUAL: Final[str] = "manual"
ROLLBACK_HYBRID: Final[str] = "hybrid"
ROLLBACK_SCHEDULED: Final[str] = "scheduled_abort"

VALID_ROLLBACK_STRATEGIES: Final[tuple[str, ...]] = (
    ROLLBACK_AUTOMATIC,
    ROLLBACK_MANUAL,
    ROLLBACK_HYBRID,
    ROLLBACK_SCHEDULED,
)


# ── Constants — Chaos experiment duration limits (PRD §F25.1) ──
MAX_DURATION_SECONDS: Final[int] = 600  # 10 minutes
MIN_DURATION_SECONDS: Final[int] = 1

# Maximum number of abort conditions per experiment.
MIN_ABORT_CONDITIONS: Final[int] = 1
MAX_ABORT_CONDITIONS: Final[int] = 4


# ── Typed result envelopes (CR 12-5 D-PARITY-01) ───────────────
class AbortCondition(TypedDict):
    """Abort condition for chaos experiment (PRD §F25.1.6 verbatim).

    Fields:
        metric: Prometheus metric name to monitor.
        threshold: Numeric threshold value.
        comparison: One of '>', '>=', '<', '<='.
        window_seconds: Window in seconds over which to evaluate.
        severity: 'warning' (logged only) | 'critical' (auto-abort).
    """

    metric: str
    threshold: float
    comparison: Literal[">", ">=", "<", "<="]
    window_seconds: int
    severity: Literal["warning", "critical"]


class ChaosExperiment(TypedDict):
    """Chaos experiment definition (PRD §F25.1 verbatim — 13 fields).

    Fields:
        experiment_id: Stable unique identifier (UUID4 string).
        name: Human-readable experiment name.
        description: Free-text description of what is being tested.
        steady_state_metric: Prometheus metric representing steady state
            (e.g. 'business_cost_engine_duration_seconds{engine,tenant}').
        hypothesis: Statement of expected steady state behavior.
        fault_type: One of 10 fault types (PRD §F25.2 verbatim).
        target_service: Target service / module name.
        target_endpoint: Optional target endpoint path (None for service-wide).
        blast_radius: One of 5 blast radius levels (PRD §F25.1.4 verbatim).
        duration_seconds: 1~600 seconds (MAX_DURATION_SECONDS = 600 = 10min).
        intensity: 'low' | 'medium' | 'high'.
        abort_conditions: List of 1~4 AbortCondition rules.
        rollback_strategy: 'automatic' | 'manual' | 'hybrid' | 'scheduled_abort'.
        owner_only: AD-22 RBAC — L3~L5 blast radius enforced owner-only.
        dry_run: If True, no actual fault injection occurs (audit-first
            INSERT `chaos_experiment_started` records dry_run flag).
    """

    experiment_id: str
    name: str
    description: str
    steady_state_metric: str
    hypothesis: str
    fault_type: str
    target_service: str
    target_endpoint: str | None
    blast_radius: str
    duration_seconds: int
    intensity: str
    abort_conditions: list[AbortCondition]
    rollback_strategy: str
    owner_only: bool
    dry_run: bool


# ── CR 12-5 D-14 typed exception envelope — 4 NEW error classes ──
class ChaosExperimentError(BaseError):
    """Base class for chaos experiment errors."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, object] | None = None,
        trace_id: str | None = None,
        http_status: int = 500,
    ) -> None:
        super().__init__(
            code=code,
            message_ko=message_ko,
            details=details or {},
            trace_id=trace_id or str(uuid.uuid4()),
            http_status=http_status,
        )


class ChaosExperimentInvalidBlastRadiusError(ChaosExperimentError):
    """400 CHAOS_EXPERIMENT_INVALID_BLAST_RADIUS — blast_radius not in 5-level enum."""

    def __init__(
        self,
        blast_radius: str,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="CHAOS_EXPERIMENT_INVALID_BLAST_RADIUS",
            message_ko=f"유효하지 않은 blast radius: {blast_radius!r}",
            details={
                "blast_radius": blast_radius,
                "valid": list(VALID_BLAST_RADII),
            },
            trace_id=trace_id,
            http_status=400,
        )


class ChaosExperimentOwnerOnlyForbiddenError(ChaosExperimentError):
    """403 CHAOS_EXPERIMENT_OWNER_ONLY_FORBIDDEN — caller is not owner.

    L3~L5 blast radius + manual abort + 2FA 챌린지 Epic 12 정합.
    """

    def __init__(
        self,
        *,
        blast_radius: str,
        caller_role: str,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="CHAOS_EXPERIMENT_OWNER_ONLY_FORBIDDEN",
            message_ko="카오스 실험은 owner 전용입니다.",
            details={
                "blast_radius": blast_radius,
                "caller_role": caller_role,
                "required_role": "owner",
            },
            trace_id=trace_id,
            http_status=403,
        )


class ChaosRollbackTriggerFailedError(ChaosExperimentError):
    """409 CHAOS_ROLLBACK_TRIGGER_FAILED — auto-rollback could not execute."""

    def __init__(
        self,
        *,
        experiment_id: str,
        reason: str,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="CHAOS_ROLLBACK_TRIGGER_FAILED",
            message_ko=f"카오스 실험 {experiment_id} 자동 롤백 실패.",
            details={
                "experiment_id": experiment_id,
                "reason": reason,
            },
            trace_id=trace_id,
            http_status=409,
        )


class ContinuousChaosProductionUnsafeError(ChaosExperimentError):
    """422 CONTINUOUS_CHAOS_PRODUCTION_UNSAFE — guard rule violation.

    Production-safe guards: blast radius L1 only + intensity low only +
    percentage ≤ 5% + duration ≤ 60s + auto-rollback ≤ 30s + dry_run
    default.
    """

    def __init__(
        self,
        *,
        violated_rule: str,
        attempted_value: str,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="CONTINUOUS_CHAOS_PRODUCTION_UNSAFE",
            message_ko=f"연속 카오스 안전 규칙 위반: {violated_rule}",
            details={
                "violated_rule": violated_rule,
                "attempted_value": attempted_value,
            },
            trace_id=trace_id,
            http_status=422,
        )


# ── Validation (pydantic v2 model_validator-equivalent) ─────────
def validate_chaos_experiment(experiment: dict[str, Any]) -> None:
    """Validate a ChaosExperiment payload. Raises typed exceptions on violation.

    Validation rules (PRD §F25.1.10 verbatim):
    - blast_radius ∈ 5 levels.
    - intensity ∈ 3 levels.
    - abort_conditions list min 1 max 4.
    - duration_seconds 1~600.
    - fault_type ∈ 10 categories.

    Args:
        experiment: ChaosExperiment-shaped dict.

    Raises:
        ChaosExperimentInvalidBlastRadiusError: 400.
        ChaosExperimentError: 400 for other validation failures.
    """
    blast_radius = experiment.get("blast_radius")
    if blast_radius not in VALID_BLAST_RADII:
        raise ChaosExperimentInvalidBlastRadiusError(blast_radius=str(blast_radius))

    intensity = experiment.get("intensity")
    if intensity not in VALID_INTENSITIES:
        raise ChaosExperimentError(
            code="CHAOS_EXPERIMENT_INVALID_INTENSITY",
            message_ko=f"유효하지 않은 intensity: {intensity!r}",
            details={"intensity": intensity, "valid": list(VALID_INTENSITIES)},
            http_status=400,
        )

    fault_type = experiment.get("fault_type")
    if fault_type not in VALID_FAULT_TYPES:
        raise ChaosExperimentError(
            code="CHAOS_EXPERIMENT_INVALID_FAULT_TYPE",
            message_ko=f"유효하지 않은 fault_type: {fault_type!r}",
            details={
                "fault_type": fault_type,
                "valid": list(VALID_FAULT_TYPES),
            },
            http_status=400,
        )

    duration = experiment.get("duration_seconds")
    if not isinstance(duration, int) or duration < MIN_DURATION_SECONDS or duration > MAX_DURATION_SECONDS:
        raise ChaosExperimentError(
            code="CHAOS_EXPERIMENT_INVALID_DURATION",
            message_ko=f"유효하지 않은 duration_seconds: {duration!r}",
            details={
                "duration_seconds": duration,
                "min": MIN_DURATION_SECONDS,
                "max": MAX_DURATION_SECONDS,
            },
            http_status=400,
        )

    abort_conditions = experiment.get("abort_conditions", [])
    if (
        not isinstance(abort_conditions, list)
        or len(abort_conditions) < MIN_ABORT_CONDITIONS
        or len(abort_conditions) > MAX_ABORT_CONDITIONS
    ):
        raise ChaosExperimentError(
            code="CHAOS_EXPERIMENT_INVALID_ABORT_CONDITIONS",
            message_ko="abort_conditions는 1~4개 필요.",
            details={
                "count": len(abort_conditions) if isinstance(abort_conditions, list) else 0,
                "min": MIN_ABORT_CONDITIONS,
                "max": MAX_ABORT_CONDITIONS,
            },
            http_status=400,
        )

    rollback_strategy = experiment.get("rollback_strategy")
    if rollback_strategy not in VALID_ROLLBACK_STRATEGIES:
        raise ChaosExperimentError(
            code="CHAOS_EXPERIMENT_INVALID_ROLLBACK_STRATEGY",
            message_ko=f"유효하지 않은 rollback_strategy: {rollback_strategy!r}",
            details={
                "rollback_strategy": rollback_strategy,
                "valid": list(VALID_ROLLBACK_STRATEGIES),
            },
            http_status=400,
        )


__all__ = [
    "ChaosExperiment",
    "AbortCondition",
    "BLAST_RADIUS_L1",
    "BLAST_RADIUS_L2",
    "BLAST_RADIUS_L3",
    "BLAST_RADIUS_L4",
    "BLAST_RADIUS_L5",
    "VALID_BLAST_RADII",
    "VALID_FAULT_TYPES",
    "VALID_INTENSITIES",
    "VALID_ROLLBACK_STRATEGIES",
    "FAULT_TYPE_LATENCY",
    "FAULT_TYPE_ERROR",
    "FAULT_TYPE_RESOURCE",
    "FAULT_TYPE_NETWORK",
    "FAULT_TYPE_DISK_IO",
    "FAULT_TYPE_DB_POOL",
    "FAULT_TYPE_CACHE",
    "FAULT_TYPE_DNS",
    "FAULT_TYPE_PROCESS",
    "FAULT_TYPE_CLOCK_SKEW",
    "INTENSITY_LOW",
    "INTENSITY_MEDIUM",
    "INTENSITY_HIGH",
    "ROLLBACK_AUTOMATIC",
    "ROLLBACK_MANUAL",
    "ROLLBACK_HYBRID",
    "ROLLBACK_SCHEDULED",
    "MAX_DURATION_SECONDS",
    "MIN_DURATION_SECONDS",
    "MIN_ABORT_CONDITIONS",
    "MAX_ABORT_CONDITIONS",
    "ChaosExperimentError",
    "ChaosExperimentInvalidBlastRadiusError",
    "ChaosExperimentOwnerOnlyForbiddenError",
    "ChaosRollbackTriggerFailedError",
    "ContinuousChaosProductionUnsafeError",
    "validate_chaos_experiment",
]
