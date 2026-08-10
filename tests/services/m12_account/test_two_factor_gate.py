"""tests.services.m12_account.test_two_factor_gate — T1.2 pure gate logic tests.

Coverage:
- check_two_factor_required boolean check
- enforce_two_factor_gate raises TwoFactorRequiredError
- enforce_role_gate AD-10 4-role gate (owner/member vs viewer/consultant_proxy)
- lockout_status bool + raise_if_locked raises TotpLockoutError
"""

from __future__ import annotations

import pytest

from packages.services.m12_account.totp import (
    LOCKOUT_DURATION_SECONDS,
    MAX_FAILED_ATTEMPTS,
    TotpLockoutError,
)
from packages.services.m12_account.two_factor_gate import (
    ALLOWED_M2_ROLES,
    ERROR_CODE_FORBIDDEN_ROLE,
    ERROR_CODE_TWO_FACTOR_REQUIRED,
    FORBIDDEN_ROLE_CONSULTANT_KO,
    FORBIDDEN_ROLE_KO,
    FORBIDDEN_ROLE_VIEWER_KO,
    READONLY_ROLES,
    TARGET_M2_INPUT,
    TWO_FACTOR_REQUIRED_KO,
    ForbiddenRoleError,
    MembershipRoleState,
    TwoFactorRequiredError,
    UserTotpState,
    check_two_factor_required,
    enforce_role_gate,
    enforce_two_factor_gate,
    lockout_status,
    raise_if_locked,
)


# ── Fixtures ────────────────────────────────────────────────
@pytest.fixture
def user_with_totp() -> UserTotpState:
    """User with TOTP registered."""
    return UserTotpState(
        user_id="00000000-0000-0000-0000-000000000001",
        totp_secret_set=True,
        totp_enabled_at=1776019200,
        failed_attempts=0,
        lockout_until=0,
    )


@pytest.fixture
def user_without_totp() -> UserTotpState:
    """User without TOTP (new account)."""
    return UserTotpState(
        user_id="00000000-0000-0000-0000-000000000002",
        totp_secret_set=False,
        totp_enabled_at=0,
        failed_attempts=0,
        lockout_until=0,
    )


@pytest.fixture
def user_locked_out() -> UserTotpState:
    """User in lockout window."""
    return UserTotpState(
        user_id="00000000-0000-0000-0000-000000000003",
        totp_secret_set=True,
        totp_enabled_at=1776019200,
        failed_attempts=MAX_FAILED_ATTEMPTS,  # 5
        lockout_until=1776019200 + LOCKOUT_DURATION_SECONDS,  # +15min
    )


@pytest.fixture
def owner_membership() -> MembershipRoleState:
    return MembershipRoleState(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-0000000000aa",
        role="owner",
    )


@pytest.fixture
def member_membership() -> MembershipRoleState:
    return MembershipRoleState(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-0000000000aa",
        role="member",
    )


@pytest.fixture
def viewer_membership() -> MembershipRoleState:
    return MembershipRoleState(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-0000000000aa",
        role="viewer",
    )


@pytest.fixture
def consultant_membership() -> MembershipRoleState:
    return MembershipRoleState(
        user_id="00000000-0000-0000-0000-000000000001",
        tenant_id="00000000-0000-0000-0000-0000000000aa",
        role="consultant_proxy",
    )


# ── Test #1: check_two_factor_required ───────────────────────
class TestCheckTwoFactorRequired:
    """Boolean check — 2FA gate decision."""

    def test_user_without_totp_requires_2fa_for_m2(
        self, user_without_totp: UserTotpState
    ) -> None:
        """totp_secret_set=False + target='m2_input' → True."""
        assert check_two_factor_required(user_without_totp) is True

    def test_user_with_totp_passes_m2_gate(
        self, user_with_totp: UserTotpState
    ) -> None:
        """totp_secret_set=True → False (gate passed)."""
        assert check_two_factor_required(user_with_totp) is False

    def test_other_targets_skip_2fa_gate(
        self, user_without_totp: UserTotpState
    ) -> None:
        """Future-proofing: non-M2 targets skip 2FA gate."""
        assert check_two_factor_required(user_without_totp, target="some_other") is False


# ── Test #2: enforce_two_factor_gate ────────────────────────
class TestEnforceTwoFactorGate:
    """Raises TwoFactorRequiredError when gate triggers."""

    def test_user_without_totp_raises(
        self, user_without_totp: UserTotpState
    ) -> None:
        """RequiredError with target='m2_input'."""
        with pytest.raises(TwoFactorRequiredError) as exc_info:
            enforce_two_factor_gate(user_without_totp)
        assert exc_info.value.target == "m2_input"
        assert exc_info.value.error_code == ERROR_CODE_TWO_FACTOR_REQUIRED
        assert exc_info.value.message_ko == TWO_FACTOR_REQUIRED_KO

    def test_user_with_totp_passes_silently(
        self, user_with_totp: UserTotpState
    ) -> None:
        """No exception raised."""
        enforce_two_factor_gate(user_with_totp)  # no raise


