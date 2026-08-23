# tests/api/core/test_phase_10_slo_burn_rate_evaluator.py —
# Phase 10 T7 (cj-style 103번째 wire) — Multi-window burn-rate
# evaluation tests. 6 cases.
#
# Verbatim Google SRE Workbook multi-window burn-rate evaluation:
#   fast_burn: 1h window, 14.4x threshold, 5min alert window
#   slow_burn: 6h window, 6x threshold, 30min alert window
#   exhaustion: 24h window, 3x threshold, 2h alert window
#   long_window: 3d window, 1x threshold, 6h alert window
import pytest

from apps.api.modules.slo.slo_burn_rate_evaluator import (
    BURN_RATE_THRESHOLDS,
    SloBurnRateEvaluation,
    SloViolationDetectedError,
    compute_burn_rate,
    evaluate_all_windows,
    evaluate_single_window,
)


def _sample(error_rate: float = 0.01):
    return {
        "fast_burn": {"error_count": int(error_rate * 3600), "total_count": 3600},
        "slow_burn": {"error_count": int(error_rate * 21600), "total_count": 21600},
        "exhaustion": {"error_count": int(error_rate * 86400), "total_count": 86400},
        "long_window": {"error_count": int(error_rate * 259200), "total_count": 259200},
    }


def test_compute_burn_rate_basic_formula():
    # objective 99.9 -> error budget 0.1%
    # error_rate 0.001 = 0.1% -> burn_rate = 0.001 / (1 - 0.999) = 1.0
    assert compute_burn_rate(error_rate=0.001, objective=99.9) == pytest.approx(1.0)


def test_evaluate_single_window_fast_burn_breach():
    samples = _sample(error_rate=0.02)  # 2% errors
    result = evaluate_single_window(
        window="fast_burn",
        samples=samples["fast_burn"],
        objective=99.9,
        slo_id="slo:cost-engine:p99-latency",
    )
    assert result["burn_rate"] >= BURN_RATE_THRESHOLDS["fast_burn"]["multiplier"]
    assert result["breach"] is True


def test_evaluate_single_window_long_window_no_breach():
    samples = _sample(error_rate=0.0005)  # 0.05% - well within 99.95%
    result = evaluate_single_window(
        window="long_window",
        samples=samples["long_window"],
        objective=99.9,
        slo_id="slo:cost-engine:p99-latency",
    )
    assert result["breach"] is False


def test_evaluate_all_windows_composite_breach_raises():
    samples = _sample(error_rate=0.05)  # 5% - extreme breach across all windows
    with pytest.raises(SloViolationDetectedError) as excinfo:
        evaluate_all_windows(
            samples=samples,
            objective=99.9,
            slo_id="slo:cost-engine:p99-latency",
        )
    assert excinfo.value.status_code == 422


def test_evaluate_all_windows_no_composite_breach_returns_clean():
    samples = _sample(error_rate=0.0001)  # 0.01% - healthy
    result = evaluate_all_windows(
        samples=samples,
        objective=99.9,
        slo_id="slo:cost-engine:p99-latency",
    )
    assert isinstance(result, dict)
    assert result["composite_breach"] is False
    assert "fast_burn" in result["windows"]
    assert "slow_burn" in result["windows"]
    assert "exhaustion" in result["windows"]
    assert "long_window" in result["windows"]


def test_burn_rate_thresholds_match_google_sre_workbook():
    # Verbatim Google SRE Workbook values
    assert BURN_RATE_THRESHOLDS["fast_burn"]["multiplier"] == 14.4
    assert BURN_RATE_THRESHOLDS["slow_burn"]["multiplier"] == 6.0
    assert BURN_RATE_THRESHOLDS["exhaustion"]["multiplier"] == 3.0
    assert BURN_RATE_THRESHOLDS["long_window"]["multiplier"] == 1.0
