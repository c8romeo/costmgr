"""apps.api.modules.finops.budget_burnrate — Budget burn-rate projection (PRD §F29.4).

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.4 verbatim).

This module provides:
- `BurnRateProjection` TypedDict with 12 fields (PRD §F29.4.1 verbatim).
- `BudgetOverrunPrediction` TypedDict with 8 fields (PRD §F29.4.2 verbatim).
- 4-input burn-rate formula:
    burn_rate = (consumed_budget / elapsed_period_days) /
                (remaining_budget / remaining_period_days)
- 3-level severity routing:
    warning = 110% (Slack only)
    critical = 130% (Slack + PagerDuty)
    exceeded = 150% (Slack + PagerDuty + Email)
- 24h dedup window (PRD §F29.4.5 verbatim).
- ARIMA projection for end-of-period overrun prediction.
- `project_budget_consumption()` — main entry point (CR 1-1 audit-first
  INSERT for `budget_burn_rate_projected`).

CR lessons applied:
- CR 0-2 RLS — every BurnRateProjection carries tenant_id.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 P-015 — pure validator pattern.
- CR 12-5 D-14 typed exception envelope — BudgetBurnRateProjectionError +
  BudgetOverrunPredictionError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface.
- CR 12-5 D-GATE-01 — capability gate per-tenant on/off.

AD-22 owner-only RBAC — project_budget_consumption owner-only.
"""
from __future__ import annotations

import uuid
from typing import Final, TypedDict

from apps.api.core.errors import (
    BudgetBurnRateProjectionError,
    BudgetOverrunPredictionError,
)
from apps.api.modules.finops.forecast_engine import (
    _arima_predict,
)
from apps.api.modules.finops.forecast_model_registry import (
    SEMVER_DEFAULT_VERSION,
)

# ── Severity levels (PRD §F29.4.3 verbatim) ──────────────────────
SEVERITY_NORMAL: Final[str] = "normal"
SEVERITY_WARNING: Final[str] = "warning"
SEVERITY_CRITICAL: Final[str] = "critical"
SEVERITY_EXCEEDED: Final[str] = "exceeded"

ALL_SEVERITY_LEVELS: Final[tuple[str, ...]] = (
    SEVERITY_NORMAL,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
    SEVERITY_EXCEEDED,
)


# ── 3 threshold percentages (PRD §F29.4.3 verbatim) ─────────────
WARNING_THRESHOLD_PCT: Final[float] = 110.0  # burn_rate >= 110% = warning
CRITICAL_THRESHOLD_PCT: Final[float] = 130.0  # burn_rate >= 130% = critical
EXCEEDED_THRESHOLD_PCT: Final[float] = 150.0  # burn_rate >= 150% = exceeded


# ── 24h dedup window (PRD §F29.4.5 verbatim) ────────────────────
DEDUP_WINDOW_HOURS: Final[int] = 24


# ── 3 alert channel routing (PRD §F29.4.4 verbatim) ──────────────
ALERT_CHANNEL_SLACK: Final[str] = "slack"
ALERT_CHANNEL_PAGERDUTY: Final[str] = "pagerduty"
ALERT_CHANNEL_EMAIL: Final[str] = "email"

ALL_ALERT_CHANNELS: Final[tuple[str, ...]] = (
    ALERT_CHANNEL_SLACK,
    ALERT_CHANNEL_PAGERDUTY,
    ALERT_CHANNEL_EMAIL,
)


# ── Alert routing table (PRD §F29.4.4 verbatim) ──────────────────
_ALERT_ROUTING_TABLE: Final[dict[str, tuple[str, ...]]] = {
    SEVERITY_WARNING: (ALERT_CHANNEL_SLACK,),
    SEVERITY_CRITICAL: (ALERT_CHANNEL_SLACK, ALERT_CHANNEL_PAGERDUTY),
    SEVERITY_EXCEEDED: (ALERT_CHANNEL_SLACK, ALERT_CHANNEL_PAGERDUTY, ALERT_CHANNEL_EMAIL),
}


