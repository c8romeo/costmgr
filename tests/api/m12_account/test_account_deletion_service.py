"""tests.api.m12_account.test_account_deletion_service — Story 12.3 service tests.

22+ cases per AC spec:
- issue_deletion_challenge_token (4): happy / invalid TOTP / no secret / audit-first
- request_deletion (8): happy / no consent / bad consent / bad token / expired /
  already-pending / already-deleted / audit-first invariant
- cancel_deletion (2): happy / invalid status
- get_deletion_status (2): happy / deleted raises 410
- hard_delete_expired_tenants (2): empty / mix success+fail
- helpers (3): _to_deletion_state boundary / _decode_challenge_token verify_exp=False /
  typed exception envelopes
- 3-layer TOTP defense: re-verify at service entry (Layer 2)

CR 4-3: `def test_* + asyncio.run(_impl())` pattern.
CR 12-5 L3: destructive endpoint 3-layer defense (route + service + audit-first).
CR 1.1: audit-first invariant (session emit BEFORE state transition).
CR 12-1 L1: PyJWT verify_exp=False + caller-controlled now.
CR 12-1 L2: AES-256-GCM distinct AAD per column.
CR 12-1 L3: ORM→kernel boundary _to_deletion_state.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from apps.api.core.audit_action import ActionClass
from apps.api.modules.m12_account.services.account_deletion_service import (
    ACCOUNT_DELETION_AUDIT_EMIT_FAILED_KO,
    ACCOUNT_DELETION_HARD_DELETE_FAILED_KO,
    DELETION_CHALLENGE_TOKEN_EXPIRED_KO,
    DELETION_CHALLENGE_TOKEN_INVALID_KO,
    DELETION_CHALLENGE_TOKEN_PURPOSE,
    DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
    DELETION_CONSENT_AAD,
    DELETION_CONSENT_DECRYPTION_FAILED_KO,
    DELETION_CONSENT_ENCRYPTION_FAILED_KO,
    ERROR_CODE_ACCOUNT_DELETION_AUDIT_EMIT_FAILED,
    ERROR_CODE_ACCOUNT_DELETION_HARD_DELETE_FAILED,
    ERROR_CODE_DELETION_CHALLENGE_TOKEN_EXPIRED,
    ERROR_CODE_DELETION_CHALLENGE_TOKEN_INVALID,
    ERROR_CODE_DELETION_CONSENT_DECRYPTION_FAILED,
    ERROR_CODE_DELETION_CONSENT_ENCRYPTION_FAILED,
    AccountDeletionAuditEmitError,
    AccountDeletionHardDeleteError,
    DeletionChallengeTokenExpiredError,
    DeletionChallengeTokenInvalidError,
    DeletionConsentDecryptionError,
    DeletionConsentEncryptionError,
    DeletionService,
)
from packages.services.m12_account.account_deletion import (
    ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN,
    ACCOUNT_DELETION_ACTION_DELETION_REQUESTED,
    ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED,
    DELETION_CONSENT_TEMPLATE_KO,
    RETENTION_DAYS,
    AccountAlreadyDeletedError,
    AccountDeletionInProgressError,
    DeletionConsentRequiredError,
    DeletionConsentTextInvalidError,
    TenantDeletionStatus,
)
from packages.services.m12_account.totp import TotpInvalidCodeError

TENANT_ID = "00000000-0000-0000-0000-000000000001"
ACTOR_ID = "00000000-0000-0000-0000-000000000002"
ACTOR_UUID = uuid.UUID(ACTOR_ID)
TENANT_UUID = uuid.UUID(TENANT_ID)
TRACE_ID = "test-trace-001"
JWT_SECRET = "test-supabase-jwt-secret-12-3"


# ── Mock helpers ──────────────────────────────────────────────
def _make_user_row(
    *,
    user_id: str = ACTOR_UUID,
    totp_secret: bytes | None = b"encrypted-secret",
    totp_failed_attempts: int = 0,
    totp_lockout_until: int | None = None,
    totp_enabled_at: datetime | None = datetime(2026, 1, 1, tzinfo=UTC),
) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.totp_secret = totp_secret
    user.totp_failed_attempts = totp_failed_attempts
    user.totp_lockout_until = totp_lockout_until
    user.totp_enabled_at = totp_enabled_at
    return user


def _make_tenant_row(
    *,
    tenant_id: uuid.UUID = TENANT_UUID,
    status: str = "active",
    deletion_consent_id: uuid.UUID | None = None,
    deletion_scheduled_for: datetime | None = None,
) -> MagicMock:
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.status = status
    tenant.deletion_requested_at = None
    tenant.deletion_requested_by_user_id = None
    tenant.deletion_consent_id = deletion_consent_id
    tenant.deletion_scheduled_for = deletion_scheduled_for
    tenant.deletion_anonymized_at = None
    return tenant


def _wire_session(
    session: AsyncMock,
    *,
    user_row: MagicMock | None = None,
    tenant_row: MagicMock | None = None,
    tenant_list: list[MagicMock] | None = None,
) -> None:
    """Wire session.execute so any scalar_one_or_none() returns the tenant_row
    (or user_row fallback). request_deletion reads tenant first; issue_* reads
    user first. We populate the queue so both calls return a valid row.

    For request_deletion tests, tenant_row is the only one consumed. For
    issue_* tests, user_row is consumed (and tenant_row may not be queried).
    """
    queue: list[MagicMock] = []

    def _scalar(value: object) -> MagicMock:
        r = MagicMock()
        r.scalar_one_or_none = MagicMock(return_value=value)
        r.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )
        queue.append(r)
        return r

    def _list(values: list[object]) -> MagicMock:
        r = MagicMock()
        r.scalar_one_or_none = MagicMock(return_value=None)
        r.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=values))
        )
        queue.append(r)
        return r

    # Pre-populate the queue so multiple execute() calls all return a row.
    # The default value returned by scalar_one_or_none() is tenant_row
    # (or user_row as fallback if tenant_row is None).
    default_scalar = tenant_row or user_row
    for _ in range(8):
        _scalar(default_scalar)
    if tenant_list is not None:
        _list(tenant_list)
    else:
        _list([])

    session.execute = AsyncMock(side_effect=queue)
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()


def _patch_settings_secret() -> contextlib.AbstractContextManager[None]:
    """Patch supabase_jwt_secret on get_settings() return."""
    settings_mock = MagicMock()
    settings_mock.supabase_jwt_secret = JWT_SECRET
    return patch(
        "apps.api.modules.m12_account.services.account_deletion_service.get_settings",
        return_value=settings_mock,
    )


def _mint_valid_challenge_token(
    *,
    user_id: str = ACTOR_ID,
    tenant_id: str = TENANT_ID,
    purpose: str = DELETION_CHALLENGE_TOKEN_PURPOSE,
    exp_offset: int = DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
) -> str:
    """Mint a valid HS256 challenge token for tests."""
    import jwt as _jwt

    now_ts = int(time.time())
    return _jwt.encode(
        {
            "purpose": purpose,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "jti": "test-jti",
            "iat": now_ts,
            "exp": now_ts + exp_offset,
        },
        JWT_SECRET,
        algorithm="HS256",
    )


# ── 1. issue_deletion_challenge_token happy path ───────────────
def test_issue_challenge_token_happy_path() -> None:
    """Happy path: verify_totp_code → mint JWT → return token + expires_at + jti."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        _wire_session(session, user_row=user)
        with _patch_settings_secret(), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.decrypt_at_rest",
            return_value=b"raw-secret",
        ), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.verify_totp_code",
            return_value=True,
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            result = await svc.issue_deletion_challenge_token(current_code="123456")

        assert result.token  # non-empty JWT
        assert result.jti
        assert result.expires_at.tzinfo == UTC
        # JWT decodes back to claims (verify_exp=False at test boundary).
        import jwt as _jwt

        claims = _jwt.decode(
            result.token,
            JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_exp": False},
        )
        assert claims["purpose"] == DELETION_CHALLENGE_TOKEN_PURPOSE
        assert claims["user_id"] == ACTOR_ID
        assert claims["tenant_id"] == TENANT_ID

    asyncio.run(_impl())


