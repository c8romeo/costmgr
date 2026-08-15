"""apps.api.modules.m12_account.services.account_deletion_service — Story 12.3.

Account deletion service layer (PRD §F12.3 + epics.md Story 12.3 +
NFR4 2절 + NFR7 2FA 강제 + CR 12-5 L3 destructive endpoint 3-layer
defense CRITICAL).

Wraps the pure kernel in `packages.services.m12_account.account_deletion`
with:
- DB I/O (SQLAlchemy 2.0 AsyncSession) — SELECT/UPDATE on tenants,
  INSERT on deletion_consents
- A5 audit-first invariant via `emit_audit_typed` (ACCOUNT_DELETION class)
- 3-layer TOTP defense (CR 12-5 L3):
  - Layer 1 (route): `require_role("owner")` + 2FA setup verified check
  - Layer 2 (service): `verify_totp_challenge(token, user)` delegation
  - Layer 3 (handler): `audit-first emit BEFORE raise` (CR 1.1 invariant)
- AES-256-GCM `encrypt_at_rest(..., aad=b"deletion_consent")` (NFR6 invariant)
- PyJWT `verify_exp=False` + caller-controlled `now` (CR 12-1 L1)
- ORM→kernel boundary `_to_deletion_state(tenant)` (CR 12-1 L3)
- Korean SSOT (AD-15 §11)

Service operations (6):
  - `issue_deletion_challenge_token` — mint short-lived JWT
    (purpose="account_deletion", 5-min TTL) AFTER verify_totp_code
  - `request_deletion` — destructive endpoint: re-verify challenge
    token + validate consent text + persist deletion_consents +
    audit-first emit (2 rows) + transition tenants.status FSM
  - `cancel_deletion` — owner-only, transition pending_deletion → active
  - `get_deletion_status` — read-only snapshot
  - `hard_delete_expired_tenants` — cron-callable, per-tenant soft-fail
  - `run_hard_delete_cron` — thin wrapper for `apps.api.jobs.tenant_hard_delete`

Layering (AD-11):
- Pure kernel: `packages/services/m12_account/account_deletion.py`
  (status FSM + consent envelope + retention_days constant)
- Service layer (this file): SQLAlchemy + audit-first + 2FA verify delegation

CRITICAL patterns applied:
- CR 12-5 L3 3-layer TOTP defense (route + service + handler audit-first)
- CR 1.1 audit-first invariant (session.begin_nested() BEFORE state transition)
- CR 12-1 L1 PyJWT verify_exp=False + caller-controlled now
- CR 12-1 L2 AES-256-GCM distinct AAD per column
- CR 12-1 L3 ORM→kernel boundary at service→kernel call site
- CR 11-3 5-file sweep for audit_action rename (mirrored in audit_action.py)
- CR 12-3 SnapshotNotFoundError split: AccountAlreadyDeletedError (410) vs
  never-existed (404 row missing — handled at handler layer)
"""

from __future__ import annotations

import contextlib
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.crypto import DEFAULT_KEY_ID, decrypt_at_rest, encrypt_at_rest
from apps.api.core.db_models import DeletionConsent, Tenant, User
from apps.api.core.settings import get_settings
from apps.api.modules.m12_account.services.two_factor_service import (
    _to_totp_state,
)
from packages.services.m12_account.account_deletion import (
    ACCOUNT_DELETION_ACTION_DELETION_CANCELLED,
    ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN,
    ACCOUNT_DELETION_ACTION_DELETION_FAILED,
    ACCOUNT_DELETION_ACTION_DELETION_REQUESTED,
    ACCOUNT_DELETION_ACTION_TENANT_HARD_DELETED,
    ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED,
    AccountAlreadyDeletedError,
    AccountDeletionNotOwnerError,
    DeletionConsentRequiredError,
    DeletionRequestEnvelope,
    DeletionStatusSnapshot,
    TenantDeletionStatus,
    assert_status_transition,
    build_deletion_envelope,
    compute_consent_hash,
    compute_deletion_scheduled_for,
    validate_consent_text,
)
from packages.services.m12_account.totp import (
    MAX_FAILED_ATTEMPTS,
    TotpInvalidCodeError,
    verify_totp_code,
)
from packages.services.m12_account.two_factor_gate import (
    UserTotpState,
    raise_if_locked,
)

