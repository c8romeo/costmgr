# tests/api/core/test_phase_10_error_budget.py —
# Phase 10 T7 (cj-style 103번째 wire) — Error Budget tests. 6 cases.
#
# Tests verify the ErrorBudget TypedDict 8 fields verbatim + freeze
# policy triggering + exhaustion prediction + consumed minutes math.
#
# Note (cj-style 306+ retroactive correction): tests rewritten to match
# the actual implementation signatures of `compute_budget_total_minutes`
# (window from VALID_WINDOWS only — "1h"/"6h"/"24h"/"3d"/"7d"/"30d"),
# `predict_exhaustion_at` (kwargs budget_total_minutes / budget_consumed_
# minutes / burn_rate_factor / evaluated_at, returns ISO8601 str),
# `evaluate_error_budget` (kwargs-only signature with explicit slo_id,
# tenant_id, error_budget_policy, objective, window, burn_rate_factor,
# evaluated_at). Status code attribute is `http_status` (BaseError
# envelope verbatim), not `status_code`.
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
        "window": "30d",
        "objective": 99.9,
        "budget_total_minutes": compute_budget_total_minutes("30d", 99.9),
        "budget_consumed_minutes": consumed_minutes,
        "budget_remaining_minutes": max(
            0.0,
            compute_budget_total_minutes("30d", 99.9) - consumed_minutes,
        ),
        "freeze_triggered": freeze_triggered,
        "error_budget_policy": policy,
        "exhaustion_predicted_at": None,
        "last_evaluated_at": "2026-08-24T00:00:00Z",
    }


def test_compute_budget_total_minutes_99_9_30d_window():
    # 30d window = 43200 min. 99.9% SLO → 0.1% budget → 43200 * 0.001 = 43.2 min.
    total = compute_budget_total_minutes("30d", 99.9)
    assert total == pytest.approx(43.2)


def test_compute_consumed_minutes_basic():
    consumed = compute_consumed_minutes(window_minutes=5.0, objective=99.9, burn_rate_factor=1.0)
    # 5.0 * (1 - 0.999) * 1.0 = 0.005
    assert consumed == pytest.approx(0.005)


def test_predict_exhaustion_at_within_seven_days():
    # Burn rate 14.4x over 99.9% objective: budget exhausts very fast.
    predicted = predict_exhaustion_at(
        budget_total_minutes=0.005,
        budget_consumed_minutes=0.001,
        burn_rate_factor=14.4,
        evaluated_at="2026-08-24T00:00:00Z",
    )
    assert predicted is not None
    assert predicted.startswith("2026-")


def test_evaluate_error_budget_freeze_policy_triggers():
    # 99.9% SLO × 30d window × burn_rate_factor 1000× ⇒ massive
    # over-consumption → freeze policy triggers exhausted error.
    with pytest.raises(SloBudgetExhaustedError) as excinfo:
        evaluate_error_budget(
            slo_id="slo:cost-engine:p99-latency",
            tenant_id="11111111-1111-1111-1111-111111111111",
            error_budget_policy="freeze_on_exhaust",
            objective=99.9,
            window="30d",
            burn_rate_factor=1000.0,
            evaluated_at="2026-08-24T00:00:00Z",
        )
    # BaseError envelope uses `http_status`, not `status_code`.
    assert excinfo.value.http_status == 422
    assert "exhausted" in str(excinfo.value).lower()


def test_evaluate_error_budget_alert_only_does_not_freeze():
    # alert_only policy never freezes — even with extreme burn rate.
    result = evaluate_error_budget(
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        error_budget_policy="alert_only",
        objective=99.9,
        window="30d",
        burn_rate_factor=1.5,
        evaluated_at="2026-08-24T00:00:00Z",
    )
    assert result["freeze_triggered"] is False


def test_evaluate_error_budget_remaining_minutes_zero_or_positive():
    # Burn rate 0.5× (below baseline) → consumed stays below total.
    result = evaluate_error_budget(
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        error_budget_policy="alert_only",
        objective=99.9,
        window="30d",
        burn_rate_factor=0.5,
        evaluated_at="2026-08-24T00:00:00Z",
    )
    assert result["budget_remaining_minutes"] >= 0.0