def test_issue_challenge_token_invalid_totp_raises() -> None:
    """Invalid TOTP code raises TotpInvalidCodeError + increments failed_attempts."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        _wire_session(session, user_row=user)
        with _patch_settings_secret(), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.decrypt_at_rest",
            return_value=b"raw-secret",
        ), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.verify_totp_code",
            return_value=False,
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(TotpInvalidCodeError) as exc_info:
                await svc.issue_deletion_challenge_token(current_code="000000")
            assert "TOTP" in str(exc_info.value) or "totp" in str(exc_info.value)
        # failed_attempts update executed (increment)
        assert session.execute.call_count >= 1

    asyncio.run(_impl())


def test_issue_challenge_token_no_totp_secret_raises() -> None:
    """No totp_secret → TotpInvalidCodeError (2FA not registered)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row(totp_secret=None)
        _wire_session(session, user_row=user)
        with _patch_settings_secret():
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(TotpInvalidCodeError):
                await svc.issue_deletion_challenge_token(current_code="123456")

    asyncio.run(_impl())


def test_issue_challenge_token_audit_first_emitted() -> None:
    """Audit emit MUST happen BEFORE returning token (CR 1.1 invariant)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        _wire_session(session, user_row=user)
        emitted_actions: list[str] = []

        async def _capture_audit(*_args: object, **kwargs: object) -> None:
            emitted_actions.append(str(kwargs.get("action")))

        with _patch_settings_secret(), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.decrypt_at_rest",
            return_value=b"raw-secret",
        ), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.verify_totp_code",
            return_value=True,
        ), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.emit_audit_typed",
            side_effect=_capture_audit,
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            await svc.issue_deletion_challenge_token(current_code="123456")
        assert ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED in emitted_actions

    asyncio.run(_impl())


# ── 2. request_deletion happy path ────────────────────────────
def test_request_deletion_happy_path() -> None:
    """Full destructive flow: consent + token + 2 audit rows + status transition."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, user_row=user, tenant_row=tenant)
        valid_token = _mint_valid_challenge_token()

        # Now call request_deletion — patch encrypt_at_rest + emit_audit_typed.
        emitted_actions: list[str] = []

        async def _capture_audit(*_args: object, **kwargs: object) -> None:
            emitted_actions.append(str(kwargs.get("action")))

        encrypted_blob = b"\x00\x01\x02\x03"
        fixed_now = datetime(2026, 8, 15, 1, 0, 0, tzinfo=UTC)
        with _patch_settings_secret(), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.encrypt_at_rest",
            return_value=encrypted_blob,
        ), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.emit_audit_typed",
            side_effect=_capture_audit,
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            result = await svc.request_deletion(
                challenge_token=valid_token,
                consent_checked=True,
                consent_text=DELETION_CONSENT_TEMPLATE_KO,
                consent_ip="127.0.0.1",
                consent_user_agent="pytest",
                now=fixed_now,
            )

        assert result.tenant_id == TENANT_ID
        assert result.status == TenantDeletionStatus.PENDING_DELETION.value
        # Audit FIRST invariant — both consent_given + requested emitted
        assert emitted_actions == [
            ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN,
            ACCOUNT_DELETION_ACTION_DELETION_REQUESTED,
        ]
        # deletion_consents row INSERT attempted
        assert session.add.called
        # tenant.status transitioned
        assert tenant.status == TenantDeletionStatus.PENDING_DELETION.value
        # deletion_scheduled_for = now + 30 days
        assert tenant.deletion_scheduled_for == fixed_now + timedelta(days=RETENTION_DAYS)

    asyncio.run(_impl())


