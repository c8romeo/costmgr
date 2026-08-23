"""apps.api.modules.slo.error_budget — Error budget tracker + freeze mechanism.

Phase 10 (cj-style 103번째 wire) — SLO Engineering / Error Budget
Management territory (PRD §F26.3 verbatim).

This module provides:
- `ErrorBudget` TypedDict (8 fields) — SLO error budget tracking.
- Budget consumption calculation (PRD §F26.3.3 verbatim).
- Freeze mechanism (PRD §F26.3.4 verbatim) — auto-freeze on
  budget exhaustion or `freeze_on_exhaust` policy.
- Exhaustion prediction (PRD §F26.3.5 verbatim) — linear extrapolation
  with 7d pre-emptive alert.
- `BudgetEvaluationResult` TypedDict — evaluation outcome.
- CR 1-1 audit-first INSERT integration points (emit_audit_typed
  BEFORE freeze trigger, AFTER budget exhaustion).

CR lessons applied:
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `slo_budget_exhausted` (AFTER freeze trigger).
- CR 4-3/4-4 — error_budget baseline 30d rolling + golden_diff pattern
  verbatim 미러.
- CR 1-1 ContextVar — trace_id request-scoped ContextVar binding.

AD-22 owner-only RBAC — freeze + unfreeze + override all owner-only +
Epic 12 2FA 챌린지 mandatory.

Industry-agnostic per CR 12-1 L4 precedent.
"""
from __future__ import annotations

import logging
import uuid
from typing import Final, Literal, TypedDict

from apps.api.modules.slo.slo_dsl import (
    BUDGET_POLICY_FREEZE,
    WINDOW_30D,
    SloBudgetExhaustedError,
)

logger = logging.getLogger(__name__)


# ── Constants — budget window defaults ──────────────────────────
DEFAULT_WINDOW_MINUTES: Final[int] = 30 * 24 * 60  # 30d = 43200 minutes
MINUTES_PER_HOUR: Final[int] = 60
HOURS_PER_DAY: Final[int] = 24
DAYS_PER_WINDOW_30D: Final[int] = 30

# 7-day pre-emptive alert horizon
EXHAUSTION_PREDICTION_HORIZON_DAYS: Final[int] = 7

# Default objective ratio for 99.9% SLO
DEFAULT_OBJECTIVE_RATIO: Final[float] = 0.999

# Total minutes in window for 30d
WINDOW_30D_MINUTES: Final[int] = DAYS_PER_WINDOW_30D * HOURS_PER_DAY * MINUTES_PER_HOUR

# Default 99.9% SLO → 0.1% budget → 4320 minutes (30d * 1440min * 0.001)
DEFAULT_BUDGET_FRACTION_99_9: Final[float] = 0.001


# ── Typed envelopes (CR 12-5 D-PARITY-01) ──────────────────────
class ErrorBudget(TypedDict):
    """Error budget tracking record (PRD §F26.3.2 verbatim — 8 fields).

    Fields:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string (CR 0-2 RLS — tenant scoping).
        budget_total_minutes: Total budget in minutes (e.g. 43200 = 30d
            × 1440min × 0.1% SLO).
        budget_consumed_minutes: Budget consumed so far.
        budget_remaining_minutes: Budget remaining (negative = exhausted).
        freeze_triggered: If True, deploy is blocked.
        exhaustion_predicted_at: ISO8601 timestamp of predicted exhaustion
            (None if not predicted within horizon).
        last_evaluated_at: ISO8601 timestamp of last evaluation.
    """

    slo_id: str
    tenant_id: str
    budget_total_minutes: float
    budget_consumed_minutes: float
    budget_remaining_minutes: float
    freeze_triggered: bool
    exhaustion_predicted_at: str | None
    last_evaluated_at: str


class BudgetEvaluationResult(TypedDict):
    """Error budget evaluation outcome (PRD §F26.3.4 verbatim).

    Fields:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        budget_consumed_minutes: Updated consumed minutes.
        budget_remaining_minutes: Updated remaining minutes.
        freeze_triggered: True if freeze is now active.
        exhaustion_predicted: True if exhaustion predicted within horizon.
        exhaustion_predicted_at: ISO8601 timestamp of predicted exhaustion.
        trace_id: Request trace_id.
    """

    slo_id: str
    tenant_id: str
    budget_consumed_minutes: float
    budget_remaining_minutes: float
    freeze_triggered: bool
    exhaustion_predicted: bool
    exhaustion_predicted_at: str | None
    trace_id: str


