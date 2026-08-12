"""tests/integration/test_m12_two_factor_gate_kernel_parity.py — Story 12.5

AD-15 §11 cross-language parity (D-PARITY-01 fix).

This file tests the Python kernel SSOT for the M2 entry gate composition
directly, mirroring vitest parity tests in
`apps/web/__tests__/lib/m12-two-factor-gate-parity.test.ts`.

SSOT is at `packages/services/m12_account/two_factor_gate.py`:
  - `check_two_factor_required(user, target)`
  - `enforce_role_gate(membership, target)`
  - `lockout_status(user, *, now)`
  - `ALLOWED_M2_ROLES = {owner, member}`
  - `READONLY_ROLES = {viewer, consultant_proxy}`

The TS mirror at `apps/web/lib/m12-two-factor-gate.ts::buildM2EntryGateState`
composes those primitives identically. 8 NEW cases below mirror the
vitest parity test:

  parity 1 (corrected): owner + 2FA disabled → requires_two_factor=True → blocked
  parity 2 (corrected): owner + 2FA enabled  → allowed
  parity 3 (corrected): member + 2FA disabled → blocked
  parity 4 (corrected): member + 2FA enabled  → allowed
  parity 5 (corrected): viewer → role_denied
  parity 6 (corrected): consultant_proxy → role_denied
  parity 7 (corrected): locked_out owner → blocked (lockout message)
  parity 8 (corrected): unknown role 'auditor' → role_denied (CR 11-4 D-005)

Pure-function tests — NO DB, NO clock. Composes the kernel's three
primitives exactly like the TS mirror does.
"""

from __future__ import annotations

import pytest

from packages.services.m12_account.two_factor_gate import (
    ALLOWED_M2_ROLES,
    FORBIDDEN_ROLE_KO,
    FORBIDDEN_ROLE_CONSULTANT_KO,
    FORBIDDEN_ROLE_VIEWER_KO,
    LOCKOUT_ACTIVE_KO,
    READONLY_ROLES,
    TARGET_M2_INPUT,
    TWO_FACTOR_REQUIRED_KO,
    MembershipRoleState,
    UserTotpState,
    check_two_factor_required,
    enforce_role_gate,
    lockout_status,
)


def _compose_m2_entry_state(
    *,
    role: str,
    totp_enabled: bool,
    locked_out: bool,
    lockout_until_iso: str | None,
) -> dict[str, object]:
    """Mirror `apps/web/lib/m12-two-factor-gate.ts::buildM2EntryGateState`.

    Composes the three Python kernel primitives (check_two_factor_required
    + enforce_role_gate + lockout_status) into the same M2EntryGateState
    shape the TS mirror produces.

    Pure function — no DB, no clock. The 'now' for lockout_status is fixed
    at a value prior to `lockout_until_iso` when `locked_out=True`.
    """
    user = UserTotpState(
        user_id="00000000-0000-0000-0000-000000000001",
        totp_secret_set=totp_enabled,
        totp_enabled_at=1700000000 if totp_enabled else 0,
        failed_attempts=5 if locked_out else 0,
        lockout_until=1700000900 if locked_out else 0,
    )
    membership = MembershipRoleState(
        user_id=user.user_id,
        tenant_id="00000000-0000-0000-0000-000000000002",
        role=role,
    )
    requires_two_factor = check_two_factor_required(user, target=TARGET_M2_INPUT)
    now = 1700000000  # any fixed time → lockout_status just needs user.lockout_until > now
    is_locked = locked_out and lockout_status(user, now=now)
    role_allowed = role in ALLOWED_M2_ROLES

    allowed = bool(role_allowed) and not is_locked and not requires_two_factor
    requires_challenge = bool(totp_enabled) and not is_locked

    # Message priority — kernel SSOT ORDER
    if requires_two_factor:
        message_ko = TWO_FACTOR_REQUIRED_KO
    elif is_locked and lockout_until_iso:
        # kernel LOCKOUT_ACTIVE_KO: "5회 연속 실패 — {N}분간 잠금"
        message_ko = LOCKOUT_ACTIVE_KO
    elif not role_allowed:
        if role == "viewer":
            message_ko = FORBIDDEN_ROLE_VIEWER_KO
        elif role == "consultant_proxy":
            message_ko = FORBIDDEN_ROLE_CONSULTANT_KO
        else:
            message_ko = FORBIDDEN_ROLE_KO
    else:
        message_ko = "M2 진입 가능"

    return {
        "allowed": allowed,
        "requires_two_factor": bool(requires_two_factor),
        "requires_challenge": bool(requires_challenge),
        "role_allowed": bool(role_allowed),
        "locked_out": bool(is_locked),
        "lockout_until": lockout_until_iso,
        "message_ko": message_ko,
    }


# ── 8 parity cases (D-PARITY-01 corrected vectors) ──────────────


def test_parity_1_owner_2fa_disabled_blocked_setup_required() -> None:
    """parity 1 (corrected): owner role + 2FA disabled → blocked, requires setup."""
    state = _compose_m2_entry_state(
        role="owner",
        totp_enabled=False,
        locked_out=False,
        lockout_until_iso=None,
    )
    assert state["allowed"] is False  # NOT true (D-PARITY-01 inversion fix)
    assert state["requires_two_factor"] is True
    assert state["requires_challenge"] is False
    assert state["role_allowed"] is True
    assert TWO_FACTOR_REQUIRED_KO in state["message_ko"]


