"""tests/integration/test_m12_account_deletion_kernel_parity.py — Story 12.3

AD-15 §11 cross-language parity (D-PARITY-01 fix + CR 12-5 D-13).

This file exercises the Python kernel SSOT for the M12 account deletion
subsystem directly, mirroring vitest parity tests in
`apps/web/__tests__/lib/m12-account-deletion-parity.test.ts`.

SSOT is at `packages/services/m12_account/account_deletion.py`:
  - `compute_deletion_scheduled_for(requested_at)`
  - `build_deletion_envelope(...)`
  - `compute_consent_hash(consent_text, *, salt="")`
  - `validate_consent_text(consent_text, *, expected_template=...)`
  - `can_transition_status(current, target)` (FSM)
  - `assert_status_transition(current, target, *, tenant_id)`
  - `TenantDeletionStatus` enum (active | pending_deletion | deleted)

The TS mirror at `apps/web/lib/m12-account-deletion.ts` exposes
`buildDeletionEnvelope` + `canTransitionStatus` + `getStatusLabel`
+ `daysUntilHardDelete`. Drift between Python and TS is caught by
`tests/integration/test_m12_account_deletion_cross_language_drift.py`.

Pure-function tests — NO DB, NO clock at module level. Caller passes
`requested_at` explicitly (CR 12-1 L1 caller-controlled timestamp).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from packages.services.m12_account.account_deletion import (
    ACCOUNT_ALREADY_DELETED_KO,
    DELETION_CONSENT_TEMPLATE_KO,
    DELETION_ENVELOPE_SCHEMA_VERSION,
    DELETION_IN_PROGRESS_KO,
    DELETION_NOT_OWNER_KO,
    ERROR_CODE_ACCOUNT_ALREADY_DELETED,
    ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS,
    ERROR_CODE_ACCOUNT_DELETION_NOT_OWNER,
    RETENTION_DAYS,
    AccountAlreadyDeletedError,
    AccountDeletionInProgressError,
    AccountDeletionNotOwnerError,
    DeletionConsentTextInvalidError,
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


# ── 1. Constants & enum invariants ───────────────────────────
def test_retention_days_is_30() -> None:
    """RETENTION_DAYS must be 30 (MVP fixed; configurable deferred — Story 12.3 honest DEFER #2)."""
    assert RETENTION_DAYS == 30


def test_envelope_schema_version_is_1_0() -> None:
    """DELETION_ENVELOPE_SCHEMA_VERSION must be "1.0" (AD-15 §6 forward-compat)."""
    assert DELETION_ENVELOPE_SCHEMA_VERSION == "1.0"


def test_tenant_deletion_status_enum_has_3_values() -> None:
    """TenantDeletionStatus must have exactly 3 values (active, pending_deletion, deleted)."""
    values = {s.value for s in TenantDeletionStatus}
    assert values == {"active", "pending_deletion", "deleted"}


def test_consent_template_ko_verbatim() -> None:
    """DELETION_CONSENT_TEMPLATE_KO must be the verbatim Korean consent string."""
    assert DELETION_CONSENT_TEMPLATE_KO == (
        "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다"
    )


# ── 2. compute_deletion_scheduled_for (4 cases) ──────────────
def test_compute_scheduled_for_30_days_later_tz_aware() -> None:
    """scheduled_for = requested_at + 30 days (UTC tz-aware input)."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled = compute_deletion_scheduled_for(requested)
    assert scheduled == datetime(2026, 9, 14, 10, 0, 0, tzinfo=UTC)


def test_compute_scheduled_for_naive_datetime_treated_as_utc() -> None:
    """Naive datetime → coerced to UTC (defensive — caller should pass tz-aware)."""
    requested = datetime(2026, 8, 15, 10, 0, 0)  # naive
    scheduled = compute_deletion_scheduled_for(requested)
    assert scheduled.tzinfo is not None
    assert scheduled == datetime(2026, 9, 14, 10, 0, 0, tzinfo=UTC)


def test_compute_scheduled_for_year_boundary() -> None:
    """scheduled_for must cross year boundary correctly (Dec 15 → Jan 14)."""
    requested = datetime(2026, 12, 15, 12, 0, 0, tzinfo=UTC)
    scheduled = compute_deletion_scheduled_for(requested)
    assert scheduled == datetime(2027, 1, 14, 12, 0, 0, tzinfo=UTC)


def test_compute_scheduled_for_idempotent() -> None:
    """Same input → same output (pure function)."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled_a = compute_deletion_scheduled_for(requested)
    scheduled_b = compute_deletion_scheduled_for(requested)
    assert scheduled_a == scheduled_b


# ── 3. build_deletion_envelope (4 cases) ─────────────────────
def test_build_envelope_schema_version_default() -> None:
    """build_deletion_envelope defaults schema_version to DELETION_ENVELOPE_SCHEMA_VERSION."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled = datetime(2026, 9, 14, 10, 0, 0, tzinfo=UTC)
    env = build_deletion_envelope(
        tenant_id="00000000-0000-0000-0000-000000000001",
        status=TenantDeletionStatus.PENDING_DELETION,
        deletion_requested_at=requested,
        deletion_scheduled_for=scheduled,
        consent_id="00000000-0000-0000-0000-000000000002",
    )
    assert env.schema_version == "1.0"
    assert env.envelope_type == "account_deletion"


def test_build_envelope_iso8601_utc_second_precision() -> None:
    """ISO-8601 UTC second-precision (NO microseconds — minute-level)."""
    requested = datetime(2026, 8, 15, 10, 0, 0, 123456, tzinfo=UTC)
    scheduled = datetime(2026, 9, 14, 10, 0, 0, 654321, tzinfo=UTC)
    env = build_deletion_envelope(
        tenant_id="tenant-id",
        status=TenantDeletionStatus.PENDING_DELETION,
        deletion_requested_at=requested,
        deletion_scheduled_for=scheduled,
        consent_id="consent-id",
    )
    assert env.deletion_requested_at == "2026-08-15T10:00:00Z"
    assert env.deletion_scheduled_for == "2026-09-14T10:00:00Z"


def test_build_envelope_retention_days_field() -> None:
    """retention_days field must equal RETENTION_DAYS = 30."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled = datetime(2026, 9, 14, 10, 0, 0, tzinfo=UTC)
    env = build_deletion_envelope(
        tenant_id="t",
        status=TenantDeletionStatus.PENDING_DELETION,
        deletion_requested_at=requested,
        deletion_scheduled_for=scheduled,
        consent_id="c",
    )
    assert env.retention_days == 30


def test_build_envelope_to_dict_keys_order() -> None:
    """envelope_to_dict MUST emit 8 fixed keys in deterministic order (CR 12-3 AC #8)."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled = datetime(2026, 9, 14, 10, 0, 0, tzinfo=UTC)
    env = build_deletion_envelope(
        tenant_id="t",
        status=TenantDeletionStatus.PENDING_DELETION,
        deletion_requested_at=requested,
        deletion_scheduled_for=scheduled,
        consent_id="c",
    )
    d = envelope_to_dict(env)
    keys = list(d.keys())
    expected_keys = [
        "schema_version",
        "envelope_type",
        "tenant_id",
        "status",
        "deletion_requested_at",
        "deletion_scheduled_for",
        "retention_days",
        "consent_id",
    ]
    assert keys == expected_keys


def test_envelope_to_json_is_deterministic() -> None:
    """envelope_to_json output must be deterministic (drift detector safe)."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled = datetime(2026, 9, 14, 10, 0, 0, tzinfo=UTC)
    env = build_deletion_envelope(
        tenant_id="t",
        status=TenantDeletionStatus.PENDING_DELETION,
        deletion_requested_at=requested,
        deletion_scheduled_for=scheduled,
        consent_id="c",
    )
    json_str = envelope_to_json(env)
    # Same envelope → same JSON
    assert envelope_to_json(env) == json_str
    # Verify key order
    assert json_str.index("schema_version") < json_str.index("envelope_type")


# ── 4. compute_consent_hash (3 cases) ────────────────────────
def test_compute_consent_hash_no_salt() -> None:
    """SHA-256 of plaintext (no salt)."""
    text = DELETION_CONSENT_TEMPLATE_KO
    h = compute_consent_hash(text)
    # SHA-256 hex is 64 chars
    assert len(h) == 64
    # Deterministic
    assert compute_consent_hash(text) == h


def test_compute_consent_hash_with_salt_different() -> None:
    """Salt prefix → different hash (tenant isolation)."""
    text = DELETION_CONSENT_TEMPLATE_KO
    no_salt = compute_consent_hash(text)
    with_salt = compute_consent_hash(text, salt="tenant-1")
    assert no_salt != with_salt


def test_compute_consent_hash_unicode_safe() -> None:
    """Korean consent text must hash correctly (UTF-8 encode)."""
    h = compute_consent_hash("본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다")
    assert len(h) == 64
    # SHA-256 hex = lowercase
    assert h == h.lower()


# ── 5. validate_consent_text (3 cases) ───────────────────────
def test_validate_consent_text_match_ok() -> None:
    """Exact match → no error."""
    validate_consent_text(DELETION_CONSENT_TEMPLATE_KO)  # no raise


def test_validate_consent_text_strip_whitespace_ok() -> None:
    """Leading/trailing whitespace stripped before compare."""
    validate_consent_text(f"  {DELETION_CONSENT_TEMPLATE_KO}  \n")  # no raise


def test_validate_consent_text_mismatch_raises() -> None:
    """Mismatch → DeletionConsentTextInvalidError with consent_text_hash context."""
    with pytest.raises(DeletionConsentTextInvalidError) as exc:
        validate_consent_text("wrong text")
    assert exc.value.consent_text_hash != ""
    assert len(exc.value.consent_text_hash) == 64


# ── 6. can_transition_status FSM (8 cases — full grid) ───────
def test_fsm_active_to_pending_allowed() -> None:
    """ACTIVE → PENDING_DELETION allowed (request_deletion succeeds)."""
    assert (
        can_transition_status(
            TenantDeletionStatus.ACTIVE,
            TenantDeletionStatus.PENDING_DELETION,
        )
        is True
    )


def test_fsm_pending_to_active_allowed() -> None:
    """PENDING_DELETION → ACTIVE allowed (cancel_deletion succeeds)."""
    assert (
        can_transition_status(
            TenantDeletionStatus.PENDING_DELETION,
            TenantDeletionStatus.ACTIVE,
        )
        is True
    )


def test_fsm_pending_to_deleted_allowed() -> None:
    """PENDING_DELETION → DELETED allowed (cron hard_delete succeeds)."""
    assert (
        can_transition_status(
            TenantDeletionStatus.PENDING_DELETION,
            TenantDeletionStatus.DELETED,
        )
        is True
    )


def test_fsm_active_to_deleted_rejected() -> None:
    """ACTIVE → DELETED rejected (must go via PENDING_DELETION first)."""
    assert (
        can_transition_status(
            TenantDeletionStatus.ACTIVE,
            TenantDeletionStatus.DELETED,
        )
        is False
    )


def test_fsm_deleted_to_anything_rejected() -> None:
    """DELETED → ANY rejected (terminal state)."""
    for target in TenantDeletionStatus:
        assert (
            can_transition_status(TenantDeletionStatus.DELETED, target) is False
        )


def test_fsm_self_loop_rejected() -> None:
    """ACTIVE → ACTIVE / PENDING_DELETION → PENDING_DELETION / DELETED → DELETED rejected."""
    for status in TenantDeletionStatus:
        assert can_transition_status(status, status) is False


def test_fsm_pending_to_pending_rejected() -> None:
    """PENDING_DELETION → PENDING_DELETION specifically rejected (idempotent no-op)."""
    assert (
        can_transition_status(
            TenantDeletionStatus.PENDING_DELETION,
            TenantDeletionStatus.PENDING_DELETION,
        )
        is False
    )


def test_fsm_full_grid_exhaustive() -> None:
    """Full 3×3 grid — exactly 3 allowed transitions (drift detector invariant)."""
    allowed_count = 0
    for current in TenantDeletionStatus:
        for target in TenantDeletionStatus:
            if can_transition_status(current, target):
                allowed_count += 1
    assert allowed_count == 3, (
        f"FSM has {allowed_count} allowed transitions, expected exactly 3"
    )


# ── 7. assert_status_transition error paths (4 cases) ────────
def test_assert_status_transition_deleted_raises_410() -> None:
    """DELETED → ANY raises AccountAlreadyDeletedError (HTTP 410, CR 11-3 split)."""
    with pytest.raises(AccountAlreadyDeletedError) as exc:
        assert_status_transition(
            TenantDeletionStatus.DELETED,
            TenantDeletionStatus.ACTIVE,
            tenant_id="t",
        )
    assert exc.value.error_code == ERROR_CODE_ACCOUNT_ALREADY_DELETED
    assert exc.value.tenant_id == "t"


def test_assert_status_transition_pending_to_pending_raises_409() -> None:
    """PENDING_DELETION → PENDING_DELETION raises AccountDeletionInProgressError (409)."""
    with pytest.raises(AccountDeletionInProgressError) as exc:
        assert_status_transition(
            TenantDeletionStatus.PENDING_DELETION,
            TenantDeletionStatus.PENDING_DELETION,
            tenant_id="t",
        )
    assert exc.value.error_code == ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS


def test_assert_status_transition_active_to_deleted_raises_409() -> None:
    """ACTIVE → DELETED rejected with AccountDeletionInProgressError (409)."""
    with pytest.raises(AccountDeletionInProgressError):
        assert_status_transition(
            TenantDeletionStatus.ACTIVE,
            TenantDeletionStatus.DELETED,
            tenant_id="t",
        )


def test_assert_status_transition_active_to_pending_ok() -> None:
    """ACTIVE → PENDING_DELETION allowed (no raise)."""
    assert_status_transition(
        TenantDeletionStatus.ACTIVE,
        TenantDeletionStatus.PENDING_DELETION,
        tenant_id="t",
    )  # no raise


# ── 8. Exception error_code & message_ko invariants ───────────
def test_not_owner_error_message_and_code() -> None:
    """AccountDeletionNotOwnerError carries Korean message + error_code + actor_role."""
    err = AccountDeletionNotOwnerError(actor_role="member")
    assert err.message_ko == DELETION_NOT_OWNER_KO
    assert err.error_code == ERROR_CODE_ACCOUNT_DELETION_NOT_OWNER
    assert err.actor_role == "member"


def test_in_progress_error_message_and_code() -> None:
    """AccountDeletionInProgressError carries Korean message + error_code + tenant_id."""
    err = AccountDeletionInProgressError(tenant_id="t-1")
    assert err.message_ko == DELETION_IN_PROGRESS_KO
    assert err.error_code == ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS
    assert err.tenant_id == "t-1"


def test_already_deleted_error_message_and_code() -> None:
    """AccountAlreadyDeletedError carries Korean message + error_code + tenant_id."""
    err = AccountAlreadyDeletedError(tenant_id="t-2")
    assert err.message_ko == ACCOUNT_ALREADY_DELETED_KO
    assert err.error_code == ERROR_CODE_ACCOUNT_ALREADY_DELETED
    assert err.tenant_id == "t-2"


# ── 9. Idempotency & determinism sanity (2 cases) ────────────
def test_envelope_idempotent_on_same_input() -> None:
    """build_deletion_envelope is idempotent for the same input (no hidden state)."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled = datetime(2026, 9, 14, 10, 0, 0, tzinfo=UTC)
    env_a = build_deletion_envelope(
        tenant_id="t",
        status=TenantDeletionStatus.PENDING_DELETION,
        deletion_requested_at=requested,
        deletion_scheduled_for=scheduled,
        consent_id="c",
    )
    env_b = build_deletion_envelope(
        tenant_id="t",
        status=TenantDeletionStatus.PENDING_DELETION,
        deletion_requested_at=requested,
        deletion_scheduled_for=scheduled,
        consent_id="c",
    )
    assert envelope_to_dict(env_a) == envelope_to_dict(env_b)


def test_scheduled_for_equals_requested_plus_retention() -> None:
    """scheduled_for = requested + timedelta(days=RETENTION_DAYS)."""
    requested = datetime(2026, 8, 15, 10, 0, 0, tzinfo=UTC)
    scheduled = compute_deletion_scheduled_for(requested)
    delta = scheduled - requested
    assert delta == timedelta(days=RETENTION_DAYS)