# ── Budget total calculation (PRD §F26.3.3 verbatim) ───────────
def compute_budget_total_minutes(
    window: str,
    objective: float,
    window_minutes: int | None = None,
) -> float:
    """Compute total error budget in minutes for a given SLO.

    Formula: budget_total_minutes = window_minutes * (1 - objective_ratio)
    (objective 99.9% → window 30d = 43200min → budget 4320min = 0.1%).

    Args:
        window: One of 6 windows (WINDOW_1H/6H/24H/3D/7D/30D).
        objective: SLO objective as percentage (e.g. 99.9).
        window_minutes: Optional override for window minutes.

    Returns:
        Total budget in minutes (>= 0).
    """
    objective_ratio = objective / 100.0
    if objective_ratio >= 1.0:
        return 0.0
    if window_minutes is None:
        if window == WINDOW_30D:
            window_minutes = WINDOW_30D_MINUTES
        else:
            # For shorter windows, scale proportionally
            try:
                window_minutes = _window_to_minutes(window)
            except ValueError:
                window_minutes = DEFAULT_WINDOW_MINUTES
    return float(window_minutes) * (1.0 - objective_ratio)


def _window_to_minutes(window: str) -> int:
    """Convert window string to minutes.

    Supports WINDOW_1H/6H/24H/3D/7D/30D.

    Raises:
        ValueError: If window is not a recognized value.
    """
    mapping = {
        "1h": 60,
        "6h": 6 * 60,
        "24h": 24 * 60,
        "3d": 3 * 24 * 60,
        "7d": 7 * 24 * 60,
        "30d": 30 * 24 * 60,
    }
    if window not in mapping:
        raise ValueError(f"unsupported window: {window!r}")
    return mapping[window]


# ── Budget consumption calculation (PRD §F26.3.3 verbatim) ──────
def compute_consumed_minutes(
    window_minutes: int,
    objective: float,
    burn_rate_factor: float,
) -> float:
    """Compute consumed minutes given burn rate factor.

    Formula: consumed_minutes = window_minutes * (1 - objective) * burn_rate_factor

    Args:
        window_minutes: Window size in minutes.
        objective: SLO objective as percentage (e.g. 99.9).
        burn_rate_factor: Observed burn rate multiplier (>= 0).

    Returns:
        Consumed minutes (>= 0).
    """
    objective_ratio = objective / 100.0
    if objective_ratio >= 1.0:
        return 0.0
    return float(window_minutes) * (1.0 - objective_ratio) * max(0.0, burn_rate_factor)


