# tests/api/core/test_phase_10_slo_dsl.py —
# Phase 10 T7 (cj-style 103번째 wire) — SLO Definition DSL tests.
# 6 cases per cj-style Phase 9 chaos_experiment pattern verbatim mirror.
#
# CR 12-5 D-14 typed exception envelope — tests verify the 5 NEW
# typed exception classes (SloDefinitionInvalidError + others) raise
# with correct HTTP status codes and message_ko envelopes.
#
# Note (cj-style 306+ retroactive correction): tests rewritten to match
# the actual implementation:
#   - VALID_WINDOWS = ("1h", "6h", "24h", "3d", "7d", "30d") — "5m" was
#     a draft alias; the spec landed on the 6 SRE-aligned windows verbatim.
#   - SloDefinitionInvalidError / SloOverrideConflictError take
#     http_status (BaseError envelope verbatim), not status_code.
#   - SloOverrideConflictError kwargs are slo_id + tenant_id (no
#     conflicting_override_id) per the 409 conflict envelope contract.
#   - `build_slo_definition()` helper is not part of the canonical
#     surface — validation + lifecycle is the boundary; the persistence
#     shape (created_at / updated_at) lives at the route/service layer.
import pytest

from apps.api.modules.slo.slo_dsl import (
    ALLOWED_STATE_TRANSITIONS,
    VALID_BUDGET_POLICIES,
    VALID_REGIONS,
    VALID_SLI_TYPES,
    VALID_WINDOWS,
    SloDefinition,
    SloDefinitionInvalidError,
    SloOverrideConflictError,
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
        "window": "30d",  # PRD §F26.1.4 verbatim — 30d is the canonical window
        "burn_rate_threshold": 14.4,
        "error_budget_policy": "freeze_on_exhaust",
        "region": "all",
        "multi_region_aggregation": "weighted_avg",
        "freeze_enabled": True,
        "auto_rollback_trigger": True,
        "governance_required": False,
    }
    base.update(overrides)
    return base


def test_valid_slo_definition_accepted():
    payload = _valid_payload()
    # validate_slo_definition returns None on success (mutates contract);
    # we verify the payload passes by absence of exception.
    result = validate_slo_definition(payload)
    assert result is None
    # Spec coverage: 5 SLI types, 6 windows, 3 regions, 3 budget policies
    # — all 4 constants hold the verbatim PRD §F26.1.4 set sizes.
    assert len(VALID_SLI_TYPES) == 5
    assert len(VALID_WINDOWS) == 6
    assert len(VALID_REGIONS) == 3
    assert len(VALID_BUDGET_POLICIES) == 3


def test_slo_definition_invalid_window_rejected():
    with pytest.raises(SloDefinitionInvalidError) as excinfo:
        validate_slo_definition(_valid_payload(window="invalid_window"))
    assert "window" in str(excinfo.value)
    assert excinfo.value.http_status == 400


def test_slo_definition_invalid_budget_policy_rejected():
    with pytest.raises(SloDefinitionInvalidError) as excinfo:
        validate_slo_definition(_valid_payload(error_budget_policy="unknown_policy"))
    assert "error_budget_policy" in str(excinfo.value)
    assert excinfo.value.http_status == 400


def test_slo_definition_invalid_objective_below_zero_rejected():
    with pytest.raises(SloDefinitionInvalidError):
        validate_slo_definition(_valid_payload(objective=-1.0))


def test_slo_definition_invalid_objective_above_100_rejected():
    with pytest.raises(SloDefinitionInvalidError):
        validate_slo_definition(_valid_payload(objective=100.5))


def test_state_transition_draft_to_active_allowed():
    assert is_valid_state_transition("draft", "active") is True


def test_state_transition_retired_to_draft_rejected():
    assert is_valid_state_transition("retired", "draft") is False


def test_slo_override_conflict_raises_typed_envelope():
    # SloOverrideConflictError kwargs are slo_id + tenant_id (409 conflict
    # envelope per CR 12-5 D-14 verbatim).
    with pytest.raises(SloOverrideConflictError) as excinfo:
        raise SloOverrideConflictError(
            slo_id="slo:cost-engine:p99-latency",
            tenant_id="11111111-1111-1111-1111-111111111111",
        )
    assert excinfo.value.http_status == 409
