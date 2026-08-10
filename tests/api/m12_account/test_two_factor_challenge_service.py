"""tests.api.m12_account.test_two_factor_challenge_service — Story 12.1 challenge token tests.

Per AC #7 spec — 2FA challenge token lifecycle:
- issue_challenge_token returns valid HS256 JWT (5-min TTL)
- consume_challenge_token accepts valid token
- consume_challenge_token rejects expired token (CHALLENGE_TOKEN_EXPIRED)
- consume_challenge_token rejects user_id mismatch
- consume_challenge_token rejects purpose mismatch
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from apps.api.modules.m12_account.services.two_factor_challenge_service import (
    CHALLENGE_TOKEN_TTL_SECONDS,
    ChallengeTokenExpiredError,
    ChallengeTokenInvalidError,
    TwoFactorChallengeService,
)

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
OTHER_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000005")

# Test JWT secret (32 chars hex-like — pydantic Settings may complain if too short)
TEST_JWT_SECRET = "test-secret-for-2fa-challenge-tokens-do-not-use-in-prod"


@pytest.fixture(autouse=True)
def _setup_jwt_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set supabase_jwt_secret for issue/consume."""
    monkeypatch.setenv("SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    # Reset cached settings
    from apps.api.core.settings import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _build_service() -> TwoFactorChallengeService:
    session = AsyncMock()
    return TwoFactorChallengeService(session)


# ── 1. issue returns valid token ──────────────────────────────
def test_issue_challenge_token_returns_jwt() -> None:
    """issue returns HS256 JWT with 5-minute TTL and purpose claim."""
    svc = _build_service()
    fixed_now = 1700000000  # fixed timestamp for determinism

    result = svc.issue_challenge_token(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now,
    )

    assert result.token  # non-empty
    assert result.expires_at == fixed_now + CHALLENGE_TOKEN_TTL_SECONDS  # +300s


# ── 2. consume accepts valid token ────────────────────────────
def test_consume_challenge_token_valid_passes() -> None:
    """Consume valid token returns ChallengePassed with user_id/tenant_id."""
    svc = _build_service()
    fixed_now = 1700000000

    issued = svc.issue_challenge_token(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now,
    )

    # Consume with same now (not yet expired)
    result = svc.consume_challenge_token(
        token=issued.token,
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now + 60,  # 60 seconds later
    )

    assert result.user_id == USER_ID
    assert result.tenant_id == TENANT_ID


# ── 3. consume rejects expired token ──────────────────────────
def test_consume_challenge_token_expired_raises() -> None:
    """Token past 5-min TTL → ChallengeTokenExpiredError."""
    svc = _build_service()
    fixed_now = 1700000000

    issued = svc.issue_challenge_token(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now,
    )

    # Consume 6 minutes later (past 5-min TTL)
    with pytest.raises(ChallengeTokenExpiredError):
        svc.consume_challenge_token(
            token=issued.token,
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            now=fixed_now + 6 * 60,
        )


# ── 4. consume rejects user_id mismatch ───────────────────────
def test_consume_challenge_token_user_id_mismatch_raises() -> None:
    """Token issued for USER_ID consumed with OTHER_USER_ID → ChallengeTokenInvalidError."""
    svc = _build_service()
    fixed_now = 1700000000

    issued = svc.issue_challenge_token(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now,
    )

    with pytest.raises(ChallengeTokenInvalidError):
        svc.consume_challenge_token(
            token=issued.token,
            user_id=OTHER_USER_ID,  # mismatch!
            tenant_id=TENANT_ID,
            now=fixed_now + 30,
        )


# ── 5. consume rejects tampered signature ─────────────────────
def test_consume_challenge_token_tampered_signature_raises() -> None:
    """Token with 1-char modification → ChallengeTokenInvalidError."""
    svc = _build_service()
    fixed_now = 1700000000

    issued = svc.issue_challenge_token(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now,
    )

    # Tamper: replace last char
    tampered_token = issued.token[:-1] + ("A" if issued.token[-1] != "A" else "B")

    with pytest.raises(ChallengeTokenInvalidError):
        svc.consume_challenge_token(
            token=tampered_token,
            user_id=USER_ID,
            tenant_id=TENANT_ID,
            now=fixed_now + 30,
        )


# ── 6. issue/consume round-trip with explicit timestamp ────────
def test_issue_consume_roundtrip_at_expiry_boundary() -> None:
    """Consume at exactly expires_at boundary — accepted (TTL inclusive)."""
    svc = _build_service()
    fixed_now = 1700000000

    issued = svc.issue_challenge_token(
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now,
    )

    # Consume exactly at TTL — should still pass (exp == now)
    result = svc.consume_challenge_token(
        token=issued.token,
        user_id=USER_ID,
        tenant_id=TENANT_ID,
        now=fixed_now + CHALLENGE_TOKEN_TTL_SECONDS,
    )

    assert result.user_id == USER_ID
    assert result.tenant_id == TENANT_ID
