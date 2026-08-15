"""packages.services.m12_account.account_deletion — Story 12.3 account deletion pure kernel.

AD-11 layer rule: pure-Python, stdlib-only, NO DB, NO clock at module
level. Service layer (`apps/api/modules/m12_account/services/`) is
responsible for fetching tenant/user/membership and calling these
helpers.

Pure-kernel components:
1. `TenantDeletionStatus` enum (active | pending_deletion | deleted)
2. `RETENTION_DAYS = 30` SSOT constant (MVP fixed, configurable deferred — Story 12.3 honest DEFER #2)
3. Pure dataclasses: `DeletionRequestEnvelope`, `DeletionConsentRecord`,
   `DeletionStatusSnapshot`, `DeletionAuditPayload`
4. Pure functions: `compute_deletion_scheduled_for`, `build_deletion_envelope`,
   `compute_consent_hash`, `validate_consent_text`, `can_transition_status` (FSM)
5. Typed exceptions: `AccountDeletionNotOwnerError`,
   `AccountDeletionInProgressError`, `AccountAlreadyDeletedError` (HTTP 410),
   `DeletionConsentRequiredError`, `DeletionConsentTextInvalidError`

PRD §F12.3 + epics.md Story 12.3 — NFR4 2절 5년 audit 보존 + 30일 후
완전 삭제 + NFR7 2FA 강제 (destructive endpoint 3-layer defense CR 12-5 L3
CRITICAL). Schema version 1.0 envelope (AD-15 §6 contract).

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m12-account-deletion.ts`.
"""

from __future__ import annotations

import enum
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────

# Retention window: MVP fixed 30일 (epics.md AC verbatim).
# Configurable retention_days deferred to AD-23 settings aggregate extension.
RETENTION_DAYS: Final[int] = 30

# Envelope schema version (AD-15 §6 contract). Wire invariant:
# top-level envelope must carry schema_version field for forward compat.
DELETION_ENVELOPE_SCHEMA_VERSION: Final[str] = "1.0"

# Audit action codes (mirrored in apps/api/core/audit_action.py
# AccountDeletionAction Literal — CR 11-3 5-file sweep).
ACCOUNT_DELETION_ACTION_DELETION_REQUESTED: Final[str] = "deletion_requested"
ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN: Final[str] = "deletion_consent_given"
ACCOUNT_DELETION_ACTION_DELETION_CANCELLED: Final[str] = "deletion_cancelled"
ACCOUNT_DELETION_ACTION_DELETION_ANONYMIZED: Final[str] = "deletion_anonymized"
ACCOUNT_DELETION_ACTION_TENANT_HARD_DELETED: Final[str] = "tenant_hard_deleted"
ACCOUNT_DELETION_ACTION_DELETION_FAILED: Final[str] = "deletion_failed"
ACCOUNT_DELETION_ACTION_DELETION_2FA_FAILED: Final[str] = "deletion_2fa_failed"
ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED: Final[str] = "two_factor_verified"

# Error codes (AD-15 §4 envelope contract)
ERROR_CODE_ACCOUNT_DELETION_NOT_OWNER: Final[str] = "ACCOUNT_DELETION_NOT_OWNER"
ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS: Final[str] = "ACCOUNT_DELETION_IN_PROGRESS"
ERROR_CODE_ACCOUNT_ALREADY_DELETED: Final[str] = "ACCOUNT_ALREADY_DELETED"
ERROR_CODE_DELETION_CONSENT_REQUIRED: Final[str] = "DELETION_CONSENT_REQUIRED"
ERROR_CODE_DELETION_CONSENT_TEXT_INVALID: Final[str] = "DELETION_CONSENT_TEXT_INVALID"

