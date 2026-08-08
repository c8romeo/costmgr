"""packages.services.m11_close.reversal_authorization — Story 11.1 pure kernel #3.

Authorization decision for AD-22 reversal sequence. Decides whether a
reversal is permitted given:
- capability_granted (Capability.REVERSAL_REQUEST — manufacturing 3종 ✅
  / service-only ❌ per A9 결정 + PRD §F11.3)
- period_status (monthly_input_periods.status — 'open' / 'closed' 허용,
  'locked' 거부; 11-2 wire 시점에 fiscal_periods.status 추가 가드 예정)
- target_event's event_type (closing_snapshot 자체 reversal 불가 —
  AD-6 close lock + PRD §F11.3; reversibility는 reversal_negating
  pure kernel의 REVERSIBLE_TARGET_EVENT_TYPES에 위임)

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO DB, NO clock, NO
random. Service layer passes all inputs explicitly.

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-reversal.ts`.
"""

from __future__ import annotations

import uuid
from typing import Final, NamedTuple

from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_negating import (
    REVERSIBLE_TARGET_EVENT_TYPES,
)

# ── Constants ────────────────────────────────────────────────
# Period status allowed for reversal. 'locked' is rejected here;
# 11-2 wire will introduce fiscal_periods.status='locked' guard.
PERIOD_STATUS_ALLOWED: Final[frozenset[str]] = frozenset({"open", "closed"})
PERIOD_STATUS_REJECTED: Final[frozenset[str]] = frozenset({"locked"})

# Error codes — pure-kernel domain semantics.
ERROR_CODE_INVALID_PERIOD_STATUS: Final[str] = "INVALID_PERIOD_STATUS"
ERROR_CODE_NO_CAPABILITY: Final[str] = "NO_CAPABILITY"
ERROR_CODE_TARGET_NOT_REVERSIBLE: Final[str] = "TARGET_NOT_REVERSIBLE"
ERROR_CODE_NON_UUID_ACTOR: Final[str] = "NON_UUID_ACTOR_ID"
ERROR_CODE_NON_UUID_TENANT: Final[str] = "NON_UUID_TENANT_ID"

# Korean constants — AD-15 §11 SSOT. Mirrored verbatim in TS.
M11_AUTHORIZE_KO: Final[str] = "M11 모듈 권한 OK"
M11_REJECT_LOCKED_KO: Final[str] = "잠긴 기간 — 역분개 불가"
M11_REJECT_NO_CAPABILITY_KO: Final[str] = "역분개 권한 미보유"
M11_REJECT_TARGET_NOT_REVERSIBLE_KO: Final[str] = (
    "이 이벤트 타입은 역분개 대상이 아닙니다"
)


