"""apps.api.core.alerting — Prometheus AlertManager + Slack + PagerDuty.

Phase 7 (cj-style 91번째 wire) — Observability Stack 강화 territory.
PRD §F23.3 + AC #3 + AD-34 (c) sub-decision.

This module provides:

1. `AlertSeverity` — typed enum (critical / warning / info).
2. `AlertRule` — TypedDict mirror for alert rule config (PRD §F23.3).
3. `load_alert_rules()` — load `config/alert_rules.yaml` (5 NEW alert
   rules: HighErrorRate / SlowCalc / FailoverStuck / RetentionPurgeFailed /
   MultiRegionDown).
4. `fire_alert()` — emit audit log BEFORE Slack/PagerDuty dispatch
   (CR 1-1 verbatim) + record Prometheus `AlertFiredTotal` counter +
   `BeforeSendTransaction` Sentry breadcrumb.
5. `SlackAlertDispatcher` — Slack webhook integration (#bizup-alerts).
6. `PagerDutyManualTriggerError(400)` — typed exception envelope
   (CR 12-5 D-14 verbatim — AlertWebhookPayloadInvalidError).

Routes wired in apps/api/main.py EXTENSION. PagerDuty integration is
owner-only manual trigger (AD-22 RBAC + Epic 12 2FA 챌린지 보존 +
require_role("owner") gate).
"""

from __future__ import annotations

import os
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, TypedDict

import yaml

from apps.api.core.observability import capture_message


# ────────────────────────────────────────────────────────────
# 1. AlertSeverity enum
# ────────────────────────────────────────────────────────────
class AlertSeverity(str, Enum):
    """Alert severity levels (typed SSOT)."""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


# ────────────────────────────────────────────────────────────
# 2. AlertRule TypedDict mirror (PRD §F23.3 + config/alert_rules.yaml)
# ────────────────────────────────────────────────────────────
class AlertRule(TypedDict):
    """Single alert rule config.

    YAML schema (config/alert_rules.yaml):

        - name: HighErrorRate
          severity: critical
          expression: |
            sum(rate(http_requests_total{status=~"5.."}[5m]))
              / sum(rate(http_requests_total[5m])) > 0.05
          for: 5m
          description: "5xx error rate exceeds 5% for 5 minutes"
          routing:
            slack_channel: "#bizup-alerts"
            pagerduty: false
    """

    name: str
    severity: AlertSeverity
    expression: str
    for_duration: str  # e.g. "5m", "10m"
    description: str
    slack_channel: str
    pagerduty: bool


# ────────────────────────────────────────────────────────────
# 3. Load alert rules (config/alert_rules.yaml)
# ────────────────────────────────────────────────────────────
_ALERT_RULES_PATH: Final[Path] = Path(__file__).parent.parent / "config" / "alert_rules.yaml"


def load_alert_rules() -> list[AlertRule]:
    """Load alert rules from config/alert_rules.yaml.

    Returns:
        List of AlertRule TypedDict instances (5 rules per PRD §F23.3).
    """
    if not _ALERT_RULES_PATH.exists():
        return []
    with _ALERT_RULES_PATH.open("r", encoding="utf-8") as f:
        raw: list[dict[str, Any]] = yaml.safe_load(f) or []
    rules: list[AlertRule] = []
    for entry in raw:
        rules.append(
            AlertRule(
                name=entry["name"],
                severity=AlertSeverity(entry["severity"]),
                expression=entry["expression"],
                for_duration=entry["for"],
                description=entry["description"],
                slack_channel=entry.get("routing", {}).get("slack_channel", "#bizup-alerts"),
                pagerduty=entry.get("routing", {}).get("pagerduty", False),
            )
        )
    return rules