# Korean constants — AD-15 §11 SSOT. 격식체 종결 (UX locked decisions).
DELETION_NOT_OWNER_KO: Final[str] = "권한이 없습니다 — 계정 해지는 owner role만 가능합니다"
DELETION_IN_PROGRESS_KO: Final[str] = (
    "계정 해지가 진행 중입니다 — 신규 설정 변경 불가. 해지 취소 후 다시 시도해 주세요"
)
ACCOUNT_ALREADY_DELETED_KO: Final[str] = "삭제된 계정입니다 — 더 이상 작업을 진행할 수 없습니다"
DELETION_CONSENT_REQUIRED_KO: Final[str] = (
    "데이터 보존 기간 및 삭제 시점 동의가 필요합니다 — 동의 체크 후 다시 시도해 주세요"
)
DELETION_CONSENT_TEXT_INVALID_KO: Final[str] = (
    "동의 텍스트가 예상 형식과 일치하지 않습니다 — 페이지를 새로 고친 후 다시 시도해 주세요"
)

# Consent template — fixed verbatim (frontend mirrors verbatim in ko-KR.json).
# Service-layer calls validate_consent_text() with this template.
DELETION_CONSENT_TEMPLATE_KO: Final[str] = (
    "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다"
)


# ── Enum ─────────────────────────────────────────────────────
class TenantDeletionStatus(str, enum.Enum):
    """Tenant lifecycle status for account deletion FSM.

    Transitions allowed (can_transition_status FSM):
    - ACTIVE → PENDING_DELETION (request_deletion)
    - PENDING_DELETION → ACTIVE (cancel_deletion)
    - PENDING_DELETION → DELETED (hard_delete_expired cron)

    All other transitions rejected (fail-closed).
    """

    ACTIVE = "active"
    PENDING_DELETION = "pending_deletion"
    DELETED = "deleted"


# ── Typed inputs (caller fetches from DB) ────────────────────
class DeletionRequestEnvelope(NamedTuple):
    """Pure-kernel envelope output — wire to frontend / audit_logs JSONB.

    schema_version field is the AD-15 §6 forward-compat marker.
    """

    schema_version: str
    envelope_type: str
    tenant_id: str
    status: str
    deletion_requested_at: str  # ISO-8601 UTC
    deletion_scheduled_for: str  # ISO-8601 UTC
    retention_days: int
    consent_id: str


class DeletionConsentRecord(NamedTuple):
    """Pure-kernel view of deletion_consents row (caller fetches from DB).

    encrypted_consent_text: AES-256-GCM ciphertext bytes (NFR6 invariant).
    consent_text_hash: SHA-256 hex of plaintext consent text (audit trace).
    """

    consent_id: str
    tenant_id: str
    consent_text_hash: str
    encrypted_consent_text: bytes
    consent_checked_at: str  # ISO-8601 UTC
    consent_checked_by_user_id: str


class DeletionStatusSnapshot(NamedTuple):
    """Pure-kernel view of tenants.status row (caller fetches from DB).

    deletion_requested_by_user_id / deletion_consent_id may be empty if
    tenant is still ACTIVE.
    """

    tenant_id: str
    status: str
    deletion_requested_at: str  # ISO-8601 UTC, "" if ACTIVE
    deletion_requested_by_user_id: str  # "" if ACTIVE
    deletion_consent_id: str  # "" if ACTIVE
    deletion_scheduled_for: str  # ISO-8601 UTC, "" if ACTIVE


class DeletionAuditPayload(NamedTuple):
    """Pure-kernel audit_logs payload for ACCOUNT_DELETION actions.

    Caller passes this to emit_audit_typed(action_class=ActionClass.ACCOUNT_DELETION, ...).
    """

    tenant_id: str
    owner_id: str
    consent_id: str  # "" if action does not involve consent (e.g. deletion_cancelled)
    action_detail: str  # e.g. "request_deletion" or "hard_delete_failed"
    trace_id: str  # request trace for cross-row correlation


