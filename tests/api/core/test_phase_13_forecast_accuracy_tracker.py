"""tests.api.core.test_phase_13_forecast_accuracy_tracker — Phase 13 accuracy tracker tests.

Phase 13 (cj-style 115번째 wire) — MAE/MAPE/RMSE + retraining trigger.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.modules.finops.forecast_accuracy_tracker import (
    INDUSTRY_BASELINE_MAPE_4_INDUSTRIES,
    MAPE_CONSECUTIVE_PERIODS_THRESHOLD,
    MAPE_RETRAINING_THRESHOLD_PCT,
    RETRAINING_CRON_DEFAULT,
    compute_mae,
    compute_mape,
    compute_rmse,
    track_forecast_accuracy,
)

TENANT_ID: str = str(uuid.uuid4())


# ── 6 NEW pytest cases ──────────────────────────────────────
def test_compute_mae_correct() -> None:
    """Test 1: MAE computation correct."""
    mae = compute_mae([10.0, 20.0, 30.0], [12.0, 18.0, 33.0])
    # |10-12| + |20-18| + |30-33| = 2 + 2 + 3 = 7; 7/3 = 2.3333
    assert abs(mae - 2.3333) < 0.01


def test_compute_mape_correct() -> None:
    """Test 2: MAPE computation correct (percentage)."""
    mape = compute_mape([110.0, 190.0], [100.0, 200.0])
    # (|10/100| + |10/200|) / 2 * 100 = (0.1 + 0.05) / 2 * 100 = 7.5%
    assert abs(mape - 7.5) < 0.01


def test_compute_rmse_correct() -> None:
    """Test 3: RMSE computation correct."""
    rmse = compute_rmse([10.0, 20.0], [12.0, 18.0])
    # sqrt((2^2 + 2^2) / 2) = sqrt(4) = 2.0
    assert abs(rmse - 2.0) < 0.01


def test_compute_mae_empty_raises() -> None:
    """Test 4: compute_mae with empty list raises."""
    with pytest.raises(Exception):
        compute_mae([], [])


def test_industry_baseline_mape_4_industries() -> None:
    """Test 5: INDUSTRY_BASELINE_MAPE_4_INDUSTRIES has 4 industries."""
    assert len(INDUSTRY_BASELINE_MAPE_4_INDUSTRIES) == 4
    assert "manufacturing" in INDUSTRY_BASELINE_MAPE_4_INDUSTRIES


def test_retraining_constants_correct() -> None:
    """Test 6: retraining trigger constants correct."""
    assert MAPE_RETRAINING_THRESHOLD_PCT == 20.0
    assert MAPE_CONSECUTIVE_PERIODS_THRESHOLD == 3
    assert RETRAINING_CRON_DEFAULT == "0 3 * * 0"