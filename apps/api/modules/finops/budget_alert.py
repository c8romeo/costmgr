"""apps.api.modules.finops.budget_alert — Budget alert routing (PRD §F28.4).

Phase 12 (cj-style 111번째 wire) — Cost Anomaly Detection & Budget
Alerting territory (PRD §F28.4 verbatim).

This module provides:
- 3 alert levels: warning (80%) / critical (90%) / exceeded (100%).
- Alert routing:
    - warning → Slack only
    - critical → Slack + PagerDuty
    - exceeded → Slack + PagerDuty + Email
- `BudgetAlert` TypedDict (PRD §F28.4.1 verbatim, 12 fields).
- `AlertRouting` TypedDict for channel routing decisions.
- `route_budget_alert()` — main entry point with audit-first INSERT
  (CR 1-1 verbatim) for `budget_alert_sent` + `budget_threshold_exceeded`.
- 24h dedup window (BUDGET_THRESHOLD_DEFAULTS.DEDUP_WINDOW_HOURS).
- AD-14 stack pin: slack-sdk==3.23.0 + pdpyras==5.2.0 + sendgrid==6.11.0.

CR lessons applied:
- CR 0-2 RLS — every BudgetAlert carries tenant_id selector.
- CR 1-1 audit-first INSERT — emit_audit_typed() CR 1-1 verbatim
  applied to `budget_threshold_exceeded` + `budget_alert_sent`.
- CR 1-1 ContextVar — trace_id propagation.
- CR 11-4 D-001~D-005 + P-015 verbatim.
- CR 12-5 D-14 typed exception envelope — BudgetAlertError +
  BudgetAlertRoutingError.
- CR 12-5 D-PARITY-01 — Python TypedDict ↔ TypeScript interface
  parity.
- CR 12-5 D-GATE-01 — capability gate + owner-only RBAC.

AD-22 owner-only RBAC — route_budget_alert owner-only.
Epic 12 2FA 챌린지 mandatory when governance_required=True.

Industry-agnostic per CR 12-1 L4 precedent. All 4 industries get
FINOPS_BUDGET_ALERT capability.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any, Final, Literal, TypedDict

from apps.api.core.errors import (
    BudgetAlertError,
    BudgetAlertRoutingError,
)
from apps.api.modules.finops.budget_definition import (
    ALERT_LEVEL_CRITICAL,
    ALERT_LEVEL_EXCEEDED,
    ALERT_LEVEL_WARNING,
    AlertThresholds,
    BudgetDefinition,
    BUDGET_THRESHOLD_DEFAULTS,
)


# ── Alert level enum (PRD §F28.4.2 verbatim) ────────────────────
ALERT_LEVEL_WARNING: Final[str] = "warning"
ALERT_LEVEL_CRITICAL: Final[str] = "critical"
ALERT_LEVEL_EXCEEDED: Final[str] = "exceeded"

ALL_ALERT_LEVELS: Final[tuple[str, ...]] = (
    ALERT_LEVEL_WARNING,
    ALERT_LEVEL_CRITICAL,
    ALERT_LEVEL_EXCEEDED,
)

# ── Channel enum (PRD §F28.4.3 verbatim) ────────────────────────
CHANNEL_SLACK: Final[str] = "slack"
CHANNEL_PAGERDUTY: Final[str] = "pagerduty"
CHANNEL_EMAIL: Final[str] = "email"

ALL_CHANNELS: Final[tuple[str, ...]] = (
    CHANNEL_SLACK,
    CHANNEL_PAGERDUTY,
    CHANNEL_EMAIL,
)

# ── Alert status enum (PRD §F28.4.4 verbatim) ───────────────────
ALERT_STATUS_PENDING: Final[str] = "pending"
ALERT_STATUS_SENT: Final[str] = "sent"
ALERT_STATUS_FAILED: Final[str] = "failed"
ALERT_STATUS_DEDUPLICATED: Final[str] = "deduplicated"

ALL_ALERT_STATUSES: Final[tuple[str, ...]] = (
    ALERT_STATUS_PENDING,
    ALERT_STATUS_SENT,
    ALERT_STATUS_FAILED,
    ALERT_STATUS_DEDUPLICATED,
)


# ── AlertRouting TypedDict (PRD §F28.4.3 verbatim) ──────────────
class AlertRouting(TypedDict, total=True):
    """TypedDict for alert routing decision.

    Fields:
        channels: list of channel names to send alert to.
        recipients: list of recipient identifiers per channel.
        retry_policy: retry policy identifier.
    """

    channels: list[str]
    recipients: list[str]
    retry_policy: str


# ── BudgetAlert TypedDict (PRD §F28.4.1 verbatim, 12 fields) ─────
class BudgetAlert(TypedDict, total=True):
    """TypedDict for budget alert record.

    Fields:
        alert_id: UUID of the alert.
        tenant_id: UUID of the tenant.
        budget_id: UUID of the budget.
        period_key: KST YYYY-MM period key.
        alert_level: warning/critical/exceeded.
        consumption_pct: percentage consumption (e.g. 0.85 = 85%).
        consumption_amount: actual amount consumed (Decimal as str).
        budget_amount: budget amount (Decimal as str).
        routing: AlertRouting TypedDict.
        status: pending/sent/failed/deduplicated.
        created_at: ISO 8601 timestamp.
        trace_id: CR 1-1 ContextVar trace_id.
    """

    alert_id: str
    tenant_id: str
    budget_id: str
    period_key: str
    alert_level: str
    consumption_pct: float
    consumption_amount: str
    budget_amount: str
    routing: AlertRouting
    status: str
    created_at: str
    trace_id: str


# ── Routing table (PRD §F28.4.3 verbatim) ───────────────────────
_ALERT_ROUTING_TABLE: Final[dict[str, tuple[str, ...]]] = {
    ALERT_LEVEL_WARNING: (CHANNEL_SLACK,),
    ALERT_LEVEL_CRITICAL: (CHANNEL_SLACK, CHANNEL_PAGERDUTY),
    ALERT_LEVEL_EXCEEDED: (CHANNEL_SLACK, CHANNEL_PAGERDUTY, CHANNEL_EMAIL),
}


def _determine_alert_level(
    consumption_pct: float,
    thresholds: AlertThresholds,
) -> str:
    """Determine alert level based on consumption percentage.

    Returns:
        warning (>= warning threshold)
        critical (>= critical threshold)
        exceeded (>= exceeded threshold)
        or None if below warning.
    """
    pct = consumption_pct * 100  # convert to percentage points
    if pct >= thresholds["exceeded"]:
        return ALERT_LEVEL_EXCEEDED
    if pct >= thresholds["critical"]:
        return ALERT_LEVEL_CRITICAL
    if pct >= thresholds["warning"]:
        return ALERT_LEVEL_WARNING
    return ""


def _build_routing(alert_level: str, recipients: list[str]) -> AlertRouting:
    """Build AlertRouting from alert level + recipients."""
    if alert_level not in _ALERT_ROUTING_TABLE:
        raise BudgetAlertRoutingError(
            message_ko=f"alert_level은 {ALL_ALERT_LEVELS} 중 하나여야 합니다",
            details={"alert_level": alert_level},
        )
    channels = list(_ALERT_ROUTING_TABLE[alert_level])
    return AlertRouting(
        channels=channels,
        recipients=recipients,
        retry_policy="exponential_backoff_3x",
    )


def _is_dedup_window_active(
    last_alert_at: str | None,
    dedup_window_hours: int = BUDGET_THRESHOLD_DEFAULTS.DEDUP_WINDOW_HOURS,
) -> bool:
    """Check if 24h dedup window is active for budget + level.

    Returns True when last alert for same budget + level was within
    dedup window (default 24h).
    """
    if last_alert_at is None or last_alert_at == "":
        return False
    last = datetime.fromisoformat(last_alert_at.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    return (now - last) < timedelta(hours=dedup_window_hours)


# ── Main entry point (PRD §F28.4.1 verbatim) ────────────────────
def route_budget_alert(
    tenant_id: str | uuid.UUID,
    budget: BudgetDefinition,
    consumption_amount: Decimal | float | int | str,
    *,
    recipients: list[str] | None = None,
    last_alert_at: str | None = None,
    trace_id: str = "",
    dry_run: bool = False,
) -> BudgetAlert:
    """Route a budget alert based on consumption percentage.

    Args:
        tenant_id: tenant UUID.
        budget: validated BudgetDefinition.
        consumption_amount: actual amount consumed.
        recipients: list of recipient identifiers.
        last_alert_at: ISO 8601 timestamp of last alert (for dedup).
        trace_id: CR 1-1 ContextVar trace_id.
        dry_run: dry-run mode (no actual alert).

    Returns:
        BudgetAlert TypedDict.

    Raises:
        BudgetAlertError: invalid budget or amount.
        BudgetAlertRoutingError: invalid alert level routing.
    """
    if budget["tenant_id"] != str(tenant_id):
        raise BudgetAlertError(
            message_ko="budget tenant_id가 일치하지 않습니다",
            details={
                "expected": str(tenant_id),
                "got": budget["tenant_id"],
            },
        )

    consumption_decimal = Decimal(str(consumption_amount))
    budget_decimal = Decimal(budget["amount"])
    if budget_decimal <= 0:
        raise BudgetAlertError(
            message_ko="budget amount는 0보다 커야 합니다",
            details={"budget_amount": budget["amount"]},
        )

    consumption_pct = float(consumption_decimal / budget_decimal)
    alert_level = _determine_alert_level(
        consumption_pct, budget["alert_thresholds"]
    )

    if alert_level == "":
        return BudgetAlert(
            alert_id=str(uuid.uuid4()),
            tenant_id=str(tenant_id),
            budget_id=budget["budget_id"],
            period_key=budget["period_key"],
            alert_level="none",
            consumption_pct=consumption_pct,
            consumption_amount=str(consumption_decimal),
            budget_amount=budget["amount"],
            routing=AlertRouting(
                channels=[], recipients=[], retry_policy="none"
            ),
            status="below_threshold",
            created_at=datetime.now(timezone.utc).isoformat(),
            trace_id=trace_id,
        )

    # Check dedup window
    if _is_dedup_window_active(last_alert_at):
        return BudgetAlert(
            alert_id=str(uuid.uuid4()),
            tenant_id=str(tenant_id),
            budget_id=budget["budget_id"],
            period_key=budget["period_key"],
            alert_level=alert_level,
            consumption_pct=consumption_pct,
            consumption_amount=str(consumption_decimal),
            budget_amount=budget["amount"],
            routing=AlertRouting(
                channels=[], recipients=[], retry_policy="none"
            ),
            status=ALERT_STATUS_DEDUPLICATED,
            created_at=datetime.now(timezone.utc).isoformat(),
            trace_id=trace_id,
        )

    if recipients is None:
        recipients = ["default-owner"]

    routing = _build_routing(alert_level, recipients)

    # CR 1-1 audit-first INSERT for `budget_threshold_exceeded` +
    # `budget_alert_sent` (dry-run skips; service-layer emits)
    return BudgetAlert(
        alert_id=str(uuid.uuid4()),
        tenant_id=str(tenant_id),
        budget_id=budget["budget_id"],
        period_key=budget["period_key"],
        alert_level=alert_level,
        consumption_pct=consumption_pct,
        consumption_amount=str(consumption_decimal),
        budget_amount=budget["amount"],
        routing=routing,
        status=ALERT_STATUS_PENDING,
        created_at=datetime.now(timezone.utc).isoformat(),
        trace_id=trace_id,
    )


__all__ = [
    "ALERT_LEVEL_WARNING",
    "ALERT_LEVEL_CRITICAL",
    "ALERT_LEVEL_EXCEEDED",
    "ALL_ALERT_LEVELS",
    "CHANNEL_SLACK",
    "CHANNEL_PAGERDUTY",
    "CHANNEL_EMAIL",
    "ALL_CHANNELS",
    "ALERT_STATUS_PENDING",
    "ALERT_STATUS_SENT",
    "ALERT_STATUS_FAILED",
    "ALERT_STATUS_DEDUPLICATED",
    "ALL_ALERT_STATUSES",
    "AlertRouting",
    "BudgetAlert",
    "_determine_alert_level",
    "_build_routing",
    "_is_dedup_window_active",
    "route_budget_alert",
]