# ── Typed exceptions ──────────────────────────────────────────
class AccountDeletionNotOwnerError(Exception):
    """Pure-kernel AD-10 role gate violation for account deletion.

    HTTP envelope (AD-15 §4): 403 ACCOUNT_DELETION_NOT_OWNER.
    """

    def __init__(
        self,
        message_ko: str = DELETION_NOT_OWNER_KO,
        *,
        actor_role: str,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_ACCOUNT_DELETION_NOT_OWNER
        self.actor_role = actor_role
        super().__init__(message_ko)


class AccountDeletionInProgressError(Exception):
    """Pure-kernel 409 — tenant status='pending_deletion' mutation 거부.

    HTTP envelope (AD-15 §4): 409 ACCOUNT_DELETION_IN_PROGRESS.
    """

    def __init__(
        self,
        message_ko: str = DELETION_IN_PROGRESS_KO,
        *,
        tenant_id: str,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS
        self.tenant_id = tenant_id
        super().__init__(message_ko)


class AccountAlreadyDeletedError(Exception):
    """Pure-kernel 410 — tenant status='deleted' (gone).

    HTTP envelope (AD-15 §4): 410 ACCOUNT_ALREADY_DELETED.
    SnapshotNotFoundError split (CR 11-3) — already-deleted (410) vs
    never-existed (404 row missing).
    """

    def __init__(
        self,
        message_ko: str = ACCOUNT_ALREADY_DELETED_KO,
        *,
        tenant_id: str,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_ACCOUNT_ALREADY_DELETED
        self.tenant_id = tenant_id
        super().__init__(message_ko)


class DeletionConsentRequiredError(Exception):
    """Pure-kernel 422 — consent_checked=False in request_deletion payload.

    HTTP envelope (AD-15 §4): 422 DELETION_CONSENT_REQUIRED.
    """

    def __init__(
        self,
        message_ko: str = DELETION_CONSENT_REQUIRED_KO,
        *,
        tenant_id: str,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_DELETION_CONSENT_REQUIRED
        self.tenant_id = tenant_id
        super().__init__(message_ko)


class DeletionConsentTextInvalidError(Exception):
    """Pure-kernel 422 — consent_text does not match expected template.

    HTTP envelope (AD-15 §4): 422 DELETION_CONSENT_TEXT_INVALID.
    """

    def __init__(
        self,
        message_ko: str = DELETION_CONSENT_TEXT_INVALID_KO,
        *,
        consent_text_hash: str,
    ) -> None:
        self.message_ko = message_ko
        self.error_code = ERROR_CODE_DELETION_CONSENT_TEXT_INVALID
        self.consent_text_hash = consent_text_hash
        super().__init__(message_ko)


# ── Pure functions ───────────────────────────────────────────
def compute_deletion_scheduled_for(requested_at: datetime) -> datetime:
    """Compute deletion_scheduled_for = requested_at + RETENTION_DAYS.

    Pure function (no DB, no clock at module level). Caller passes
    requested_at explicitly (CR 12-1 L1 caller-controlled timestamp).

    Args:
        requested_at: tz-aware UTC datetime of deletion request.

    Returns:
        tz-aware UTC datetime 30일 후.
    """
    if requested_at.tzinfo is None:
        # Treat naive datetime as UTC (defensive — caller should pass tz-aware)
        requested_at = requested_at.replace(tzinfo=UTC)
    return requested_at + timedelta(days=RETENTION_DAYS)


def build_deletion_envelope(
    *,
    tenant_id: str,
    status: TenantDeletionStatus,
    deletion_requested_at: datetime,
    deletion_scheduled_for: datetime,
    consent_id: str,
    schema_version: str = DELETION_ENVELOPE_SCHEMA_VERSION,
) -> DeletionRequestEnvelope:
    """Build pure-kernel DeletionRequestEnvelope.

    Deterministic ISO-8601 UTC serialization (no microseconds — minute-level
    precision to avoid drift across serialization round-trips).

    Args:
        tenant_id: UUID string.
        status: TenantDeletionStatus enum value.
        deletion_requested_at: tz-aware UTC datetime of request.
        deletion_scheduled_for: tz-aware UTC datetime of scheduled delete.
        consent_id: UUID string.
        schema_version: defaults to DELETION_ENVELOPE_SCHEMA_VERSION (1.0).

    Returns:
        DeletionRequestEnvelope NamedTuple.
    """

    def _iso(dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        # Force UTC + second precision (avoid microsecond drift)
        utc_dt = dt.astimezone(UTC)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return DeletionRequestEnvelope(
        schema_version=schema_version,
        envelope_type="account_deletion",
        tenant_id=tenant_id,
        status=status.value,
        deletion_requested_at=_iso(deletion_requested_at),
        deletion_scheduled_for=_iso(deletion_scheduled_for),
        retention_days=RETENTION_DAYS,
        consent_id=consent_id,
    )


def envelope_to_dict(envelope: DeletionRequestEnvelope) -> dict[str, object]:
    """Convert DeletionRequestEnvelope → dict for JSON serialization.

    Deterministic key order (CR 12-3 AC #8 envelope keys 9종 고정).
    """
    return {
        "schema_version": envelope.schema_version,
        "envelope_type": envelope.envelope_type,
        "tenant_id": envelope.tenant_id,
        "status": envelope.status,
        "deletion_requested_at": envelope.deletion_requested_at,
        "deletion_scheduled_for": envelope.deletion_scheduled_for,
        "retention_days": envelope.retention_days,
        "consent_id": envelope.consent_id,
    }


def compute_consent_hash(consent_text: str, *, salt: str = "") -> str:
    """Compute SHA-256 hex digest of consent text (+ optional salt).

    Pure function (stdlib-only). NFR4 audit trace: plaintext NEVER stored,
    only hash retained in deletion_consents row.

    Args:
        consent_text: User-typed consent string (UTF-8).
        salt: Optional salt for tenant isolation (defensive — production
            uses tenant_id as salt to prevent cross-tenant hash collisions).

    Returns:
        SHA-256 hex digest (lowercase, 64 chars).
    """
    canonical = f"{salt}::{consent_text}" if salt else consent_text
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_consent_text(
    consent_text: str,
    *,
    expected_template: str = DELETION_CONSENT_TEMPLATE_KO,
) -> None:
    """Validate consent_text matches expected template verbatim.

    Raises DeletionConsentTextInvalidError if mismatch.

    Args:
        consent_text: User-typed consent string.
        expected_template: Fixed Korean template (default DELETION_CONSENT_TEMPLATE_KO).

    Raises:
        DeletionConsentTextInvalidError: If consent_text != expected_template
            (after whitespace stripping).
    """
    normalized = consent_text.strip()
    if normalized != expected_template:
        # Compute hash for error context (audit trace — never log plaintext)
        consent_hash = compute_consent_hash(normalized)
        raise DeletionConsentTextInvalidError(
            DELETION_CONSENT_TEXT_INVALID_KO,
            consent_text_hash=consent_hash,
        )


def can_transition_status(
    current: TenantDeletionStatus,
    target: TenantDeletionStatus,
) -> bool:
    """FSM check — can tenant.status transition from current → target?

    Allowed transitions:
    - ACTIVE → PENDING_DELETION (request_deletion)
    - PENDING_DELETION → ACTIVE (cancel_deletion)
    - PENDING_DELETION → DELETED (hard_delete_expired cron)

    All other transitions rejected (fail-closed).

    Args:
        current: Current TenantDeletionStatus.
        target: Desired TenantDeletionStatus.

    Returns:
        True if transition allowed, False otherwise.
    """
    if current == TenantDeletionStatus.ACTIVE:
        return target == TenantDeletionStatus.PENDING_DELETION
    if current == TenantDeletionStatus.PENDING_DELETION:
        return target in (
            TenantDeletionStatus.ACTIVE,
            TenantDeletionStatus.DELETED,
        )
    # DELETED is terminal — no transitions allowed
    return False


def assert_status_transition(
    current: TenantDeletionStatus,
    target: TenantDeletionStatus,
    *,
    tenant_id: str,
) -> None:
    """Assert FSM transition allowed — raise on rejection.

    Args:
        current: Current TenantDeletionStatus.
        target: Desired TenantDeletionStatus.
        tenant_id: For error context.

    Raises:
        AccountAlreadyDeletedError: If current == DELETED (410).
        AccountDeletionInProgressError: If current == PENDING_DELETION AND
            target == PENDING_DELETION (idempotent no-op rejected).
    """
    if current == TenantDeletionStatus.DELETED:
        raise AccountAlreadyDeletedError(
            ACCOUNT_ALREADY_DELETED_KO,
            tenant_id=tenant_id,
        )
    if not can_transition_status(current, target):
        if current == TenantDeletionStatus.PENDING_DELETION:
            raise AccountDeletionInProgressError(
                DELETION_IN_PROGRESS_KO,
                tenant_id=tenant_id,
            )
        # Unknown FSM violation — fail-closed
        raise AccountDeletionInProgressError(
            DELETION_IN_PROGRESS_KO,
            tenant_id=tenant_id,
        )


# ── Serialization helpers (test parity) ─────────────────────
def envelope_to_json(envelope: DeletionRequestEnvelope) -> str:
    """Deterministic JSON serialization for parity tests.

    Key order matches envelope_to_dict() — required for cross-language
    drift detector (CR 12-5 D-13).
    """
    return json.dumps(envelope_to_dict(envelope), ensure_ascii=False, sort_keys=False)


__all__ = [
    # constants
    "RETENTION_DAYS",
    "DELETION_ENVELOPE_SCHEMA_VERSION",
    "ACCOUNT_DELETION_ACTION_DELETION_REQUESTED",
    "ACCOUNT_DELETION_ACTION_DELETION_CONSENT_GIVEN",
    "ACCOUNT_DELETION_ACTION_DELETION_CANCELLED",
    "ACCOUNT_DELETION_ACTION_DELETION_ANONYMIZED",
    "ACCOUNT_DELETION_ACTION_TENANT_HARD_DELETED",
    "ACCOUNT_DELETION_ACTION_DELETION_FAILED",
    "ACCOUNT_DELETION_ACTION_DELETION_2FA_FAILED",
    "ACCOUNT_DELETION_ACTION_TWO_FACTOR_VERIFIED",
    "ERROR_CODE_ACCOUNT_DELETION_NOT_OWNER",
    "ERROR_CODE_ACCOUNT_DELETION_IN_PROGRESS",
    "ERROR_CODE_ACCOUNT_ALREADY_DELETED",
    "ERROR_CODE_DELETION_CONSENT_REQUIRED",
    "ERROR_CODE_DELETION_CONSENT_TEXT_INVALID",
    "DELETION_NOT_OWNER_KO",
    "DELETION_IN_PROGRESS_KO",
    "ACCOUNT_ALREADY_DELETED_KO",
    "DELETION_CONSENT_REQUIRED_KO",
    "DELETION_CONSENT_TEXT_INVALID_KO",
    "DELETION_CONSENT_TEMPLATE_KO",
    # enum
    "TenantDeletionStatus",
    # result types
    "DeletionRequestEnvelope",
    "DeletionConsentRecord",
    "DeletionStatusSnapshot",
    "DeletionAuditPayload",
    # exceptions
    "AccountDeletionNotOwnerError",
    "AccountDeletionInProgressError",
    "AccountAlreadyDeletedError",
    "DeletionConsentRequiredError",
    "DeletionConsentTextInvalidError",
    # functions
    "compute_deletion_scheduled_for",
    "build_deletion_envelope",
    "envelope_to_dict",
    "compute_consent_hash",
    "validate_consent_text",
    "can_transition_status",
    "assert_status_transition",
    "envelope_to_json",
]
