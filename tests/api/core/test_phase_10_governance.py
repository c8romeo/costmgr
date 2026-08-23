# tests/api/core/test_phase_10_governance.py —
# Phase 10 T7 (cj-style 103번째 wire) — SLO Governance + auto-rollback
# SLO breach trigger tests. 6 cases.
#
# Verbatim PRD §F26.5 + AD-37 governance 4 conditions + AD-22 owner-only
# RBAC + Phase 9 chaos_experiment integration via correlation id
# `slo:{slo_id}:{trace_id}` (link_to_chaos_rollback).
import pytest

from apps.api.modules.slo.governance import (
    AutoRollbackDecision,
    GovernanceReview,
    SloGovernanceRequiredForbiddenError,
    build_governance_review,
    link_to_chaos_rollback,
    should_trigger_auto_rollback,
    trigger_auto_rollback,
)


def _sample_governance_review(status: str = "pending"):
    return {
        "review_id": "review:123",
        "slo_id": "slo:cost-engine:p99-latency",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "reviewer_id": "22222222-2222-2222-2222-222222222222",
        "review_status": status,
        "governance_notes": "Pending review",
        "reviewed_at": "2026-08-24T00:00:00Z",
    }


def test_should_trigger_auto_rollback_fast_burn():
    should, condition, within = should_trigger_auto_rollback(
        slo_id="slo:cost-engine:p99-latency",
        burn_rate_evaluation={
            "composite_breach": True,
            "windows": {
                "fast_burn": {"breach": True},
                "slow_burn": {"breach": False},
                "exhaustion": {"breach": False},
                "long_window": {"breach": False},
            },
        },
        auto_rollback_trigger_enabled=True,
    )
    assert should is True
    assert condition == "fast_burn"
    assert within == 60


def test_should_trigger_auto_rollback_slow_burn():
    should, condition, within = should_trigger_auto_rollback(
        slo_id="slo:cost-engine:p99-latency",
        burn_rate_evaluation={
            "composite_breach": True,
            "windows": {
                "fast_burn": {"breach": False},
                "slow_burn": {"breach": True},
                "exhaustion": {"breach": False},
                "long_window": {"breach": False},
            },
        },
        auto_rollback_trigger_enabled=True,
    )
    assert should is True
    assert condition == "slow_burn"
    assert within == 30 * 60


def test_should_not_trigger_auto_rollback_when_disabled():
    should, condition, within = should_trigger_auto_rollback(
        slo_id="slo:cost-engine:p99-latency",
        burn_rate_evaluation={
            "composite_breach": True,
            "windows": {
                "fast_burn": {"breach": True},
                "slow_burn": {"breach": False},
                "exhaustion": {"breach": False},
                "long_window": {"breach": False},
            },
        },
        auto_rollback_trigger_enabled=False,
    )
    assert should is False


def test_governance_required_raises_typed_exception():
    review = _sample_governance_review(status="pending")
    with pytest.raises(SloGovernanceRequiredForbiddenError) as excinfo:
        # Caller tries to bypass a pending review
        from apps.api.modules.slo.governance import require_governance_approval

        require_governance_approval(review)
    assert excinfo.value.status_code == 403


def test_build_governance_review_validates_status():
    with pytest.raises(ValueError):
        build_governance_review(
            review_id="review:invalid",
            slo_id="slo:cost-engine:p99-latency",
            tenant_id="11111111-1111-1111-1111-111111111111",
            reviewer_id="22222222-2222-2222-2222-222222222222",
            review_status="invalid_status",
            governance_notes="",
        )


def test_link_to_chaos_rollback_returns_correlation_id():
    decision: AutoRollbackDecision = {
        "decision_id": "decision:abc",
        "slo_id": "slo:cost-engine:p99-latency",
        "trigger_condition": "fast_burn",
        "rollback_strategy": "automatic",
        "issued_at": "2026-08-24T00:00:00Z",
        "correlation_id": "",
    }
    correlate = link_to_chaos_rollback(decision, trace_id="trace:xyz")
    assert correlate == "slo:slo:cost-engine:p99-latency:trace:xyz"
