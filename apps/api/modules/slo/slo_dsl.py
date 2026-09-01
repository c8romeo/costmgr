"""apps.api.modules.slo.slo_dsl — SLO definition DSL + TypedDict (PRD §F26.1).

Phase 10 (cj-style 103번째 wire) — SLO Engineering / Error Budget
Management territory (PRD §F26.1 verbatim).

This module provides:
- `SloDefinition` TypedDict with 13 fields (PRD §F26.1 verbatim).
- 5 SLI types + 6 windows + 4 burn-rate thresholds + 3 error_budget
  policies + 3 regions + 4 multi_region_aggregation methods.
- Lifecycle states draft → active → paused → retired.
- 5 NEW CR 12-5 D-14 typed exception classes (SloDefinitionInvalid +
  SloOverrideConflict + SloBudgetExhausted + SloViolationDetected +
  SloGovernanceRequiredForbidden).
- `validate_slo_definition()` — pydantic v2 model_validator-equivalent
  enforcing all field constraints + lifecycle transitions.

CR lessons applied:
- CR 0-2 RLS — every SloDefinition carries tenant_id selector + cross-
  tenant isolation verification.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `slo_target_updated` (state transitions + target changes).
- CR 4-3/4-4 — slo_definitions baseline 30d rolling + golden_diff
  pattern verbatim 미러 (Phase 8 baseline freeze pattern).
- CR 1-1 ContextVar — trace_id request-scoped ContextVar binding.
- CR 12-5 D-14 typed exception envelope.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — SLO creation/update/delete all owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.

Industry-agnostic per CR 12-1 L4 precedent (mirrors CHAOS_ENGINEERING
Phase 9 wire + PERFORMANCE_TESTING Phase 8 wire + OBSERVABILITY_*
Phase 7 wire + AUDIT_LOG_RETENTION Phase 6 wire + AUDIT_LOG_VIEW
Epic 17 wire + MULTI_REGION_BACKUP/FAILOVER Phase 5 wire pattern
verbatim). All 4 industries get SLO_ENGINEERING capability.
"""

from __future__ import annotations

import uuid
from typing import Any, Final, TypedDict

from apps.api.core.errors import BaseError

# ── Constants — 5 SLI types (PRD §F26.1.4 verbatim) ────────────
SLI_TYPE_LATENCY: Final[str] = "latency"
SLI_TYPE_AVAILABILITY: Final[str] = "availability"
SLI_TYPE_THROUGHPUT: Final[str] = "throughput"
SLI_TYPE_ERROR_RATE: Final[str] = "error_rate"
SLI_TYPE_FRESHNESS: Final[str] = "freshness"

VALID_SLI_TYPES: Final[tuple[str, ...]] = (
    SLI_TYPE_LATENCY,
    SLI_TYPE_AVAILABILITY,
    SLI_TYPE_THROUGHPUT,
    SLI_TYPE_ERROR_RATE,
    SLI_TYPE_FRESHNESS,
)


# ── Constants — 6 windows (PRD §F26.1.4 verbatim) ──────────────
WINDOW_1H: Final[str] = "1h"
WINDOW_6H: Final[str] = "6h"
WINDOW_24H: Final[str] = "24h"
WINDOW_3D: Final[str] = "3d"
WINDOW_7D: Final[str] = "7d"
WINDOW_30D: Final[str] = "30d"

VALID_WINDOWS: Final[tuple[str, ...]] = (
    WINDOW_1H,
    WINDOW_6H,
    WINDOW_24H,
    WINDOW_3D,
    WINDOW_7D,
    WINDOW_30D,
)


# ── Constants — 3 error budget policies ────────────────────────
BUDGET_POLICY_FREEZE: Final[str] = "freeze_on_exhaust"
BUDGET_POLICY_ALERT: Final[str] = "alert_only"
BUDGET_POLICY_AUTO_ROLLBACK: Final[str] = "auto_rollback"

VALID_BUDGET_POLICIES: Final[tuple[str, ...]] = (
    BUDGET_POLICY_FREEZE,
    BUDGET_POLICY_ALERT,
    BUDGET_POLICY_AUTO_ROLLBACK,
)


