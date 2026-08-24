"""tests.api.core.test_phase_14_optimization_accuracy_tracker — Phase 14 accuracy tracker tests.

Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
territory (PRD §F30.5). precision + recall + realized_savings +
projected_vs_realized + false_positive + retraining trigger.

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import uuid

import pytest

from apps.api.core.errors import (
    OptimizationAccuracyTrackingError,
)
from apps.api.modules.finops.optimization_accuracy_tracker import (
    ACCURACY_KEY_FORMAT,
    ACCURACY_SCORE_CONSECUTIVE_MONTHS_THRESHOLD,
    ACCURACY_SCORE_RETRAINING_THRESHOLD_PCT,
    ALL_FALSE_POSITIVE_REASONS,
    FALSE_POSITIVE_APPLICATION_CHANGE,
    FALSE_POSITIVE_BUSINESS_GROWTH,
    FALSE_POSITIVE_OVERESTIMATION,
    FALSE_POSITIVE_PERFORMANCE_DEGRADATION,
    FALSE_POSITIVE_SEASONALITY_MISMATCH,
    PRECISION_THRESHOLD_HIGH_PCT,
    PRECISION_THRESHOLD_MODERATE_PCT,
    RETRAINING_CRON_DEFAULT,
    OptimizationAccuracyReport,
    check_accuracy_degradation,
    compute_accuracy_score,
    compute_precision,
    compute_recall,
    track_optimization_accuracy,
)
from apps.api.modules.finops.optimization_definition import (
    RESOURCE_TYPE_COMPUTE,
    STRATEGY_COMPOSITE,
)

TENANT_ID: str = str(uuid.uuid4())


# ── 5 NEW pytest cases ──────────────────────────────────────
def test_precision_calculation() -> None:
    """Test 1: precision = TP / (TP + FP) × 100."""
    # TP=80, FP=20 → 80%
    assert compute_precision(80, 20) == 80.0
    # TP=100, FP=0 → 100%
    assert compute_precision(100, 0) == 100.0
    # TP=0, FP=0 → 0.0 (no recommendations)
    assert compute_precision(0, 0) == 0.0


def test_recall_calculation() -> None:
    """Test 2: recall = TP / (TP + FN) × 100."""
    # TP=80, FN=20 → 80%
    assert compute_recall(80, 20) == 80.0
    # TP=0, FN=0 → 0.0
    assert compute_recall(0, 0) == 0.0


def test_accuracy_score_calculation() -> None:
    """Test 3: accuracy_score = realized / projected × 100."""
    # realized 80k / projected 100k → 80%
    assert compute_accuracy_score(80000.0, 100000.0) == 80.0
    # projected=0 → 0.0 (safe)
    assert compute_accuracy_score(1000.0, 0.0) == 0.0


def test_check_accuracy_degradation_three_states() -> None:
    """Test 4: check_accuracy_degradation 3-state output."""
    # High score → ok
    assert check_accuracy_degradation(85.0, 0) == "ok"
    # Below threshold but < 3 months → flag
    assert check_accuracy_degradation(60.0, 2) == "flag_degradation"
    # Below threshold + ≥ 3 months → trigger retraining
    assert check_accuracy_degradation(60.0, 3) == "trigger_retraining"
    assert check_accuracy_degradation(50.0, 5) == "trigger_retraining"


def test_build_optimization_accuracy_report_validates_strategy() -> None:
    """Test 5: report builder validates resource_type + strategy enums."""
    from apps.api.modules.finops.optimization_accuracy_tracker import (
        _build_optimization_accuracy_report,
    )
    # valid
    report = _build_optimization_accuracy_report(
        tenant_id=TENANT_ID,
        resource_type=RESOURCE_TYPE_COMPUTE,
        optimization_strategy=STRATEGY_COMPOSITE,
        total_recommendations=100,
        applied_recommendations=80,
        true_positives=70,
        false_positives=10,
        false_negatives=20,
        realized_savings_krw=80000.0,
        projected_savings_krw=100000.0,
    )
    assert report["precision"] == 87.5  # 70 / (70+10) = 87.5
    assert report["recall"] == 77.7778  # 70 / (70+20)
    assert report["accuracy_score"] == 80.0
    assert report["tenant_id"] == TENANT_ID
    # invalid strategy
    with pytest.raises(OptimizationAccuracyTrackingError):
        _build_optimization_accuracy_report(
            tenant_id=TENANT_ID,
            resource_type=RESOURCE_TYPE_COMPUTE,
            optimization_strategy="unknown_strategy",
            total_recommendations=10,
            applied_recommendations=5,
            true_positives=4,
            false_positives=1,
            false_negatives=2,
            realized_savings_krw=1000.0,
            projected_savings_krw=2000.0,
        )


# ── enum invariants ─────────────────────────────────────────
def test_enum_invariants_and_thresholds() -> None:
    """Test 6: enum invariants + threshold constants."""
    assert len(ALL_FALSE_POSITIVE_REASONS) == 5
    assert FALSE_POSITIVE_OVERESTIMATION in ALL_FALSE_POSITIVE_REASONS
    assert FALSE_POSITIVE_PERFORMANCE_DEGRADATION in ALL_FALSE_POSITIVE_REASONS
    assert FALSE_POSITIVE_BUSINESS_GROWTH in ALL_FALSE_POSITIVE_REASONS
    assert FALSE_POSITIVE_SEASONALITY_MISMATCH in ALL_FALSE_POSITIVE_REASONS
    assert FALSE_POSITIVE_APPLICATION_CHANGE in ALL_FALSE_POSITIVE_REASONS
    assert ACCURACY_SCORE_RETRAINING_THRESHOLD_PCT == 70.0
    assert ACCURACY_SCORE_CONSECUTIVE_MONTHS_THRESHOLD == 3
    assert PRECISION_THRESHOLD_HIGH_PCT == 80.0
    assert PRECISION_THRESHOLD_MODERATE_PCT == 60.0
    assert RETRAINING_CRON_DEFAULT == "0 3 * * 0"
    assert ACCURACY_KEY_FORMAT == "{tenant_id}:{resource_type}:{optimization_strategy}"


def test_track_optimization_accuracy_placeholder() -> None:
    """Test 7: track_optimization_accuracy returns valid placeholder report."""
    report = track_optimization_accuracy(
        tenant_id=TENANT_ID,
        resource_type=RESOURCE_TYPE_COMPUTE,
        optimization_strategy=STRATEGY_COMPOSITE,
    )
    assert isinstance(report, dict)
    assert report["tenant_id"] == TENANT_ID
    assert report["resource_type"] == RESOURCE_TYPE_COMPUTE
    assert report["optimization_strategy"] == STRATEGY_COMPOSITE
    assert "report_id" in report
    assert "generated_at" in report
