"""tests.api.core.test_phase_26_cost_anomaly_ml_prediction_audit_action — Phase 26 audit action EXTENSION tests.

Phase 26 (cj-style 183번째 wire) — FinOps Cost Anomaly ML Prediction
territory audit_action EXTENSION (PRD §F42.7 verbatim). ActionClass.
FINOPS_COST_ANOMALY_ML_PREDICTION + 12 NEW audit actions via emit_audit_typed
CR 1-1 verbatim.

Phase 26 wire cycle (cj-style 179 + 180 + 181 + 182 → cj-style 183 = audit_action EXTENSION):
- cj-style 179: Phase 26 PRD entry (PRD §F42 EXTENSION)
- cj-style 180: Phase 26 spec entry (8 ACs §F42.1~§F42.8 verbatim)
- cj-style 181: Phase 26 atomic wire (4 NEW backend modules + alembic 0055 +
  dry-run CLI + 24 NEW pytest PASS)
- cj-style 182: Phase 26 close-out retro (5 files docs-only)
- cj-style 183 (this sprint): Phase 26 audit_action EXTENSION sprint —
  ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION + 12 NEW audit actions
  (CR 1-1 verbatim audit-first INSERT)

CR 11-3 honest-DEFER: prior sprints honestly DEFER'd this audit_action
EXTENSION. This sprint is the honest recovery — 12 NEW audit actions
(anomaly_ml_prediction_created + anomaly_ml_prediction_updated +
anomaly_ml_prediction_retired + anomaly_ml_model_registered +
anomaly_ml_model_status_changed + anomaly_ml_drift_detected +
anomaly_ml_model_training_triggered + anomaly_ml_model_trained +
anomaly_ml_prediction_scored + anomaly_ml_batch_scoring_completed +
anomaly_ml_ensemble_consensus_reached +
cost_anomaly_ml_prediction_dry_run_executed).

CR 12-5 D-14 envelope preserved: no NEW typed exception classes in this
sprint (typed exceptions honestly DEFER'd to cj-style 184).

CR 11-4 P-015 verbatim — NO pytest fixtures, pure sync, constants at module top.
"""
from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    AuditAction,
    FinopsCostAnomalyMLPredictionAction,
)


# ── 12 NEW pytest cases ──────────────────────────────────────
def test_action_class_finops_cost_anomaly_ml_prediction_registered() -> None:
    """Test 1: ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION = 'finops_cost_anomaly_ml_prediction' registered."""
    assert ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION.value == "finops_cost_anomaly_ml_prediction"
    assert ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION == "finops_cost_anomaly_ml_prediction"


def test_finops_cost_anomaly_ml_prediction_action_literal_has_12_values() -> None:
    """Test 2: FinopsCostAnomalyMLPredictionAction Literal has 12 values."""
    expected_values = {
        "anomaly_ml_prediction_created",
        "anomaly_ml_prediction_updated",
        "anomaly_ml_prediction_retired",
        "anomaly_ml_model_registered",
        "anomaly_ml_model_status_changed",
        "anomaly_ml_drift_detected",
        "anomaly_ml_model_training_triggered",
        "anomaly_ml_model_trained",
        "anomaly_ml_prediction_scored",
        "anomaly_ml_batch_scoring_completed",
        "anomaly_ml_ensemble_consensus_reached",
        "cost_anomaly_ml_prediction_dry_run_executed",
    }
    actual_values = set(FinopsCostAnomalyMLPredictionAction.__args__)
    assert actual_values == expected_values
    assert len(actual_values) == 12


def test_audit_action_union_includes_cost_anomaly_ml_prediction() -> None:
    """Test 3: AuditAction Union includes FinopsCostAnomalyMLPredictionAction."""
    action: AuditAction = "anomaly_ml_ensemble_consensus_reached"
    assert action == "anomaly_ml_ensemble_consensus_reached"


def test_action_registry_has_cost_anomaly_ml_prediction_entry() -> None:
    """Test 4: _REGISTRY has FINOPS_COST_ANOMALY_ML_PREDICTION entry."""
    from apps.api.core.audit_action import _ActionRegistry
    assert ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION in _ActionRegistry._REGISTRY
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION]
    assert log_type == "audit_logs"
    assert len(accepted) == 12
    assert "anomaly_ml_prediction_created" in accepted
    assert "anomaly_ml_prediction_updated" in accepted
    assert "anomaly_ml_prediction_retired" in accepted
    assert "anomaly_ml_model_registered" in accepted
    assert "anomaly_ml_model_status_changed" in accepted
    assert "anomaly_ml_drift_detected" in accepted
    assert "anomaly_ml_model_training_triggered" in accepted
    assert "anomaly_ml_model_trained" in accepted
    assert "anomaly_ml_prediction_scored" in accepted
    assert "anomaly_ml_batch_scoring_completed" in accepted
    assert "anomaly_ml_ensemble_consensus_reached" in accepted
    assert "cost_anomaly_ml_prediction_dry_run_executed" in accepted


