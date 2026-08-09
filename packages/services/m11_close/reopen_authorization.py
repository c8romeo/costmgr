"""packages.services.m11_close.reopen_authorization — Story 11.3 pure kernel.

W2 reopen authorization decision (PRD §F11.4 reopen flow).

AD-10 owner-only + AD-15 audit-justification + 4-stage close_sequence_state
guard. Decides whether a reopen of a closed fiscal period is permitted
given:
- capability_granted (Capability.REOPEN_OPERATOR — manufacturing 3종 ✅
  / service-only ❌)
- role (AD-10 owner-only)
- operator_action ∈ REOPEN_OPERATOR_ACTIONS (4-value enum)
- reason length 20-500 (AD-15 audit-justification)

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO DB, NO clock, NO
random. Service layer passes all inputs explicitly.

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-reopen.ts`.

W2 reopen flow spec (PRD §F11.4):
1. fiscal_periods.status='closed' AND close_sequence_state='confirmed'
2. AD-10 owner-only role
3. AD-15 reason length 20-500 chars (audit-justification minimum)
4. operator_action 4-value enum (operator_reopen | audit_finding |
   legal_compliance | data_correction) — disambiguates reopen purpose
   for the audit trail
5. AD-25 multi-channel publish (fiscal_period_cache + closing_snapshot_cache)

After reopen:
- fiscal_periods.status → 'open' (or stays 'closed' with reopen flag)
- close_sequence_state → 'reopened' (new 11-3 AD-6 transition)
- audit_log emits `reopen_operator_invoked`
"""

from __future__ import annotations

import uuid
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# 4-value operator_action enum (W2 reopen flow).
REOPEN_OPERATOR_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "operator_reopen",
        "audit_finding",
        "legal_compliance",
        "data_correction",
    }
)

# Reason length bounds (AD-15 §11 audit-justification minimum).
REOPEN_REASON_MIN_LENGTH: Final[int] = 20
REOPEN_REASON_MAX_LENGTH: Final[int] = 500

# Error codes — pure-kernel domain semantics.
ERROR_CODE_INVALID_OPERATOR_ACTION: Final[str] = "INVALID_OPERATOR_ACTION"
ERROR_CODE_INVALID_REASON_LENGTH: Final[str] = "INVALID_REASON_LENGTH"
ERROR_CODE_NO_CAPABILITY: Final[str] = "NO_CAPABILITY"
ERROR_CODE_NOT_OWNER: Final[str] = "NOT_OWNER_ROLE"
ERROR_CODE_NON_UUID_ACTOR: Final[str] = "NON_UUID_ACTOR_ID"
ERROR_CODE_NON_UUID_TENANT: Final[str] = "NON_UUID_TENANT_ID"

# Korean constants — AD-15 §11 SSOT.
REOPEN_AUTHORIZE_OK_KO: Final[str] = "재오픈 승인 완료"
REOPEN_REJECT_NOT_OWNER_KO: Final[str] = "소유자 역할이 아닙니다 — 재오픈 불가"
REOPEN_REJECT_NO_CAPABILITY_KO: Final[str] = "재오픈 권한 미보유"
REOPEN_REJECT_INVALID_OPERATOR_KO: Final[str] = (
    "재오픈 사유 분류가 올바르지 않습니다"
)
REOPEN_REJECT_REASON_TOO_SHORT_KO: Final[str] = (
    "재오픈 사유는 20자 이상이어야 합니다"
)
REOPEN_REJECT_REASON_TOO_LONG_KO: Final[str] = (
    "재오픈 사유는 500자 이하여야 합니다"
)


