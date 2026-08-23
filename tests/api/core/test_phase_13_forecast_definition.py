"""tests.api.core.test_phase_13_forecast_definition — Phase 13 forecast definition tests.

Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
Planning territory (PRD §F29.1).

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import (
    ForecastDefinitionInvalidError,
    ForecastScopeInvalidError,
)
from apps.api.modules.finops.forecast_definition import (
    ALL_HORIZON_MONTHS,
    ALL_MODEL_TYPES,
    ALL_TARGET_METRICS,
    FORECAST_DEFAULTS,
    ForecastDefinition,
    define_forecast,
    parse_forecast_definition,
)

TENANT_ID: str = str(uuid.uuid4())


# ── 6 NEW pytest cases ──────────────────────────────────────
def test_define_forecast_default_returns_valid_definition() -> None:
    """Test 1: define_forecast with defaults returns valid definition."""
    definition = define_forecast(tenant_id=TENANT_ID)
    assert isinstance(definition, dict)
    assert definition["tenant_id"] == TENANT_ID
    assert definition["target_metric"] == "tenant_total"
    assert definition["horizon_months"] == FORECAST_DEFAULTS.HORIZON_MONTHS
    assert definition["model_type"] == FORECAST_DEFAULTS.MODEL_TYPE


def test_parse_forecast_definition_validates_required_fields() -> None:
    """Test 2: parse_forecast_definition enforces 8 required fields."""
    with pytest.raises(ForecastDefinitionInvalidError):
        parse_forecast_definition(TENANT_ID, {})


def test_parse_forecast_definition_validates_target_metric() -> None:
    """Test 3: parse_forecast_definition enforces target_metric enum."""
    with pytest.raises(ForecastScopeInvalidError):
        parse_forecast_definition(
            TENANT_ID,
            {
                "target_metric": "invalid_metric",
                "dimension_value": "*",
                "horizon_months": "12m",
                "model_type": "ensemble",
                "confidence_level": 95,
                "retraining_cron": "0 3 * * 0",
                "status": "active",
            },
        )


def test_parse_forecast_definition_validates_horizon_months() -> None:
    """Test 4: parse_forecast_definition enforces horizon_months enum."""
    with pytest.raises(ForecastDefinitionInvalidError):
        parse_forecast_definition(
            TENANT_ID,
            {
                "target_metric": "tenant_total",
                "dimension_value": "*",
                "horizon_months": "1m",  # invalid
                "model_type": "ensemble",
                "confidence_level": 95,
                "retraining_cron": "0 3 * * 0",
                "status": "active",
            },
        )


def test_all_horizon_months_exhaustive() -> None:
    """Test 5: ALL_HORIZON_MONTHS has exactly 4 options."""
    assert len(ALL_HORIZON_MONTHS) == 4
    assert "3m" in ALL_HORIZON_MONTHS
    assert "24m" in ALL_HORIZON_MONTHS


def test_all_target_metrics_exhaustive() -> None:
    """Test 6: ALL_TARGET_METRICS has exactly 5 options."""
    assert len(ALL_TARGET_METRICS) == 5
    assert "tenant_total" in ALL_TARGET_METRICS
    assert ALL_MODEL_TYPES == ("arima", "prophet", "lstm", "ensemble")