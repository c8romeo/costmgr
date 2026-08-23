# tests/api/core/test_phase_12_forecast_accuracy.py —
# Phase 12 T6.5 (cj-style 111번째 wire) — Forecast accuracy tests.
# 10 cases per cj-style Phase 11 Chargeback engine pattern verbatim mirror.
import pytest

from apps.api.core.errors import (
    ForecastAccuracyDegradedError,
    ForecastAccuracyInvalidError,
)
from apps.api.modules.finops.forecast_accuracy import (
    ACCURACY_STATUS_ACCEPTABLE,
    ACCURACY_STATUS_DEGRADED,
    ACCURACY_STATUS_HIGH,
    ALL_ACCURACY_STATUSES,
    HIGH_ACCURACY_MAPE_THRESHOLD,
    RETRAIN_TRIGGER_MAPE_THRESHOLD,
    compute_mae,
    compute_mape,
    compute_rmse,
    evaluate_forecast_accuracy,
)


_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def test_compute_mae_basic():
    """MAE = mean(|actual - predicted|)."""
    predicted = [100.0, 200.0, 300.0]
    actual = [110.0, 190.0, 330.0]
    assert abs(compute_mae(predicted, actual) - (10.0 + 10.0 + 30.0) / 3) < 0.001


def test_compute_mape_basic():
    """MAPE = mean(|actual - predicted| / actual)."""
    predicted = [90.0, 200.0, 270.0]
    actual = [100.0, 200.0, 300.0]
    expected = (10.0 / 100.0 + 0.0 + 30.0 / 300.0) / 3
    assert abs(compute_mape(predicted, actual) - expected) < 0.001


def test_compute_rmse_basic():
    """RMSE = sqrt(mean((actual - predicted)^2))."""
    predicted = [100.0, 200.0, 300.0]
    actual = [110.0, 190.0, 330.0]
    expected_diff = (10.0 ** 2 + 10.0 ** 2 + 30.0 ** 2) / 3
    expected = expected_diff ** 0.5
    assert abs(compute_rmse(predicted, actual) - expected) < 0.001


def test_compute_mae_length_mismatch_raises():
    with pytest.raises(ForecastAccuracyInvalidError):
        compute_mae([100.0], [100.0, 200.0])


def test_compute_mape_zero_division_raises():
    with pytest.raises(ForecastAccuracyInvalidError):
        compute_mape([100.0, 200.0], [0.0, 200.0])


def test_evaluate_high_accuracy():
    """MAPE < 10% produces high accuracy status."""
    result = evaluate_forecast_accuracy(
        _TENANT_ID, "2026-08", "moving_avg",
        [100.0, 200.0, 300.0], [105.0, 195.0, 305.0],
    )
    assert result["status"] == ACCURACY_STATUS_HIGH
    assert result["retraining_recommended"] is False


def test_evaluate_acceptable_accuracy():
    """MAPE 10-20% produces acceptable accuracy status."""
    result = evaluate_forecast_accuracy(
        _TENANT_ID, "2026-08", "moving_avg",
        [100.0, 200.0, 300.0], [85.0, 220.0, 350.0],
    )
    # mape = (15/100 + 20/200 + 50/300) / 3 ≈ 0.194
    assert result["status"] == ACCURACY_STATUS_ACCEPTABLE
    assert result["retraining_recommended"] is False


def test_evaluate_degraded_triggers_retraining():
    """MAPE > 20% produces degraded status + retraining_recommended True."""
    result = evaluate_forecast_accuracy(
        _TENANT_ID, "2026-08", "moving_avg",
        [100.0, 200.0, 300.0], [50.0, 300.0, 500.0],
    )
    assert result["status"] == ACCURACY_STATUS_DEGRADED
    assert result["retraining_recommended"] is True


def test_evaluate_insufficient_periods_raises():
    """evaluate_forecast_accuracy requires minimum 3 periods."""
    with pytest.raises(ForecastAccuracyInvalidError):
        evaluate_forecast_accuracy(
            _TENANT_ID, "2026-08", "moving_avg",
            [100.0, 200.0], [110.0, 190.0],
        )


def test_accuracy_thresholds_and_statuses_defined():
    """3 status levels + 2 thresholds defined."""
    assert len(ALL_ACCURACY_STATUSES) == 3
    assert HIGH_ACCURACY_MAPE_THRESHOLD == 0.10
    assert RETRAIN_TRIGGER_MAPE_THRESHOLD == 0.20
    assert ACCURACY_STATUS_HIGH in ALL_ACCURACY_STATUSES
    assert ACCURACY_STATUS_ACCEPTABLE in ALL_ACCURACY_STATUSES
    assert ACCURACY_STATUS_DEGRADED in ALL_ACCURACY_STATUSES