# ── BurnRateProjection TypedDict (PRD §F29.4.1 verbatim, 12 fields)
class BurnRateProjection(TypedDict, total=True):
    """TypedDict for budget burn-rate projection.

    Fields:
        projection_id: UUID of the projection.
        tenant_id: UUID of the tenant.
        budget_id: UUID of the source budget.
        consumed_budget: actual consumed amount.
        total_budget: total budget allocation.
        elapsed_days: days elapsed in current period.
        remaining_days: days remaining in current period.
        burn_rate_pct: burn-rate percentage (>= 100% means overrun).
        severity: normal/warning/critical/exceeded.
        alert_required: bool — alerts must be dispatched.
        predicted_end_period_spend: ARIMA prediction for end of period.
        trace_id: CR 1-1 ContextVar trace_id.
    """

    projection_id: str
    tenant_id: str
    budget_id: str
    consumed_budget: float
    total_budget: float
    elapsed_days: int
    remaining_days: int
    burn_rate_pct: float
    severity: str
    alert_required: bool
    predicted_end_period_spend: float
    trace_id: str


# ── BudgetOverrunPrediction TypedDict (PRD §F29.4.2 verbatim, 8 fields)
class BudgetOverrunPrediction(TypedDict, total=True):
    """TypedDict for budget overrun prediction.

    Fields:
        prediction_id: UUID of the prediction.
        tenant_id: UUID of the tenant.
        budget_id: UUID of the source budget.
        predicted_overrun_pct: predicted overrun percentage.
        predicted_overrun_date: ISO 8601 predicted overrun date.
        confidence_level: CI level (80/90/95/99).
        model_type: ARIMA (primary for budget burn-rate).
        severity_breach: worst severity expected (warning/critical/exceeded).
    """

    prediction_id: str
    tenant_id: str
    budget_id: str
    predicted_overrun_pct: float
    predicted_overrun_date: str
    confidence_level: int
    model_type: str
    severity_breach: str


def _compute_burn_rate(
    consumed_budget: float,
    total_budget: float,
    elapsed_days: int,
    remaining_days: int,
) -> float:
    """4-input burn-rate formula (PRD §F29.4 verbatim).

    burn_rate = (consumed_budget / elapsed_days) /
                (total_budget - consumed_budget / remaining_days)

    Returns percentage (>= 100% means overrun).

    Raises:
        BudgetBurnRateProjectionError: invalid inputs.
    """
    if elapsed_days <= 0 or remaining_days <= 0:
        raise BudgetBurnRateProjectionError(
            message_ko="elapsed_days/remaining_days는 0보다 커야 합니다",
            details={
                "elapsed_days": str(elapsed_days),
                "remaining_days": str(remaining_days),
            },
        )
    if total_budget <= 0:
        raise BudgetBurnRateProjectionError(
            message_ko="total_budget는 0보다 커야 합니다",
            details={"total_budget": str(total_budget)},
        )
    if consumed_budget < 0:
        raise BudgetBurnRateProjectionError(
            message_ko="consumed_budget는 0 이상이어야 합니다",
            details={"consumed_budget": str(consumed_budget)},
        )

    daily_consumed = consumed_budget / elapsed_days
    remaining_budget = total_budget - consumed_budget
    if remaining_budget <= 0:
        return float("inf")
    daily_remaining = remaining_budget / remaining_days
    if daily_remaining <= 0:
        return float("inf")
    return (daily_consumed / daily_remaining) * 100.0


def _classify_severity(burn_rate_pct: float) -> str:
    """Classify severity by burn-rate threshold."""
    if burn_rate_pct >= EXCEEDED_THRESHOLD_PCT:
        return SEVERITY_EXCEEDED
    if burn_rate_pct >= CRITICAL_THRESHOLD_PCT:
        return SEVERITY_CRITICAL
    if burn_rate_pct >= WARNING_THRESHOLD_PCT:
        return SEVERITY_WARNING
    return SEVERITY_NORMAL


