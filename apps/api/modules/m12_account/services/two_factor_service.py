"""apps.api.modules.m12_account.services.two_factor_service — Story 12.1 PRIMARY.

2FA mandatory gate service layer (PRD §F12.1 + §M12-a + AD-15 §4).

Wraps the pure kernels in `packages.services.m12_account` (TOTP +
2FA gate validation) with:
- DB persistence (users.totp_secret BYTEA + users.totp_recovery_codes_hash
  JSONB) via SQLAlchemy 2.0 AsyncSession
- NFR6 AES-256-GCM column-level encryption via apps.api.core.crypto
- A5 audit-first invariant via apps.api.core.audit_action.emit_audit_typed
- NFR5 TLS in transit (plaintext secret NEVER logged)
- AD-10 4-role gate (owner/member allowed, viewer/consultant_proxy denied)
- Lockout state (users.totp_failed_attempts + users.totp_lockout_until)
- Idempotent no-op for re-setup (CR 1.1 lesson)

Service operations (5):
  - `setup_totp` — generate secret + recovery codes; encrypt secret;
    `users.totp_secret` ciphertext UPDATE; audit `two_factor_setup_initiated`.
    Returns URI + recovery_codes (1회 plaintext 응답).
  - `verify_and_enable_totp` — verify first TOTP code; flip
    `users.twofa_enabled` = true + `users.totp_enabled_at` set;
    audit `two_factor_setup_completed`.
  - `verify_totp_challenge` — verify code against encrypted secret;
    `users.totp_failed_attempts` increment OR reset on success;
    audit `two_factor_challenge_passed` OR `two_factor_challenge_failed`.
  - `verify_recovery_code` — verify against PBKDF2 JSONB hash;
    mark entry used_at; audit `two_factor_recovery_consumed`.
  - `disable_totp` — verify code OR admin authorization;
    NULL `users.totp_secret` + `users.totp_recovery_codes_hash`;
    `users.twofa_enabled` = false; audit `two_factor_disabled`.

Layering (AD-11):
- Pure kernel: `packages/services/m12_account/totp.py` (RFC 6238 +
  recovery codes)
- Pure kernel: `packages/services/m12_account/two_factor_gate.py`
  (gate validation)
- Service layer (this file): SQLAlchemy + AES-256-GCM + audit-first
  + 8 typed exceptions (apps/api/modules/m12_account/exceptions.py)

A5 forward-lock (Story 12.1 wire):
- Audit rows route to `audit_logs` (ActionClass.TWO_FACTOR_AUTH) via
  `emit_audit_typed()`. 6 NEW values:
  - `two_factor_setup_initiated`
  - `two_factor_setup_completed`
  - `two_factor_challenge_passed`
  - `two_factor_challenge_failed`
  - `two_factor_recovery_consumed`
  - `two_factor_disabled`
- Drift detector: tests/integration/test_audit_action_consistency.py
  + tests/services/test_audit_action_centralization.py extensions.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.crypto import (
    DEFAULT_KEY_ID,
    CryptoError,
    encrypt_at_rest,
)
from apps.api.core.db_models import User
from apps.api.modules.m12_account.exceptions import (
    TwoFactorAlreadyEnabledError,
    TwoFactorAuditEmitError,
    TwoFactorCryptoKeyMissingError,
    TwoFactorDisableUnauthorizedError,
    TwoFactorEncryptionError,
    TwoFactorNotEnabledError,
    TwoFactorRecoveryExhaustedError,
    TwoFactorUserNotFoundError,
)
from packages.services.m12_account.totp import (
    LOCKOUT_DURATION_SECONDS,
    MAX_FAILED_ATTEMPTS,
    TotpInvalidCodeError,
    TotpLockoutError,
    TotpRecoveryInvalidError,
    generate_recovery_code_hashes,
    generate_recovery_codes,
    generate_totp_secret,
    generate_totp_uri,
    verify_recovery_code,
    verify_totp_code,
)
from packages.services.m12_account.two_factor_gate import (
    UserTotpState,
    lockout_status,
)


def _now_utc() -> datetime:
    """UTC now (AD-5: pure kernel no clock, service layer owns)."""
    return datetime.now(tz=UTC)


def _now_timestamp() -> int:
    """Unix timestamp (seconds) for TOTP computation."""
    return int(_now_utc().timestamp())


def _to_totp_state(user: User) -> UserTotpState:
    """Adapt SQLAlchemy `User` row → pure-kernel `UserTotpState`.

    Boundary conversion at service→kernel call site (CR 4-3 /
    pure-kernel contract invariant). Pure kernel uses struct-style
    fields; ORM uses snake_case columns.
    """
    return UserTotpState(
        user_id=str(user.id),
        totp_secret_set=user.totp_secret is not None,
        totp_enabled_at=int(user.totp_enabled_at.timestamp())
        if user.totp_enabled_at
        else 0,
        failed_attempts=user.totp_failed_attempts or 0,
        lockout_until=int(user.totp_lockout_until.timestamp())
        if user.totp_lockout_until
        else 0,
    )


# ── Typed results ─────────────────────────────────────────────
class TotpSetupResult:
    """Result of `setup_totp` — secret + URI + recovery codes.

    Service contract: caller MUST immediately show all 3 to user
    (secret for QR generation, URI for fallback manual entry,
    recovery_codes for 1회-only secure storage display).
    """

    def __init__(
        self,
        *,
        secret: str,
        uri: str,
        recovery_codes: list[str],
    ) -> None:
        self.secret = secret  # base32-encoded (NOT ciphertext — caller-side render)
        self.uri = uri
        self.recovery_codes = recovery_codes


class TotpChallengeResult:
    """Result of `verify_totp_challenge`."""

    def __init__(self, *, passed: bool, remaining_attempts: int) -> None:
        self.passed = passed
        self.remaining_attempts = remaining_attempts


# ── Service class ─────────────────────────────────────────────
class TwoFactorService:
    """2FA mandatory gate service (PRD §F12.1 + §M12-a).

    AD-10 4-role gate: caller MUST pass `is_owner_or_member` (resolved
    via membership lookup in handler). Service-layer role check
    delegates to `enforce_role_gate` pure kernel.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Setup ────────────────────────────────────────────────
    async def setup_totp(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> TotpSetupResult:
        """Initiate 2FA setup — generate secret + recovery codes.

        Idempotent no-op: if 2FA already enabled for this user, raises
        TwoFactorAlreadyEnabledError (CR 1.1 lesson — re-setup must
        be explicit disable first).

        Args:
            user_id: User performing setup.
            tenant_id: User's tenant (for audit scoping).

        Returns:
            TotpSetupResult(secret, uri, recovery_codes).
            Caller MUST render recovery_codes to user immediately
            (1회만 응답; 이후 recovery_codes_hash JSONB만 저장됨).

        Raises:
            TwoFactorUserNotFoundError, TwoFactorAlreadyEnabledError,
            TwoFactorEncryptionError, TwoFactorCryptoKeyMissingError,
            TwoFactorAuditEmitError.
        """
        user = await self._load_user(user_id, tenant_id)
        if user.twofa_enabled:
            enabled_at_iso = (
                user.totp_enabled_at.isoformat()
                if user.totp_enabled_at
                else "unknown"
            )
            raise TwoFactorAlreadyEnabledError(
                user_id=user_id,
                enabled_at=enabled_at_iso,
                trace_id=str(uuid.uuid4()),
            )

        # Generate TOTP secret + URI + recovery codes (pure kernel)
        secret_bytes = generate_totp_secret()
        uri = generate_totp_uri(secret_bytes, email=user.email)
        recovery_codes = generate_recovery_codes()
        recovery_hashes = generate_recovery_code_hashes(recovery_codes)

        # Encrypt TOTP secret at rest (NFR6 AES-256-GCM)
        try:
            totp_secret_ct = encrypt_at_rest(
                secret_bytes,
                key_id=DEFAULT_KEY_ID,
                aad=b"totp_secret",
            )
        except CryptoError as exc:
            raise TwoFactorCryptoKeyMissingError(
                key_id=DEFAULT_KEY_ID,
                trace_id=str(uuid.uuid4()),
            ) from exc
        except Exception as exc:
            raise TwoFactorEncryptionError(
                message=str(exc),
                trace_id=str(uuid.uuid4()),
            ) from exc

        # Persist encrypted secret + recovery hashes (NOT yet enabled)
        user.totp_secret = totp_secret_ct
        user.totp_recovery_codes_hash = recovery_hashes
        user.totp_failed_attempts = 0
        user.totp_lockout_until = None
        # NOTE: twofa_enabled stays False until verify_and_enable_totp succeeds.
        await self.session.flush()

        # Audit FIRST (CR 1.1 lesson) — `two_factor_setup_initiated`.
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.TWO_FACTOR_AUTH,
                action="two_factor_setup_initiated",
                actor_id=user_id,
                target_id=user_id,
                reason="user initiated 2FA setup",
                payload={
                    "user_email": user.email,
                    "recovery_codes_count": len(recovery_codes),
                },
                tenant_id=tenant_id,
                flush=True,
            )
        except Exception as exc:
            raise TwoFactorAuditEmitError(
                message=f"audit emit failed for two_factor_setup_initiated: {exc}",
                trace_id=str(uuid.uuid4()),
            ) from exc

        # caller receives base32 secret for QR rendering
        import base64

        secret_b32 = base64.b32encode(secret_bytes).decode("ascii").rstrip("=")
        return TotpSetupResult(
            secret=secret_b32,
            uri=uri,
            recovery_codes=recovery_codes,
        )

    # ── Verify + Enable (first TOTP code) ────────────────────
    async def verify_and_enable_totp(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        code: str,
    ) -> bool:
        """Verify first TOTP code + flip `twofa_enabled` = true.

        Called once after setup_totp. User scans QR + enters code from
        authenticator app to confirm setup.

        Args:
            user_id: User completing setup.
            tenant_id: User's tenant.
            code: 6-digit TOTP code from authenticator app.

        Returns:
            True on success.

        Raises:
            TwoFactorUserNotFoundError, TwoFactorNotEnabledError
            (no pending setup), TotpInvalidCodeError,
            TwoFactorAuditEmitError.
        """
        from apps.api.core.crypto import decrypt_at_rest

        user = await self._load_user(user_id, tenant_id)
        if not user.totp_secret:
            raise TwoFactorNotEnabledError(
                user_id=user_id,
                trace_id=str(uuid.uuid4()),
            )

        # Decrypt TOTP secret (NFR6 AES-256-GCM)
        secret_bytes = decrypt_at_rest(
            user.totp_secret,
            key_id=DEFAULT_KEY_ID,
            aad=b"totp_secret",
        )

        # Check lockout
        now = _now_utc()
        if lockout_status(_to_totp_state(user), now=int(now.timestamp())):
            retry_after = user.totp_lockout_until - now if user.totp_lockout_until else LOCKOUT_DURATION_SECONDS
            raise TotpLockoutError(retry_after_seconds=int(retry_after.total_seconds()))

        # Verify code
        if not verify_totp_code(
            secret_bytes,
            code,
            timestamp=_now_timestamp(),
            tolerance_windows=1,
        ):
            await self._increment_failed_attempts(user)
            raise TotpInvalidCodeError()

        # Enable 2FA + audit (CR 1.1 invariant — emit before commit)
        user.twofa_enabled = True
        user.totp_enabled_at = now
        user.totp_failed_attempts = 0
        user.totp_lockout_until = None
        await self.session.flush()

        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.TWO_FACTOR_AUTH,
                action="two_factor_setup_completed",
                actor_id=user_id,
                target_id=user_id,
                reason="user verified first TOTP code",
                payload={
                    "user_email": user.email,
                    "enabled_at": now.isoformat(),
                },
                tenant_id=tenant_id,
                flush=True,
            )
        except Exception as exc:
            raise TwoFactorAuditEmitError(
                message=f"audit emit failed for two_factor_setup_completed: {exc}",
                trace_id=str(uuid.uuid4()),
            ) from exc

        return True

    # ── Challenge (M2 entry gate) ────────────────────────────
    async def verify_totp_challenge(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        code: str,
    ) -> TotpChallengeResult:
        """Verify TOTP code at M2 entry gate.

        On success: reset failed_attempts = 0, audit `two_factor_challenge_passed`.
        On failure: increment failed_attempts; if ≥ MAX → set lockout_until;
        audit `two_factor_challenge_failed`.

        Args:
            user_id: User challenging.
            tenant_id: User's tenant.
            code: 6-digit TOTP code.

        Returns:
            TotpChallengeResult(passed, remaining_attempts).

        Raises:
            TwoFactorUserNotFoundError, TwoFactorNotEnabledError,
            TotpLockoutError (active lockout), TotpInvalidCodeError,
            TwoFactorAuditEmitError.
        """
        from apps.api.core.crypto import decrypt_at_rest

        user = await self._load_user(user_id, tenant_id)
        if not user.twofa_enabled or not user.totp_secret:
            raise TwoFactorNotEnabledError(
                user_id=user_id,
                trace_id=str(uuid.uuid4()),
            )

        # Check lockout first
        now = _now_utc()
        if lockout_status(_to_totp_state(user), now=int(now.timestamp())):
            retry_after = user.totp_lockout_until - now if user.totp_lockout_until else LOCKOUT_DURATION_SECONDS
            raise TotpLockoutError(retry_after_seconds=int(retry_after.total_seconds()))

        # Decrypt + verify
        secret_bytes = decrypt_at_rest(
            user.totp_secret,
            key_id=DEFAULT_KEY_ID,
            aad=b"totp_secret",
        )
        passed = verify_totp_code(
            secret_bytes,
            code,
            timestamp=_now_timestamp(),
            tolerance_windows=1,
        )

        if passed:
            user.totp_failed_attempts = 0
            user.totp_lockout_until = None
            await self.session.flush()
            try:
                await emit_audit_typed(
                    self.session,
                    action_class=ActionClass.TWO_FACTOR_AUTH,
                    action="two_factor_challenge_passed",
                    actor_id=user_id,
                    target_id=user_id,
                    reason="M2 entry gate TOTP challenge passed",
                    payload={"user_email": user.email},
                    tenant_id=tenant_id,
                    flush=True,
                )
            except Exception as exc:
                raise TwoFactorAuditEmitError(
                    message=f"audit emit failed for two_factor_challenge_passed: {exc}",
                    trace_id=str(uuid.uuid4()),
                ) from exc
            return TotpChallengeResult(
                passed=True,
                remaining_attempts=MAX_FAILED_ATTEMPTS,
            )

        # Failure path — increment + check threshold
        await self._increment_failed_attempts(user)
        remaining = max(0, MAX_FAILED_ATTEMPTS - user.totp_failed_attempts)

        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.TWO_FACTOR_AUTH,
                action="two_factor_challenge_failed",
                actor_id=user_id,
                target_id=user_id,
                reason="M2 entry gate TOTP challenge failed",
                payload={
                    "user_email": user.email,
                    "failed_attempts": user.totp_failed_attempts,
                    "remaining_attempts": remaining,
                },
                tenant_id=tenant_id,
                flush=True,
            )
        except Exception as exc:
            raise TwoFactorAuditEmitError(
                message=f"audit emit failed for two_factor_challenge_failed: {exc}",
                trace_id=str(uuid.uuid4()),
            ) from exc

        return TotpChallengeResult(
            passed=False,
            remaining_attempts=remaining,
        )

    # ── Recovery code ────────────────────────────────────────
    async def verify_recovery_code(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        code: str,
    ) -> TotpChallengeResult:
        """Verify 1회용 recovery code (fallback when authenticator lost).

        On success: mark entry used_at; audit `two_factor_recovery_consumed`.
        If no unused entries → TwoFactorRecoveryExhaustedError.

        Args:
            user_id, tenant_id, code.

        Returns:
            TotpChallengeResult(passed=True, remaining_attempts=...).

        Raises:
            TwoFactorUserNotFoundError, TwoFactorNotEnabledError,
            TwoFactorRecoveryExhaustedError, TotpRecoveryInvalidError,
            TwoFactorAuditEmitError.
        """
        user = await self._load_user(user_id, tenant_id)
        if not user.twofa_enabled or not user.totp_recovery_codes_hash:
            raise TwoFactorNotEnabledError(
                user_id=user_id,
                trace_id=str(uuid.uuid4()),
            )

        hashes = user.totp_recovery_codes_hash
        unused_count = sum(1 for h in hashes if not h.get("used_at"))
        if unused_count == 0:
            raise TwoFactorRecoveryExhaustedError(
                user_id=user_id,
                trace_id=str(uuid.uuid4()),
            )

        try:
            result = verify_recovery_code(
                code,
                hashes=hashes,
            )
        except TotpRecoveryInvalidError:
            # Audit failure (invalid format or no match)
            try:
                await emit_audit_typed(
                    self.session,
                    action_class=ActionClass.TWO_FACTOR_AUTH,
                    action="two_factor_challenge_failed",
                    actor_id=user_id,
                    target_id=user_id,
                    reason="recovery code invalid or already used",
                    payload={
                        "user_email": user.email,
                        "recovery_attempt": True,
                    },
                    tenant_id=tenant_id,
                    flush=True,
                )
            except Exception as exc:
                raise TwoFactorAuditEmitError(
                    message=f"audit emit failed (recovery invalid): {exc}",
                    trace_id=str(uuid.uuid4()),
                ) from exc
            raise

        # Mark used_at (CR 1.1 — single 1회용 invariant)
        hashes[result.code_index]["used_at"] = _now_utc().isoformat()
        user.totp_recovery_codes_hash = hashes
        user.totp_failed_attempts = 0
        user.totp_lockout_until = None
        await self.session.flush()

        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.TWO_FACTOR_AUTH,
                action="two_factor_recovery_consumed",
                actor_id=user_id,
                target_id=user_id,
                reason="recovery code consumed",
                payload={
                    "user_email": user.email,
                    "code_index": result.code_index,
                    "remaining_codes": unused_count - 1,
                },
                tenant_id=tenant_id,
                flush=True,
            )
        except Exception as exc:
            raise TwoFactorAuditEmitError(
                message=f"audit emit failed for two_factor_recovery_consumed: {exc}",
                trace_id=str(uuid.uuid4()),
            ) from exc

        return TotpChallengeResult(
            passed=True,
            remaining_attempts=unused_count - 1,
        )

    # ── Disable ──────────────────────────────────────────────
    async def disable_totp(
        self,
        *,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        actor_id: uuid.UUID,
        current_code: str | None,
        reason: str,
    ) -> None:
        """Disable 2FA (NULL secret + recovery codes + flip enabled=false).

        Requires ONE of:
        1. `current_code` — current valid TOTP code (user possession proof)
        2. `actor_id` != `user_id` — admin override (caller is owner)
        3. `reason` length ≥ 20 (AD-15 audit-justification)

        On success: NULL totp_secret, NULL totp_recovery_codes_hash,
        twofa_enabled=False; audit `two_factor_disabled`.

        Raises:
            TwoFactorUserNotFoundError, TwoFactorDisableUnauthorizedError,
            TwoFactorAuditEmitError.
        """
        from apps.api.core.crypto import decrypt_at_rest

        user = await self._load_user(user_id, tenant_id)
        if not user.twofa_enabled:
            raise TwoFactorNotEnabledError(
                user_id=user_id,
                trace_id=str(uuid.uuid4()),
            )

        # Authorization check: code verification OR admin override
        if current_code and user.totp_secret:
            secret_bytes = decrypt_at_rest(
                user.totp_secret,
                key_id=DEFAULT_KEY_ID,
                aad=b"totp_secret",
            )
            if not verify_totp_code(
                secret_bytes,
                current_code,
                timestamp=_now_timestamp(),
                tolerance_windows=1,
            ):
                raise TwoFactorDisableUnauthorizedError(
                    user_id=user_id,
                    reason="current TOTP code invalid",
                    trace_id=str(uuid.uuid4()),
                )
        elif actor_id != user_id:
            # admin override — actor_id != user_id (AD-10 owner role
            # enforcement lives in handler; service accepts trust signal)
            if len(reason) < 20:
                raise TwoFactorDisableUnauthorizedError(
                    user_id=user_id,
                    reason=f"admin override reason too short "
                    f"(len={len(reason)}, expected ≥20)",
                    trace_id=str(uuid.uuid4()),
                )
        else:
            raise TwoFactorDisableUnauthorizedError(
                user_id=user_id,
                reason="neither current code nor admin override provided",
                trace_id=str(uuid.uuid4()),
            )

        # Mutate: clear 2FA state
        user.twofa_enabled = False
        user.totp_secret = None
        user.totp_recovery_codes_hash = None
        user.totp_enabled_at = None
        user.totp_failed_attempts = 0
        user.totp_lockout_until = None
        await self.session.flush()

        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.TWO_FACTOR_AUTH,
                action="two_factor_disabled",
                actor_id=actor_id,
                target_id=user_id,
                reason=reason,
                payload={
                    "user_email": user.email,
                    "actor_is_owner": actor_id != user_id,
                    "method": ("code" if current_code else "admin_override"),
                },
                tenant_id=tenant_id,
                flush=True,
            )
        except Exception as exc:
            raise TwoFactorAuditEmitError(
                message=f"audit emit failed for two_factor_disabled: {exc}",
                trace_id=str(uuid.uuid4()),
            ) from exc

    # ── Helpers ──────────────────────────────────────────────
    async def _load_user(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> User:
        """Load user with RLS-scoped tenant_id filter.

        Raises:
            TwoFactorUserNotFoundError: If user_id not found or wrong tenant.
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .where(User.tenant_id == tenant_id)
        )
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise TwoFactorUserNotFoundError(
                user_id=user_id,
                trace_id=str(uuid.uuid4()),
            )
        return user

    async def _increment_failed_attempts(self, user: User) -> None:
        """Increment failed_attempts; lock account at threshold.

        Idempotent within same session. CR 1.1 audit emit happens
        separately in caller (two_factor_challenge_failed).
        """
        user.totp_failed_attempts = (user.totp_failed_attempts or 0) + 1
        if user.totp_failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.totp_lockout_until = _now_utc() + timedelta(
                seconds=LOCKOUT_DURATION_SECONDS
            )
        await self.session.flush()


__all__ = [
    "TotpSetupResult",
    "TotpChallengeResult",
    "TwoFactorService",
]
