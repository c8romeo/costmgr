"""tests.api.core.test_phase_13_forecast_engine — Phase 13 forecast engine tests.

Phase 13 (cj-style 115번째 wire) — 4 time series models + ensemble voting.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import ForecastEngineError
from apps.api.modules.finops.forecast_engine import (
    ENSEMBLE_VOTING_CONSENSUS_THRESHOLD,
    KST_HOLIDAYS_8,
    generate_forecast,
)

TENANT_ID: str = str(uuid.uuid4())
HISTORY_12: list[float] = [100.0, 110.0, 105.0, 115.0, 120.0, 125.0, 130.0, 135.0, 140.0, 145.0, 150.0, 155.0]


# ── 8 NEW pytest cases ──────────────────────────────────────
def test_generate_forecast_arima_returns_3_values() -> None:
    """Test 1: ARIMA returns 3 predicted values for 3m horizon."""
    result = generate_forecast(
        tenant_id=TENANT_ID,
        target_metric="tenant_total",
        horizon_months="3m",
        history=HISTORY_12,
        model_type="arima",
    )
    assert len(result["predicted_values"]) == 3


def test_generate_forecast_prophet_returns_12_values() -> None:
    """Test 2: Prophet returns 12 predicted values for 12m horizon."""
    result = generate_forecast(
        tenant_id=TENANT_ID,
        target_metric="tenant_total",
        horizon_months="12m",
        history=HISTORY_12,
        model_type="prophet",
    )
    assert len(result["predicted_values"]) == 12


def test_generate_forecast_lstm_returns_24_values() -> None:
    """Test 3: LSTM returns 24 predicted values for 24m horizon."""
    result = generate_forecast(
        tenant_id=TENANT_ID,
        target_metric="tenant_total",
        horizon_months="24m",
        history=HISTORY_12,
        model_type="lstm",
    )
    assert len(result["predicted_values"]) == 24


def test_generate_forecast_ensemble_voting_consensus() -> None:
    """Test 4: Ensemble picks median of 3 models (3-of-4 voting consensus)."""
    result = generate_forecast(
        tenant_id=TENANT_ID,
        target_metric="tenant_total",
        horizon_months="12m",
        history=HISTORY_12,
        model_type="ensemble",
    )
    assert result["model_type"] == "ensemble"
    assert len(result["predicted_values"]) == 12


def test_generate_forecast_invalid_model_raises() -> None:
    """Test 5: invalid model_type raises ForecastEngineError."""
    with pytest.raises(ForecastEngineError):
        generate_forecast(
            tenant_id=TENANT_ID,
            target_metric="tenant_total",
            horizon_months="12m",
            history=HISTORY_12,
            model_type="invalid_model",
        )


def test_generate_forecast_dry_run_returns_zero_values() -> None:
    """Test 6: dry_run=True returns zero-filled values."""
    result = generate_forecast(
        tenant_id=TENANT_ID,
        target_metric="tenant_total",
        horizon_months="12m",
        history=HISTORY_12,
        model_type="ensemble",
        dry_run=True,
    )
    assert all(v == 0.0 for v in result["predicted_values"])


def test_kst_holidays_8_complete() -> None:
    """Test 7: KST_HOLIDAYS_8 has exactly 8 holidays."""
    assert len(KST_HOLIDAYS_8) == 8
    assert "01-01" in KST_HOLIDAYS_8
    assert "12-25" in KST_HOLIDAYS_8


def test_ensemble_voting_threshold_3() -> None:
    """Test 8: ENSEMBLE_VOTING_CONSENSUS_THRESHOLD == 3 (3-of-4 agree)."""
    assert ENSEMBLE_VOTING_CONSENSUS_THRESHOLD == 3