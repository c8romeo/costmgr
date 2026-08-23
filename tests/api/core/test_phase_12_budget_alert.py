# tests/api/core/test_phase_12_budget_alert.py —
# Phase 12 T6.5 (cj-style 111번째 wire) — Budget alert routing tests.
# 10 cases per cj-style Phase 11 Chargeback engine pattern verbatim mirror.
from datetime import datetime, timezone, timedelta

import pytest

from apps.api.core.errors import BudgetAlertError, BudgetAmountInvalidError
from apps.api.modules.finops.budget_alert import (
    ALERT_LEVEL_CRITICAL,
    ALERT_LEVEL_EXCEEDED,
    ALERT_LEVEL_WARNING,
    ALL_CHANNELS,
    ALL_ALERT_LEVELS,
    ALERT_STATUS_DEDUPLICATED,
    ALERT_STATUS_PENDING,
    CHANNEL_EMAIL,
    CHANNEL_PAGERDUTY,
    CHANNEL_SLACK,
    route_budget_alert,
)
from apps.api.modules.finops.budget_definition import (
    BUDGET_SCOPE_TENANT,
    define_budget,
)


_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _make_budget(amount="1000000.00"):
    return define_budget(
        _TENANT_ID, "2026-08", BUDGET_SCOPE_TENANT, "TENANT", amount
    )


def test_warning_alert_routes_to_slack_only():
    """Warning (80%) routes only to Slack."""
    budget = _make_budget()
    alert = route_budget_alert(_TENANT_ID, budget, 850000.00)
    assert alert["alert_level"] == ALERT_LEVEL_WARNING
    assert alert["routing"]["channels"] == [CHANNEL_SLACK]


def test_critical_alert_routes_to_slack_and_pagerduty():
    """Critical (90%) routes to Slack + PagerDuty."""
    budget = _make_budget()
    alert = route_budget_alert(_TENANT_ID, budget, 950000.00)
    assert alert["alert_level"] == ALERT_LEVEL_CRITICAL
    assert CHANNEL_SLACK in alert["routing"]["channels"]
    assert CHANNEL_PAGERDUTY in alert["routing"]["channels"]
    assert CHANNEL_EMAIL not in alert["routing"]["channels"]


def test_exceeded_alert_routes_to_all_channels():
    """Exceeded (100%) routes to Slack + PagerDuty + Email."""
    budget = _make_budget()
    alert = route_budget_alert(_TENANT_ID, budget, 1100000.00)
    assert alert["alert_level"] == ALERT_LEVEL_EXCEEDED
    assert set(alert["routing"]["channels"]) == {
        CHANNEL_SLACK,
        CHANNEL_PAGERDUTY,
        CHANNEL_EMAIL,
    }


def test_below_warning_threshold_no_alert():
    """Consumption below warning threshold produces no alert."""
    budget = _make_budget()
    alert = route_budget_alert(_TENANT_ID, budget, 100000.00)
    assert alert["alert_level"] == "none"
    assert alert["status"] == "below_threshold"
    assert alert["routing"]["channels"] == []


def test_dedup_window_active_within_24h():
    """Within 24h dedup window returns deduplicated status."""
    budget = _make_budget()
    last_alert = (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat()
    alert = route_budget_alert(
        _TENANT_ID, budget, 950000.00, last_alert_at=last_alert
    )
    assert alert["status"] == ALERT_STATUS_DEDUPLICATED
    assert alert["alert_level"] == ALERT_LEVEL_CRITICAL


def test_dedup_window_expired_after_24h():
    """After 24h dedup window expires, alert is dispatched."""
    budget = _make_budget()
    last_alert = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
    alert = route_budget_alert(
        _TENANT_ID, budget, 950000.00, last_alert_at=last_alert
    )
    assert alert["status"] == ALERT_STATUS_PENDING


def test_tenant_id_mismatch_raises():
    budget = _make_budget()
    with pytest.raises(BudgetAlertError):
        route_budget_alert(
            "22222222-2222-2222-2222-222222222222", budget, 950000.00
        )


def test_invalid_amount_zero_raises():
    with pytest.raises(BudgetAmountInvalidError):
        _make_budget(amount="0")


def test_all_alert_levels_and_channels_defined():
    """3 alert levels + 3 channels defined."""
    assert len(ALL_ALERT_LEVELS) == 3
    assert len(ALL_CHANNELS) == 3
    assert ALERT_LEVEL_WARNING in ALL_ALERT_LEVELS
    assert ALERT_LEVEL_CRITICAL in ALL_ALERT_LEVELS
    assert ALERT_LEVEL_EXCEEDED in ALL_ALERT_LEVELS
    assert CHANNEL_SLACK in ALL_CHANNELS
    assert CHANNEL_PAGERDUTY in ALL_CHANNELS
    assert CHANNEL_EMAIL in ALL_CHANNELS


def test_consumption_pct_calculated_correctly():
    """consumption_pct = consumption / budget."""
    budget = _make_budget(amount="1000000.00")
    alert = route_budget_alert(_TENANT_ID, budget, 850000.00)
    assert abs(alert["consumption_pct"] - 0.85) < 0.001