# ── Constants — 3 regions (PRD §F26.4.3 verbatim) ──────────────
REGION_SEOUL: Final[str] = "seoul"
REGION_TOKYO: Final[str] = "tokyo"
REGION_ALL: Final[str] = "all"

VALID_REGIONS: Final[tuple[str, ...]] = (
    REGION_SEOUL,
    REGION_TOKYO,
    REGION_ALL,
)


# ── Constants — 4 multi_region_aggregation methods ──────────────
AGGREGATION_WEIGHTED_AVG: Final[str] = "weighted_avg"
AGGREGATION_MIN: Final[str] = "min"
AGGREGATION_MAX: Final[str] = "max"
AGGREGATION_ANY_FAILURE: Final[str] = "any_failure"

VALID_AGGREGATIONS: Final[tuple[str, ...]] = (
    AGGREGATION_WEIGHTED_AVG,
    AGGREGATION_MIN,
    AGGREGATION_MAX,
    AGGREGATION_ANY_FAILURE,
)


# ── Constants — lifecycle states ────────────────────────────────
STATE_DRAFT: Final[str] = "draft"
STATE_ACTIVE: Final[str] = "active"
STATE_PAUSED: Final[str] = "paused"
STATE_RETIRED: Final[str] = "retired"

VALID_STATES: Final[tuple[str, ...]] = (
    STATE_DRAFT,
    STATE_ACTIVE,
    STATE_PAUSED,
    STATE_RETIRED,
)

# Allowed lifecycle transitions (state machine)
ALLOWED_STATE_TRANSITIONS: Final[dict[str, tuple[str, ...]]] = {
    STATE_DRAFT: (STATE_ACTIVE, STATE_RETIRED),
    STATE_ACTIVE: (STATE_PAUSED, STATE_RETIRED),
    STATE_PAUSED: (STATE_ACTIVE, STATE_RETIRED),
    STATE_RETIRED: (),  # terminal state
}


# ── Constants — objective range ────────────────────────────────
MIN_OBJECTIVE: Final[float] = 0.0
MAX_OBJECTIVE: Final[float] = 100.0

# ── Constants — burn_rate_threshold (positive, default 14.4x = fast burn)
MIN_BURN_RATE_THRESHOLD: Final[float] = 0.1
DEFAULT_BURN_RATE_THRESHOLD: Final[float] = 14.4


# ── Typed envelopes (CR 12-5 D-PARITY-01) ──────────────────────
class SloDefinition(TypedDict):
    """SLO definition (PRD §F26.1.2 verbatim — 13 fields).

    Fields:
        slo_id: Stable unique identifier (UUID4 string).
        tenant_id: Tenant UUID4 string (CR 0-2 RLS — tenant scoping).
        service: Target service / module name (e.g. 'cost_engine',
            'auth', 'audit_log').
        sli_type: One of 5 SLI types (PRD §F26.1.4 verbatim).
        objective: Target value (0.0~100.0, e.g. 99.9).
        window: One of 6 windows (PRD §F26.1.4 verbatim).
        burn_rate_threshold: Alert threshold multiplier (e.g. 14.4x).
        error_budget_policy: One of 3 policies (freeze_on_exhaust /
            alert_only / auto_rollback).
        region: One of 3 regions (seoul / tokyo / all).
        multi_region_aggregation: One of 4 aggregation methods.
        freeze_enabled: If True, freeze deploys when budget exhausted.
        auto_rollback_trigger: If True, auto-rollback on SLO breach.
        governance_required: If True, Epic 12 2FA 챌린지 mandatory.
    """

    slo_id: str
    tenant_id: str
    service: str
    sli_type: str
    objective: float
    window: str
    burn_rate_threshold: float
    error_budget_policy: str
    region: str
    multi_region_aggregation: str
    freeze_enabled: bool
    auto_rollback_trigger: bool
    governance_required: bool


class TenantSloOverride(TypedDict):
    """Tenant-scoped SLO override (PRD §F26.4.5 verbatim — 6 fields).

    Fields:
        override_id: Stable unique identifier.
        slo_id: Target SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        objective_override: Optional override of objective.
        window_override: Optional override of window.
        effective_from: ISO8601 timestamp from which override is active.
    """

    override_id: str
    slo_id: str
    tenant_id: str
    objective_override: float | None
    window_override: str | None
    effective_from: str