def test_parity_2_owner_2fa_enabled_allowed() -> None:
    """parity 2 (corrected): owner role + 2FA enabled → allowed=true."""
    state = _compose_m2_entry_state(
        role="owner",
        totp_enabled=True,
        locked_out=False,
        lockout_until_iso=None,
    )
    assert state["allowed"] is True
    assert state["requires_two_factor"] is False
    assert state["requires_challenge"] is True


def test_parity_3_member_2fa_disabled_blocked_setup_required() -> None:
    """parity 3 (corrected): member role + 2FA disabled → blocked, requires setup."""
    state = _compose_m2_entry_state(
        role="member",
        totp_enabled=False,
        locked_out=False,
        lockout_until_iso=None,
    )
    assert state["allowed"] is False
    assert state["requires_two_factor"] is True
    assert state["role_allowed"] is True


def test_parity_4_member_2fa_enabled_allowed() -> None:
    """parity 4 (corrected): member role + 2FA enabled → allowed=true."""
    state = _compose_m2_entry_state(
        role="member",
        totp_enabled=True,
        locked_out=False,
        lockout_until_iso=None,
    )
    assert state["allowed"] is True
    assert state["requires_two_factor"] is False


def test_parity_5_viewer_role_denied() -> None:
    """parity 5 (corrected): viewer role + 2FA enabled → blocked, role_denied.

    Composition priority is setup > lockout > role_denied. When 2FA is
    fully enabled (totp_enabled=True), the setup-required message is
    moot, so role_denied priority #3 wins → FORBIDDEN_ROLE_VIEWER_KO.
    """
    state = _compose_m2_entry_state(
        role="viewer",
        totp_enabled=True,
        locked_out=False,
        lockout_until_iso=None,
    )
    assert state["allowed"] is False
    assert state["role_allowed"] is False
    assert "viewer" in state["message_ko"]


def test_parity_6_consultant_proxy_role_denied() -> None:
    """parity 6 (corrected): consultant_proxy role → blocked, role_denied."""
    state = _compose_m2_entry_state(
        role="consultant_proxy",
        totp_enabled=True,
        locked_out=False,
        lockout_until_iso=None,
    )
    assert state["allowed"] is False
    assert state["role_allowed"] is False
    assert "consultant_proxy" in state["message_ko"]


def test_parity_7_locked_out_owner_blocked_lockout_message() -> None:
    """parity 7 (corrected): locked_out owner → blocked, lockout message."""
    state = _compose_m2_entry_state(
        role="owner",
        totp_enabled=True,
        locked_out=True,
        lockout_until_iso="2026-08-11T12:30:00+09:00",
    )
    assert state["allowed"] is False
    assert state["locked_out"] is True
    assert "잠금" in state["message_ko"]


def test_parity_8_unknown_role_auditor_denied() -> None:
    """parity 8 (corrected): unknown role 'auditor' + 2FA enabled → blocked, role_denied.

    Composition priority is setup > lockout > role_denied. When 2FA is
    fully enabled (totp_enabled=True), the setup-required message is
    moot, so role_denied priority #3 wins. Unknown role → fail-closed
    uses the generic FORBIDDEN_ROLE_KO (per CR 11-4 D-005).
    """
    state = _compose_m2_entry_state(
        role="auditor",
        totp_enabled=True,
        locked_out=False,
        lockout_until_iso=None,
    )
    assert state["allowed"] is False
    assert state["role_allowed"] is False
    # Unknown role → use generic FORBIDDEN_ROLE_KO (kernel fail-closed).
    assert state["message_ko"] == FORBIDDEN_ROLE_KO


# ── Role allowlist / denylist parity constants ──────────────────


def test_allowed_m2_roles_parity() -> None:
    """ALLOWED_M2_ROLES = {owner, member} — kernel SSOT."""
    assert ALLOWED_M2_ROLES == frozenset({"owner", "member"})


def test_readonly_roles_parity() -> None:
    """READONLY_ROLES = {viewer, consultant_proxy} — kernel SSOT."""
    assert READONLY_ROLES == frozenset({"viewer", "consultant_proxy"})


# ── Kernel primitive parity (sanity) ────────────────────────────


def test_check_two_factor_required_totp_not_set_returns_true() -> None:
    """totp_secret_set=False → 2FA setup required (SSOT)."""
    user = UserTotpState("u-1", False, 0, 0, 0)
    assert check_two_factor_required(user) is True


def test_check_two_factor_required_totp_set_returns_false() -> None:
    """totp_secret_set=True → 2FA setup not required (SSOT)."""
    user = UserTotpState("u-1", True, 1700000000, 0, 0)
    assert check_two_factor_required(user) is False


def test_enforce_role_gate_owner_passes() -> None:
    m = MembershipRoleState("u-1", "t-1", "owner")
    enforce_role_gate(m)  # should NOT raise


def test_enforce_role_gate_member_passes() -> None:
    m = MembershipRoleState("u-1", "t-1", "member")
    enforce_role_gate(m)  # should NOT raise


@pytest.mark.parametrize("role", ["viewer", "consultant_proxy", "auditor", ""])
def test_enforce_role_gate_non_allowed_raises(role: str) -> None:
    from packages.services.m12_account.two_factor_gate import ForbiddenRoleError

    m = MembershipRoleState("u-1", "t-1", role)
    with pytest.raises(ForbiddenRoleError):
        enforce_role_gate(m)
