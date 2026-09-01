"""packages.services.m12_account.two_factor_gate — Story 12.1 2FA gate pure kernel.

AD-11 layer rule: pure-Python, stdlib-only, NO DB, NO clock at module
level. Service layer (`apps/api/modules/m12_account/services/`) is
responsible for fetching user/membership and calling these helpers.

Gate logic:
1. `check_two_factor_required(user, membership, target)` — boolean check
2. `enforce_two_factor_gate(...)` — raises TwoFactorRequiredError
3. `enforce_role_gate(membership, target)` — AD-10 4-role gate (raises ForbiddenRoleError)
4. `lockout_status(user, now)` — bool check (lockout active or not)

PRD §F12.1 + §M12-a — 2FA 미설정 시 [월 입력] (M2) 진입 차단.

Korean constants — AD-15 §11 SSOT.
"""

from __future__ import annotations

from typing import Final, NamedTuple

from packages.services.m12_account.totp import (
    LOCKOUT_DURATION_SECONDS,
    MAX_FAILED_ATTEMPTS,
    TotpLockoutError,
)

# ── Constants ────────────────────────────────────────────────
# AD-10 4-role values (per apps/api/alembic/versions/0001_tenants_users_memberships_settings.py:38)
ALLOWED_M2_ROLES: Final[frozenset[str]] = frozenset({"owner", "member"})
READONLY_ROLES: Final[frozenset[str]] = frozenset({"viewer", "consultant_proxy"})

# M2 entry target identifier
TARGET_M2_INPUT: Final[str] = "m2_input"

# Error codes (AD-15 §4 envelope contract)
ERROR_CODE_TWO_FACTOR_REQUIRED: Final[str] = "TWO_FACTOR_REQUIRED"
ERROR_CODE_FORBIDDEN_ROLE: Final[str] = "FORBIDDEN_ROLE"

# Korean constants — AD-15 §11 SSOT
TWO_FACTOR_REQUIRED_KO: Final[str] = "2FA 설정이 필요합니다 — [설정하기]"
TWO_FACTOR_REQUIRED_REASON_KO: Final[str] = "[월 입력] 화면은 2FA 등록 후에만 진입 가능합니다"
FORBIDDEN_ROLE_KO: Final[str] = "권한이 없습니다 — owner/member role만 진입 가능합니다"
FORBIDDEN_ROLE_VIEWER_KO: Final[str] = "viewer role은 [월 입력] 화면 진입 불가 — 읽기 전용"
FORBIDDEN_ROLE_CONSULTANT_KO: Final[str] = (
    "consultant_proxy role은 [월 입력] 화면 진입 불가 — 읽기 전용"
)
LOCKOUT_ACTIVE_KO: Final[str] = f"5회 연속 실패 — {LOCKOUT_DURATION_SECONDS // 60}분간 잠금"


# ── Typed user / membership inputs ─────────────────────────────
class UserTotpState(NamedTuple):
    """Pure-kernel view of user's TOTP state (caller fetches from DB).

    Attributes:
        user_id: UUID.
        totp_secret_set: True if TOTP secret registered
            (users.totp_secret IS NOT NULL).
        totp_enabled_at: Unix timestamp of TOTP enable, or 0 if not set.
        failed_attempts: Current failed_attempts count.
        lockout_until: Unix timestamp of lockout end, or 0 if not locked.
    """

    user_id: str
    totp_secret_set: bool
    totp_enabled_at: int
    failed_attempts: int
    lockout_until: int


class MembershipRoleState(NamedTuple):
    """Pure-kernel view of user's tenant membership (caller fetches from DB).

    Attributes:
        user_id: UUID.
        tenant_id: UUID.
        role: One of "owner" / "member" / "viewer" / "consultant_proxy".
    """

    user_id: str
    tenant_id: str
    role: str


