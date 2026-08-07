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


# ── CR 6-1 R4 patch D15: 3-way drift detector extension ───────
# The previous tests verified Python registry ↔ DB CHECK constraint (2-way).
# Adding call site coverage for the 3-way gate: every accepted action MUST
# have at least one call site that invokes `emit_audit_typed` with that
# action. Drift detector fails if a registered action is never emitted
# (dead-letter) OR if an unregistered action is emitted (CR 1.1 violation).


import re  # noqa: E402
from pathlib import Path  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
_CLOSING_PERIOD_SERVICE = (
    _REPO_ROOT
    / "apps/api/modules/m4_inventory/services/closing_period_service.py"
)
_V4_VERIFIER = (
    _REPO_ROOT
    / "apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py"
)


def _read(p: Path) -> str:
    """Read source file (UTF-8)."""
    return p.read_text(encoding="utf-8")


def _audit_emit_calls(src: str, action: str) -> list[str]:
    """Return emit_audit_typed call sites that mention `action=<action>`.

    Regex tolerates whitespace / multi-line wrapping.
    """
    pattern = re.compile(
        rf"emit_audit_typed\([^)]*?action\s*=\s*[\"']{re.escape(action)}[\"']",
        re.DOTALL,
    )
    return pattern.findall(src)


def test_closing_period_confirmed_emitted_by_service() -> None:
    """closing_period_confirmed MUST be emitted by closing_period_service.

    Call site: `_emit_audit_confirmed` in
    `apps/api/modules/m4_inventory/services/closing_period_service.py`.
    """
    src = _read(_CLOSING_PERIOD_SERVICE)
    matches = _audit_emit_calls(src, "closing_period_confirmed")
    assert matches, (
        "3-way drift: `closing_period_confirmed` is registered but NOT "
        "emitted by closing_period_service. Fix: add emit_audit_typed "
        "call with action='closing_period_confirmed'."
    )


def test_closing_period_blocked_emitted_by_service() -> None:
    """closing_period_blocked MUST be emitted by closing_period_service.

    Call site: `_emit_audit_blocked` in
    `apps/api/modules/m4_inventory/services/closing_period_service.py`.
    """
    src = _read(_CLOSING_PERIOD_SERVICE)
    matches = _audit_emit_calls(src, "closing_period_blocked")
    assert matches, (
        "3-way drift: `closing_period_blocked` is registered but NOT "
        "emitted by closing_period_service. Fix: add emit_audit_typed "
        "call with action='closing_period_blocked'."
    )


def test_closing_period_snapshot_inconsistency_emitted_by_v4_verifier() -> None:
    """closing_period_snapshot_inconsistency MUST be emitted by V4 verifier.

    Call site: `ClosingPeriodSnapshotVerifier.verify_v4_closing_period_consistency`
    in `apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py`.
    CR 6-1 R4 patch D4: audit-first emit BEFORE raise (CR 1.1 invariant).
    """
    src = _read(_V4_VERIFIER)
    matches = _audit_emit_calls(src, "closing_period_snapshot_inconsistency")
    assert matches, (
        "3-way drift: `closing_period_snapshot_inconsistency` is "
        "registered but NOT emitted by the V4 verifier. Fix: add "
        "emit_audit_typed call with action='closing_period_snapshot_inconsistency' "
        "BEFORE raising ClosingPeriodSnapshotInconsistencyError."
    )


def test_closing_period_no_orphan_emits_in_call_sites() -> None:
    """closing_period_* emit count == registered set (no orphan / dead-letter).

    Walks both source files and confirms no unregistered closing_period_*
    action is emitted (CR 1.1 — free-form string drift is forbidden).
    """
    accepted = set(_ActionRegistry._REGISTRY[ActionClass.CLOSING_PERIOD][1])
    pattern = re.compile(
        r"emit_audit_typed\([^)]*?action\s*=\s*[\"'](closing_period_[a-z_]+)[\"']",
        re.DOTALL,
    )
    found: set[str] = set()
    for path in (_CLOSING_PERIOD_SERVICE, _V4_VERIFIER):
        src = _read(path)
        for m in pattern.finditer(src):
            found.add(m.group(1))
    # All found actions MUST be in the registry.
    orphans = found - accepted
    assert not orphans, (
        f"3-way drift: call sites emit unregistered closing_period_* "
        f"actions: {sorted(orphans)}. Add to "
        f"ActionClass.CLOSING_PERIOD Literal + registry."
    )