# ── Constants ────────────────────────────────────────────────
DELETION_CHALLENGE_TOKEN_PURPOSE: str = "account_deletion"
DELETION_CHALLENGE_TOKEN_TTL_SECONDS: int = 300  # 5 min (mirror 12-1)

# AES-256-GCM AAD for consent text encryption (CR 12-1 L2 — distinct per column).
DELETION_CONSENT_AAD: bytes = b"deletion_consent"

# Error codes (AD-15 §4 envelope contract)
ERROR_CODE_DELETION_CHALLENGE_TOKEN_INVALID: str = "DELETION_CHALLENGE_TOKEN_INVALID"
ERROR_CODE_DELETION_CHALLENGE_TOKEN_EXPIRED: str = "DELETION_CHALLENGE_TOKEN_EXPIRED"
ERROR_CODE_DELETION_CONSENT_ENCRYPTION_FAILED: str = "DELETION_CONSENT_ENCRYPTION_FAILED"
ERROR_CODE_DELETION_CONSENT_DECRYPTION_FAILED: str = "DELETION_CONSENT_DECRYPTION_FAILED"
ERROR_CODE_ACCOUNT_DELETION_AUDIT_EMIT_FAILED: str = "ACCOUNT_DELETION_AUDIT_EMIT_FAILED"
ERROR_CODE_ACCOUNT_DELETION_HARD_DELETE_FAILED: str = "ACCOUNT_DELETION_HARD_DELETE_FAILED"

# Korean SSOT — AD-15 §11. 격식체 종결 (UX locked decisions).
DELETION_CHALLENGE_TOKEN_INVALID_KO: str = (
    "인증 토큰이 유효하지 않습니다 — 페이지를 새로 고친 후 다시 시도해 주세요"
)
DELETION_CHALLENGE_TOKEN_EXPIRED_KO: str = (
    "인증 토큰이 만료되었습니다 (5분 초과) — [2FA 코드]를 다시 입력해 주세요"
)
DELETION_CONSENT_ENCRYPTION_FAILED_KO: str = (
    "동의 정보 암호화에 실패했습니다 — 잠시 후 다시 시도해 주세요"
)
DELETION_CONSENT_DECRYPTION_FAILED_KO: str = (
    "동의 정보 복호화에 실패했습니다 — 관리자에게 문의해 주세요"
)
ACCOUNT_DELETION_AUDIT_EMIT_FAILED_KO: str = (
    "감사 로그 기록에 실패했습니다 — 잠시 후 다시 시도해 주세요 (일시 오류)"
)
ACCOUNT_DELETION_HARD_DELETE_FAILED_KO: str = (
    "계정 완전 삭제에 실패했습니다 — 관리자가 확인 후 재시도합니다"
)


# ── Typed exceptions ──────────────────────────────────────────
class DeletionChallengeTokenInvalidError(Exception):
    """401 DELETION_CHALLENGE_TOKEN_INVALID — JWT signature/decode failed."""

    def __init__(self, *, reason: str, trace_id: str) -> None:
        super().__init__(f"deletion challenge token invalid: {reason}")
        self.message_ko = DELETION_CHALLENGE_TOKEN_INVALID_KO
        self.error_code = ERROR_CODE_DELETION_CHALLENGE_TOKEN_INVALID
        self.reason = reason
        self.trace_id = trace_id


class DeletionChallengeTokenExpiredError(Exception):
    """401 DELETION_CHALLENGE_TOKEN_EXPIRED — past 5-min TTL."""

    def __init__(self, *, token_jti: str, expired_at: int) -> None:
        super().__init__(
            f"deletion challenge token expired (jti={token_jti}, expired_at={expired_at})"
        )
        self.message_ko = DELETION_CHALLENGE_TOKEN_EXPIRED_KO
        self.error_code = ERROR_CODE_DELETION_CHALLENGE_TOKEN_EXPIRED
        self.token_jti = token_jti
        self.expired_at = expired_at