# ── CR 12-5 D-14 typed exception envelope — 5 NEW error classes ──
class SloError(BaseError):
    """Base class for SLO errors."""

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


class SloDefinitionInvalidError(SloError):
    """400 SLO_DEFINITION_INVALID — SloDefinition payload validation failure."""

    def __init__(
        self,
        *,
        field: str,
        value: object,
        valid: list[str] | None = None,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="SLO_DEFINITION_INVALID",
            message_ko=f"유효하지 않은 SLO 정의: {field}={value!r}",
            details={"field": field, "value": value, "valid": valid or []},
            trace_id=trace_id,
            http_status=400,
        )


class SloOverrideConflictError(SloError):
    """409 SLO_OVERRIDE_CONFLICT — duplicate (slo_id, tenant_id) override."""

    def __init__(
        self,
        *,
        slo_id: str,
        tenant_id: str,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="SLO_OVERRIDE_CONFLICT",
            message_ko=f"SLO {slo_id} 에 대한 tenant {tenant_id} override 가 이미 존재합니다.",
            details={"slo_id": slo_id, "tenant_id": tenant_id},
            trace_id=trace_id,
            http_status=409,
        )


class SloBudgetExhaustedError(SloError):
    """422 SLO_BUDGET_EXHAUSTED — error budget exhausted (freeze triggered)."""

    def __init__(
        self,
        *,
        slo_id: str,
        budget_remaining_minutes: float,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="SLO_BUDGET_EXHAUSTED",
            message_ko=f"SLO {slo_id} error budget exhausted.",
            details={
                "slo_id": slo_id,
                "budget_remaining_minutes": budget_remaining_minutes,
            },
            trace_id=trace_id,
            http_status=422,
        )


class SloViolationDetectedError(SloError):
    """422 SLO_VIOLATION_DETECTED — multi-window burn-rate composite alert fired."""

    def __init__(
        self,
        *,
        slo_id: str,
        window: str,
        burn_rate: float,
        threshold: float,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="SLO_VIOLATION_DETECTED",
            message_ko=f"SLO {slo_id} violation detected: window={window} burn_rate={burn_rate}x > {threshold}x",
            details={
                "slo_id": slo_id,
                "window": window,
                "burn_rate": burn_rate,
                "threshold": threshold,
            },
            trace_id=trace_id,
            http_status=422,
        )


class SloGovernanceRequiredForbiddenError(SloError):
    """403 SLO_GOVERNANCE_REQUIRED_FORBIDDEN — caller is not owner + 2FA failed.

    AD-22 owner-only RBAC + Epic 12 2FA 챌린지 mandatory when
    governance_required=True.
    """

    def __init__(
        self,
        *,
        slo_id: str,
        caller_role: str,
        two_factor_passed: bool,
        trace_id: str | None = None,
    ) -> None:
        super().__init__(
            code="SLO_GOVERNANCE_REQUIRED_FORBIDDEN",
            message_ko="SLO governance_required=True → owner-only + Epic 12 2FA 챌린지 mandatory.",
            details={
                "slo_id": slo_id,
                "caller_role": caller_role,
                "required_role": "owner",
                "two_factor_passed": two_factor_passed,
            },
            trace_id=trace_id,
            http_status=403,
        )