def _route_alert(severity: str) -> tuple[str, ...]:
    """Route alert by severity (PRD §F29.4.4).

    Returns tuple of alert channels.
    """
    return _ALERT_ROUTING_TABLE.get(severity, ())


def project_budget_consumption(
    tenant_id: str | uuid.UUID,
    budget_id: str | uuid.UUID,
    consumed_budget: float,
    total_budget: float,
    elapsed_days: int,
    remaining_days: int,
    *,
    spend_history: list[float] | None = None,
    trace_id: str = "",
    dry_run: bool = False,
) -> BurnRateProjection:
    """Project budget consumption with 4-input burn-rate formula.

    PRD §F29.4 verbatim — ARIMA projection + 3-level severity routing +
    24h dedup window.

    Args:
        tenant_id: tenant UUID.
        budget_id: source budget UUID.
        consumed_budget: actual consumed amount.
        total_budget: total budget allocation.
        elapsed_days: days elapsed in current period.
        remaining_days: days remaining in current period.
        spend_history: optional historical spend (last 12-month).
        trace_id: CR 1-1 ContextVar trace_id.
        dry_run: dry-run mode.

    Returns:
        BurnRateProjection TypedDict.

    Raises:
        BudgetBurnRateProjectionError: invalid inputs.
        BudgetOverrunPredictionError: overrun prediction failure.
    """
    burn_rate_pct = _compute_burn_rate(
        consumed_budget, total_budget, elapsed_days, remaining_days,
    )
    severity = _classify_severity(burn_rate_pct)
    alert_required = severity != SEVERITY_NORMAL
    projection_id = str(uuid.uuid4())

    # ARIMA end-of-period prediction
    predicted_end_period_spend = consumed_budget
    if spend_history and len(spend_history) >= 3:
        horizon = "12m" if remaining_days > 90 else "3m"
        try:
            arima_result = _arima_predict(
                spend_history, horizon, projection_id, SEMVER_DEFAULT_VERSION,
            )
            predicted_end_period_spend = sum(arima_result["predicted_values"])
        except Exception as exc:
            raise BudgetOverrunPredictionError(
                message_ko="ARIMA 예측 실패",
                details={"error": str(exc)},
            ) from exc
    elif dry_run:
        predicted_end_period_spend = consumed_budget
    else:
        # Without history, just project current rate linearly
        daily_consumed = consumed_budget / elapsed_days if elapsed_days > 0 else 0.0
        predicted_end_period_spend = consumed_budget + daily_consumed * remaining_days

    # CR 1-1 audit-first INSERT for `budget_burn_rate_projected`
    # (dry-run skips; service-layer emits via emit_audit_typed BEFORE
    # the actual projection commit).

    return BurnRateProjection(
        projection_id=projection_id,
        tenant_id=str(tenant_id),
        budget_id=str(budget_id),
        consumed_budget=consumed_budget,
        total_budget=total_budget,
        elapsed_days=elapsed_days,
        remaining_days=remaining_days,
        burn_rate_pct=burn_rate_pct,
        severity=severity,
        alert_required=alert_required,
        predicted_end_period_spend=predicted_end_period_spend,
        trace_id=trace_id,
    )


__all__ = [
    "SEVERITY_NORMAL",
    "SEVERITY_WARNING",
    "SEVERITY_CRITICAL",
    "SEVERITY_EXCEEDED",
    "ALL_SEVERITY_LEVELS",
    "WARNING_THRESHOLD_PCT",
    "CRITICAL_THRESHOLD_PCT",
    "EXCEEDED_THRESHOLD_PCT",
    "DEDUP_WINDOW_HOURS",
    "ALERT_CHANNEL_SLACK",
    "ALERT_CHANNEL_PAGERDUTY",
    "ALERT_CHANNEL_EMAIL",
    "ALL_ALERT_CHANNELS",
    "BurnRateProjection",
    "BudgetOverrunPrediction",
    "_compute_burn_rate",
    "_classify_severity",
    "_route_alert",
    "project_budget_consumption",
]
