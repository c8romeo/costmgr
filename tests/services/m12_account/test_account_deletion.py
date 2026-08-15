"""tests.services.m12_account.test_account_deletion — T1 pure kernel tests.

Coverage:
- TenantDeletionStatus enum (3 values)
- RETENTION_DAYS / DELETION_ENVELOPE_SCHEMA_VERSION constants
- compute_deletion_scheduled_for (naive, tz-aware UTC, far future)
- build_deletion_envelope (schema_version default, all fields)
- envelope_to_dict / envelope_to_json (deterministic key order)
- compute_consent_hash (deterministic, with/without salt)
- validate_consent_text (match, mismatch, whitespace)
- can_transition_status FSM (active→pending, pending→active, pending→deleted, deleted→*, etc.)
- assert_status_transition (success, already deleted, in progress)
- Typed exceptions (error_code, message_ko, attributes)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

import pytest

from packages.services.m12_account.account_deletion import (
    ACCOUNT_ALREADY_DELETED_KO,
    ACCOUNT_DELETION_ACTION_DELETION_2FA_FAILED,
    ACCOUNT_DELETION_ACTION_DELETION_ANONYMIZED,
    ACCOUNT_DELETION_ACTION_DELETION_CANCELLED,
    ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN,
    ACCOUNT_DELETION_ACTION_DELETION_FAILED,
    ACCOUNT_DELETION_ACTION_DELETION_REQUESTED,
    ACCOUNT_DELETION_ACTION_TENANT_HARD_DELETED,
    ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED,
    DELETION_CONSENT_TEMPLATE_KO,
    DELETION_ENVELOPE_SCHEMA_VERSION,
    DELETION_IN_PROGRESS_KO,
    DELETION_NOT_OWNER_KO,
    ERROR_CODE_ACCOUNT_ALREADY_DELETED,
    ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS,
    ERROR_CODE_ACCOUNT_DELETION_NOT_OWNER,
    ERROR_CODE_DELETION_CONSENT_REQUIRED,
    ERROR_CODE_DELETION_CONSENT_TEXT_INVALID,
    RETENTION_DAYS,
    AccountAlreadyDeletedError,
    AccountDeletionInProgressError,
    AccountDeletionNotOwnerError,
    DeletionAuditPayload,
    DeletionConsentRecord,
    DeletionConsentRequiredError,
    DeletionConsentTextInvalidError,
    DeletionRequestEnvelope,
    DeletionStatusSnapshot,
    TenantDeletionStatus,
    assert_status_transition,
    build_deletion_envelope,
    can_transition_status,
    compute_consent_hash,
    compute_deletion_scheduled_for,
    envelope_to_dict,
    envelope_to_json,
    validate_consent_text,
)


# ── Fixtures ────────────────────────────────────────────────
@pytest.fixture
def fixed_requested_at() -> datetime:
    """Fixed tz-aware UTC datetime for deterministic envelope tests."""
    return datetime(2026, 8, 15, 1, 0, 0, tzinfo=UTC)


@pytest.fixture
def fixed_scheduled_for(fixed_requested_at: datetime) -> datetime:
    return fixed_requested_at + timedelta(days=RETENTION_DAYS)


@pytest.fixture
def sample_tenant_id() -> str:
    return "00000000-0000-0000-0000-0000000000aa"


@pytest.fixture
def sample_consent_id() -> str:
    return "00000000-0000-0000-0000-0000000000bb"


# ── TenantDeletionStatus enum ───────────────────────────────
class TestTenantDeletionStatus:
    def test_active_value(self) -> None:
        assert TenantDeletionStatus.ACTIVE.value == "active"

    def test_pending_deletion_value(self) -> None:
        assert TenantDeletionStatus.PENDING_DELETION.value == "pending_deletion"

    def test_deleted_value(self) -> None:
        assert TenantDeletionStatus.DELETED.value == "deleted"

    def test_enum_count(self) -> None:
        assert len(TenantDeletionStatus) == 3


# ── Constants ──────────────────────────────────────────────
class TestConstants:
    def test_retention_days_is_30(self) -> None:
        assert RETENTION_DAYS == 30

    def test_envelope_schema_version_is_1_0(self) -> None:
        assert DELETION_ENVELOPE_SCHEMA_VERSION == "1.0"

    def test_consent_template_non_empty(self) -> None:
        assert DELETION_CONSENT_TEMPLATE_KO
        assert "30일" in DELETION_CONSENT_TEMPLATE_KO

    def test_8_account_deletion_action_constants(self) -> None:
        # Verify 8 audit action constants per AC #4
        actions = {
            ACCOUNT_DELETION_ACTION_DELETION_REQUESTED,
            ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN,
            ACCOUNT_DELETION_ACTION_DELETION_CANCELLED,
            ACCOUNT_DELETION_ACTION_DELETION_ANONYMIZED,
            ACCOUNT_DELETION_ACTION_TENANT_HARD_DELETED,
            ACCOUNT_DELETION_ACTION_DELETION_FAILED,
            ACCOUNT_DELETION_ACTION_DELETION_2FA_FAILED,
            ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED,
        }
        assert len(actions) == 8


# ── compute_deletion_scheduled_for ─────────────────────────
class TestComputeDeletionScheduledFor:
    def test_adds_30_days_tz_aware(self, fixed_requested_at: datetime) -> None:
        result = compute_deletion_scheduled_for(fixed_requested_at)
        assert result == fixed_requested_at + timedelta(days=30)

    def test_naive_datetime_treated_as_utc(self) -> None:
        naive = datetime(2026, 8, 15, 1, 0, 0)
        result = compute_deletion_scheduled_for(naive)
        assert result.tzinfo == UTC
        assert result == datetime(2026, 9, 14, 1, 0, 0, tzinfo=UTC)

    def test_preserves_time_of_day(self, fixed_requested_at: datetime) -> None:
        result = compute_deletion_scheduled_for(fixed_requested_at)
        assert result.hour == fixed_requested_at.hour
        assert result.minute == fixed_requested_at.minute


# ── build_deletion_envelope ────────────────────────────────
class TestBuildDeletionEnvelope:
    def test_default_schema_version(
        self,
        sample_tenant_id: str,
        sample_consent_id: str,
        fixed_requested_at: datetime,
        fixed_scheduled_for: datetime,
    ) -> None:
        env = build_deletion_envelope(
            tenant_id=sample_tenant_id,
            status=TenantDeletionStatus.PENDING_DELETION,
            deletion_requested_at=fixed_requested_at,
            deletion_scheduled_for=fixed_scheduled_for,
            consent_id=sample_consent_id,
        )
        assert env.schema_version == "1.0"

    def test_explicit_schema_version(
        self,
        sample_tenant_id: str,
        sample_consent_id: str,
        fixed_requested_at: datetime,
        fixed_scheduled_for: datetime,
    ) -> None:
        env = build_deletion_envelope(
            tenant_id=sample_tenant_id,
            status=TenantDeletionStatus.PENDING_DELETION,
            deletion_requested_at=fixed_requested_at,
            deletion_scheduled_for=fixed_scheduled_for,
            consent_id=sample_consent_id,
            schema_version="1.0",
        )
        assert env.schema_version == "1.0"

    def test_iso_8601_utc_format(
        self,
        sample_tenant_id: str,
        sample_consent_id: str,
        fixed_requested_at: datetime,
        fixed_scheduled_for: datetime,
    ) -> None:
        env = build_deletion_envelope(
            tenant_id=sample_tenant_id,
            status=TenantDeletionStatus.PENDING_DELETION,
            deletion_requested_at=fixed_requested_at,
            deletion_scheduled_for=fixed_scheduled_for,
            consent_id=sample_consent_id,
        )
        assert env.deletion_requested_at == "2026-08-15T01:00:00Z"
        assert env.deletion_scheduled_for == "2026-09-14T01:00:00Z"

    def test_retention_days_in_envelope(
        self,
        sample_tenant_id: str,
        sample_consent_id: str,
        fixed_requested_at: datetime,
        fixed_scheduled_for: datetime,
    ) -> None:
        env = build_deletion_envelope(
            tenant_id=sample_tenant_id,
            status=TenantDeletionStatus.PENDING_DELETION,
            deletion_requested_at=fixed_requested_at,
            deletion_scheduled_for=fixed_scheduled_for,
            consent_id=sample_consent_id,
        )
        assert env.retention_days == 30


# ── envelope_to_dict / envelope_to_json ─────────────────────
class TestEnvelopeSerialization:
    def test_to_dict_deterministic_key_order(
        self,
        sample_tenant_id: str,
        sample_consent_id: str,
        fixed_requested_at: datetime,
        fixed_scheduled_for: datetime,
    ) -> None:
        env = build_deletion_envelope(
            tenant_id=sample_tenant_id,
            status=TenantDeletionStatus.PENDING_DELETION,
            deletion_requested_at=fixed_requested_at,
            deletion_scheduled_for=fixed_scheduled_for,
            consent_id=sample_consent_id,
        )
        d = envelope_to_dict(env)
        keys = list(d.keys())
        # AC #8: envelope keys 9종 고정 (deterministic order)
        assert keys == [
            "schema_version",
            "envelope_type",
            "tenant_id",
            "status",
            "deletion_requested_at",
            "deletion_scheduled_for",
            "retention_days",
            "consent_id",
        ]

    def test_to_json_parseable(
        self,
        sample_tenant_id: str,
        sample_consent_id: str,
        fixed_requested_at: datetime,
        fixed_scheduled_for: datetime,
    ) -> None:
        env = build_deletion_envelope(
            tenant_id=sample_tenant_id,
            status=TenantDeletionStatus.PENDING_DELETION,
            deletion_requested_at=fixed_requested_at,
            deletion_scheduled_for=fixed_scheduled_for,
            consent_id=sample_consent_id,
        )
        json_str = envelope_to_json(env)
        parsed = json.loads(json_str)
        assert parsed["schema_version"] == "1.0"
        assert parsed["tenant_id"] == sample_tenant_id


# ── compute_consent_hash ───────────────────────────────────
class TestComputeConsentHash:
    def test_deterministic_no_salt(self) -> None:
        h1 = compute_consent_hash("동의합니다")
        h2 = compute_consent_hash("동의합니다")
        assert h1 == h2

    def test_different_inputs_different_hashes(self) -> None:
        h1 = compute_consent_hash("동의합니다")
        h2 = compute_consent_hash("거부합니다")
        assert h1 != h2

    def test_with_salt_changes_hash(self) -> None:
        no_salt = compute_consent_hash("동의합니다")
        with_salt = compute_consent_hash("동의합니다", salt="tenant-aaa")
        assert no_salt != with_salt

    def test_hash_is_64_hex_chars(self) -> None:
        h = compute_consent_hash("동의합니다")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)


# ── validate_consent_text ──────────────────────────────────
class TestValidateConsentText:
    def test_match_returns_none(self) -> None:
        validate_consent_text(DELETION_CONSENT_TEMPLATE_KO)  # no raise

    def test_whitespace_stripped(self) -> None:
        # leading/trailing whitespace stripped before comparison
        validate_consent_text(f"  {DELETION_CONSENT_TEMPLATE_KO}  ")  # no raise

    def test_mismatch_raises(self) -> None:
        with pytest.raises(DeletionConsentTextInvalidError) as exc_info:
            validate_consent_text("다른 내용입니다")
        assert exc_info.value.error_code == ERROR_CODE_DELETION_CONSENT_TEXT_INVALID

    def test_custom_template(self) -> None:
        with pytest.raises(DeletionConsentTextInvalidError):
            validate_consent_text("anything", expected_template="custom template")


# ── can_transition_status FSM ──────────────────────────────
class TestCanTransitionStatus:
    def test_active_to_pending_allowed(self) -> None:
        assert (
            can_transition_status(
                TenantDeletionStatus.ACTIVE, TenantDeletionStatus.PENDING_DELETION
            )
            is True
        )

    def test_active_to_deleted_rejected(self) -> None:
        assert (
            can_transition_status(
                TenantDeletionStatus.ACTIVE, TenantDeletionStatus.DELETED
            )
            is False
        )

    def test_pending_to_active_allowed(self) -> None:
        assert (
            can_transition_status(
                TenantDeletionStatus.PENDING_DELETION, TenantDeletionStatus.ACTIVE
            )
            is True
        )

    def test_pending_to_deleted_allowed(self) -> None:
        assert (
            can_transition_status(
                TenantDeletionStatus.PENDING_DELETION, TenantDeletionStatus.DELETED
            )
            is True
        )

    def test_deleted_is_terminal(self) -> None:
        for target in TenantDeletionStatus:
            assert (
                can_transition_status(TenantDeletionStatus.DELETED, target) is False
            )

    def test_pending_to_pending_rejected(self) -> None:
        assert (
            can_transition_status(
                TenantDeletionStatus.PENDING_DELETION, TenantDeletionStatus.PENDING_DELETION
            )
            is False
        )


# ── assert_status_transition ───────────────────────────────
class TestAssertStatusTransition:
    def test_active_to_pending_succeeds(self, sample_tenant_id: str) -> None:
        assert_status_transition(
            TenantDeletionStatus.ACTIVE,
            TenantDeletionStatus.PENDING_DELETION,
            tenant_id=sample_tenant_id,
        )

    def test_deleted_current_raises_account_already_deleted(
        self, sample_tenant_id: str
    ) -> None:
        with pytest.raises(AccountAlreadyDeletedError) as exc_info:
            assert_status_transition(
                TenantDeletionStatus.DELETED,
                TenantDeletionStatus.PENDING_DELETION,
                tenant_id=sample_tenant_id,
            )
        assert exc_info.value.error_code == ERROR_CODE_ACCOUNT_ALREADY_DELETED
        assert exc_info.value.tenant_id == sample_tenant_id

    def test_pending_to_pending_raises_in_progress(
        self, sample_tenant_id: str
    ) -> None:
        with pytest.raises(AccountDeletionInProgressError) as exc_info:
            assert_status_transition(
                TenantDeletionStatus.PENDING_DELETION,
                TenantDeletionStatus.PENDING_DELETION,
                tenant_id=sample_tenant_id,
            )
        assert exc_info.value.error_code == ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS


# ── Typed exceptions ───────────────────────────────────────
class TestTypedExceptions:
    def test_account_deletion_not_owner_error(self) -> None:
        err = AccountDeletionNotOwnerError(actor_role="member")
        assert err.error_code == ERROR_CODE_ACCOUNT_DELETION_NOT_OWNER
        assert err.actor_role == "member"
        assert err.message_ko == DELETION_NOT_OWNER_KO

    def test_account_deletion_in_progress_error(self, sample_tenant_id: str) -> None:
        err = AccountDeletionInProgressError(tenant_id=sample_tenant_id)
        assert err.error_code == ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS
        assert err.tenant_id == sample_tenant_id
        assert err.message_ko == DELETION_IN_PROGRESS_KO

    def test_account_already_deleted_error(self, sample_tenant_id: str) -> None:
        err = AccountAlreadyDeletedError(tenant_id=sample_tenant_id)
        assert err.error_code == ERROR_CODE_ACCOUNT_ALREADY_DELETED
        assert err.tenant_id == sample_tenant_id
        assert err.message_ko == ACCOUNT_ALREADY_DELETED_KO

    def test_deletion_consent_required_error(self, sample_tenant_id: str) -> None:
        err = DeletionConsentRequiredError(tenant_id=sample_tenant_id)
        assert err.error_code == ERROR_CODE_DELETION_CONSENT_REQUIRED
        assert err.tenant_id == sample_tenant_id

    def test_deletion_consent_text_invalid_error(self) -> None:
        err = DeletionConsentTextInvalidError(consent_text_hash="abc123")
        assert err.error_code == ERROR_CODE_DELETION_CONSENT_TEXT_INVALID
        assert err.consent_text_hash == "abc123"


# ── NamedTuple types (smoke) ───────────────────────────────
class TestNamedTuples:
    def test_deletion_request_envelope_fields(self) -> None:
        env = DeletionRequestEnvelope(
            schema_version="1.0",
            envelope_type="account_deletion",
            tenant_id="t",
            status="pending_deletion",
            deletion_requested_at="2026-08-15T01:00:00Z",
            deletion_scheduled_for="2026-09-14T01:00:00Z",
            retention_days=30,
            consent_id="c",
        )
        assert env.retention_days == 30

    def test_deletion_consent_record_fields(self) -> None:
        rec = DeletionConsentRecord(
            consent_id="c",
            tenant_id="t",
            consent_text_hash="abc",
            encrypted_consent_text=b"\x00\x01",
            consent_checked_at="2026-08-15T01:00:00Z",
            consent_checked_by_user_id="u",
        )
        assert rec.encrypted_consent_text == b"\x00\x01"

    def test_deletion_status_snapshot_active(self) -> None:
        snap = DeletionStatusSnapshot(
            tenant_id="t",
            status="active",
            deletion_requested_at="",
            deletion_requested_by_user_id="",
            deletion_consent_id="",
            deletion_scheduled_for="",
        )
        assert snap.status == "active"

    def test_deletion_audit_payload_fields(self) -> None:
        p = DeletionAuditPayload(
            tenant_id="t",
            owner_id="u",
            consent_id="c",
            action_detail="request_deletion",
            trace_id="trace-001",
        )
        assert p.trace_id == "trace-001"