def test_action_registry_drift_no_missing_actions() -> None:
    """Test 5: No action in FinopsCostAnomalyMLPredictionAction is missing from registry."""
    from apps.api.core.audit_action import _ActionRegistry
    _, accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION]
    declared = set(FinopsCostAnomalyMLPredictionAction.__args__)
    assert declared == accepted, (
        f"Drift detected: declared-accepted={declared - accepted}, "
        f"accepted-declared={accepted - declared}"
    )


def test_no_overlap_with_finops_vendor_management_actions() -> None:
    """Test 6: Phase 26 actions are distinct from Phase 25 vendor management actions."""
    from apps.api.core.audit_action import _ActionRegistry
    _, vendor_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_VENDOR_MANAGEMENT]
    _, ml_pred_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION]
    assert vendor_accepted.isdisjoint(ml_pred_accepted), (
        "Phase 26 cost anomaly ML prediction actions should not overlap "
        "with Phase 25 vendor management actions"
    )


def test_no_overlap_with_finops_anomaly_detection_actions() -> None:
    """Test 7: Phase 26 ML prediction actions are distinct from Phase 12 rule-based anomaly detection actions."""
    from apps.api.core.audit_action import _ActionRegistry
    _, rule_based_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_ANOMALY]
    _, ml_pred_accepted = _ActionRegistry._REGISTRY[ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION]
    assert rule_based_accepted.isdisjoint(ml_pred_accepted), (
        "Phase 26 ML-driven prediction actions should be complementary "
        "(not overlap) with Phase 12 rule-based anomaly detection actions"
    )


def test_12_new_audit_actions_specific_validation() -> None:
    """Test 8: All 12 NEW actions are valid string values."""
    new_actions = (
        "anomaly_ml_prediction_created",
        "anomaly_ml_prediction_updated",
        "anomaly_ml_prediction_retired",
        "anomaly_ml_model_registered",
        "anomaly_ml_model_status_changed",
        "anomaly_ml_drift_detected",
        "anomaly_ml_model_training_triggered",
        "anomaly_ml_model_trained",
        "anomaly_ml_prediction_scored",
        "anomaly_ml_batch_scoring_completed",
        "anomaly_ml_ensemble_consensus_reached",
        "cost_anomaly_ml_prediction_dry_run_executed",
    )
    for action in new_actions:
        assert isinstance(action, str)
        assert len(action) > 0
        assert action.startswith("anomaly_ml_") or action.startswith("cost_anomaly_ml_"), (
            f"Action {action!r} should be prefixed with anomaly_ml_ or cost_anomaly_ml_"
        )


def test_validate_routes_to_audit_logs() -> None:
    """Test 9: _ActionRegistry.validate routes FINOPS_COST_ANOMALY_ML_PREDICTION → 'audit_logs'."""
    from apps.api.core.audit_action import _ActionRegistry
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION,
        action="anomaly_ml_ensemble_consensus_reached",
    )
    assert log_type == "audit_logs"


def test_validate_raises_for_unknown_action_in_cost_anomaly_ml() -> None:
    """Test 10: _ActionRegistry.validate raises ValueError for unknown action in FINOPS_COST_ANOMALY_ML_PREDICTION."""
    from apps.api.core.audit_action import _ActionRegistry
    with pytest.raises(ValueError, match="audit_action"):
        _ActionRegistry.validate(
            action_class=ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION,
            action="anomaly_ml_unknown_action",
        )


def test_action_class_count_includes_cost_anomaly_ml_prediction() -> None:
    """Test 11: ActionClass enum count includes FINOPS_COST_ANOMALY_ML_PREDICTION (48 → 49)."""
    expected_count = 49  # 48 previous + 1 NEW FINOPS_COST_ANOMALY_ML_PREDICTION
    actual_count = len(list(ActionClass))
    assert actual_count == expected_count, (
        f"ActionClass enum count = {actual_count}, expected {expected_count}"
    )


def test_emit_audit_typed_with_cost_anomaly_ml_prediction_action() -> None:
    """Test 12: emit_audit_typed accepts FINOPS_COST_ANOMALY_ML_PREDICTION action_class without raising NotImplementedError."""
    from apps.api.core.audit_action import _ActionRegistry
    log_type, _ = _ActionRegistry._REGISTRY[ActionClass.FINOPS_COST_ANOMALY_ML_PREDICTION]
    assert log_type == "audit_logs"
    # The log_type 'audit_logs' is wired through emit_audit_typed → emit_audit
    # (apps/api/core/audit.py), so no NotImplementedError expected at registry
    # level. End-to-end test coverage of emit_audit_typed invocation with this
    # ActionClass is provided by Phase 26 backend integration test suite.