class DeletionConsentEncryptionError(Exception):
    """500 DELETION_CONSENT_ENCRYPTION_FAILED — AES-256-GCM encrypt failure."""

    def __init__(self, *, tenant_id: str, reason: str) -> None:
        super().__init__(f"deletion consent encryption failed: {reason}")
        self.message_ko = DELETION_CONSENT_ENCRYPTION_FAILED_KO
        self.error_code = ERROR_CODE_DELETION_CONSENT_ENCRYPTION_FAILED
        self.tenant_id = tenant_id
        self.reason = reason


class DeletionConsentDecryptionError(Exception):
    """500 DELETION_CONSENT_DECRYPTION_FAILED — AES-256-GCM decrypt failure."""

    def __init__(self, *, tenant_id: str, reason: str) -> None:
        super().__init__(f"deletion consent decryption failed: {reason}")
        self.message_ko = DELETION_CONSENT_DECRYPTION_FAILED_KO
        self.error_code = ERROR_CODE_DELETION_CONSENT_DECRYPTION_FAILED
        self.tenant_id = tenant_id
        self.reason = reason


class AccountDeletionAuditEmitError(Exception):
    """503 ACCOUNT_DELETION_AUDIT_EMIT_FAILED — audit-first guard failed.

    HTTP envelope (AD-15 §4): 503 + Retry-After: 5 (transient audit subsystem
    blip — retry-able, mirror CR 11-3 ReopenAuditEmitFailedError precedent).
    """

    def __init__(self, *, action: str, tenant_id: str, reason: str) -> None:
        super().__init__(f"audit emit failed (action={action}, tenant_id={tenant_id}): {reason}")
        self.message_ko = ACCOUNT_DELETION_AUDIT_EMIT_FAILED_KO
        self.error_code = ERROR_CODE_ACCOUNT_DELETION_AUDIT_EMIT_FAILED
        self.action = action
        self.tenant_id = tenant_id
        self.reason = reason


class AccountDeletionHardDeleteError(Exception):
    """500 ACCOUNT_DELETION_HARD_DELETE_FAILED — cron hard-delete failure."""

    def __init__(self, *, tenant_id: str, reason: str) -> None:
        super().__init__(f"hard delete failed (tenant_id={tenant_id}): {reason}")
        self.message_ko = ACCOUNT_DELETION_HARD_DELETE_FAILED_KO
        self.error_code = ERROR_CODE_ACCOUNT_DELETION_HARD_DELETE_FAILED
        self.tenant_id = tenant_id
        self.reason = reason


# ── Typed results ────────────────────────────────────────────
@dataclass
class DeletionChallengeTokenIssued:
    """Result of `issue_deletion_challenge_token`."""

    token: str
    expires_at: datetime
    jti: str


@dataclass
class DeletionResult:
    """Result of `request_deletion` / `cancel_deletion`."""

    tenant_id: str
    status: str  # TenantDeletionStatus value
    deletion_scheduled_for: datetime  # tz-aware UTC
    envelope: DeletionRequestEnvelope


@dataclass
class DeletionStatusResponse:
    """Read-only snapshot for `get_deletion_status`."""

    tenant_id: str
    status: str
    deletion_requested_at: datetime | None
    deletion_requested_by_user_id: str | None
    deletion_consent_id: str | None
    deletion_scheduled_for: datetime | None


@dataclass
class HardDeleteResult:
    """Result of `hard_delete_expired_tenants`."""

    deleted_tenant_ids: list[str]
    failed_tenant_ids: list[tuple[str, str]]  # (tenant_id, reason)