# ── Typed exception ──────────────────────────────────────────
class ReversalAuthorizationError(Exception):
    """Pure-kernel authorization decision violation.

    Distinct from service-layer `ReversalUnauthorizedError`. NO HTTP
    mapping; service layer wraps with envelope details.

    Service-layer dispatch uses `err.error_code` (stable Literal).
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = ERROR_CODE_NO_CAPABILITY,
        target_event_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.target_event_id = target_event_id


# ── ReversalAuthorizationResult NamedTuple ───────────────────
class ReversalAuthorizationResult(NamedTuple):
    """Authorization outcome — service layer wraps this in the wire response."""

    authorized: bool
    reject_reason_ko: str | None
    period_status: str  # "open" | "closed" | "locked"
    capability_granted: bool
    target_reversible: bool
    actor_id: uuid.UUID
    tenant_id: uuid.UUID


# ── authorize_reversal ───────────────────────────────────────
def authorize_reversal(
    *,
    tenant_id: uuid.UUID,
    target_event: InventoryLedgerEvent,
    actor_id: uuid.UUID,
    period_status: str,
    capability_granted: bool,
) -> ReversalAuthorizationResult:
    """Decide whether a reversal of `target_event` is permitted.

    Args:
        tenant_id: Owning tenant (audit attribution).
        target_event: Original InventoryLedgerEvent row.
        actor_id: UUID of the reversal initiator.
        period_status: `monthly_input_periods.status` snapshot — must be
            "open" or "closed" for reversal; "locked" is rejected.
        capability_granted: Whether the tenant has `Capability.REVERSAL_REQUEST`
            (manufacturing 3종 ✅ / service-only ❌).

    Returns:
        ReversalAuthorizationResult with `authorized` flag +
        `reject_reason_ko` (Korean SSOT) when rejected.

    Raises:
        ReversalAuthorizationError: On invalid input shape (non-UUID
            actor / tenant / unknown period_status). These represent
            caller bugs and should not normally surface at runtime.
    """
    if not isinstance(tenant_id, uuid.UUID):
        raise ReversalAuthorizationError(
            message=f"tenant_id must be UUID, got {type(tenant_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_TENANT,
        )
    if not isinstance(actor_id, uuid.UUID):
        raise ReversalAuthorizationError(
            message=f"actor_id must be UUID, got {type(actor_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_ACTOR,
        )
    if target_event is None:
        raise ReversalAuthorizationError(
            message="target_event must not be None",
            error_code=ERROR_CODE_TARGET_NOT_REVERSIBLE,
        )

    # Target reversibility (defense-in-depth — same set as reversal_negating).
    target_reversible = target_event.event_type in REVERSIBLE_TARGET_EVENT_TYPES
    if not target_reversible:
        return ReversalAuthorizationResult(
            authorized=False,
            reject_reason_ko=M11_REJECT_TARGET_NOT_REVERSIBLE_KO,
            period_status=period_status,
            capability_granted=capability_granted,
            target_reversible=False,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Capability gate.
    if not capability_granted:
        return ReversalAuthorizationResult(
            authorized=False,
            reject_reason_ko=M11_REJECT_NO_CAPABILITY_KO,
            period_status=period_status,
            capability_granted=False,
            target_reversible=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Period status gate.
    if period_status not in PERIOD_STATUS_ALLOWED and period_status not in PERIOD_STATUS_REJECTED:
        raise ReversalAuthorizationError(
            message=(
                f"period_status {period_status!r} is not in the known set "
                f"({sorted(PERIOD_STATUS_ALLOWED | PERIOD_STATUS_REJECTED)})"
            ),
            error_code=ERROR_CODE_INVALID_PERIOD_STATUS,
            target_event_id=target_event.event_id,
        )
    if period_status in PERIOD_STATUS_REJECTED:
        return ReversalAuthorizationResult(
            authorized=False,
            reject_reason_ko=M11_REJECT_LOCKED_KO,
            period_status=period_status,
            capability_granted=True,
            target_reversible=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Authorized.
    return ReversalAuthorizationResult(
        authorized=True,
        reject_reason_ko=None,
        period_status=period_status,
        capability_granted=True,
        target_reversible=True,
        actor_id=actor_id,
        tenant_id=tenant_id,
    )


__all__ = [
    "ERROR_CODE_INVALID_PERIOD_STATUS",
    "ERROR_CODE_NO_CAPABILITY",
    "ERROR_CODE_TARGET_NOT_REVERSIBLE",
    "ERROR_CODE_NON_UUID_ACTOR",
    "ERROR_CODE_NON_UUID_TENANT",
    "M11_AUTHORIZE_KO",
    "M11_REJECT_LOCKED_KO",
    "M11_REJECT_NO_CAPABILITY_KO",
    "M11_REJECT_TARGET_NOT_REVERSIBLE_KO",
    "PERIOD_STATUS_ALLOWED",
    "PERIOD_STATUS_REJECTED",
    "ReversalAuthorizationError",
    "ReversalAuthorizationResult",
    "authorize_reversal",
]
