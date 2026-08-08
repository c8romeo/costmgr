"""tests.api.test_audit_action_m11_extension — Story 11.1 T9 A5+A9 forward-lock tests.

A5 forward-lock: ActionClass.REVERSAL_LOG frozenset filled with 5 values
(D3 R4 triage decision — full AD-22 reversal sequence + AD-25 publisher):
- reversal_negating_inserted (sign-negating row INSERTED)
- reversal_corrected_inserted (corrected row INSERTED)
- reversal_rejected (authorize_reversal denied / duplicate)
- reversal_unauthorized (caller actor/role mismatch)
- m11_reversal_handler_invoked (M11 module entrypoint audit-first)

A9 fill: ActionClass.MONTHLY_INPUT_PERIOD frozenset extended with:
- monthly_input_period_opening_unlocked

These tests verify the registry's frozenset membership + the typed
Literal definitions match the registry exactly (drift detector).
"""

from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    InventoryLedgerAction,
    MonthlyInputPeriodAction,
    ReversalLogAction,
    _ActionRegistry,
)


# ── A5 forward-lock: REVERSAL_LOG 5 values (D3 R4 triage) ─────


def test_reversal_log_action_literal_has_5_values() -> None:
    """ReversalLogAction Literal has 5 values (D3 R4 triage full fill)."""
    # Use get_type_hints to introspect the Literal
    import typing

    values = typing.get_args(ReversalLogAction)
    assert len(values) == 5
    assert "m11_reversal_handler_invoked" in values
    assert "reversal_negating_inserted" in values
    assert "reversal_corrected_inserted" in values
    assert "reversal_rejected" in values
    assert "reversal_unauthorized" in values


def test_reversal_log_registry_frozenset_has_5_values() -> None:
    """ActionClass.REVERSAL_LOG registry frozenset has 5 values (D3)."""
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.REVERSAL_LOG]
    assert log_type == "reversal_log"
    assert len(accepted) == 5
    assert "m11_reversal_handler_invoked" in accepted
    assert "reversal_negating_inserted" in accepted
    assert "reversal_corrected_inserted" in accepted
    assert "reversal_rejected" in accepted
    assert "reversal_unauthorized" in accepted


def test_reversal_log_validate_accepts_known_values() -> None:
    """_ActionRegistry.validate accepts all 5 REVERSAL_LOG values (D3)."""
    for action in (
        "m11_reversal_handler_invoked",
        "reversal_negating_inserted",
        "reversal_corrected_inserted",
        "reversal_rejected",
        "reversal_unauthorized",
    ):
        # Should not raise
        _ActionRegistry.validate(
            action_class=ActionClass.REVERSAL_LOG,
            action=action,
        )


def test_reversal_log_validate_rejects_unknown_values() -> None:
    """_ActionRegistry.validate rejects unknown REVERSAL_LOG values."""
    with pytest.raises(ValueError):
        _ActionRegistry.validate(
            action_class=ActionClass.REVERSAL_LOG,
            action="not_a_valid_action",
        )


# ── A9 fill: MONTHLY_INPUT_PERIOD 4 values ───────────────────


def test_monthly_input_period_action_literal_has_4_values() -> None:
    """MonthlyInputPeriodAction Literal has 4 values (added opening_unlocked)."""
    import typing

    values = typing.get_args(MonthlyInputPeriodAction)
    assert len(values) == 4
    assert "monthly_input_mode_changed" in values
    assert "monthly_input_period_opening_carried" in values
    assert "monthly_input_period_opening_locked" in values
    assert "monthly_input_period_opening_unlocked" in values


def test_monthly_input_period_registry_frozenset_has_4_values() -> None:
    """ActionClass.MONTHLY_INPUT_PERIOD registry frozenset has 4 values."""
    log_type, accepted = _ActionRegistry._REGISTRY[
        ActionClass.MONTHLY_INPUT_PERIOD
    ]
    assert log_type == "audit_logs"
    assert len(accepted) == 4
    assert "monthly_input_period_opening_unlocked" in accepted


def test_monthly_input_period_validate_accepts_opening_unlocked() -> None:
    """_ActionRegistry.validate accepts the new opening_unlocked action."""
    # Should not raise
    _ActionRegistry.validate(
        action_class=ActionClass.MONTHLY_INPUT_PERIOD,
        action="monthly_input_period_opening_unlocked",
    )


# ── A5 forward-lock: INVENTORY_LEDGER unchanged wire ─────────


def test_inventory_ledger_action_literal_has_6_values() -> None:
    """InventoryLedgerAction Literal has 6 values (Epic 5+11+6 forward-fill)."""
    import typing

    values = typing.get_args(InventoryLedgerAction)
    assert len(values) == 6
    assert "inventory_ledger_event_appended" in values
    assert "inventory_ledger_event_rejected" in values
    assert "inventory_ledger_reversal_requested" in values
    assert "inventory_ledger_reversal_logged" in values
    assert "inventory_ledger_reversal_rejected" in values
    assert "inventory_ledger_reprojection_triggered" in values


def test_inventory_ledger_registry_frozenset_has_6_values() -> None:
    """ActionClass.INVENTORY_LEDGER registry frozenset has 6 values."""
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.INVENTORY_LEDGER]
    assert log_type == "inventory_ledger"
    assert len(accepted) == 6


# ── Capability.REVERSAL_REQUEST wire ─────────────────────────


def test_capability_reversal_request_added_to_manufacturing_industries() -> None:
    """Capability.REVERSAL_REQUEST is granted to manufacturing 3종."""
    from apps.api.core.capability import (
        Capability,
        _INDUSTRY_CAPABILITIES,
    )
    from packages.services.m0_onboarding.industry_menu import Industry

    # Manufacturing 3종 (manufacturing / mfg+service / mfg+service+other)
    for industry in (
        Industry.MANUFACTURING,
        Industry.MANUFACTURING_SERVICE,
        Industry.MANUFACTURING_SERVICE_OTHER,
    ):
        assert (
            Capability.REVERSAL_REQUEST in _INDUSTRY_CAPABILITIES[industry]
        ), f"{industry} should have REVERSAL_REQUEST"


def test_capability_reversal_request_not_in_service_only() -> None:
    """Service-only tenant does NOT have REVERSAL_REQUEST."""
    from apps.api.core.capability import (
        Capability,
        _INDUSTRY_CAPABILITIES,
    )
    from packages.services.m0_onboarding.industry_menu import Industry

    assert (
        Capability.REVERSAL_REQUEST
        not in _INDUSTRY_CAPABILITIES[Industry.SERVICE]
    )
