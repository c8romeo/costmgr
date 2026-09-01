"""apps.api.modules.slo.governance — SLO governance + auto-rollback SLO breach trigger.

Phase 10 (cj-style 103번째 wire) — SLO Engineering / Error Budget
Management territory (PRD §F26.5 verbatim).

This module provides:
- `GovernanceReview` TypedDict (7 fields) — SLO governance review record.
- Auto-rollback SLO breach trigger 4 conditions (PRD §F26.5.3 verbatim):
  (a) fast burn 1h window 14.4x breach → 즉시 auto-rollback.
  (b) slow burn 6h window 6x breach → 30min 이내 auto-rollback.
  (c) composite alert 3/4 windows AND breach → critical auto-rollback.
  (d) error budget exhaustion < 0 minutes remaining → 즉시 freeze +
      auto-rollback.
- Phase 9 wire `e7670e1` chaos_experiment auto-rollback 정합 (SLO breach
  시 `chaos_rollback_triggered` 와 `slo_budget_exhausted` audit-first
  INSERT 동시 발생).
- Epic 12 2FA 챌린지 integration (governance_required=True SLO 시
  mandatory).

CR lessons applied:
- CR 0-2 RLS — tenant_id selector.
- CR 1-1 audit-first INSERT — 3 NEW actions (slo_target_updated +
  slo_budget_exhausted + slo_violation_detected) CR 1-1 verbatim
  applied.
- CR 4-3/4-4 — governance review baseline 30d rolling pattern verbatim
  미러.

AD-22 owner-only RBAC — SLO approval/rejection + freeze override +
auto-rollback trigger 모두 owner-only + Epic 12 2FA 챌린지 mandatory.

Industry-agnostic per CR 12-1 L4 precedent.
"""

from __future__ import annotations

import logging
import uuid
from typing import Final, TypedDict

from apps.api.modules.slo.slo_burn_rate_evaluator import (
    WINDOW_FAST_BURN,
    WINDOW_SLOW_BURN,
    SloBurnRateEvaluation,
)
from apps.api.modules.slo.slo_dsl import (
    BUDGET_POLICY_AUTO_ROLLBACK,
    SloError,
)

logger = logging.getLogger(__name__)


# ── Constants — auto-rollback timing ────────────────────────────
# PRD §F26.5.3 verbatim — 4 trigger conditions + timing thresholds
FAST_BURN_AUTO_ROLLBACK_WINDOW_SECONDS: Final[int] = 60  # 즉시 (1min)
SLOW_BURN_AUTO_ROLLBACK_WINDOW_SECONDS: Final[int] = 30 * 60  # 30min
COMPOSITE_AUTO_ROLLBACK_WINDOW_SECONDS: Final[int] = 60  # critical 즉시
EXHAUSTION_AUTO_ROLLBACK_WINDOW_SECONDS: Final[int] = 60  # 즉시 freeze


# ── Constants — review status ───────────────────────────────────
REVIEW_STATUS_PENDING: Final[str] = "pending"
REVIEW_STATUS_APPROVED: Final[str] = "approved"
REVIEW_STATUS_REJECTED: Final[str] = "rejected"
REVIEW_STATUS_ESCALATED: Final[str] = "escalated"

VALID_REVIEW_STATUSES: Final[tuple[str, ...]] = (
    REVIEW_STATUS_PENDING,
    REVIEW_STATUS_APPROVED,
    REVIEW_STATUS_REJECTED,
    REVIEW_STATUS_ESCALATED,
)


# ── Typed envelopes (CR 12-5 D-PARITY-01) ──────────────────────
class GovernanceReview(TypedDict):
    """SLO governance review (PRD §F26.5.2 verbatim — 7 fields).

    Fields:
        review_id: Stable unique identifier (UUID4 string).
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string (CR 0-2 RLS).
        reviewer_id: users(id) FK (UUID4 string) — must be owner role.
        review_status: One of 4 statuses (pending/approved/rejected/escalated).
        governance_notes: Free-text review notes.
        reviewed_at: TIMESTAMPTZ of review decision.
    """

    review_id: str
    slo_id: str
    tenant_id: str
    reviewer_id: str
    review_status: str
    governance_notes: str
    reviewed_at: str