# ── Typed exception ──────────────────────────────────────────
class ReopenAuthorizationError(Exception):
    """Pure-kernel authorization decision violation.

    Distinct from service-layer `ReopenOperatorActionInvalidError`.
    NO HTTP mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


# ── ReopenAuthorizationResult NamedTuple ───────────────────
class ReopenAuthorizationResult(NamedTuple):
    """Authorization outcome — service layer wraps this in the wire response."""

    authorized: bool
    reject_reason_ko: str | None
    operator_action: str
    reason_length: int
    capability_granted: bool
    is_owner: bool
    actor_id: uuid.UUID
    tenant_id: uuid.UUID


# ── authorize_reopen ────────────────────────────────────────
def authorize_reopen(
    *,
    tenant_id: uuid.UUID,
    actor_id: uuid.UUID,
    operator_action: str,
    reason: str,
    capability_granted: bool,
    is_owner: bool,
) -> ReopenAuthorizationResult:
    """Decide whether a reopen is permitted.

    Args:
        tenant_id: Owning tenant (audit attribution).
        actor_id: UUID of the reopen initiator.
        operator_action: One of REOPEN_OPERATOR_ACTIONS.
        reason: Free-text justification (20-500 chars).
        capability_granted: Whether the tenant has `Capability.REOPEN_OPERATOR`
            (manufacturing 3종 ✅ / service-only ❌).
        is_owner: Whether the actor has the owner role (AD-10).

    Returns:
        ReopenAuthorizationResult with `authorized` flag +
        `reject_reason_ko` (Korean SSOT) when rejected.

    Raises:
        ReopenAuthorizationError: On invalid input shape (non-UUID
            actor / tenant).
    """
    if not isinstance(tenant_id, uuid.UUID):
        raise ReopenAuthorizationError(
            message=f"tenant_id must be UUID, got {type(tenant_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_TENANT,
        )
    if not isinstance(actor_id, uuid.UUID):
        raise ReopenAuthorizationError(
            message=f"actor_id must be UUID, got {type(actor_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_ACTOR,
        )

    reason_length = len(reason) if isinstance(reason, str) else 0

    # Role gate (AD-10 owner-only).
    if not is_owner:
        return ReopenAuthorizationResult(
            authorized=False,
            reject_reason_ko=REOPEN_REJECT_NOT_OWNER_KO,
            operator_action=operator_action,
            reason_length=reason_length,
            capability_granted=capability_granted,
            is_owner=False,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Capability gate.
    if not capability_granted:
        return ReopenAuthorizationResult(
            authorized=False,
            reject_reason_ko=REOPEN_REJECT_NO_CAPABILITY_KO,
            operator_action=operator_action,
            reason_length=reason_length,
            capability_granted=False,
            is_owner=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # operator_action enum gate.
    if operator_action not in REOPEN_OPERATOR_ACTIONS:
        return ReopenAuthorizationResult(
            authorized=False,
            reject_reason_ko=REOPEN_REJECT_INVALID_OPERATOR_KO,
            operator_action=operator_action,
            reason_length=reason_length,
            capability_granted=True,
            is_owner=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Reason length gate.
    if reason_length < REOPEN_REASON_MIN_LENGTH:
        return ReopenAuthorizationResult(
            authorized=False,
            reject_reason_ko=REOPEN_REJECT_REASON_TOO_SHORT_KO,
            operator_action=operator_action,
            reason_length=reason_length,
            capability_granted=True,
            is_owner=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    if reason_length > REOPEN_REASON_MAX_LENGTH:
        return ReopenAuthorizationResult(
            authorized=False,
            reject_reason_ko=REOPEN_REJECT_REASON_TOO_LONG_KO,
            operator_action=operator_action,
            reason_length=reason_length,
            capability_granted=True,
            is_owner=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Authorized.
    return ReopenAuthorizationResult(
        authorized=True,
        reject_reason_ko=None,
        operator_action=operator_action,
        reason_length=reason_length,
        capability_granted=True,
        is_owner=True,
        actor_id=actor_id,
        tenant_id=tenant_id,
    )


__all__ = [
    "ERROR_CODE_INVALID_OPERATOR_ACTION",
    "ERROR_CODE_INVALID_REASON_LENGTH",
    "ERROR_CODE_NO_CAPABILITY",
    "ERROR_CODE_NOT_OWNER",
    "ERROR_CODE_NON_UUID_ACTOR",
    "ERROR_CODE_NON_UUID_TENANT",
    "REOPEN_AUTHORIZE_OK_KO",
    "REOPEN_OPERATOR_ACTIONS",
    "REOPEN_REASON_MAX_LENGTH",
    "REOPEN_REASON_MIN_LENGTH",
    "REOPEN_REJECT_INVALID_OPERATOR_KO",
    "REOPEN_REJECT_NO_CAPABILITY_KO",
    "REOPEN_REJECT_NOT_OWNER_KO",
    "REOPEN_REJECT_REASON_TOO_LONG_KO",
    "REOPEN_REJECT_REASON_TOO_SHORT_KO",
    "ReopenAuthorizationError",
    "ReopenAuthorizationResult",
    "authorize_reopen",
]