# ── Test #3: enforce_role_gate (AD-10) ───────────────────────
class TestEnforceRoleGate:
    """AD-10 4-role gate — owner/member allowed, viewer/consultant_proxy denied."""

    def test_owner_allowed(self, owner_membership: MembershipRoleState) -> None:
        """owner role → no exception."""
        enforce_role_gate(owner_membership)  # no raise

    def test_member_allowed(self, member_membership: MembershipRoleState) -> None:
        """member role → no exception."""
        enforce_role_gate(member_membership)  # no raise

    def test_viewer_denied(self, viewer_membership: MembershipRoleState) -> None:
        """viewer → ForbiddenRoleError with viewer-specific message."""
        with pytest.raises(ForbiddenRoleError) as exc_info:
            enforce_role_gate(viewer_membership)
        assert exc_info.value.role == "viewer"
        assert exc_info.value.message_ko == FORBIDDEN_ROLE_VIEWER_KO

    def test_consultant_proxy_denied(self, consultant_membership: MembershipRoleState) -> None:
        """consultant_proxy → ForbiddenRoleError with consultant message."""
        with pytest.raises(ForbiddenRoleError) as exc_info:
            enforce_role_gate(consultant_membership)
        assert exc_info.value.role == "consultant_proxy"
        assert exc_info.value.message_ko == FORBIDDEN_ROLE_CONSULTANT_KO

    def test_unknown_role_fails_closed(self) -> None:
        """Unknown role → ForbiddenRoleError (fail-closed)."""
        membership = MembershipRoleState(
            user_id="x",
            tenant_id="y",
            role="super_admin",  # not in 4-role set
        )
        with pytest.raises(ForbiddenRoleError) as exc_info:
            enforce_role_gate(membership)
        assert exc_info.value.role == "super_admin"
        assert exc_info.value.message_ko == FORBIDDEN_ROLE_KO

    def test_other_targets_skip_role_gate(self) -> None:
        """Future-proofing: non-M2 targets skip role gate."""
        membership = MembershipRoleState(
            user_id="x",
            tenant_id="y",
            role="viewer",
        )
        enforce_role_gate(membership, target="some_other")  # no raise


# ── Test #4: lockout_status + raise_if_locked ─────────────────
class TestLockoutStatus:
    """PRD §F12.1 — 5회 실패 + 15분 lockout."""

    def test_no_failed_attempts_not_locked(self, user_with_totp: UserTotpState) -> None:
        """failed_attempts=0 → not locked."""
        assert lockout_status(user_with_totp, now=1776019200) is False

    def test_below_threshold_not_locked(self) -> None:
        """failed_attempts=4 (below MAX) → not locked even if lockout_until set."""
        user = UserTotpState(
            user_id="x",
            totp_secret_set=True,
            totp_enabled_at=1776019200,
            failed_attempts=MAX_FAILED_ATTEMPTS - 1,  # 4
            lockout_until=1776019200 + 600,  # future
        )
        assert lockout_status(user, now=1776019200) is False

    def test_at_threshold_with_future_lockout_is_locked(self, user_locked_out: UserTotpState) -> None:
        """failed_attempts=5 + lockout_until > now → locked."""
        now = 1776019200  # lockout ends at +900s
        assert lockout_status(user_locked_out, now=now) is True

    def test_at_threshold_with_expired_lockout_not_locked(self) -> None:
        """failed_attempts=5 + lockout_until ≤ now → not locked."""
        user = UserTotpState(
            user_id="x",
            totp_secret_set=True,
            totp_enabled_at=1776019200,
            failed_attempts=MAX_FAILED_ATTEMPTS,
            lockout_until=1776019200 - 1,  # past
        )
        assert lockout_status(user, now=1776019200) is False

    def test_lockout_until_zero_means_unlocked(self) -> None:
        """lockout_until=0 → not locked regardless of failed_attempts."""
        user = UserTotpState(
            user_id="x",
            totp_secret_set=True,
            totp_enabled_at=1776019200,
            failed_attempts=MAX_FAILED_ATTEMPTS,
            lockout_until=0,
        )
        assert lockout_status(user, now=1776019200) is False


class TestRaiseIfLocked:
    """raise_if_locked — converts bool check to typed exception."""

    def test_locked_user_raises_with_retry_after(self, user_locked_out: UserTotpState) -> None:
        """Locked → TotpLockoutError with retry_after_seconds = lockout_until - now."""
        now = 1776019200
        with pytest.raises(TotpLockoutError) as exc_info:
            raise_if_locked(user_locked_out, now=now)
        expected_retry = user_locked_out.lockout_until - now  # 900
        assert exc_info.value.retry_after_seconds == expected_retry

    def test_unlocked_user_passes_silently(self, user_with_totp: UserTotpState) -> None:
        """No exception."""
        raise_if_locked(user_with_totp, now=1776019200)  # no raise


# ── Test #5: Constants ───────────────────────────────────────
class TestGateConstants:
    """Verify constants match AD-10 4-role + PRD §F12.1 lockout."""

    def test_allowed_m2_roles(self) -> None:
        """owner + member = M2 진입 가능."""
        assert frozenset({"owner", "member"}) == ALLOWED_M2_ROLES

    def test_readonly_roles(self) -> None:
        """viewer + consultant_proxy = M2 진입 불가."""
        assert frozenset({"viewer", "consultant_proxy"}) == READONLY_ROLES

    def test_target_m2_input(self) -> None:
        """target identifier = 'm2_input'."""
        assert TARGET_M2_INPUT == "m2_input"

    def test_error_codes(self) -> None:
        """AD-15 §4 envelope error codes."""
        assert ERROR_CODE_TWO_FACTOR_REQUIRED == "TWO_FACTOR_REQUIRED"
        assert ERROR_CODE_FORBIDDEN_ROLE == "FORBIDDEN_ROLE"
