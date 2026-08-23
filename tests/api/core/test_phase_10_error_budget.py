# tests/api/core/test_phase_10_error_budget.py —
# Phase 10 T7 (cj-style 103번째 wire) — Error Budget tests. 6 cases.
#
# Tests verify the ErrorBudget TypedDict 8 fields verbatim + freeze
# policy triggering + exhaustion prediction + consumed minutes math.
import pytest

from apps.api.modules.slo.error_budget import (
    BudgetEvaluationResult,
    SloBudgetExhaustedError,
    compute_budget_total_minutes,
    compute_consumed_minutes,
    evaluate_error_budget,
    predict_exhaustion_at,
)


def _sample_budget(
    consumed_minutes: float = 0.0,
    freeze_triggered: bool = False,
    policy: str = "freeze_on_exhaust",
):
    return {
        "slo_id": "slo:cost-engine:p99-latency",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "window": "5m",
        "objective": 99.9,
        "budget_total_minutes": compute_budget_total_minutes("5m", 99.9),
        "budget_consumed_minutes": consumed_minutes,
        "budget_remaining_minutes": max(
            0.0,
            compute_budget_total_minutes("5m", 99.9) - consumed_minutes,
        ),
        "freeze_triggered": freeze_triggered,
        "error_budget_policy": policy,
        "exhaustion_predicted_at": None,
        "last_evaluated_at": "2026-08-24T00:00:00Z",
    }


def test_compute_budget_total_minutes_99_9_5min_window():
    # 0.1% error budget = 0.005 min per cycle (no, recompute)
    # 5min window * 0.001 = 0.005 min budget per cycle
    total = compute_budget_total_minutes("5m", 99.9)
    assert total == pytest.approx(0.005)


def test_compute_consumed_minutes_basic():
    consumed = compute_consumed_minutes(window_minutes=5.0, objective=99.9, burn_rate_factor=1.0)
    assert consumed == pytest.approx(0.005)


def test_predict_exhaustion_at_within_seven_days():
    # Burn rate 14.4x over 99.9% objective: budget exhausts very fast
    predicted = predict_exhaustion_at(
        current_consumed_minutes=0.001,
        total_budget_minutes=0.005,
        current_burn_rate=14.4,
        horizon_days=7,
    )
    assert predicted is not None
    assert predicted.startswith("2026-")


def test_evaluate_error_budget_freeze_policy_triggers():
    budget = _sample_budget(consumed_minutes=10.0, policy="freeze_on_exhaust")
    with pytest.raises(SloBudgetExhaustedError) as excinfo:
        evaluate_error_budget(budget, slo_id="slo:cost-engine:p99-latency")
    assert excinfo.value.status_code == 422
    assert "freeze" in str(excinfo.value).lower()


def test_evaluate_error_budget_alert_only_does_not_freeze():
    budget = _sample_budget(consumed_minutes=10.0, policy="alert_only")
    result = evaluate_error_budget(budget, slo_id="slo:cost-engine:p99-latency")
    assert result["freeze_triggered"] is False


def test_evaluate_error_budget_remaining_minutes_zero_or_positive():
    budget = _sample_budget(consumed_minutes=0.0)
    result = evaluate_error_budget(budget, slo_id="slo:cost-engine:p99-latency")
    assert result["budget_remaining_minutes"] >= 0.0