# ── Typed exceptions ──────────────────────────────────────────
class TwoFactorRequiredError(Exception):
    """Pure-kernel 2FA gate violation — user must register TOTP first.

    HTTP envelope (AD-15 §4): 403 TWO_FACTOR_REQUIRED + actionable message.
    """

    def __init__(
        self,
        message_ko: str = TWO_FACTOR_REQUIRED_KO,
        *,
        target: str = TARGET_M2_INPUT,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_TWO_FACTOR_REQUIRED
        self.target = target
        super().__init__(message_ko)


class ForbiddenRoleError(Exception):
    """Pure-kernel AD-10 role gate violation.

    HTTP envelope (AD-15 §4): 403 FORBIDDEN_ROLE.
    """

    def __init__(
        self,
        message_ko: str = FORBIDDEN_ROLE_KO,
        *,
        role: str,
        target: str = TARGET_M2_INPUT,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_FORBIDDEN_ROLE
        self.role = role
        self.target = target
        super().__init__(message_ko)


# ── Gate logic ────────────────────────────────────────────────
def check_two_factor_required(
    user: UserTotpState,
    target: str = TARGET_M2_INPUT,
) -> bool:
    """Check if 2FA is required for target entry.

    Returns True if:
    - target is M2 entry (TARGET_M2_INPUT) AND
    - user has not registered TOTP (totp_secret_set is False)

    Args:
        user: UserTotpState (caller fetches from DB).
        target: Target route identifier (default "m2_input").

    Returns:
        True if 2FA gate should block. False otherwise.
    """
    if target != TARGET_M2_INPUT:
        # Future-proofing: 다른 target은 2FA gate 적용 안 함
        return False
    return not user.totp_secret_set


def enforce_two_factor_gate(
    user: UserTotpState,
    target: str = TARGET_M2_INPUT,
) -> None:
    """Enforce 2FA gate — raises TwoFactorRequiredError if required.

    Args:
        user: UserTotpState (caller fetches from DB).
        target: Target route identifier.

    Raises:
        TwoFactorRequiredError: If 2FA gate blocks target entry.
    """
    if check_two_factor_required(user, target=target):
        raise TwoFactorRequiredError(
            TWO_FACTOR_REQUIRED_KO,
            target=target,
        )


def enforce_role_gate(
    membership: MembershipRoleState,
    target: str = TARGET_M2_INPUT,
) -> None:
    """Enforce AD-10 4-role gate for target entry.

    M2 entry target: owner/member만 허용 (PRD §F12.1 + §AD-10).

    Args:
        membership: MembershipRoleState (caller fetches from DB).
        target: Target route identifier.

    Raises:
        ForbiddenRoleError: If role not in {owner, member}.
    """
    if target != TARGET_M2_INPUT:
        # Future-proofing: 다른 target은 role gate 적용 안 함
        return
    role = membership.role
    if role in READONLY_ROLES:
        if role == "viewer":
            raise ForbiddenRoleError(FORBIDDEN_ROLE_VIEWER_KO, role=role, target=target)
        if role == "consultant_proxy":
            raise ForbiddenRoleError(FORBIDDEN_ROLE_CONSULTANT_KO, role=role, target=target)
    if role not in ALLOWED_M2_ROLES:
        # Unknown role → fail-closed
        raise ForbiddenRoleError(FORBIDDEN_ROLE_KO, role=role, target=target)


def lockout_status(user: UserTotpState, *, now: int) -> bool:
    """Check if user is in 2FA lockout window.

    Lockout: failed_attempts ≥ MAX_FAILED_ATTEMPTS AND
             now < lockout_until.

    Args:
        user: UserTotpState (caller fetches from DB).
        now: Unix timestamp (caller-controlled for testability).

    Returns:
        True if lockout is active. False otherwise.
    """
    if user.failed_attempts < MAX_FAILED_ATTEMPTS:
        return False
    if user.lockout_until <= 0:
        return False
    return now < user.lockout_until


def raise_if_locked(user: UserTotpState, *, now: int) -> None:
    """Raise TotpLockoutError if user is locked out.

    Service-layer wrapper — converts lockout_status bool check to exception.

    Args:
        user: UserTotpState (caller fetches from DB).
        now: Unix timestamp (caller-controlled for testability).

    Raises:
        TotpLockoutError: If lockout active. retry_after_seconds set.
    """
    if lockout_status(user, now=now):
        retry_after = max(0, user.lockout_until - now)
        raise TotpLockoutError(
            LOCKOUT_ACTIVE_KO,
            retry_after_seconds=retry_after,
        )


__all__ = [
    # constants
    "ALLOWED_M2_ROLES",
    "READONLY_ROLES",
    "TARGET_M2_INPUT",
    "ERROR_CODE_TWO_FACTOR_REQUIRED",
    "ERROR_CODE_FORBIDDEN_ROLE",
    "TWO_FACTOR_REQUIRED_KO",
    "TWO_FACTOR_REQUIRED_REASON_KO",
    "FORBIDDEN_ROLE_KO",
    "FORBIDDEN_ROLE_VIEWER_KO",
    "FORBIDDEN_ROLE_CONSULTANT_KO",
    "LOCKOUT_ACTIVE_KO",
    # result types
    "UserTotpState",
    "MembershipRoleState",
    # exceptions
    "TwoFactorRequiredError",
    "ForbiddenRoleError",
    # functions
    "check_two_factor_required",
    "enforce_two_factor_gate",
    "enforce_role_gate",
    "lockout_status",
    "raise_if_locked",
]