# ── Service class ────────────────────────────────────────────
class DeletionService:
    """Story 12.3 account deletion service (destructive endpoint).

    CR 12-5 L3 3-layer TOTP defense:
    - Layer 1 (route): `require_role("owner")` + 2FA setup verified check
    - Layer 2 (service): `verify_totp_challenge(token, user)` delegation
    - Layer 3 (handler): `audit-first emit BEFORE raise` (CR 1.1 invariant)
    """

    def __init__(
        self,
        session: AsyncSession,
        *,
        tenant_id: str,
        actor_id: str,
        trace_id: str,
    ) -> None:
        self.session = session
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.trace_id = trace_id

    # ── Layer 2: issue_deletion_challenge_token ─────────────
    async def issue_deletion_challenge_token(
        self,
        *,
        current_code: str,
    ) -> DeletionChallengeTokenIssued:
        """Mint short-lived JWT after verify_totp_code (Layer 2).

        CR 12-5 L3 Layer 2 — verify 6-digit TOTP code BEFORE minting
        the challenge token. Token is bound to (user_id, tenant_id,
        purpose="account_deletion") and 5-min TTL.
        """
        # Fetch user (caller-controlled — no module-level clock).
        user = await self._load_user(self.actor_id, self.tenant_id)
        totp_state = _to_totp_state(user)
        now_ts = int(time.time())
        # Lockout check (5회 실패 시 429)
        raise_if_locked(totp_state, now=now_ts)
        if not user.totp_secret:
            raise TotpInvalidCodeError(
                "TOTP not registered — issue_deletion_challenge_token requires 2FA setup"
            )
        # Decrypt TOTP secret (mirror two_factor_service.py: AAD = b"totp_secret")
        secret_bytes = decrypt_at_rest(
            user.totp_secret, key_id=DEFAULT_KEY_ID, aad=b"totp_secret"
        )
        # Verify code (Layer 2 — re-verify at service entry)
        passed = verify_totp_code(secret_bytes, current_code, timestamp=now_ts)
        if not passed:
            # Increment failed_attempts + audit `deletion_2fa_failed`
            await self._increment_failed_attempts(user, totp_state, now=now_ts)
            raise TotpInvalidCodeError(
                f"invalid TOTP code (failed_attempts={totp_state.failed_attempts + 1})"
            )
        # Mint PyJWT (HS256) — `verify_exp=False` later + caller-controlled now.
        settings = get_settings()
        jti = str(uuid.uuid4())
        issued_at = now_ts
        expires_at_ts = now_ts + DELETION_CHALLENGE_TOKEN_TTL_SECONDS
        payload = {
            "purpose": DELETION_CHALLENGE_TOKEN_PURPOSE,
            "user_id": str(user.id),
            "tenant_id": self.tenant_id,
            "jti": jti,
            "iat": issued_at,
            "exp": expires_at_ts,
        }
        token = jwt.encode(payload, settings.supabase_jwt_secret, algorithm="HS256")
        # Audit-first emit (CR 1.1) — `two_factor_verified` BEFORE returning token.
        await self._record_audit(
            action=ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED,
            payload={
                "tenant_id": self.tenant_id,
                "owner_id": self.actor_id,
                "jti": jti,
                "purpose": DELETION_CHALLENGE_TOKEN_PURPOSE,
                "trace_id": self.trace_id,
            },
        )
        return DeletionChallengeTokenIssued(
            token=token,
            expires_at=datetime.fromtimestamp(expires_at_ts, tz=UTC),
            jti=jti,
        )

    # ── Layer 2: request_deletion (CRITICAL destructive endpoint) ──
    async def request_deletion(
        self,
        *,
        challenge_token: str,
        consent_checked: bool,
        consent_text: str,
        consent_ip: str | None = None,
        consent_user_agent: str | None = None,
        now: datetime | None = None,
    ) -> DeletionResult:
        """Destructive endpoint — 3-layer TOTP defense + audit-first.

        CR 12-5 L3 — Layer 2 re-verify + Layer 3 audit-first BEFORE state
        transition. On ANY exception path, audit row is guaranteed.
        """
        now = now or datetime.now(UTC)
        now_ts = int(now.timestamp())
        # ── Consent pre-checks (fail-fast) ─────────────────
        if not consent_checked:
            raise DeletionConsentRequiredError(tenant_id=self.tenant_id)
        # Validate consent text matches expected template verbatim.
        validate_consent_text(consent_text)
        # ── Layer 2 — re-verify challenge token (no trust boundary) ──
        claims = self._decode_challenge_token(challenge_token, now=now_ts)
        # ── Verify ownership (caller pre-resolved via require_role) ──
        await self._verify_owner(claims)
        # ── Fetch tenant + assert status FSM (active → pending_deletion) ──
        tenant = await self._load_tenant(self.tenant_id)
        snapshot = self._to_deletion_state(tenant)
        assert_status_transition(
            TenantDeletionStatus(snapshot.status),
            TenantDeletionStatus.PENDING_DELETION,
            tenant_id=self.tenant_id,
        )
        # ── Encrypt consent text (AES-256-GCM, distinct AAD) ──
        try:
            encrypted = encrypt_at_rest(
                consent_text.encode("utf-8"),
                key_id=DEFAULT_KEY_ID,
                aad=DELETION_CONSENT_AAD,
            )
        except Exception as exc:
            raise DeletionConsentEncryptionError(
                tenant_id=self.tenant_id, reason=str(exc)
            ) from exc
        consent_id = uuid.uuid4()
        consent_hash = compute_consent_hash(
            consent_text, salt=str(self.tenant_id)
        )
        # ── Insert deletion_consents row (CR 11-3 audit rename — 2-row append) ──
        consent_row = DeletionConsent(
            consent_id=consent_id,
            tenant_id=tenant.id,
            consent_text_hash=consent_hash,
            encrypted_consent_text=encrypted,
            consent_checked_at=now,
            consent_checked_by_user_id=uuid.UUID(self.actor_id),
            consent_ip=consent_ip,
            consent_user_agent=consent_user_agent,
        )
        self.session.add(consent_row)
        # ── Audit FIRST (CR 1.1 invariant) — 2 rows: consent_given + requested ──
        scheduled_for = compute_deletion_scheduled_for(now)
        try:
            await self._record_audit(
                action=ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN,
                payload={
                    "tenant_id": self.tenant_id,
                    "owner_id": self.actor_id,
                    "consent_id": str(consent_id),
                    "consent_text_hash": consent_hash,
                    "trace_id": self.trace_id,
                },
            )
            await self._record_audit(
                action=ACCOUNT_DELETION_ACTION_DELETION_REQUESTED,
                payload={
                    "tenant_id": self.tenant_id,
                    "owner_id": self.actor_id,
                    "consent_id": str(consent_id),
                    "deletion_scheduled_for": scheduled_for.isoformat(),
                    "trace_id": self.trace_id,
                },
            )
        except AccountDeletionAuditEmitError:
            # Audit emit failed — do NOT transition state (idempotent rollback).
            # Re-raise so handler emits 503 envelope.
            raise
        # ── Transition tenants.status FSM ──
        tenant.status = TenantDeletionStatus.PENDING_DELETION.value
        tenant.deletion_requested_at = now
        tenant.deletion_requested_by_user_id = uuid.UUID(self.actor_id)
        tenant.deletion_consent_id = consent_id
        tenant.deletion_scheduled_for = scheduled_for
        await self.session.flush()
        # ── Build envelope for response ──
        envelope = build_deletion_envelope(
            tenant_id=self.tenant_id,
            status=TenantDeletionStatus.PENDING_DELETION,
            deletion_requested_at=now,
            deletion_scheduled_for=scheduled_for,
            consent_id=str(consent_id),
        )
        return DeletionResult(
            tenant_id=self.tenant_id,
            status=tenant.status,
            deletion_scheduled_for=scheduled_for,
            envelope=envelope,
        )

    # ── cancel_deletion ─────────────────────────────────────
    async def cancel_deletion(self) -> DeletionResult:
        """Owner cancel — transition pending_deletion → active."""
        tenant = await self._load_tenant(self.tenant_id)
        snapshot = self._to_deletion_state(tenant)
        assert_status_transition(
            TenantDeletionStatus(snapshot.status),
            TenantDeletionStatus.ACTIVE,
            tenant_id=self.tenant_id,
        )
        # Audit FIRST (CR 1.1 invariant)
        await self._record_audit(
            action=ACCOUNT_DELETION_ACTION_DELETION_CANCELLED,
            payload={
                "tenant_id": self.tenant_id,
                "owner_id": self.actor_id,
                "trace_id": self.trace_id,
            },
        )
        # Transition
        tenant.status = TenantDeletionStatus.ACTIVE.value
        tenant.deletion_scheduled_for = None
        await self.session.flush()
        envelope = build_deletion_envelope(
            tenant_id=self.tenant_id,
            status=TenantDeletionStatus.ACTIVE,
            deletion_requested_at=datetime.now(UTC),
            deletion_scheduled_for=datetime.now(UTC),
            consent_id=snapshot.deletion_consent_id or "",
        )
        return DeletionResult(
            tenant_id=self.tenant_id,
            status=tenant.status,
            deletion_scheduled_for=tenant.deletion_scheduled_for or datetime.now(UTC),
            envelope=envelope,
        )

    # ── get_deletion_status ─────────────────────────────────
    async def get_deletion_status(self) -> DeletionStatusResponse:
        """Read-only snapshot — owner-only."""
        tenant = await self._load_tenant(self.tenant_id)
        snapshot = self._to_deletion_state(tenant)
        if snapshot.status == TenantDeletionStatus.DELETED.value:
            raise AccountAlreadyDeletedError(tenant_id=self.tenant_id)
        return DeletionStatusResponse(
            tenant_id=snapshot.tenant_id,
            status=snapshot.status,
            deletion_requested_at=_parse_iso_or_none(snapshot.deletion_requested_at),
            deletion_requested_by_user_id=snapshot.deletion_requested_by_user_id or None,
            deletion_consent_id=snapshot.deletion_consent_id or None,
            deletion_scheduled_for=_parse_iso_or_none(snapshot.deletion_scheduled_for),
        )

    # ── hard_delete_expired_tenants (cron-callable) ────────
    async def hard_delete_expired_tenants(
        self,
        *,
        cutoff: datetime,
    ) -> HardDeleteResult:
        """Cron-callable — iterate expired tenants, soft-fail per tenant."""
        # Select all tenants where status='pending_deletion' AND
        # deletion_scheduled_for <= cutoff.
        result = await self.session.execute(
            select(Tenant).where(
                Tenant.status == TenantDeletionStatus.PENDING_DELETION.value,
                Tenant.deletion_scheduled_for <= cutoff,
            )
        )
        expired_tenants = result.scalars().all()
        deleted_ids: list[str] = []
        failed_ids: list[tuple[str, str]] = []
        for tenant in expired_tenants:
            tenant_id_str = str(tenant.id)
            try:
                await self._hard_delete_one(tenant)
                deleted_ids.append(tenant_id_str)
            except Exception as exc:
                # Per-tenant soft-fail — audit `deletion_failed` and continue.
                failed_ids.append((tenant_id_str, str(exc)))
                await self._record_audit_safe(
                    action=ACCOUNT_DELETION_ACTION_DELETION_FAILED,
                    payload={
                        "tenant_id": tenant_id_str,
                        "owner_id": self.actor_id,
                        "reason": str(exc),
                        "phase": "hard_delete",
                        "trace_id": self.trace_id,
                    },
                )
        return HardDeleteResult(
            deleted_tenant_ids=deleted_ids,
            failed_tenant_ids=failed_ids,
        )

    async def run_hard_delete_cron(
        self,
        *,
        now: datetime | None = None,
    ) -> HardDeleteResult:
        """Thin wrapper — `apps.api.jobs.tenant_hard_delete` cron entry."""
        now = now or datetime.now(UTC)
        return await self.hard_delete_expired_tenants(cutoff=now)

    # ── ORM→kernel boundary (CR 12-1 L3) ──────────────────
    def _to_deletion_state(self, tenant: Tenant) -> DeletionStatusSnapshot:
        """Convert SQLAlchemy Tenant row → pure-kernel DeletionStatusSnapshot.

        Service→kernel boundary — kernel NEVER touches SQLAlchemy ORM.
        """
        return DeletionStatusSnapshot(
            tenant_id=str(tenant.id),
            status=tenant.status,
            deletion_requested_at=(
                tenant.deletion_requested_at.isoformat() if tenant.deletion_requested_at else ""
            ),
            deletion_requested_by_user_id=(
                str(tenant.deletion_requested_by_user_id)
                if tenant.deletion_requested_by_user_id
                else ""
            ),
            deletion_consent_id=(
                str(tenant.deletion_consent_id) if tenant.deletion_consent_id else ""
            ),
            deletion_scheduled_for=(
                tenant.deletion_scheduled_for.isoformat()
                if tenant.deletion_scheduled_for
                else ""
            ),
        )

    # ── Private helpers ────────────────────────────────────
    async def _load_user(self, user_id: str, tenant_id: str) -> User:  # noqa: ARG002
        # tenant_id kept in signature for parity with other M12 services; not
        # used here because user_id is globally unique (PK) and tenant context
        # is enforced via the async session RLS listener (AD-3).

        result = await self.session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise TotpInvalidCodeError(f"user not found (id={user_id})")
        return user

    async def _load_tenant(self, tenant_id: str) -> Tenant:
        result = await self.session.execute(
            select(Tenant).where(Tenant.id == uuid.UUID(tenant_id))
        )
        tenant = result.scalar_one_or_none()
        if tenant is None:
            raise AccountDeletionNotOwnerError(actor_role="unknown")
        return tenant

    async def _verify_owner(self, claims: dict[str, Any]) -> None:
        """Verify owner role (Layer 1 caller pre-resolved, Layer 2 re-check)."""
        # Caller pre-resolves via require_role("owner") — re-check tenant_id match.
        if claims.get("tenant_id") != self.tenant_id:
            raise DeletionChallengeTokenInvalidError(
                reason="tenant_id mismatch",
                trace_id=self.trace_id,
            )
        if claims.get("user_id") != self.actor_id:
            raise DeletionChallengeTokenInvalidError(
                reason="user_id mismatch",
                trace_id=self.trace_id,
            )

    def _decode_challenge_token(self, token: str, *, now: int) -> dict[str, Any]:
        """PyJWT decode — verify_exp=False + caller-controlled now (CR 12-1 L1)."""
        settings = get_settings()
        try:
            claims = jwt.decode(
                token,
                settings.supabase_jwt_secret,
                algorithms=["HS256"],
                options={
                    "require": ["exp", "iat", "purpose", "user_id", "tenant_id", "jti"],
                    "verify_exp": False,  # caller-controlled now check below
                },
            )
        except jwt.PyJWTError as exc:
            raise DeletionChallengeTokenInvalidError(
                reason=str(exc), trace_id=self.trace_id
            ) from exc
        # Manual exp check (caller-controlled now)
        exp = claims.get("exp", 0)
        if now >= exp:
            raise DeletionChallengeTokenExpiredError(
                token_jti=claims.get("jti", ""),
                expired_at=exp,
            )
        # Purpose claim must match
        if claims.get("purpose") != DELETION_CHALLENGE_TOKEN_PURPOSE:
            raise DeletionChallengeTokenInvalidError(
                reason="purpose mismatch",
                trace_id=self.trace_id,
            )
        return claims

    async def _increment_failed_attempts(
        self, user: User, state: UserTotpState, *, now: int
    ) -> None:
        """Increment failed_attempts + lockout if threshold reached."""
        new_count = state.failed_attempts + 1
        await self.session.execute(
            update(User)
            .where(User.id == user.id)
            .values(totp_failed_attempts=new_count)
        )
        if new_count >= MAX_FAILED_ATTEMPTS:
            lockout_until = now + 900  # 15 min
            await self.session.execute(
                update(User)
                .where(User.id == user.id)
                .values(totp_lockout_until=lockout_until)
            )
        await self.session.flush()

    async def _record_audit(
        self,
        *,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        """Emit audit row BEFORE state transition (CR 1.1 invariant).

        Raises AccountDeletionAuditEmitError on failure (handler emits 503).
        """
        try:
            await emit_audit_typed(
                self.session,
                action_class=ActionClass.ACCOUNT_DELETION,
                action=action,
                actor_id=uuid.UUID(self.actor_id),
                target_id=uuid.UUID(self.tenant_id),
                reason=f"account_deletion: {action}",
                payload=payload,
                tenant_id=uuid.UUID(self.tenant_id),
                flush=True,
            )
        except Exception as exc:
            raise AccountDeletionAuditEmitError(
                action=action,
                tenant_id=self.tenant_id,
                reason=str(exc),
            ) from exc

    async def _record_audit_safe(
        self,
        *,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        """Audit emit WITHOUT raise — for cron soft-fail paths (best-effort)."""
        with contextlib.suppress(Exception):
            await self._record_audit(action=action, payload=payload)

    async def _hard_delete_one(self, tenant: Tenant) -> None:
        """Hard-delete single tenant + cascade FK chain."""
        tenant_id_str = str(tenant.id)
        # Audit FIRST (CR 1.1) — `tenant_hard_deleted` BEFORE DELETE.
        await self._record_audit(
            action=ACCOUNT_DELETION_ACTION_TENANT_HARD_DELETED,
            payload={
                "tenant_id": tenant_id_str,
                "owner_id": self.actor_id,
                "trace_id": self.trace_id,
            },
        )
        # DELETE tenant (cascade FK chain — products, bom_lines,
        # monthly_input_periods, monthly_input_rows, fiscal_period_snapshots,
        # fiscal_periods, tenant_backups, deletion_consents, ai_documents,
        # input_drafts, m2_user_invitations).
        await self.session.delete(tenant)
        await self.session.flush()


# ── Helpers ─────────────────────────────────────────────────
def _parse_iso_or_none(value: str) -> datetime | None:
    """Parse ISO-8601 string → tz-aware datetime. Returns None if empty."""
    if not value:
        return None
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


__all__ = [
    # constants
    "DELETION_CHALLENGE_TOKEN_PURPOSE",
    "DELETION_CHALLENGE_TOKEN_TTL_SECONDS",
    "DELETION_CONSENT_AAD",
    "ERROR_CODE_DELETION_CHALLENGE_TOKEN_INVALID",
    "ERROR_CODE_DELETION_CHALLENGE_TOKEN_EXPIRED",
    "ERROR_CODE_DELETION_CONSENT_ENCRYPTION_FAILED",
    "ERROR_CODE_DELETION_CONSENT_DECRYPTION_FAILED",
    "ERROR_CODE_ACCOUNT_DELETION_AUDIT_EMIT_FAILED",
    "ERROR_CODE_ACCOUNT_DELETION_HARD_DELETE_FAILED",
    "DELETION_CHALLENGE_TOKEN_INVALID_KO",
    "DELETION_CHALLENGE_TOKEN_EXPIRED_KO",
    "DELETION_CONSENT_ENCRYPTION_FAILED_KO",
    "DELETION_CONSENT_DECRYPTION_FAILED_KO",
    "ACCOUNT_DELETION_AUDIT_EMIT_FAILED_KO",
    "ACCOUNT_DELETION_HARD_DELETE_FAILED_KO",
    # typed exceptions
    "DeletionChallengeTokenInvalidError",
    "DeletionChallengeTokenExpiredError",
    "DeletionConsentEncryptionError",
    "DeletionConsentDecryptionError",
    "AccountDeletionAuditEmitError",
    "AccountDeletionHardDeleteError",
    # typed results
    "DeletionChallengeTokenIssued",
    "DeletionResult",
    "DeletionStatusResponse",
    "HardDeleteResult",
    # service
    "DeletionService",
]
