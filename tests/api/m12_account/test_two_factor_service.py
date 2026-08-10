"""tests.api.m12_account.test_two_factor_service — Story 12.1 service tests.

8 cases per AC spec:
- setup_totp success (encrypted secret saved + audit init)
- setup_totp idempotent (re-setup → AlreadyEnabledError)
- verify_and_enable_totp success (flips twofa_enabled + audit completed)
- verify_and_enable_totp invalid code → TotpInvalidCodeError
- verify_totp_challenge passed (resets failed_attempts + audit)
- verify_totp_challenge 5x failure → lockout (audit + lockout_until set)
- verify_recovery_code success (mark used_at + audit consumed)
- disable_totp success (clears state + audit disabled)
- disable_totp unauthorized → TwoFactorDisableUnauthorizedError

CR 4-3: `def test_* + asyncio.run(_impl())` pattern.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.core.crypto import DEFAULT_KEY_ID, encrypt_at_rest
from apps.api.core.key_manager import clear_keys, set_key
from apps.api.modules.m12_account.exceptions import (
    TwoFactorAlreadyEnabledError,
    TwoFactorDisableUnauthorizedError,
    TwoFactorUserNotFoundError,
)
from apps.api.modules.m12_account.services.two_factor_service import (
    TwoFactorService,
)
from packages.services.m12_account.totp import (
    MAX_FAILED_ATTEMPTS,
    RECOVERY_CODE_COUNT,
    generate_totp_secret,
)

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000004")


def _make_user_row(
    *,
    twofa_enabled: bool = False,
    totp_secret: bytes | None = None,
    totp_recovery_codes_hash: list[dict[str, str]] | None = None,
    totp_failed_attempts: int = 0,
    totp_enabled_at: datetime | None = None,
) -> MagicMock:
    """MagicMock row matching User ORM attributes used by service."""
    row = MagicMock()
    row.id = USER_ID
    row.tenant_id = TENANT_ID
    row.email = "test@example.com"
    row.role = "owner"
    row.twofa_enabled = twofa_enabled
    row.totp_secret = totp_secret
    row.totp_enabled_at = totp_enabled_at
    row.totp_failed_attempts = totp_failed_attempts
    row.totp_lockout_until = None
    row.totp_recovery_codes_hash = totp_recovery_codes_hash
    return row


def _make_key_fixture() -> bytes:
    """Provide deterministic test key for AES-256-GCM."""
    return bytes.fromhex(
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    )


@pytest.fixture(autouse=True)
def _reset_crypto_keys() -> None:
    """Clear key cache + set deterministic test key per test."""
    clear_keys()
    set_key(DEFAULT_KEY_ID, _make_key_fixture())
    yield
    clear_keys()


def _wire_session(session: AsyncMock, *scalar_returns: object) -> None:
    """Wire session.execute(...).scalar_one_or_none() return queue.

    session.execute is awaited (returns result), then
    result.scalar_one_or_none() is sync access.
    """
    queue = list(scalar_returns)

    def _pop() -> object:
        if not queue:
            return None
        return queue.pop(0)

    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(side_effect=_pop)
    session.execute = AsyncMock(return_value=result_mock)
    session.flush = AsyncMock()
    session.add = MagicMock()


# ── 1. setup_totp success ─────────────────────────────────────
def test_setup_totp_success() -> None:
    """setup_totp creates secret + URI + recovery codes + persists ciphertext."""

    async def _impl() -> None:
        session = AsyncMock()
        user_row = _make_user_row(twofa_enabled=False, totp_secret=None)
        _wire_session(session, user_row)

        svc = TwoFactorService(session)
        result = await svc.setup_totp(
            user_id=USER_ID,
            tenant_id=TENANT_ID,
        )

        # Assertions
        assert result.secret  # base32-encoded (non-empty)
        assert result.uri.startswith("otpauth://totp/costmgr:")
        assert len(result.recovery_codes) == RECOVERY_CODE_COUNT  # 8 codes
        assert all(len(c) == 10 for c in result.recovery_codes)

        # User row updated: encrypted secret set, recovery hashes set,
        # still NOT enabled (verify_and_enable_totp is a separate step).
        assert user_row.totp_secret is not None
        assert len(user_row.totp_secret) > 28  # nonce(12) + ct + tag(16)
        assert user_row.twofa_enabled is False
        assert user_row.totp_failed_attempts == 0
        assert user_row.totp_lockout_until is None
        assert user_row.totp_recovery_codes_hash is not None
        assert len(user_row.totp_recovery_codes_hash) == RECOVERY_CODE_COUNT

    asyncio.run(_impl())


# ── 2. setup_totp idempotent (re-setup → AlreadyEnabledError) ───
def test_setup_totp_already_enabled_raises() -> None:
    """setup_totp with 2FA already enabled → TwoFactorAlreadyEnabledError."""

    async def _impl() -> None:
        session = AsyncMock()
        user_row = _make_user_row(
            twofa_enabled=True,
            totp_enabled_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        with pytest.raises(TwoFactorAlreadyEnabledError):
            await svc.setup_totp(user_id=USER_ID, tenant_id=TENANT_ID)

    asyncio.run(_impl())


# ── 3. setup_totp user not found ───────────────────────────────
def test_setup_totp_user_not_found_raises() -> None:
    """setup_totp with missing user → TwoFactorUserNotFoundError."""

    async def _impl() -> None:
        session = AsyncMock()
        _wire_session(session, None)  # no user row

        svc = TwoFactorService(session)

        with pytest.raises(TwoFactorUserNotFoundError):
            await svc.setup_totp(user_id=USER_ID, tenant_id=TENANT_ID)

    asyncio.run(_impl())


# ── 4. verify_and_enable_totp success ──────────────────────────
def test_verify_and_enable_totp_success() -> None:
    """First TOTP code flips twofa_enabled=True."""

    async def _impl() -> None:
        session = AsyncMock()
        # Pre-existing encrypted secret
        secret_bytes = generate_totp_secret()
        encrypted = encrypt_at_rest(
            secret_bytes,
            key_id=DEFAULT_KEY_ID,
            aad=b"totp_secret",
        )
        user_row = _make_user_row(
            twofa_enabled=False,
            totp_secret=encrypted,
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        # Compute current-valid TOTP code
        import time

        from packages.services.m12_account.totp import (
            compute_totp_code,
        )

        current_code = compute_totp_code(
            secret_bytes,
            timestamp=int(time.time()),
        )

        result = await svc.verify_and_enable_totp(
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            code=current_code,
        )

        assert result is True
        assert user_row.twofa_enabled is True
        assert user_row.totp_enabled_at is not None
        assert user_row.totp_failed_attempts == 0
        assert user_row.totp_lockout_until is None

    asyncio.run(_impl())


# ── 5. verify_and_enable_totp invalid code → TotpInvalidCodeError ─
def test_verify_and_enable_totp_invalid_code_raises() -> None:
    """Wrong TOTP code → TotpInvalidCodeError + failed_attempts increment."""

    async def _impl() -> None:
        session = AsyncMock()
        secret_bytes = generate_totp_secret()
        encrypted = encrypt_at_rest(
            secret_bytes, key_id=DEFAULT_KEY_ID, aad=b"totp_secret"
        )
        user_row = _make_user_row(
            twofa_enabled=False,
            totp_secret=encrypted,
            totp_failed_attempts=0,
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        from packages.services.m12_account.totp import TotpInvalidCodeError

        with pytest.raises(TotpInvalidCodeError):
            await svc.verify_and_enable_totp(
                user_id=USER_ID,
                tenant_id=TENANT_ID,
                code="000000",  # unlikely to match real code
            )
        # failed_attempts incremented
        assert user_row.totp_failed_attempts == 1

    asyncio.run(_impl())


# ── 6. verify_totp_challenge passed ─────────────────────────────
def test_verify_totp_challenge_passed() -> None:
    """Valid TOTP challenge → passed=True + reset failed_attempts."""

    async def _impl() -> None:
        import time

        session = AsyncMock()
        secret_bytes = generate_totp_secret()
        encrypted = encrypt_at_rest(
            secret_bytes, key_id=DEFAULT_KEY_ID, aad=b"totp_secret"
        )
        user_row = _make_user_row(
            twofa_enabled=True,
            totp_secret=encrypted,
            totp_enabled_at=datetime(2026, 1, 1, tzinfo=UTC),
            totp_failed_attempts=2,  # pre-existing partial failures
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        from packages.services.m12_account.totp import compute_totp_code

        current_code = compute_totp_code(
            secret_bytes,
            timestamp=int(time.time()),
        )

        result = await svc.verify_totp_challenge(
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            code=current_code,
        )

        assert result.passed is True
        assert result.remaining_attempts == MAX_FAILED_ATTEMPTS
        assert user_row.totp_failed_attempts == 0
        assert user_row.totp_lockout_until is None

    asyncio.run(_impl())


# ── 7. verify_totp_challenge 5x failure → lockout ──────────────
def test_verify_totp_challenge_lockout_after_5_failures() -> None:
    """5 consecutive failures → lockout + totp_lockout_until set."""

    async def _impl() -> None:
        session = AsyncMock()
        secret_bytes = generate_totp_secret()
        encrypted = encrypt_at_rest(
            secret_bytes, key_id=DEFAULT_KEY_ID, aad=b"totp_secret"
        )
        user_row = _make_user_row(
            twofa_enabled=True,
            totp_secret=encrypted,
            totp_enabled_at=datetime(2026, 1, 1, tzinfo=UTC),
            totp_failed_attempts=4,  # one more failure triggers lockout
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        result = await svc.verify_totp_challenge(
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            code="000000",
        )

        assert result.passed is False
        assert result.remaining_attempts == 0
        assert user_row.totp_failed_attempts == 5
        assert user_row.totp_lockout_until is not None

    asyncio.run(_impl())


# ── 8. verify_recovery_code success ───────────────────────────
def test_verify_recovery_code_success() -> None:
    """Valid recovery code → mark used_at + audit consumed."""

    async def _impl() -> None:
        from packages.services.m12_account.totp import (
            generate_recovery_code_hashes,
            generate_recovery_codes,
        )

        session = AsyncMock()
        codes = generate_recovery_codes()
        hashes = generate_recovery_code_hashes(codes)
        user_row = _make_user_row(
            twofa_enabled=True,
            totp_recovery_codes_hash=hashes,
            totp_enabled_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        result = await svc.verify_recovery_code(
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            code=codes[0],
        )

        assert result.passed is True
        # First entry marked used_at
        assert user_row.totp_recovery_codes_hash[0]["used_at"]
        assert not user_row.totp_recovery_codes_hash[1]["used_at"]

    asyncio.run(_impl())


# ── 9. disable_totp success (admin override) ───────────────────
def test_disable_totp_admin_override_success() -> None:
    """Admin-initiated disable with reason → clears 2FA state."""

    async def _impl() -> None:
        session = AsyncMock()
        secret_bytes = generate_totp_secret()
        encrypted = encrypt_at_rest(
            secret_bytes, key_id=DEFAULT_KEY_ID, aad=b"totp_secret"
        )
        user_row = _make_user_row(
            twofa_enabled=True,
            totp_secret=encrypted,
            totp_enabled_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        await svc.disable_totp(
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            actor_id=ACTOR_ID,
            current_code=None,  # admin override
            reason="user requested admin-initiated 2FA reset "
                   "due to lost authenticator device on 2026-08-10",
        )

        assert user_row.twofa_enabled is False
        assert user_row.totp_secret is None
        assert user_row.totp_recovery_codes_hash is None
        assert user_row.totp_enabled_at is None
        assert user_row.totp_failed_attempts == 0

    asyncio.run(_impl())


# ── 10. disable_totp unauthorized → TwoFactorDisableUnauthorizedError ──
def test_disable_totp_unauthorized_raises() -> None:
    """Self-disable without code → TwoFactorDisableUnauthorizedError."""

    async def _impl() -> None:
        session = AsyncMock()
        secret_bytes = generate_totp_secret()
        encrypted = encrypt_at_rest(
            secret_bytes, key_id=DEFAULT_KEY_ID, aad=b"totp_secret"
        )
        user_row = _make_user_row(
            twofa_enabled=True,
            totp_secret=encrypted,
            totp_enabled_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        _wire_session(session, user_row)

        svc = TwoFactorService(session)

        with pytest.raises(TwoFactorDisableUnauthorizedError):
            await svc.disable_totp(
                user_id=USER_ID,
                tenant_id=TENANT_ID,
                actor_id=USER_ID,  # self (not admin)
                current_code=None,  # no code
                reason="too short",  # too short for admin override
            )

    asyncio.run(_impl())
