"""apps.api.modules.m12_account.exceptions — Story 12.1 typed exception classes.

8 NEW exception types for 2FA mandatory gate (PRD §F12.1 + §M12-a
+ AD-15 §4 envelope). Each exception carries the minimum context
required for the corresponding handler in `apps/api/main.py` to
produce a deterministic AD-15 §4 envelope.

Error code contract:
  - TwoFactorNotEnabledError            → 400 TWO_FACTOR_NOT_ENABLED
  - TwoFactorAlreadyEnabledError        → 409 TWO_FACTOR_ALREADY_ENABLED
  - TwoFactorAuditEmitError             → 503 TWO_FACTOR_AUDIT_EMIT_FAILED
  - TwoFactorEncryptionError            → 500 TWO_FACTOR_ENCRYPTION_FAILED
  - TwoFactorCryptoKeyMissingError      → 500 TWO_FACTOR_KEY_MISSING
  - TwoFactorRecoveryExhaustedError     → 410 TWO_FACTOR_RECOVERY_EXHAUSTED
  - TwoFactorDisableUnauthorizedError   → 403 TWO_FACTOR_DISABLE_UNAUTHORIZED
  - TwoFactorUserNotFoundError          → 404 TWO_FACTOR_USER_NOT_FOUND

Korean SSOT (AD-15 §11) is supplied by the handler, not the exception
itself — keeps the exception module free of presentation strings
(parity with m11_close.exceptions per CR 11-3/11-2 lesson).
"""

from __future__ import annotations

import uuid


# ── 1. TwoFactorNotEnabledError ─────────────────────────────
class TwoFactorNotEnabledError(Exception):
    """400 TWO_FACTOR_NOT_ENABLED — challenge attempt on user without 2FA.

    Setup flow completes via setup_totp → verify_and_enable_totp
    (flips `users.twofa_enabled` to True). If a challenge attempt
    comes in before setup completed, this error fires.

    Distinct from TwoFactorAlreadyEnabledError (which signals
    re-setup attempt). The two errors together cover the full
    state-machine of `users.twofa_enabled`.
    """

    def __init__(self, *, user_id: uuid.UUID, trace_id: str) -> None:
        super().__init__(
            f"2FA not enabled for user {user_id} — "
            f"complete setup_totp + verify_and_enable first"
        )
        self.user_id = user_id
        self.trace_id = trace_id


# ── 2. TwoFactorAlreadyEnabledError ────────────────────────
class TwoFactorAlreadyEnabledError(Exception):
    """409 TWO_FACTOR_ALREADY_ENABLED — duplicate setup attempt.

    Re-setup rejected (idempotent no-op per CR 1.1 lesson). To re-key
    TOTP secret: explicit disable_totp (requires current valid code)
    → setup_totp again. Forces an audit trail of why the secret
    rotated (e.g., compromised device).
    """

    def __init__(
        self,
        *,
        user_id: uuid.UUID,
        enabled_at: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"2FA already enabled for user {user_id} "
            f"(enabled_at={enabled_at}); disable first to re-setup"
        )
        self.user_id = user_id
        self.enabled_at = enabled_at
        self.trace_id = trace_id


# ── 3. TwoFactorAuditEmitError ─────────────────────────────
class TwoFactorAuditEmitError(Exception):
    """503 TWO_FACTOR_AUDIT_EMIT_FAILED — audit-first emit failed.

    All 6 mutations (setup_initiated / setup_completed / challenge_passed /
    challenge_failed / recovery_consumed / disabled) emit audit-first via
    `emit_audit_typed`. If the audit row fails to persist, the data write
    is rolled back and this error fires. 503 (transient, retry-able) —
    audit subsystem failure is typically a DB blip.

    Mirrors m11_close.exceptions.ReopenAuditEmitFailedError pattern.
    """

    def __init__(self, *, message: str, trace_id: str) -> None:
        super().__init__(message)
        self.message = message
        self.trace_id = trace_id


