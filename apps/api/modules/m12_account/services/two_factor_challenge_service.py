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
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.settings import get_settings


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

    def consume_challenge_token(
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

        Args:
            token: Challenge token string from cookie / Authorization header.
            user_id: Expected user_id (handler validates from session).
            tenant_id: Expected tenant_id.
            now: Current unix timestamp (caller passes for testability).

        Returns:
            ChallengePassed(user_id, tenant_id) on success.

        Raises:
            ChallengeTokenExpiredError, ChallengeTokenInvalidError,
            ChallengeTokenPurposeMismatchError.
        """
        check_now = now if now is not None else int(time.time())
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

        return ChallengePassed(user_id=user_id, tenant_id=tenant_id)


__all__ = [
    "CHALLENGE_TOKEN_TTL_SECONDS",
    "CHALLENGE_TOKEN_PURPOSE",
    "ChallengeTokenError",
    "ChallengeTokenExpiredError",
    "ChallengeTokenInvalidError",
    "ChallengeTokenPurposeMismatchError",
    "ChallengeTokenIssued",
    "ChallengePassed",
    "TwoFactorChallengeService",
]