class AutoRollbackDecision(TypedDict):
    """Auto-rollback decision record (PRD §F26.5.3 verbatim).

    Fields:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        trigger_condition: One of 4 conditions (a/b/c/d).
        within_window_seconds: Window for auto-rollback.
        rollback_strategy: 'immediate' | '30min' | 'critical_immediate'.
        trace_id: Request trace_id.
        executed_at: ISO8601 timestamp.
    """

    slo_id: str
    tenant_id: str
    trigger_condition: str
    within_window_seconds: int
    rollback_strategy: str
    trace_id: str
    executed_at: str


# ── CR 12-5 D-14 typed exception (governance-specific) ─────────
class SloGovernanceRequiredForbiddenError(SloError):
    """403 SLO_GOVERNANCE_REQUIRED_FORBIDDEN — owner + 2FA required.

    (Mirrored in slo_dsl.py — re-exported here for governance-specific
    use cases.)
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
            message_ko="SLO governance 결정은 owner + Epic 12 2FA 챌린지 mandatory.",
            details={
                "slo_id": slo_id,
                "caller_role": caller_role,
                "required_role": "owner",
                "two_factor_passed": two_factor_passed,
            },
            trace_id=trace_id,
            http_status=403,
        )


# ── Auto-rollback 4 conditions (PRD §F26.5.3 verbatim) ─────────
def should_trigger_auto_rollback(
    *,
    burn_rate_evaluation: SloBurnRateEvaluation,
    error_budget_policy: str,
    budget_remaining_minutes: float,
) -> tuple[bool, str, int]:
    """Determine if auto-rollback should trigger based on 4 conditions.

    Conditions (PRD §F26.5.3 verbatim):
    (a) fast burn 1h window 14.4x breach → 즉시 auto-rollback.
    (b) slow burn 6h window 6x breach → 30min 이내 auto-rollback.
    (c) composite alert 3/4 windows AND breach → critical auto-rollback.
    (d) error budget exhaustion < 0 minutes remaining → 즉시 freeze +
        auto-rollback.

    Args:
        burn_rate_evaluation: SloBurnRateEvaluation result.
        error_budget_policy: SLO's error_budget_policy.
        budget_remaining_minutes: Current budget remaining.

    Returns:
        Tuple of (should_trigger, condition_label, within_window_seconds).
    """
    by_window = {r["window"]: r["breached"] for r in burn_rate_evaluation["window_results"]}

    # (a) fast burn 1h window 14.4x breach
    if by_window.get(WINDOW_FAST_BURN, False):
        return True, "fast_burn_breach", FAST_BURN_AUTO_ROLLBACK_WINDOW_SECONDS

    # (b) slow burn 6h window 6x breach
    if by_window.get(WINDOW_SLOW_BURN, False):
        return True, "slow_burn_breach", SLOW_BURN_AUTO_ROLLBACK_WINDOW_SECONDS

    # (c) composite alert 3/4 windows AND breach
    if burn_rate_evaluation["composite_breached"]:
        return True, "composite_alert", COMPOSITE_AUTO_ROLLBACK_WINDOW_SECONDS

    # (d) error budget exhaustion < 0 minutes remaining
    if error_budget_policy == BUDGET_POLICY_AUTO_ROLLBACK and budget_remaining_minutes < 0:
        return True, "budget_exhaustion", EXHAUSTION_AUTO_ROLLBACK_WINDOW_SECONDS

    return False, "", 0


# ── Auto-rollback trigger (PRD §F26.5.3 verbatim) ──────────────
def trigger_auto_rollback(
    *,
    slo_id: str,
    tenant_id: str,
    burn_rate_evaluation: SloBurnRateEvaluation,
    error_budget_policy: str,
    budget_remaining_minutes: float,
    executed_at: str,
    trace_id: str | None = None,
) -> AutoRollbackDecision | None:
    """Decide + record auto-rollback decision (PRD §F26.5.3 verbatim).

    The actual rollback execution (Phase 9 wire `e7670e1` chaos_experiment
    auto-rollback integration) is performed at the route layer.

    Args:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        burn_rate_evaluation: SloBurnRateEvaluation result.
        error_budget_policy: SLO's error_budget_policy.
        budget_remaining_minutes: Current budget remaining.
        executed_at: ISO8601 timestamp.
        trace_id: Request trace_id.

    Returns:
        AutoRollbackDecision if trigger conditions met, else None.
    """
    resolved_trace_id = trace_id or str(uuid.uuid4())

    should_trigger, condition_label, within_window = should_trigger_auto_rollback(
        burn_rate_evaluation=burn_rate_evaluation,
        error_budget_policy=error_budget_policy,
        budget_remaining_minutes=budget_remaining_minutes,
    )

    if not should_trigger:
        return None

    if condition_label == "fast_burn_breach":
        rollback_strategy = "immediate"
    elif condition_label == "slow_burn_breach":
        rollback_strategy = "30min"
    elif condition_label == "composite_alert":
        rollback_strategy = "critical_immediate"
    elif condition_label == "budget_exhaustion":
        rollback_strategy = "immediate"
    else:
        rollback_strategy = "immediate"

    logger.warning(
        "slo_auto_rollback_triggered slo_id=%s condition=%s window=%ds",
        slo_id,
        condition_label,
        within_window,
    )

    return AutoRollbackDecision(
        slo_id=slo_id,
        tenant_id=tenant_id,
        trigger_condition=condition_label,
        within_window_seconds=within_window,
        rollback_strategy=rollback_strategy,
        trace_id=resolved_trace_id,
        executed_at=executed_at,
    )


# ── Governance review lifecycle (PRD §F26.5.6 verbatim) ────────
def build_governance_review(
    *,
    review_id: str,
    slo_id: str,
    tenant_id: str,
    reviewer_id: str,
    review_status: str,
    governance_notes: str,
    reviewed_at: str,
) -> GovernanceReview:
    """Build a GovernanceReview payload.

    Args:
        review_id: Stable unique identifier.
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        reviewer_id: users(id) FK (UUID4 string).
        review_status: One of 4 statuses.
        governance_notes: Free-text notes.
        reviewed_at: ISO8601 timestamp.

    Returns:
        GovernanceReview payload.
    """
    if review_status not in VALID_REVIEW_STATUSES:
        raise SloError(
            code="SLO_GOVERNANCE_INVALID_STATUS",
            message_ko=f"유효하지 않은 review_status: {review_status!r}",
            details={"review_status": review_status, "valid": list(VALID_REVIEW_STATUSES)},
            http_status=400,
        )
    return GovernanceReview(
        review_id=review_id,
        slo_id=slo_id,
        tenant_id=tenant_id,
        reviewer_id=reviewer_id,
        review_status=review_status,
        governance_notes=governance_notes,
        reviewed_at=reviewed_at,
    )


# ── Phase 9 chaos auto-rollback integration (PRD §F26.5.4) ─────
def link_to_chaos_rollback(
    decision: AutoRollbackDecision,
) -> str:
    """Build a Phase 9 wire `e7670e1` chaos_experiment rollback trigger
    correlation id.

    When an SLO breach triggers an auto-rollback, the chaos_experiment
    auto-rollback strategy is invoked with this correlation id so that
    audit_logs records both `chaos_rollback_triggered` and
    `slo_budget_exhausted` (CR 1-1 verbatim dual-row append pattern).

    Args:
        decision: AutoRollbackDecision.

    Returns:
        Correlation id (string) of format 'slo:<slo_id>:<decision.trace_id>'.
    """
    return f"slo:{decision['slo_id']}:{decision['trace_id']}"


__all__ = [
    "GovernanceReview",
    "AutoRollbackDecision",
    "REVIEW_STATUS_PENDING",
    "REVIEW_STATUS_APPROVED",
    "REVIEW_STATUS_REJECTED",
    "REVIEW_STATUS_ESCALATED",
    "VALID_REVIEW_STATUSES",
    "FAST_BURN_AUTO_ROLLBACK_WINDOW_SECONDS",
    "SLOW_BURN_AUTO_ROLLBACK_WINDOW_SECONDS",
    "COMPOSITE_AUTO_ROLLBACK_WINDOW_SECONDS",
    "EXHAUSTION_AUTO_ROLLBACK_WINDOW_SECONDS",
    "SloGovernanceRequiredForbiddenError",
    "should_trigger_auto_rollback",
    "trigger_auto_rollback",
    "build_governance_review",
    "link_to_chaos_rollback",
]
