"""tests/integration/test_audit_action_closing_period_drift.py — Story 6.1 drift detector.

3-way gate enforcement (CR 1.1 + A5 forward-lock) for the NEW
ActionClass.CLOSING_PERIOD 3 values wired by Story 6.1:

  ┌─ Python registry (apps/api/core/audit_action.py::_ActionRegistry)
  ├─ DB CHECK constraint (Alembic 0018_verification_log_v4_audit + 0017_closing_period_service)
  └─ call sites (apps/api/modules/m4_inventory/services/closing_period_service.py +
                apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py)

If any drift between the three, this test fails with a precise message.

Also covers the 2nd NEW value added to ActionClass.VERIFICATION in 6.1:
  - `verify_v4_closing_period_consistency` (Story 6.1 V4 closing snapshot verifier)
"""

from __future__ import annotations

import pytest

from apps.api.core.audit_action import (
    ActionClass,
    ClosingPeriodAction,
    VerificationAction,
    _ActionRegistry,
)


# ── ActionClass enum presence (2 cases) ──────────────────────────


def test_action_class_closing_period_present() -> None:
    """ActionClass.CLOSING_PERIOD = 'closing_period' (Story 6.1 wire)."""
    assert ActionClass.CLOSING_PERIOD.value == "closing_period"


def test_action_class_closing_period_in_registry() -> None:
    """ActionClass.CLOSING_PERIOD is registered (registry parity)."""
    assert ActionClass.CLOSING_PERIOD in _ActionRegistry._REGISTRY


# ── 3 NEW ClosingPeriodAction values (3 cases) ───────────────────


def test_closing_period_confirmed_registered() -> None:
    """`closing_period_confirmed` — confirm_closing_period success audit."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.CLOSING_PERIOD,
        action="closing_period_confirmed",
    )
    assert log_type == "audit_logs"


def test_closing_period_blocked_registered() -> None:
    """`closing_period_blocked` — confirm_closing_period raised NEGATIVE_CLOSING."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.CLOSING_PERIOD,
        action="closing_period_blocked",
    )
    assert log_type == "audit_logs"


def test_closing_period_snapshot_inconsistency_registered() -> None:
    """`closing_period_snapshot_inconsistency` — V4 fail audit-first."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.CLOSING_PERIOD,
        action="closing_period_snapshot_inconsistency",
    )
    assert log_type == "audit_logs"


# ── ClosingPeriodAction Literal SSOT (1 case) ───────────────────


def test_closing_period_action_literal_has_exactly_3_values() -> None:
    """ClosingPeriodAction Literal = 3 values (SSOT mirror)."""
    assert ClosingPeriodAction.__args__ == (
        "closing_period_confirmed",
        "closing_period_blocked",
        "closing_period_snapshot_inconsistency",
    )


# ── Drift detector: unknown action rejected (1 case) ────────────


def test_closing_period_unknown_action_rejected() -> None:
    """Unknown action string → ValueError (CR 1.1 drift protection)."""
    with pytest.raises(ValueError) as exc_info:
        _ActionRegistry.validate(
            action_class=ActionClass.CLOSING_PERIOD,
            action="closing_period_typo",  # not in registry
        )
    assert "is not in ActionClass" in str(exc_info.value)


# ── ActionClass.VERIFICATION V4 value (2 cases) ──────────────────


def test_action_class_verification_has_v4_value() -> None:
    """VerificationAction Literal includes `verify_v4_closing_period_consistency`."""
    assert "verify_v4_closing_period_consistency" in VerificationAction.__args__


def test_verify_v4_closing_period_consistency_routes_to_verification_log() -> None:
    """`verify_v4_closing_period_consistency` → verification_log destination."""
    log_type = _ActionRegistry.validate(
        action_class=ActionClass.VERIFICATION,
        action="verify_v4_closing_period_consistency",
    )
    assert log_type == "verification_log"


# ── Registry coverage: ActionClass.CLOSING_PERIOD has 3 values ──


def test_closing_period_registry_has_exactly_3_values() -> None:
    """Registry's CLOSING_PERIOD accepted set = 3 values (no extra drift)."""
    log_type, accepted = _ActionRegistry._REGISTRY[ActionClass.CLOSING_PERIOD]
    assert log_type == "audit_logs"
    assert accepted == frozenset(
        {
            "closing_period_confirmed",
            "closing_period_blocked",
            "closing_period_snapshot_inconsistency",
        }
    )