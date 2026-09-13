# tests/api/core/test_phase_10_slo_burn_rate_evaluator.py —
# Phase 10 T7 (cj-style 103번째 wire) — Multi-window burn-rate
# evaluation tests. 6 cases.
#
# Verbatim Google SRE Workbook multi-window burn-rate evaluation:
#   fast_burn: 1h window, 14.4x threshold, 5min alert window
#   slow_burn: 6h window, 6x threshold, 30min alert window
#   exhaustion: 24h window, 3x threshold, 2h alert window
#   long_window: 3d window, 1x threshold, 6h alert window
#
# Note (cj-style 306+ retroactive correction): tests rewritten to match
# the actual `evaluate_single_window(window, error_rate, objective)` and
# `evaluate_all_windows(slo_id, tenant_id, objective,
# error_rates_by_window, *, evaluated_at)` signatures. Thresholds live
# in the `WINDOW_THRESHOLDS` module-level dict (window → float threshold).
# SloViolationDetectedError uses `http_status` (BaseError envelope
# verbatim), not `status_code`. `breached` field, not `breach`.
import pytest

from apps.api.modules.slo.slo_burn_rate_evaluator import (
    SloViolationDetectedError,
    WINDOW_FAST_BURN,
    WINDOW_LONG,
    WINDOW_THRESHOLDS,
    compute_burn_rate,
    evaluate_all_windows,
    evaluate_single_window,
)


def _sample_error_rates(error_rate: float = 0.01) -> dict[str, float]:
    # error_rates_by_window: dict[window, error_rate] (0.0~1.0).
    return {
        WINDOW_FAST_BURN: error_rate,
        "6h": error_rate,
        "24h": error_rate,
        WINDOW_LONG: error_rate,
    }


def test_compute_burn_rate_basic_formula():
    # objective 99.9 → error budget 0.1%
    # error_rate 0.001 = 0.1% → burn_rate = 0.001 / (1 - 0.999) = 1.0
    assert compute_burn_rate(error_rate=0.001, objective=99.9) == pytest.approx(1.0)


def test_evaluate_single_window_fast_burn_breach():
    # 2% error rate × 99.9% objective → burn_rate = 0.02 / 0.001 = 20x
    # (well above fast_burn threshold 14.4x) → breached = True.
    result = evaluate_single_window(
        window=WINDOW_FAST_BURN,
        error_rate=0.02,
        objective=99.9,
    )
    assert result["burn_rate"] >= WINDOW_THRESHOLDS[WINDOW_FAST_BURN]
    assert result["breached"] is True


def test_evaluate_single_window_long_window_no_breach():
    # 0.05% error rate × 99.9% objective → burn_rate = 0.0005 / 0.001 = 0.5x
    # (below long_window threshold 1.0x) → breached = False.
    result = evaluate_single_window(
        window=WINDOW_LONG,
        error_rate=0.0005,
        objective=99.9,
    )
    assert result["breached"] is False


def test_evaluate_all_windows_composite_breach_raises():
    # 5% error rate across all 4 windows triggers composite AND pattern
    # → SloViolationDetectedError (http_status=422).
    error_rates = _sample_error_rates(error_rate=0.05)
    with pytest.raises(SloViolationDetectedError) as excinfo:
        evaluate_all_windows(
            slo_id="slo:cost-engine:p99-latency",
            tenant_id="11111111-1111-1111-1111-111111111111",
            objective=99.9,
            error_rates_by_window=error_rates,
            evaluated_at="2026-08-24T00:00:00Z",
        )
    assert excinfo.value.http_status == 422


def test_evaluate_all_windows_no_composite_breach_returns_clean():
    # 0.0001% error rate across all 4 windows → composite_breached=False.
    error_rates = _sample_error_rates(error_rate=0.0001)
    result = evaluate_all_windows(
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        objective=99.9,
        error_rates_by_window=error_rates,
        evaluated_at="2026-08-24T00:00:00Z",
    )
    assert result["composite_breached"] is False
    # window_results is list[SloBurnRateWindow] with all 4 SRE windows.
    by_window = {r["window"]: r for r in result["window_results"]}
    assert WINDOW_FAST_BURN in by_window
    assert "6h" in by_window
    assert "24h" in by_window
    assert WINDOW_LONG in by_window


def test_burn_rate_thresholds_match_google_sre_workbook():
    # Verbatim Google SRE Workbook values (PRD §F26.2.2 verbatim).
    assert WINDOW_THRESHOLDS[WINDOW_FAST_BURN] == pytest.approx(14.4)
    assert WINDOW_THRESHOLDS["6h"] == pytest.approx(6.0)
    assert WINDOW_THRESHOLDS["24h"] == pytest.approx(3.0)
    assert WINDOW_THRESHOLDS[WINDOW_LONG] == pytest.approx(1.0)
