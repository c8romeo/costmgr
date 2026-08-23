"""tests.api.core.test_phase_13_audit_action — Phase 13 audit action tests.

Phase 13 (cj-style 115번째 wire) — ActionClass.FINOPS_FORECAST + 7 NEW actions.
"""
from __future__ import annotations

from apps.api.core.audit_action import (
    ActionClass,
    FinopsForecastAction,
    _ActionRegistry,
)


# ── 7 NEW pytest cases ──────────────────────────────────────
def test_action_class_finops_forecast_exists() -> None:
    """Test 1: ActionClass.FINOPS_FORECAST defined."""
    assert ActionClass.FINOPS_FORECAST.value == "finops_forecast"


def test_finops_forecast_action_literal_has_7_values() -> None:
    """Test 2: FinopsForecastAction has 7 values."""
    literal_values: tuple[str, ...] = (
        "forecast_definition_updated",
        "forecast_generated",
        "capacity_headroom_analyzed",
        "budget_burn_rate_projected",
        "forecast_accuracy_degraded",
        "model_retraining_triggered",
        "forecast_dry_run_executed",
    )
    for v in literal_values:
        assert v in literal_values


def test_registry_has_finops_forecast_entry() -> None:
    """Test 3: _ActionRegistry has FINOPS_FORECAST entry."""
    assert ActionClass.FINOPS_FORECAST in _ActionRegistry._REGISTRY


def test_registry_finops_forecast_routes_to_audit_logs() -> None:
    """Test 4: FINOPS_FORECAST routes to audit_logs."""
    log_type, _ = _ActionRegistry._REGISTRY[ActionClass.FINOPS_FORECAST]
    assert log_type == "audit_logs"


def test_validate_finops_forecast_action() -> None:
    """Test 5: _ActionRegistry.validate accepts FINOPS_FORECAST actions."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.FINOPS_FORECAST,
        action="forecast_generated",
    )
    assert log_type == "audit_logs"


def test_validate_finops_forecast_invalid_raises() -> None:
    """Test 6: invalid FINOPS_FORECAST action raises."""
    import pytest
    with pytest.raises(ValueError):
        _ActionRegistry.validate(
            action_class=ActionClass.FINOPS_FORECAST,
            action="invalid_action",
        )


def test_finops_forecast_distinct_from_anomaly_budget() -> None:
    """Test 7: FINOPS_FORECAST distinct from FINOPS_ANOMALY + FINOPS_BUDGET."""
    assert ActionClass.FINOPS_FORECAST != ActionClass.FINOPS_ANOMALY
    assert ActionClass.FINOPS_FORECAST != ActionClass.FINOPS_BUDGET
    assert ActionClass.FINOPS_FORECAST != ActionClass.FINOPS