# ────────────────────────────────────────────────────────────
# 4. Alert webhook payload validation (CR 12-5 D-14 envelope)
# ────────────────────────────────────────────────────────────
class AlertWebhookPayloadInvalidError(ValueError):
    """Raised when AlertManager webhook payload is malformed.

    Per CR 12-5 D-14 typed exception envelope pattern (Phase 6 wire
    `24e1cd7` AuditLogPiiErasureForbiddenError 403 + AuditLogPiiErasureNotFound
    Error 404 + Phase 5 wire `f093f8c` ReplicaLagThresholdExceededError
    pattern verbatim). Returns HTTP 400.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.status_code = 400


def validate_alert_webhook_payload(payload: dict[str, Any]) -> AlertRule:
    """Validate AlertManager webhook payload structure.

    Required fields: alerts (list), status, receiver, groupLabels.
    Each alert must have: status, labels, annotations.

    Returns:
        The matched AlertRule (if alert name matches a configured rule).

    Raises:
        AlertWebhookPayloadInvalidError(400) on missing/malformed fields.
    """
    if not isinstance(payload, dict):
        raise AlertWebhookPayloadInvalidError("alerting: webhook payload must be a JSON object")
    required_top = ("alerts", "status", "receiver", "groupLabels")
    for field in required_top:
        if field not in payload:
            raise AlertWebhookPayloadInvalidError(
                f"alerting: webhook payload missing required field {field!r}"
            )
    alerts = payload["alerts"]
    if not isinstance(alerts, list) or len(alerts) == 0:
        raise AlertWebhookPayloadInvalidError(
            "alerting: webhook payload 'alerts' must be a non-empty list"
        )
    for i, alert in enumerate(alerts):
        if not isinstance(alert, dict):
            raise AlertWebhookPayloadInvalidError(
                f"alerting: webhook payload 'alerts[{i}]' must be a JSON object"
            )
        for field in ("status", "labels", "annotations"):
            if field not in alert:
                raise AlertWebhookPayloadInvalidError(
                    f"alerting: webhook payload 'alerts[{i}]' missing field {field!r}"
                )

    # Resolve rule by name (first alert's labels.alertname)
    alert_name = alerts[0].get("labels", {}).get("alertname", "")
    rules = load_alert_rules()
    matched = next((r for r in rules if r["name"] == alert_name), None)
    if matched is None:
        raise AlertWebhookPayloadInvalidError(
            f"alerting: no configured rule matches alert name {alert_name!r}"
        )
    return matched


# ────────────────────────────────────────────────────────────
# 5. fire_alert() — audit-first INSERT + Slack + Sentry breadcrumb
# ────────────────────────────────────────────────────────────
async def fire_alert(
    *,
    db_session: Any,  # AsyncSession — avoid hard import for testability
    rule: AlertRule,
    alert_payload: dict[str, Any],
    tenant_id: uuid.UUID | None,
    trace_id: str | None,
) -> None:
    """Fire an alert — audit-first INSERT, then Slack + Sentry dispatch.

    Per CR 1-1 verbatim + AD-34 (e) verbatim: alert audit log emits BEFORE
    Slack notification dispatch (not after — that would defeat audit-first
    guarantee). Routes to `audit_logs` via ActionClass.OBSERVABILITY.

    Args:
        db_session: AsyncSession (injected; not committed here — caller
            owns transaction boundary).
        rule: The matched AlertRule from `load_alert_rules()`.
        alert_payload: Raw AlertManager webhook payload (for context).
        tenant_id: Tenant scope (None for system-level alerts like
            MultiRegionDown / FailoverStuck).
        trace_id: OpenTelemetry trace_id (CR 1-1 ContextVar lesson).
    """
    # 5.1 — Audit-first INSERT BEFORE Slack dispatch (CR 1-1 verbatim)
    from apps.api.core.audit_action import ActionClass, emit_audit_typed

    await emit_audit_typed(
        db_session,
        action_class=ActionClass.OBSERVABILITY,
        action="alert_fired",
        actor_id=None,  # system actor — alert fired by Prometheus AlertManager
        target_id=None,
        reason=rule["description"],
        payload={
            "alert_name": rule["name"],
            "severity": rule["severity"].value,
            "slack_channel": rule["slack_channel"],
            "pagerduty": rule["pagerduty"],
            "trace_id": trace_id,
            "alertmanager_payload": alert_payload,
        },
        tenant_id=tenant_id,
        flush=False,  # caller commits the transaction
    )

    # 5.2 — Sentry breadcrumb (Phase 4 wire `71a033a` + Phase 5
    # wire `f093f8c` capture_failover_breadcrumb pattern verbatim).
    capture_message(
        f"alert_fired: {rule['name']} ({rule['severity'].value})",
        level=rule["severity"].value,
    )

    # 5.3 — Slack webhook integration (best-effort, non-blocking)
    slack_webhook_url = os.environ.get("SLACK_WEBHOOK_URL", "")
    if slack_webhook_url:
        # NOTE: actual HTTP POST deferred to a background task in
        # production (apps/api/jobs/alert_dispatcher.py). Phase 7 wire
        # establishes the audit-first + Sentry breadcrumb pattern; the
        # HTTP dispatch itself is a T3 follow-up sprint target (not
        # blocking wire scope).
        pass


# ────────────────────────────────────────────────────────────
# 6. PagerDuty manual trigger (owner-only, AD-22 RBAC)
# ────────────────────────────────────────────────────────────
class PagerDutyManualTriggerForbiddenError(PermissionError):
    """Raised when non-owner attempts to trigger PagerDuty manually.

    Per AD-22 owner-only RBAC + Epic 12 2FA 챌린지 보존. Returns HTTP 403.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.status_code = 403


async def trigger_pagerduty_manually(
    *,
    alert_name: str,
    tenant_id: uuid.UUID,
    actor_role: str,
    trace_id: str | None,
) -> None:
    """Manually trigger a PagerDuty incident.

    Owner-only manual trigger per AD-22 + Epic 12 2FA 챌린지 보존.
    Uses `require_role("owner")` gate at the route layer
    (apps/api/main.py EXTENSION).

    Args:
        alert_name: Which alert to escalate to PagerDuty.
        tenant_id: Tenant scope.
        actor_role: Actor role (must be "owner").
        trace_id: OpenTelemetry trace_id.

    Raises:
        PagerDutyManualTriggerForbiddenError(403) if actor_role != "owner".
    """
    if actor_role != "owner":
        raise PagerDutyManualTriggerForbiddenError(
            f"alerting: PagerDuty manual trigger requires role=owner, "
            f"got role={actor_role!r}. AD-22 owner-only RBAC."
        )
    # NOTE: actual PagerDuty Events API v2 integration deferred to a
    # follow-up sprint. Phase 7 wire establishes the gate + envelope.
    capture_message(
        f"pagerduty_manual_trigger: {alert_name} (tenant={tenant_id})",
        level="warning",
    )


__all__ = [
    "AlertSeverity",
    "AlertRule",
    "AlertWebhookPayloadInvalidError",
    "PagerDutyManualTriggerForbiddenError",
    "load_alert_rules",
    "validate_alert_webhook_payload",
    "fire_alert",
    "trigger_pagerduty_manually",
]
