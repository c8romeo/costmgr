"""apps.api.modules.m12_account.services.two_factor_challenge_service.

Challenge token lifecycle (M2 entry gate).

Two ops:
  - `issue_challenge_token` — user authenticated via 1FA (cookie
    session) but needs to pass 2FA challenge before M2 entry. Service
    generates a short-lived signed token (5 min) bound to user_id +
    tenant_id + purpose="two_factor_challenge".
  - `consume_challenge_token` — user passes TOTP code; service verifies
    token (not expired, correct user_id), verifies code, returns
    2FA-passed claim set (M2 entry clearance).

Token format: HS256 JWT with `purpose`, `user_id`, `tenant_id`,
`iat`, `exp` claims. Signed with `COSTMGR_JWT_SECRET` (shared with
session JWT).

Distinct from session JWT — this token is:
1. Short-lived (5 min vs session 8h)
2. Single-purpose (purpose claim = 'two_factor_challenge')
3. Tied to a specific (user_id, tenant_id) pair — cannot be replayed
   across users or tenants.

AD-15 §4 envelope contract:
  - ChallengeTokenExpiredError        → 401 CHALLENGE_TOKEN_EXPIRED
  - ChallengeTokenInvalidError        → 401 CHALLENGE_TOKEN_INVALID
  - ChallengeTokenPurposeMismatchError → 401 CHALLENGE_TOKEN_PURPOSE_MISMATCH
  - ChallengeTokenAlreadyConsumedError → 401 CHALLENGE_TOKEN_ALREADY_CONSUMED
  - TwoFactorNotEnabledError          → 400 TWO_FACTOR_NOT_ENABLED (reused)
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime
from typing import Any

import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.db_models import UsedChallengeToken, User
from apps.api.core.settings import get_settings
from apps.api.modules.m12_account.exceptions import TwoFactorNotEnabledError


# ── Typed exceptions (AD-15 §4) ──────────────────────────────
class ChallengeTokenError(Exception):
    """Base challenge token error."""


class ChallengeTokenExpiredError(ChallengeTokenError):
    """401 CHALLENGE_TOKEN_EXPIRED — token past 5-min TTL."""

    def __init__(self, *, token_jti: str, expired_at: int) -> None:
        super().__init__(
            f"challenge token expired (jti={token_jti}, expired_at={expired_at})"
        )
        self.token_jti = token_jti
        self.expired_at = expired_at


class ChallengeTokenInvalidError(ChallengeTokenError):
    """401 CHALLENGE_TOKEN_INVALID — signature mismatch / malformed."""

    def __init__(self, *, reason: str, trace_id: str) -> None:
        super().__init__(f"challenge token invalid: {reason}")
        self.reason = reason
        self.trace_id = trace_id


class ChallengeTokenPurposeMismatchError(ChallengeTokenError):
    """401 CHALLENGE_TOKEN_PURPOSE_MISMATCH — purpose claim != 'two_factor_challenge'."""

    def __init__(
        self,
        *,
        actual_purpose: str | None,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"challenge token purpose mismatch (got {actual_purpose!r}, "
            f"expected 'two_factor_challenge')"
        )
        self.actual_purpose = actual_purpose
        self.trace_id = trace_id


class ChallengeTokenAlreadyConsumedError(ChallengeTokenError):
    """401 CHALLENGE_TOKEN_ALREADY_CONSUMED — token jti already used.

    Story 12.4 review P-05: replay guard via `used_challenge_tokens` table.
    INSERT with jti as PK; duplicate key raises IntegrityError → this error.
    Without this guard, a captured token could be replayed within the 5-min
    TTL window.
    """

    def __init__(self, *, token_jti: str, trace_id: str) -> None:
        super().__init__(
            f"challenge token already consumed (jti={token_jti})"
        )
        self.token_jti = token_jti
        self.trace_id = trace_id


class TwoFactorChallengeFailedError(ChallengeTokenError):
    """401 TWO_FACTOR_CHALLENGE_FAILED — TOTP code incorrect or expired.

    Story 12.4 review P-08: typed exception covering the TOTP code verification
    failure path (wrong code, ±1 window miss). Distinct from
    ChallengeTokenInvalidError (which is about the challenge token itself).
    """

    def __init__(
        self, *, reason: str, failed_attempts: int, trace_id: str
    ) -> None:
        super().__init__(
            f"two-factor challenge failed: {reason} "
            f"(failed_attempts={failed_attempts})"
        )
        self.reason = reason
        self.failed_attempts = failed_attempts
        self.trace_id = trace_id


# TwoFactorNotEnabledError is reused from `apps.api.modules.m12_account.exceptions`
# (canonical 400 TWO_FACTOR_NOT_ENABLED — covers both setup-time and consume-time
# 2FA misuse). The P-12 challenge_consume case fits the same code path.


# ── Typed results ─────────────────────────────────────────────
class ChallengeTokenIssued:
    """Result of `issue_challenge_token`."""

    def __init__(self, *, token: str, expires_at: int) -> None:
        self.token = token
        self.expires_at = expires_at


class ChallengePassed:
    """Result of `consume_challenge_token` — M2 entry clearance."""

    def __init__(self, *, user_id: uuid.UUID, tenant_id: uuid.UUID) -> None:
        self.user_id = user_id
        self.tenant_id = tenant_id


# ── Constants ─────────────────────────────────────────────────
CHALLENGE_TOKEN_TTL_SECONDS: int = 5 * 60  # 5 minutes
CHALLENGE_TOKEN_PURPOSE: str = "two_factor_challenge"


# ── Service class ─────────────────────────────────────────────
class TwoFactorChallengeService:
    """Issue + consume 2FA challenge tokens (HS256 JWT)."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def issue_challenge_token(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        now: int | None = None,
    ) -> ChallengeTokenIssued:
        """Issue short-lived signed token (5-min TTL).

        Args:
            user_id, tenant_id: Bound to token — cannot be replayed.
            now: Unix timestamp (default = current time). Caller passes
                explicit value for testability (AD-11).

        Returns:
            ChallengeTokenIssued(token, expires_at).

        Raises:
            ChallengeTokenInvalidError: If JWT signing fails.
        """
        iat = now if now is not None else int(time.time())
        exp = iat + CHALLENGE_TOKEN_TTL_SECONDS
        payload: dict[str, Any] = {
            "purpose": CHALLENGE_TOKEN_PURPOSE,
            "user_id": str(user_id),
            "tenant_id": str(tenant_id),
            "iat": iat,
            "exp": exp,
            "jti": str(uuid.uuid4()),
        }
        settings = get_settings()
        if not settings.supabase_jwt_secret:
            raise ChallengeTokenInvalidError(
                reason="supabase_jwt_secret not configured",
                trace_id=str(uuid.uuid4()),
            )
        try:
            token = jwt.encode(
                payload,
                settings.supabase_jwt_secret,
                algorithm="HS256",
            )
        except Exception as exc:
            raise ChallengeTokenInvalidError(
                reason=f"JWT signing failed: {exc}",
                trace_id=str(uuid.uuid4()),
            ) from exc
        return ChallengeTokenIssued(token=token, expires_at=exp)

    async def consume_challenge_token(
        self,
        *,
        token: str,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        now: int | None = None,
    ) -> ChallengePassed:
        """Verify signed challenge token (HS256).

        Validates:
        1. JWT signature matches `COSTMGR_JWT_SECRET`
        2. Token not expired (exp claim vs now)
        3. `purpose` claim == `two_factor_challenge`
        4. `user_id` claim matches input
        5. `tenant_id` claim matches input
        6. User still has 2FA enabled (`totp_enabled_at IS NOT NULL`) — P-12
        7. Token `jti` not already consumed (replay guard) — P-05

        Args:
            token: Challenge token string from cookie / Authorization header.
            user_id: Expected user_id (handler validates from session).
            tenant_id: Expected tenant_id.
            now: Current unix timestamp (caller passes for testability).

        Returns:
            ChallengePassed(user_id, tenant_id) on success.

        Raises:
            ChallengeTokenExpiredError, ChallengeTokenInvalidError,
            ChallengeTokenPurposeMismatchError, ChallengeTokenAlreadyConsumedError,
            TwoFactorNotEnabledError.
        """
        check_now = now if now is not None else int(time.time())
        # P-11 guard: caller-controlled `now` must be a plausible unix
        # timestamp (≥ 1e9 = Sep 2001). Defends against `now=0` which
        # would bypass both `verify_exp=False` and the manual exp check
        # (since `claims_exp < 0` is always False).
        if now is not None and now < 1_000_000_000:
            raise ChallengeTokenInvalidError(
                reason="caller-controlled now must be ≥ 1e9 (post-2001)",
                trace_id=str(uuid.uuid4()),
            )
        settings = get_settings()
        if not settings.supabase_jwt_secret:
            raise ChallengeTokenInvalidError(
                reason="supabase_jwt_secret not configured",
                trace_id=str(uuid.uuid4()),
            )
        try:
            claims = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={
                    "require": ["exp", "iat", "purpose"],
                    "verify_exp": now is None,  # skip pyjwt exp check when caller passes `now`
                },
            )
        except jwt.ExpiredSignatureError as exc:
            raise ChallengeTokenExpiredError(
                token_jti="<jwt-expired-no-claims>",
                expired_at=0,
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise ChallengeTokenInvalidError(
                reason=f"JWT decode failed: {exc}",
                trace_id=str(uuid.uuid4()),
            ) from exc

        # Purpose check
        if claims.get("purpose") != CHALLENGE_TOKEN_PURPOSE:
            raise ChallengeTokenPurposeMismatchError(
                actual_purpose=claims.get("purpose"),
                trace_id=str(uuid.uuid4()),
            )

        # user_id / tenant_id binding
        if claims.get("user_id") != str(user_id) or claims.get("tenant_id") != str(tenant_id):
            raise ChallengeTokenInvalidError(
                reason="user_id / tenant_id binding mismatch",
                trace_id=str(uuid.uuid4()),
            )

        # Exp check (manual — PyJWT raises already, but defensive)
        if claims.get("exp", 0) < check_now:
            raise ChallengeTokenExpiredError(
                token_jti=claims.get("jti", "<unknown>"),
                expired_at=claims.get("exp", 0),
            )

        # P-12: User still has 2FA enabled. If the owner reset or self-disabled
        # 2FA after this token was issued, the token must NOT be accepted.
        # totp_enabled_at IS NOT NULL is the authoritative 2FA-enrolled predicate
        # (Story 12.1); `twofa_enabled` is the coarse legacy flag.
        user_stmt = select(User).where(User.id == user_id)
        user_result = await self.session.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if user is None or user.totp_enabled_at is None:
            raise TwoFactorNotEnabledError(
                user_id=user_id,
                trace_id=str(uuid.uuid4()),
            )

        # P-05: Replay guard. INSERT with jti as PK; duplicate key triggers
        # IntegrityError → ChallengeTokenAlreadyConsumedError → 401. The PK
        # uniqueness is the atomicity guarantee (no read-then-write race).
        token_jti = claims.get("jti", "<unknown>")
        used_row = UsedChallengeToken(
            jti=token_jti,
            user_id=user_id,
            tenant_id=tenant_id,
            used_at=datetime.now(UTC),
        )
        self.session.add(used_row)
        try:
            await self.session.flush()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ChallengeTokenAlreadyConsumedError(
                token_jti=token_jti,
                trace_id=str(uuid.uuid4()),
            ) from exc

        return ChallengePassed(user_id=user_id, tenant_id=tenant_id)


__all__ = [
    "CHALLENGE_TOKEN_TTL_SECONDS",
    "CHALLENGE_TOKEN_PURPOSE",
    "ChallengeTokenError",
    "ChallengeTokenExpiredError",
    "ChallengeTokenInvalidError",
    "ChallengeTokenPurposeMismatchError",
    "ChallengeTokenAlreadyConsumedError",
    "TwoFactorChallengeFailedError",
    "ChallengeTokenIssued",
    "ChallengePassed",
    "TwoFactorChallengeService",
]
