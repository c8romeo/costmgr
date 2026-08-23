"""tests/api/core/test_phase_7_alerting.py — Phase 7 alerting module tests.

Phase 7 (cj-style 91번째 wire) — T7a backend pytest tests.
PRD §F23.3 + AC #3 + AD-34 (c) verbatim.

Drift detector enforces:
1. load_alert_rules loads 5 NEW alert rules from config/alert_rules.yaml.
2. validate_alert_webhook_payload raises AlertWebhookPayloadInvalidError(400)
   on missing fields.
3. validate_alert_webhook_payload raises AlertWebhookPayloadInvalidError(400)
   on unknown alert name.
4. PagerDutyManualTriggerForbiddenError(403) raised on non-owner role.
"""
from __future__ import annotations

import pytest

from apps.api.core.alerting import (
    AlertSeverity,
    AlertRule,
    AlertWebhookPayloadInvalidError,
    PagerDutyManualTriggerForbiddenError,
    load_alert_rules,
    validate_alert_webhook_payload,
    trigger_pagerduty_manually,
)


def test_load_alert_rules_returns_5_rules() -> None:
    """load_alert_rules returns 5 NEW alert rules per PRD §F23.3."""
    rules = load_alert_rules()
    assert len(rules) == 5
    names = {r["name"] for r in rules}
    assert "HighErrorRate" in names
    assert "SlowCalc" in names
    assert "FailoverStuck" in names
    assert "RetentionPurgeFailed" in names
    assert "MultiRegionDown" in names


def test_validate_payload_missing_alerts_field() -> None:
    """validate_alert_webhook_payload raises 400 on missing 'alerts' field."""
    payload: dict = {"status": "firing", "receiver": "bizup", "groupLabels": {}}
    with pytest.raises(AlertWebhookPayloadInvalidError, match="alerts"):
        validate_alert_webhook_payload(payload)


def test_validate_payload_unknown_alert_name() -> None:
    """validate_alert_webhook_payload raises 400 on unknown alert name."""
    payload = {
        "status": "firing",
        "receiver": "bizup",
        "groupLabels": {"alertname": "NotARule"},
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "NotARule"},
                "annotations": {"summary": "test"},
            }
        ],
    }
    with pytest.raises(AlertWebhookPayloadInvalidError, match="no configured rule"):
        validate_alert_webhook_payload(payload)


@pytest.mark.asyncio
async def test_pagerduty_forbidden_for_non_owner() -> None:
    """trigger_pagerduty_manually raises 403 for non-owner role."""
    import uuid

    with pytest.raises(PagerDutyManualTriggerForbiddenError, match="owner"):
        await trigger_pagerduty_manually(
            alert_name="HighErrorRate",
            tenant_id=uuid.uuid4(),
            actor_role="admin",  # not owner
            trace_id=None,
        )