# ── 4. TwoFactorEncryptionError ──────────────────────────────
class TwoFactorEncryptionError(Exception):
    """500 TWO_FACTOR_ENCRYPTION_FAILED — AES-256-GCM layer failure.

    The service layer wraps `users.totp_secret` BYTEA via
    `apps.api.core.crypto.encrypt_at_rest`. If the encryption layer
    raises (corrupted key cache, env-var hex malformed, etc.), the
    setup attempt aborts and this error surfaces.

    Distinct from TwoFactorCryptoKeyMissingError (key retrieval
    failure before encryption begins).
    """

    def __init__(self, *, message: str, trace_id: str) -> None:
        super().__init__(f"2FA encryption failed: {message}")
        self.message = message
        self.trace_id = trace_id


# ── 5. TwoFactorCryptoKeyMissingError ───────────────────────
class TwoFactorCryptoKeyMissingError(Exception):
    """500 TWO_FACTOR_KEY_MISSING — key_manager cannot resolve COSTMGR_AT_REST_KEY_V1.

    Production requires KMS — env-var is dev/CI only. The key_manager
    falls back to ephemeral in-memory key (dev convenience) on cache
    miss; in production this surfaces as a configuration error.
    """

    def __init__(self, *, key_id: str, trace_id: str) -> None:
        super().__init__(
            f"2FA encryption key {key_id!r} not resolvable from "
            f"cache / env-var / KMS — configure via COSTMGR_AT_REST_KEY_<KEY_ID>"
        )
        self.key_id = key_id
        self.trace_id = trace_id


# ── 6. TwoFactorRecoveryExhaustedError ──────────────────────
class TwoFactorRecoveryExhaustedError(Exception):
    """410 TWO_FACTOR_RECOVERY_EXHAUSTED — all 8 recovery codes consumed.

    Once all 8 recovery codes are marked `used_at`, future recovery
    attempts trigger this error. User must re-setup TOTP via
    disable + setup_totp (admin-initiated only after identity
    verification — `two_factor_disabled` audit captures reason).
    """

    def __init__(self, *, user_id: uuid.UUID, trace_id: str) -> None:
        super().__init__(
            f"all 8 recovery codes consumed for user {user_id}; "
            f"admin re-setup required"
        )
        self.user_id = user_id
        self.trace_id = trace_id


# ── 7. TwoFactorDisableUnauthorizedError ────────────────────
class TwoFactorDisableUnauthorizedError(Exception):
    """403 TWO_FACTOR_DISABLE_UNAUTHORIZED — disable attempt without valid code.

    Disable_totp requires:
    1. Current valid TOTP code (proves user possession of auth device), OR
    2. Recovery code (proves backup access)
    3. Owner role authorization (AD-10 — admin-initiated disable)

    Missing any of the 3 → this error. Mirrors m11_close 403 envelope pattern.
    """

    def __init__(
        self,
        *,
        user_id: uuid.UUID,
        reason: str,
        trace_id: str,
    ) -> None:
        super().__init__(
            f"2FA disable unauthorized for user {user_id}: {reason}"
        )
        self.user_id = user_id
        self.reason = reason
        self.trace_id = trace_id


# ── 8. TwoFactorUserNotFoundError ───────────────────────────
class TwoFactorUserNotFoundError(Exception):
    """404 TWO_FACTOR_USER_NOT_FOUND — user_id does not resolve.

    Distinct from m11_close.SnapshotNotFoundError pattern — keeps
    root-cause error semantics (AD-15 §4 envelope contract).
    """

    def __init__(self, *, user_id: uuid.UUID, trace_id: str) -> None:
        super().__init__(f"user {user_id} not found")
        self.user_id = user_id
        self.trace_id = trace_id


__all__ = [
    "TwoFactorNotEnabledError",
    "TwoFactorAlreadyEnabledError",
    "TwoFactorAuditEmitError",
    "TwoFactorEncryptionError",
    "TwoFactorCryptoKeyMissingError",
    "TwoFactorRecoveryExhaustedError",
    "TwoFactorDisableUnauthorizedError",
    "TwoFactorUserNotFoundError",
]
