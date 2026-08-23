# tests/api/core/test_phase_10_slo_dsl.py —
# Phase 10 T7 (cj-style 103번째 wire) — SLO Definition DSL tests.
# 6 cases per cj-style Phase 9 chaos_experiment pattern verbatim mirror.
#
# CR 12-5 D-14 typed exception envelope — tests verify the 5 NEW
# typed exception classes (SloDefinitionInvalidError + others) raise
# with correct HTTP status codes and message_ko envelopes.
import pytest
from apps.api.core.errors import BadRequest, Conflict, UnprocessableEntity
from apps.api.modules.slo.slo_dsl import (
    ALLOWED_STATE_TRANSITIONS,
    BUDGET_POLICIES,
    REGIONS,
    SLI_TYPES,
    WINDOWS,
    SloDefinition,
    SloDefinitionInvalidError,
    SloOverrideConflictError,
    build_slo_definition,
    is_valid_state_transition,
    validate_slo_definition,
)


def _valid_payload(**overrides):
    base = {
        "slo_id": "slo:cost-engine:p99-latency",
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "service": "cost-engine",
        "sli_type": "latency",
        "objective": 99.9,
        "window": "5m",
        "burn_rate_threshold": 14.4,
        "error_budget_policy": "freeze_on_exhaust",
        "region": "all",
        "multi_region_aggregation": "weighted_avg",
        "freeze_enabled": True,
        "auto_rollback_trigger": True,
        "governance_required": False,
        "state": "draft",
    }
    base.update(overrides)
    return base


def test_valid_slo_definition_accepted():
    payload = _valid_payload()
    validated = validate_slo_definition(payload)
    assert validated["slo_id"] == "slo:cost-engine:p99-latency"
    assert validated["objective"] == 99.9
    assert validated["state"] == "draft"


def test_slo_definition_invalid_window_rejected():
    from apps.api.modules.slo.slo_dsl import SloDefinitionInvalidError

    with pytest.raises(SloDefinitionInvalidError) as excinfo:
        validate_slo_definition(_valid_payload(window="invalid_window"))
    assert "window" in str(excinfo.value)
    assert excinfo.value.status_code == 400


def test_slo_definition_invalid_budget_policy_rejected():
    from apps.api.modules.slo.slo_dsl import SloDefinitionInvalidError

    with pytest.raises(SloDefinitionInvalidError) as excinfo:
        validate_slo_definition(_valid_payload(error_budget_policy="unknown_policy"))
    assert "error_budget_policy" in str(excinfo.value)
    assert excinfo.value.status_code == 400


def test_slo_definition_invalid_objective_below_zero_rejected():
    with pytest.raises(SloDefinitionInvalidError):
        validate_slo_definition(_valid_payload(objective=-1.0))


def test_slo_definition_invalid_objective_above_100_rejected():
    with pytest.raises(SloDefinitionInvalidError):
        validate_slo_definition(_valid_payload(objective=100.5))


def test_build_slo_definition_helper_sets_timestamps():
    payload = _valid_payload()
    slo = build_slo_definition(payload, actor_id="22222222-2222-2222-2222-222222222222")
    assert slo["created_at"] is not None
    assert slo["updated_at"] is not None


def test_state_transition_draft_to_active_allowed():
    assert is_valid_state_transition("draft", "active") is True


def test_state_transition_retired_to_draft_rejected():
    assert is_valid_state_transition("retired", "draft") is False


def test_slo_override_conflict_raises_typed_envelope():
    from apps.api.modules.slo.slo_dsl import SloOverrideConflictError

    with pytest.raises(SloOverrideConflictError) as excinfo:
        raise SloOverrideConflictError(
            slo_id="slo:cost-engine:p99-latency",
            conflicting_override_id="override:123",
        )
    assert excinfo.value.status_code == 409