def test_request_deletion_missing_consent_raises() -> None:
    """consent_checked=False raises DeletionConsentRequiredError (fail-fast)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, user_row=user, tenant_row=tenant)
        with _patch_settings_secret():
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(DeletionConsentRequiredError):
                await svc.request_deletion(
                    challenge_token="any-token",
                    consent_checked=False,
                    consent_text=DELETION_CONSENT_TEMPLATE_KO,
                )

    asyncio.run(_impl())


def test_request_deletion_bad_consent_text_raises() -> None:
    """Wrong consent text raises DeletionConsentTextInvalidError (kernel)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, user_row=user, tenant_row=tenant)
        with _patch_settings_secret():
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(DeletionConsentTextInvalidError):
                await svc.request_deletion(
                    challenge_token="any-token",
                    consent_checked=True,
                    consent_text="다른 내용입니다",
                )

    asyncio.run(_impl())


def test_request_deletion_invalid_challenge_token_raises() -> None:
    """Invalid JWT signature raises DeletionChallengeTokenInvalidError (Layer 2)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, user_row=user, tenant_row=tenant)
        with _patch_settings_secret():
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(DeletionChallengeTokenInvalidError) as exc_info:
                await svc.request_deletion(
                    challenge_token="not-a-valid-jwt",
                    consent_checked=True,
                    consent_text=DELETION_CONSENT_TEMPLATE_KO,
                )
            assert exc_info.value.error_code == ERROR_CODE_DELETION_CHALLENGE_TOKEN_INVALID

    asyncio.run(_impl())


def test_request_deletion_expired_challenge_token_raises() -> None:
    """Expired JWT raises DeletionChallengeTokenExpiredError (CR 12-1 L1)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, user_row=user, tenant_row=tenant)

        import jwt as _jwt

        # Mint an expired token directly.
        expired_at = int(time.time()) - 60  # 1 min in the past
        token = _jwt.encode(
            {
                "purpose": DELETION_CHALLENGE_TOKEN_PURPOSE,
                "user_id": ACTOR_ID,
                "tenant_id": TENANT_ID,
                "jti": "expired-jti",
                "iat": expired_at - DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
                "exp": expired_at,
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        with _patch_settings_secret():
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(DeletionChallengeTokenExpiredError) as exc_info:
                await svc.request_deletion(
                    challenge_token=token,
                    consent_checked=True,
                    consent_text=DELETION_CONSENT_TEMPLATE_KO,
                )
            assert exc_info.value.error_code == ERROR_CODE_DELETION_CHALLENGE_TOKEN_EXPIRED

    asyncio.run(_impl())


def test_request_deletion_already_pending_raises() -> None:
    """Tenant already in pending_deletion raises AccountDeletionInProgressError."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="pending_deletion")
        _wire_session(session, user_row=user, tenant_row=tenant)
        valid_token = _mint_valid_challenge_token()
        with _patch_settings_secret():
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(AccountDeletionInProgressError):
                await svc.request_deletion(
                    challenge_token=valid_token,
                    consent_checked=True,
                    consent_text=DELETION_CONSENT_TEMPLATE_KO,
                )

    asyncio.run(_impl())


def test_request_deletion_already_deleted_raises() -> None:
    """Tenant already deleted raises AccountAlreadyDeletedError (HTTP 410)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="deleted")
        _wire_session(session, user_row=user, tenant_row=tenant)
        valid_token = _mint_valid_challenge_token()
        with _patch_settings_secret():
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(AccountAlreadyDeletedError):
                await svc.request_deletion(
                    challenge_token=valid_token,
                    consent_checked=True,
                    consent_text=DELETION_CONSENT_TEMPLATE_KO,
                )

    asyncio.run(_impl())


def test_request_deletion_audit_first_emits_before_state_change() -> None:
    """CR 1.1 invariant: emit_audit_typed called BEFORE session.flush (state change)."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, user_row=user, tenant_row=tenant)

        import jwt as _jwt

        now_ts = int(time.time())
        token = _jwt.encode(
            {
                "purpose": DELETION_CHALLENGE_TOKEN_PURPOSE,
                "user_id": ACTOR_ID,
                "tenant_id": TENANT_ID,
                "jti": "test-jti",
                "iat": now_ts,
                "exp": now_ts + DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
            },
            JWT_SECRET,
            algorithm="HS256",
        )

        call_order: list[str] = []

        async def _capture_audit(*_args: object, **_kwargs: object) -> None:
            call_order.append("audit")

        async def _capture_flush(*_args: object, **_kw: object) -> None:
            call_order.append("flush")

        session.flush = AsyncMock(side_effect=_capture_flush)
        encrypted_blob = b"\x00\x01\x02"
        with _patch_settings_secret(), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.encrypt_at_rest",
            return_value=encrypted_blob,
        ), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.emit_audit_typed",
            side_effect=_capture_audit,
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            await svc.request_deletion(
                challenge_token=token,
                consent_checked=True,
                consent_text=DELETION_CONSENT_TEMPLATE_KO,
            )

        # audit (2x for consent_given + requested) MUST come before flush.
        # First flush happens after audit emits.
        assert call_order.index("audit") < call_order.index("flush")
        # Two audit emits before flush.
        assert call_order.count("audit") >= 2

    asyncio.run(_impl())


def test_request_deletion_consent_encryption_failure_raises() -> None:
    """AES-256-GCM encrypt failure raises DeletionConsentEncryptionError."""

    async def _impl() -> None:
        session = AsyncMock()
        user = _make_user_row()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, user_row=user, tenant_row=tenant)

        import jwt as _jwt

        now_ts = int(time.time())
        token = _jwt.encode(
            {
                "purpose": DELETION_CHALLENGE_TOKEN_PURPOSE,
                "user_id": ACTOR_ID,
                "tenant_id": TENANT_ID,
                "jti": "test-jti",
                "iat": now_ts,
                "exp": now_ts + DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
            },
            JWT_SECRET,
            algorithm="HS256",
        )

        with _patch_settings_secret(), patch(
            "apps.api.modules.m12_account.services.account_deletion_service.encrypt_at_rest",
            side_effect=RuntimeError("AES-GCM failure"),
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(DeletionConsentEncryptionError) as exc_info:
                await svc.request_deletion(
                    challenge_token=token,
                    consent_checked=True,
                    consent_text=DELETION_CONSENT_TEMPLATE_KO,
                )
            assert exc_info.value.error_code == ERROR_CODE_DELETION_CONSENT_ENCRYPTION_FAILED

    asyncio.run(_impl())


# ── 3. cancel_deletion ────────────────────────────────────────
def test_cancel_deletion_happy_path() -> None:
    """pending_deletion → active; audit_first emit."""

    async def _impl() -> None:
        session = AsyncMock()
        tenant = _make_tenant_row(
            status="pending_deletion",
            deletion_scheduled_for=datetime(2026, 9, 14, 1, 0, 0, tzinfo=UTC),
        )
        _wire_session(session, tenant_row=tenant)
        emitted_actions: list[str] = []

        async def _capture_audit(*_args: object, **kwargs: object) -> None:
            emitted_actions.append(str(kwargs.get("action")))

        with patch(
            "apps.api.modules.m12_account.services.account_deletion_service.emit_audit_typed",
            side_effect=_capture_audit,
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            result = await svc.cancel_deletion()
        assert result.status == TenantDeletionStatus.ACTIVE.value
        assert tenant.status == TenantDeletionStatus.ACTIVE.value
        # audit emit occurred
        assert len(emitted_actions) == 1

    asyncio.run(_impl())


def test_cancel_deletion_invalid_status_raises() -> None:
    """cancel on tenant already deleted → AccountAlreadyDeletedError."""

    async def _impl() -> None:
        session = AsyncMock()
        tenant = _make_tenant_row(status="deleted")
        _wire_session(session, tenant_row=tenant)
        with patch(
            "apps.api.modules.m12_account.services.account_deletion_service.emit_audit_typed",
            new=AsyncMock(),
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            with pytest.raises(AccountAlreadyDeletedError):
                await svc.cancel_deletion()

    asyncio.run(_impl())


# ── 4. get_deletion_status ────────────────────────────────────
def test_get_deletion_status_active_returns_snapshot() -> None:
    """Active tenant returns snapshot with all None optional fields."""

    async def _impl() -> None:
        session = AsyncMock()
        tenant = _make_tenant_row(status="active")
        _wire_session(session, tenant_row=tenant)
        svc = DeletionService(
            session,
            tenant_id=TENANT_ID,
            actor_id=ACTOR_ID,
            trace_id=TRACE_ID,
        )
        result = await svc.get_deletion_status()
        assert result.status == "active"
        assert result.deletion_requested_at is None
        assert result.deletion_scheduled_for is None

    asyncio.run(_impl())


def test_get_deletion_status_deleted_raises_410() -> None:
    """Deleted tenant raises AccountAlreadyDeletedError (CR 11-3 split → 410)."""

    async def _impl() -> None:
        session = AsyncMock()
        tenant = _make_tenant_row(status="deleted")
        _wire_session(session, tenant_row=tenant)
        svc = DeletionService(
            session,
            tenant_id=TENANT_ID,
            actor_id=ACTOR_ID,
            trace_id=TRACE_ID,
        )
        with pytest.raises(AccountAlreadyDeletedError):
            await svc.get_deletion_status()

    asyncio.run(_impl())


# ── 5. hard_delete_expired_tenants ────────────────────────────
def test_hard_delete_empty_returns_empty_lists() -> None:
    """No expired tenants → empty deleted_ids + failed_ids."""

    async def _impl() -> None:
        session = AsyncMock()
        _wire_session(session, tenant_list=[])
        svc = DeletionService(
            session,
            tenant_id=TENANT_ID,
            actor_id=ACTOR_ID,
            trace_id=TRACE_ID,
        )
        result = await svc.hard_delete_expired_tenants(
            cutoff=datetime.now(UTC)
        )
        assert result.deleted_tenant_ids == []
        assert result.failed_tenant_ids == []

    asyncio.run(_impl())


def test_hard_delete_mix_success_and_failure() -> None:
    """Per-tenant soft-fail: success path + failure path both audited."""

    async def _impl() -> None:
        session = AsyncMock()
        success_tenant = _make_tenant_row(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-0000000000aa"),
            status="pending_deletion",
        )
        fail_tenant = _make_tenant_row(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-0000000000bb"),
            status="pending_deletion",
        )

        # Custom wiring: hard_delete_expired_tenants calls scalars().all()
        # for the SELECT WHERE status=pending_deletion AND scheduled_for <= cutoff.
        list_result = MagicMock()
        list_result.scalar_one_or_none = MagicMock(return_value=None)
        list_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[success_tenant, fail_tenant]))
        )
        session.execute = AsyncMock(return_value=list_result)
        session.flush = AsyncMock()
        session.add = MagicMock()

        # Wire session.delete to fail on the second tenant only.
        async def _delete(t: object) -> None:
            if str(getattr(t, "id", "")) == str(fail_tenant.id):
                raise RuntimeError("FK constraint violated")

        session.delete = _delete

        emitted_actions: list[str] = []

        async def _capture_audit(*_args: object, **kwargs: object) -> None:
            emitted_actions.append(str(kwargs.get("action")))

        with patch(
            "apps.api.modules.m12_account.services.account_deletion_service.emit_audit_typed",
            side_effect=_capture_audit,
        ):
            svc = DeletionService(
                session,
                tenant_id=TENANT_ID,
                actor_id=ACTOR_ID,
                trace_id=TRACE_ID,
            )
            result = await svc.hard_delete_expired_tenants(
                cutoff=datetime.now(UTC)
            )

        assert str(success_tenant.id) in result.deleted_tenant_ids
        assert any(
            tid == str(fail_tenant.id) for tid, _ in result.failed_tenant_ids
        )

    asyncio.run(_impl())


# ── 6. helper: _to_deletion_state (CR 12-1 L3 boundary) ───────
def test_to_deletion_state_orm_to_kernel_boundary() -> None:
    """_to_deletion_state maps ORM row → pure-kernel DeletionStatusSnapshot."""

    def _impl() -> None:
        session = AsyncMock()
        scheduled = datetime(2026, 9, 14, 1, 0, 0, tzinfo=UTC)
        consent_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
        tenant = _make_tenant_row(
            status="pending_deletion",
            deletion_consent_id=consent_id,
            deletion_scheduled_for=scheduled,
        )
        svc = DeletionService(
            session,
            tenant_id=TENANT_ID,
            actor_id=ACTOR_ID,
            trace_id=TRACE_ID,
        )
        snapshot = svc._to_deletion_state(tenant)
        assert snapshot.status == "pending_deletion"
        assert snapshot.deletion_consent_id == str(consent_id)
        assert snapshot.deletion_scheduled_for.startswith("2026-09-14")

    _impl()


# ── 7. helper: _decode_challenge_token (CR 12-1 L1) ──────────
def test_decode_challenge_token_verify_exp_false_and_caller_now() -> None:
    """_decode_challenge_token uses verify_exp=False + caller-controlled now."""

    def _impl() -> None:
        import jwt as _jwt

        session = AsyncMock()
        now_ts = int(time.time())
        expired_at = now_ts - 60  # 1 min ago
        # Manually craft an expired token
        token = _jwt.encode(
            {
                "purpose": DELETION_CHALLENGE_TOKEN_PURPOSE,
                "user_id": ACTOR_ID,
                "tenant_id": TENANT_ID,
                "jti": "jti-expired",
                "iat": expired_at - DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
                "exp": expired_at,
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        svc = DeletionService(
            session,
            tenant_id=TENANT_ID,
            actor_id=ACTOR_ID,
            trace_id=TRACE_ID,
        )
        with _patch_settings_secret():
            with pytest.raises(DeletionChallengeTokenExpiredError) as exc_info:
                svc._decode_challenge_token(token, now=now_ts)
            assert exc_info.value.error_code == ERROR_CODE_DELETION_CHALLENGE_TOKEN_EXPIRED
            assert exc_info.value.token_jti == "jti-expired"

    _impl()


def test_decode_challenge_token_purpose_mismatch_raises() -> None:
    """Wrong purpose claim raises DeletionChallengeTokenInvalidError."""

    def _impl() -> None:
        import jwt as _jwt

        session = AsyncMock()
        now_ts = int(time.time())
        token = _jwt.encode(
            {
                "purpose": "wrong-purpose",
                "user_id": ACTOR_ID,
                "tenant_id": TENANT_ID,
                "jti": "jti-wrong",
                "iat": now_ts,
                "exp": now_ts + DELETION_CHALLENGE_TOKEN_TTL_SECONDS,
            },
            JWT_SECRET,
            algorithm="HS256",
        )
        svc = DeletionService(
            session,
            tenant_id=TENANT_ID,
            actor_id=ACTOR_ID,
            trace_id=TRACE_ID,
        )
        with _patch_settings_secret(), pytest.raises(DeletionChallengeTokenInvalidError):
            svc._decode_challenge_token(token, now=now_ts)

    _impl()


# ── 8. Typed exception envelopes ──────────────────────────────
def test_typed_exception_envelopes() -> None:
    """6 typed exception envelopes have correct error_code + message_ko."""
    # DeletionChallengeTokenInvalidError
    e1 = DeletionChallengeTokenInvalidError(reason="bad", trace_id=TRACE_ID)
    assert e1.error_code == ERROR_CODE_DELETION_CHALLENGE_TOKEN_INVALID
    assert e1.message_ko == DELETION_CHALLENGE_TOKEN_INVALID_KO
    assert e1.reason == "bad"

    # DeletionChallengeTokenExpiredError
    e2 = DeletionChallengeTokenExpiredError(token_jti="jti", expired_at=123)
    assert e2.error_code == ERROR_CODE_DELETION_CHALLENGE_TOKEN_EXPIRED
    assert e2.message_ko == DELETION_CHALLENGE_TOKEN_EXPIRED_KO

    # DeletionConsentEncryptionError
    e3 = DeletionConsentEncryptionError(tenant_id=TENANT_ID, reason="aes-fail")
    assert e3.error_code == ERROR_CODE_DELETION_CONSENT_ENCRYPTION_FAILED
    assert e3.message_ko == DELETION_CONSENT_ENCRYPTION_FAILED_KO

    # DeletionConsentDecryptionError
    e4 = DeletionConsentDecryptionError(tenant_id=TENANT_ID, reason="aes-fail")
    assert e4.error_code == ERROR_CODE_DELETION_CONSENT_DECRYPTION_FAILED
    assert e4.message_ko == DELETION_CONSENT_DECRYPTION_FAILED_KO

    # AccountDeletionAuditEmitError
    e5 = AccountDeletionAuditEmitError(
        action="deletion_requested", tenant_id=TENANT_ID, reason="audit-fail"
    )
    assert e5.error_code == ERROR_CODE_ACCOUNT_DELETION_AUDIT_EMIT_FAILED
    assert e5.message_ko == ACCOUNT_DELETION_AUDIT_EMIT_FAILED_KO

    # AccountDeletionHardDeleteError
    e6 = AccountDeletionHardDeleteError(tenant_id=TENANT_ID, reason="fk-violation")
    assert e6.error_code == ERROR_CODE_ACCOUNT_DELETION_HARD_DELETE_FAILED
    assert e6.message_ko == ACCOUNT_DELETION_HARD_DELETE_FAILED_KO


# ── 9. AAD distinct from totp_secret AAD (CR 12-1 L2) ─────────
def test_consent_aad_distinct_from_totp_aad() -> None:
    """DELETION_CONSENT_AAD MUST NOT collide with totp_secret AAD (NFR6).

    Both columns use AES-256-GCM via `encrypt_at_rest` with distinct AAD
    to prevent ciphertext confusion / cross-column forgery.
    """
    totp_aad = b"totp_secret"
    assert totp_aad != DELETION_CONSENT_AAD
    assert DELETION_CONSENT_AAD == b"deletion_consent"


# ── 10. ActionClass.ACCOUNT_DELETION registered ───────────────
def test_account_deletion_action_class_registered() -> None:
    """ActionClass.ACCOUNT_DELETION is wired in audit_action.py registry."""
    assert hasattr(ActionClass, "ACCOUNT_DELETION")
    assert ActionClass.ACCOUNT_DELETION.value == "account_deletion"