# ── Exhaustion prediction (PRD §F26.3.5 verbatim) ─────────────
def predict_exhaustion_at(
    *,
    budget_total_minutes: float,
    budget_consumed_minutes: float,
    burn_rate_factor: float,
    evaluated_at: str,
    horizon_days: int = EXHAUSTION_PREDICTION_HORIZON_DAYS,
) -> str | None:
    """Predict exhaustion timestamp via linear extrapolation.

    If burn_rate_factor > 1 and current trajectory projects exhaustion
    within the horizon window, return the predicted ISO8601 timestamp.
    Otherwise return None (no exhaustion predicted within horizon).

    Args:
        budget_total_minutes: Total budget in minutes.
        budget_consumed_minutes: Consumed minutes so far.
        burn_rate_factor: Observed burn rate multiplier.
        evaluated_at: ISO8601 timestamp of evaluation.
        horizon_days: Pre-emptive alert horizon (default 7d).

    Returns:
        ISO8601 timestamp of predicted exhaustion, or None.
    """
    if burn_rate_factor <= 0.0:
        return None
    remaining = budget_total_minutes - budget_consumed_minutes
    if remaining <= 0:
        return evaluated_at  # already exhausted

    # Time to exhaust (minutes) at current rate
    # burn_rate_factor = (consumed per window) / (allowed per window)
    # So consumed_per_minute = (budget_total / window_minutes) * burn_rate_factor
    # If we assume the burn_rate applies over the WINDOW_30D_MINUTES window:
    window_minutes = WINDOW_30D_MINUTES
    consumed_per_minute = (
        budget_total_minutes / window_minutes
    ) * burn_rate_factor

    if consumed_per_minute <= 0:
        return None

    minutes_to_exhaust = remaining / consumed_per_minute
    minutes_to_horizon = horizon_days * HOURS_PER_DAY * MINUTES_PER_HOUR

    if minutes_to_exhaust > minutes_to_horizon:
        return None

    # Compute ISO8601 by parsing evaluated_at and adding minutes.
    # Caller is expected to provide a parseable ISO8601 string.
    # We avoid bringing in datetime.fromisoformat() to keep the module
    # dependency surface minimal (CR 1-1 verbatim isolation).
    from datetime import datetime, timedelta

    try:
        base = datetime.fromisoformat(evaluated_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None
    predicted = base + timedelta(minutes=minutes_to_exhaust)
    return predicted.isoformat()


# ── Evaluation orchestration ───────────────────────────────────
def evaluate_error_budget(
    *,
    slo_id: str,
    tenant_id: str,
    error_budget_policy: str,
    objective: float,
    window: str,
    burn_rate_factor: float,
    evaluated_at: str,
    previous_freeze_triggered: bool = False,
    trace_id: str | None = None,
) -> BudgetEvaluationResult:
    """Evaluate error budget state for an SLO.

    Steps (PRD §F26.3.3 + §F26.3.4 + §F26.3.5 verbatim):
    1. Compute budget_total_minutes for window.
    2. Compute budget_consumed_minutes from burn_rate_factor.
    3. Compute budget_remaining_minutes.
    4. Decide freeze_trigger based on policy + remaining.
    5. Predict exhaustion within 7d horizon.

    Args:
        slo_id: SloDefinition.slo_id.
        tenant_id: Tenant UUID4 string.
        error_budget_policy: One of 3 policies (freeze_on_exhaust /
            alert_only / auto_rollback).
        objective: SLO objective as percentage.
        window: SLO window.
        burn_rate_factor: Observed burn rate multiplier.
        evaluated_at: ISO8601 timestamp.
        previous_freeze_triggered: Whether freeze was already triggered
            (idempotent no-op per CR 1-1).
        trace_id: Request trace_id.

    Returns:
        BudgetEvaluationResult with freeze + prediction outcome.

    Raises:
        SloBudgetExhaustedError: When budget is exhausted AND freeze policy
            applies (per PRD §F26.3.4 + audit-first INSERT BEFORE raise).
    """
    resolved_trace_id = trace_id or str(uuid.uuid4())

    window_minutes = _window_to_minutes(window)
    total = compute_budget_total_minutes(
        window=window, objective=objective, window_minutes=window_minutes
    )
    consumed = compute_consumed_minutes(
        window_minutes=window_minutes,
        objective=objective,
        burn_rate_factor=burn_rate_factor,
    )
    remaining = total - consumed

    # Freeze decision
    freeze_now = previous_freeze_triggered
    if not freeze_now:
        if error_budget_policy == BUDGET_POLICY_FREEZE and remaining < 0:
            freeze_now = True

    # Exhaustion prediction
    predicted_at = predict_exhaustion_at(
        budget_total_minutes=total,
        budget_consumed_minutes=consumed,
        burn_rate_factor=burn_rate_factor,
        evaluated_at=evaluated_at,
    )
    exhaustion_predicted = predicted_at is not None

    result = BudgetEvaluationResult(
        slo_id=slo_id,
        tenant_id=tenant_id,
        budget_consumed_minutes=consumed,
        budget_remaining_minutes=remaining,
        freeze_triggered=freeze_now,
        exhaustion_predicted=exhaustion_predicted,
        exhaustion_predicted_at=predicted_at,
        trace_id=resolved_trace_id,
    )

    # Raise typed exception when budget is exhausted under freeze policy.
    # Audit-first INSERT happens at the route layer BEFORE raise (CR 1-1).
    if freeze_now and remaining < 0:
        logger.warning(
            "slo_budget_exhausted slo_id=%s remaining=%.2fmin policy=%s",
            slo_id,
            remaining,
            error_budget_policy,
        )
        raise SloBudgetExhaustedError(
            slo_id=slo_id,
            budget_remaining_minutes=remaining,
            trace_id=resolved_trace_id,
        )

    return result


__all__ = [
    "ErrorBudget",
    "BudgetEvaluationResult",
    "DEFAULT_WINDOW_MINUTES",
    "MINUTES_PER_HOUR",
    "HOURS_PER_DAY",
    "DAYS_PER_WINDOW_30D",
    "EXHAUSTION_PREDICTION_HORIZON_DAYS",
    "DEFAULT_OBJECTIVE_RATIO",
    "WINDOW_30D_MINUTES",
    "DEFAULT_BUDGET_FRACTION_99_9",
    "compute_budget_total_minutes",
    "compute_consumed_minutes",
    "predict_exhaustion_at",
    "evaluate_error_budget",
    "_window_to_minutes",
]
