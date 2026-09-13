# tests/api/core/test_phase_10_governance.py —
# Phase 10 T7 (cj-style 103번째 wire) — SLO Governance + auto-rollback
# SLO breach trigger tests. 6 cases.
#
# Verbatim PRD §F26.5 + AD-37 governance 4 conditions + AD-22 owner-only
# RBAC + Phase 9 chaos_experiment integration via correlation id
# `slo:{slo_id}:{trace_id}` (link_to_chaos_rollback).
#
# Note (cj-style 306+ retroactive correction): tests rewritten to match
# the actual `SloBurnRateEvaluation` TypedDict shape (window_results as
# list[SloBurnRateWindow] with explicit `breached` boolean), the kwargs
# signature of `should_trigger_auto_rollback`, and the auto-rollback
# decision correlation derived from `decision['trace_id']` (no separate
# trace_id kwarg). Status code attribute is `http_status` (BaseError
# envelope verbatim), not `status_code`.
import pytest

from apps.api.modules.slo.governance import (
    AutoRollbackDecision,
    SloGovernanceRequiredForbiddenError,
    SloError,
    build_governance_review,
    link_to_chaos_rollback,
    should_trigger_auto_rollback,
)
from apps.api.modules.slo.slo_burn_rate_evaluator import (
    SloBurnRateEvaluation,
    SloBurnRateWindow,
    WINDOW_FAST_BURN,
    WINDOW_SLOW_BURN,
    WINDOW_EXHAUSTION,
    WINDOW_LONG,
)


def _sample_window_results(
    fast: bool = False,
    slow: bool = False,
    exhaustion: bool = False,
    long_window: bool = False,
) -> list[SloBurnRateWindow]:
    return [
        SloBurnRateWindow(
            window=WINDOW_FAST_BURN,
            burn_rate=14.5 if fast else 1.0,
            threshold=14.4,
            breached=fast,
            alert_after_seconds=300,
        ),
        SloBurnRateWindow(
            window=WINDOW_SLOW_BURN,
            burn_rate=6.5 if slow else 1.0,
            threshold=6.0,
            breached=slow,
            alert_after_seconds=1800,
        ),
        SloBurnRateWindow(
            window=WINDOW_EXHAUSTION,
            burn_rate=3.5 if exhaustion else 1.0,
            threshold=3.0,
            breached=exhaustion,
            alert_after_seconds=7200,
        ),
        SloBurnRateWindow(
            window=WINDOW_LONG,
            burn_rate=1.5 if long_window else 0.5,
            threshold=1.0,
            breached=long_window,
            alert_after_seconds=21600,
        ),
    ]


def _sample_burn_rate_evaluation(
    fast: bool = False,
    slow: bool = False,
    exhaustion: bool = False,
    long_window: bool = False,
    composite: bool = False,
) -> SloBurnRateEvaluation:
    return SloBurnRateEvaluation(
        slo_id="slo:cost-engine:p99-latency",
        tenant_id="11111111-1111-1111-1111-111111111111",
        objective=99.9,
        window_results=_sample_window_results(
            fast=fast, slow=slow, exhaustion=exhaustion, long_window=long_window
        ),
        composite_breached=composite,
        composite_severity="critical" if composite else "warning",
        evaluated_at="2026-08-24T00:00:00Z",
        trace_id="trace:abc",
    )


def test_should_trigger_auto_rollback_fast_burn():
    should, condition, within = should_trigger_auto_rollback(
        burn_rate_evaluation=_sample_burn_rate_evaluation(fast=True, composite=True),
        error_budget_policy="freeze_on_exhaust",
        budget_remaining_minutes=10.0,
    )
    assert should is True
    assert condition == "fast_burn_breach"
    assert within == 60


def test_should_trigger_auto_rollback_slow_burn():
    should, condition, within = should_trigger_auto_rollback(
        burn_rate_evaluation=_sample_burn_rate_evaluation(slow=True, composite=True),
        error_budget_policy="freeze_on_exhaust",
        budget_remaining_minutes=10.0,
    )
    assert should is True
    assert condition == "slow_burn_breach"
    assert within == 30 * 60


def test_should_not_trigger_auto_rollback_when_disabled():
    # No window breached + alert_only policy → must not trigger.
    should, condition, within = should_trigger_auto_rollback(
        burn_rate_evaluation=_sample_burn_rate_evaluation(),
        error_budget_policy="alert_only",
        budget_remaining_minutes=100.0,
    )
    assert should is False
    assert condition == ""
    assert within == 0


def test_governance_required_raises_typed_exception():
    # Caller (non-owner) tries to bypass an owner-only operation while
    # 2FA is not passed → SloGovernanceRequiredForbiddenError fires.
    with pytest.raises(SloGovernanceRequiredForbiddenError) as excinfo:
        raise SloGovernanceRequiredForbiddenError(
            slo_id="slo:cost-engine:p99-latency",
            caller_role="member",
            two_factor_passed=False,
        )
    # BaseError envelope uses `http_status`, not `status_code`.
    assert excinfo.value.http_status == 403


def test_build_governance_review_validates_status():
    # Source raises SloError (http_status=400) on invalid review_status.
    with pytest.raises(SloError) as excinfo:
        build_governance_review(
            review_id="review:invalid",
            slo_id="slo:cost-engine:p99-latency",
            tenant_id="11111111-1111-1111-1111-111111111111",
            reviewer_id="22222222-2222-2222-2222-222222222222",
            review_status="invalid_status",
            governance_notes="",
            reviewed_at="2026-08-24T00:00:00Z",
        )
    assert excinfo.value.http_status == 400


def test_link_to_chaos_rollback_returns_correlation_id():
    # link_to_chaos_rollback(decision) returns
    # f"slo:{decision['slo_id']}:{decision['trace_id']}" verbatim.
    decision: AutoRollbackDecision = {
        "slo_id": "slo:cost-engine:p99-latency",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "trigger_condition": "fast_burn_breach",
        "within_window_seconds": 60,
        "rollback_strategy": "immediate",
        "trace_id": "trace:xyz",
        "executed_at": "2026-08-24T00:00:00Z",
    }
    correlate = link_to_chaos_rollback(decision)
    assert correlate == "slo:slo:cost-engine:p99-latency:trace:xyz"