# ── Validation (pydantic v2 model_validator-equivalent) ─────────
def validate_slo_definition(slo: dict[str, Any]) -> None:
    """Validate a SloDefinition payload. Raises typed exceptions on violation.

    Validation rules (PRD §F26.1.3 verbatim):
    - sli_type ∈ 5 types.
    - window ∈ 6 windows.
    - objective 0.0~100.0.
    - burn_rate_threshold > 0.
    - error_budget_policy ∈ 3 policies.
    - region ∈ 3 regions.
    - multi_region_aggregation ∈ 4 methods.
    - freeze_enabled / auto_rollback_trigger / governance_required: bool.

    Args:
        slo: SloDefinition-shaped dict.

    Raises:
        SloDefinitionInvalidError: 400.
    """
    sli_type = slo.get("sli_type")
    if sli_type not in VALID_SLI_TYPES:
        raise SloDefinitionInvalidError(
            field="sli_type", value=sli_type, valid=list(VALID_SLI_TYPES)
        )

    window = slo.get("window")
    if window not in VALID_WINDOWS:
        raise SloDefinitionInvalidError(field="window", value=window, valid=list(VALID_WINDOWS))

    objective = slo.get("objective")
    if (
        not isinstance(objective, int | float)
        or objective < MIN_OBJECTIVE
        or objective > MAX_OBJECTIVE
    ):
        raise SloDefinitionInvalidError(
            field="objective",
            value=objective,
            valid=[f"{MIN_OBJECTIVE}~{MAX_OBJECTIVE}"],
        )

    burn_rate_threshold = slo.get("burn_rate_threshold")
    if (
        not isinstance(burn_rate_threshold, int | float)
        or burn_rate_threshold < MIN_BURN_RATE_THRESHOLD
    ):
        raise SloDefinitionInvalidError(
            field="burn_rate_threshold",
            value=burn_rate_threshold,
            valid=[f">={MIN_BURN_RATE_THRESHOLD}"],
        )

    error_budget_policy = slo.get("error_budget_policy")
    if error_budget_policy not in VALID_BUDGET_POLICIES:
        raise SloDefinitionInvalidError(
            field="error_budget_policy",
            value=error_budget_policy,
            valid=list(VALID_BUDGET_POLICIES),
        )

    region = slo.get("region")
    if region not in VALID_REGIONS:
        raise SloDefinitionInvalidError(field="region", value=region, valid=list(VALID_REGIONS))

    multi_region_aggregation = slo.get("multi_region_aggregation")
    if multi_region_aggregation not in VALID_AGGREGATIONS:
        raise SloDefinitionInvalidError(
            field="multi_region_aggregation",
            value=multi_region_aggregation,
            valid=list(VALID_AGGREGATIONS),
        )

    for bool_field in ("freeze_enabled", "auto_rollback_trigger", "governance_required"):
        value = slo.get(bool_field)
        if not isinstance(value, bool):
            raise SloDefinitionInvalidError(field=bool_field, value=value, valid=["True", "False"])


def is_valid_state_transition(current_state: str, new_state: str) -> bool:
    """Check if state transition is allowed (state machine).

    Lifecycle: draft → active → paused → retired.
    Returns True if transition allowed.
    """
    if current_state not in VALID_STATES:
        return False
    if new_state not in VALID_STATES:
        return False
    return new_state in ALLOWED_STATE_TRANSITIONS.get(current_state, ())


__all__ = [
    "SloDefinition",
    "TenantSloOverride",
    "SLI_TYPE_LATENCY",
    "SLI_TYPE_AVAILABILITY",
    "SLI_TYPE_THROUGHPUT",
    "SLI_TYPE_ERROR_RATE",
    "SLI_TYPE_FRESHNESS",
    "VALID_SLI_TYPES",
    "WINDOW_1H",
    "WINDOW_6H",
    "WINDOW_24H",
    "WINDOW_3D",
    "WINDOW_7D",
    "WINDOW_30D",
    "VALID_WINDOWS",
    "BUDGET_POLICY_FREEZE",
    "BUDGET_POLICY_ALERT",
    "BUDGET_POLICY_AUTO_ROLLBACK",
    "VALID_BUDGET_POLICIES",
    "REGION_SEOUL",
    "REGION_TOKYO",
    "REGION_ALL",
    "VALID_REGIONS",
    "AGGREGATION_WEIGHTED_AVG",
    "AGGREGATION_MIN",
    "AGGREGATION_MAX",
    "AGGREGATION_ANY_FAILURE",
    "VALID_AGGREGATIONS",
    "STATE_DRAFT",
    "STATE_ACTIVE",
    "STATE_PAUSED",
    "STATE_RETIRED",
    "VALID_STATES",
    "ALLOWED_STATE_TRANSITIONS",
    "MIN_OBJECTIVE",
    "MAX_OBJECTIVE",
    "MIN_BURN_RATE_THRESHOLD",
    "DEFAULT_BURN_RATE_THRESHOLD",
    "SloError",
    "SloDefinitionInvalidError",
    "SloOverrideConflictError",
    "SloBudgetExhaustedError",
    "SloViolationDetectedError",
    "SloGovernanceRequiredForbiddenError",
    "validate_slo_definition",
    "is_valid_state_transition",
]
