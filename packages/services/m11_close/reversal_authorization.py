"""packages.services.m11_close.reversal_authorization — Story 11.1 pure kernel #3.

Authorization decision for AD-22 reversal sequence. Decides whether a
reversal is permitted given:
- capability_granted (Capability.REVERSAL_REQUEST — manufacturing 3종 ✅
  / service-only ❌ per A9 결정 + PRD §F11.3)
- period_status (monthly_input_periods.status — 'open' / 'closed' 허용,
  'locked' 거부; 11-2 wire 시점에 fiscal_periods.status 추가 가드)
- target_event's event_type (authorization-layer
  AUTHORIZABLE_TARGET_EVENT_TYPES — 11-2 divergence from build-layer
  REVERSIBLE_TARGET_EVENT_TYPES: closing_snapshot AD-6 sealed final
  상태는 authorization layer에서 거부, reversal_negating/reversal_corrected
  재역분개 시도는 authorization layer에서 허용 후 build layer
  validate_reversal_negating_constraints 에서 별도 거부)

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO DB, NO clock, NO
random. Service layer passes all inputs explicitly.

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-reversal.ts`.

Story 11.2 3rd-sweep fix (AC#6 dual guard semantics):
- REVERSAL is allowed ONLY when fiscal_periods.status='closed'
  (the closed-period reversal pattern). Once the 4-stage close
  sequence is `confirmed`, the period is sealed for direct edits
  (AD-6 INSERT 거부) — AD-22 reversal is the ONLY edit path.
- 'open' / 'closing' / 'reversed' fiscal_periods.status REJECTED.
- This is the spec-mandated semantics per AC#6(a). Previous
  implementation had the semantics inverted (only 'open' allowed),
  which would have made AD-22 reversal impossible after close.
"""

from __future__ import annotations

import uuid
from typing import Final, NamedTuple

from packages.services.m4_inventory.ledger import InventoryLedgerEvent
from packages.services.m11_close.reversal_negating import (
    REVERSIBLE_TARGET_EVENT_TYPES,
)

# ── Constants ────────────────────────────────────────────────
# Period status allowed for reversal. 'locked' is rejected here.
# Story 11.2 wire (AD-6 close lock + 4-stage close_sequence_state):
# `fiscal_periods.status` adds a SECOND guard layer on top of
# `monthly_input_periods.status`. Both statuses must be in
# PERIOD_STATUS_ALLOWED for reversal to be authorized.
PERIOD_STATUS_ALLOWED: Final[frozenset[str]] = frozenset({"open", "closed"})
PERIOD_STATUS_REJECTED: Final[frozenset[str]] = frozenset({"locked"})

# fiscal_periods.status values (AD-6 1-way state machine).
# Story 11.2 3rd-sweep fix — flip semantics per AC#6(a) + PRD §F11.2:
# AD-22 reversal is the closed-period reversal pattern. Once the
# 4-stage close sequence is `confirmed`, fiscal_periods.status='closed'
# and reversal is the ONLY way to fix mistakes (AD-6 INSERT 거부
# blocks direct edits). 'open' / 'closing' / 'reversed' are rejected
# at the authorization layer (direct edit OR re-edit window).
FISCAL_PERIOD_STATUS_ALLOWED: Final[frozenset[str]] = frozenset({"closed"})
FISCAL_PERIOD_STATUS_REJECTED: Final[frozenset[str]] = frozenset(
    {"open", "closing", "reversed"}
)

# 11-2 EXTENSION — authorization-layer reversibility diverges from
# build-layer `REVERSIBLE_TARGET_EVENT_TYPES` (reversal_negating.py):
# - `closing_snapshot` (AD-6 sealed final state) → NOT reversible at
#   authorization layer. Once `fiscal_periods.status='closed'`, the
#   closing snapshot is immutable summary record — reversal would
#   undermine the close lock invariant (PRD §F11.3 + AD-6 Rule).
#   Defense-in-depth: closing_snapshot is REJECTED at the authorization
#   layer (this module) BEFORE any other gate. The build layer keeps
#   `closing_snapshot` in REVERSIBLE_TARGET_EVENT_TYPES for the rare
#   case where authorization somehow allows it (e.g., direct service
#   layer call bypassing the authorization gate).
# - `reversal_negating` / `reversal_corrected` (re-reversal attempt) →
#   ARE reversible at the authorization layer. The build layer
#   `validate_reversal_negating_constraints` (reversal_negating.py)
#   separately rejects self-reversal with ERROR_CODE_SELF_REVERSAL as
#   defense-in-depth. This split lets the audit trail distinguish
#   "authorization denied" (capability/period gate) from "build denied"
#   (self-reversal gate).
AUTHORIZABLE_TARGET_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    REVERSIBLE_TARGET_EVENT_TYPES - {"closing_snapshot"}
    | {"reversal_negating", "reversal_corrected"}
)

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
    """Authorization outcome — service layer wraps this in the wire response.

    Story 11.2 wire: extends with `fiscal_period_status` to capture the
    SECOND guard layer added by AD-6 close lock + 4-stage close_sequence_state.
    Both `period_status` (monthly_input_periods.status) AND
    `fiscal_period_status` (fiscal_periods.status) gate the authorization.
    """

    authorized: bool
    reject_reason_ko: str | None
    period_status: str  # "open" | "closed" | "locked"
    fiscal_period_status: str  # "open" | "closing" | "closed" | "reversed"
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
    fiscal_period_status: str,
) -> ReversalAuthorizationResult:
    """Decide whether a reversal of `target_event` is permitted.

    Story 11.2 wire — dual guard:
      1. `period_status` (monthly_input_periods.status — 11-1 SSOT):
         must be "open" or "closed" for reversal; "locked" is rejected.
      2. `fiscal_period_status` (fiscal_periods.status — 11-2 PRIMARY):
         must be "closed" for reversal (closed-period reversal pattern
         per AC#6(a) + PRD §F11.2). "open" / "closing" / "reversed" are
         rejected at the authorization layer. AD-22 reversal is the
         ONLY edit path once fiscal_periods.status='closed'.

    Args:
        tenant_id: Owning tenant (audit attribution).
        target_event: Original InventoryLedgerEvent row.
        actor_id: UUID of the reversal initiator.
        period_status: `monthly_input_periods.status` snapshot — must be
            "open" or "closed" for reversal; "locked" is rejected.
        capability_granted: Whether the tenant has `Capability.REVERSAL_REQUEST`
            (manufacturing 3종 ✅ / service-only ❌).
        fiscal_period_status: `fiscal_periods.status` snapshot — must be
            "closed" for reversal. Story 11.2 PRIMARY guard. Required
            (no default — fail-closed per PATCH 3rd-sweep). Callers MUST
            explicitly fetch and pass the fiscal_periods row status.

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

    # Target reversibility — authorization-layer set (AUTHORIZABLE_TARGET_EVENT_TYPES).
    # Diverges from build-layer REVERSIBLE_TARGET_EVENT_TYPES:
    # - closing_snapshot excluded (AD-6 sealed final state)
    # - reversal_negating / reversal_corrected included (re-reversal allowed at
    #   authorization layer; build layer separately rejects self-reversal).
    target_reversible = target_event.event_type in AUTHORIZABLE_TARGET_EVENT_TYPES
    if not target_reversible:
        return ReversalAuthorizationResult(
            authorized=False,
            reject_reason_ko=M11_REJECT_TARGET_NOT_REVERSIBLE_KO,
            period_status=period_status,
            fiscal_period_status=fiscal_period_status,
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
            fiscal_period_status=fiscal_period_status,
            capability_granted=False,
            target_reversible=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Period status gate (monthly_input_periods.status — 11-1 SSOT).
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
            fiscal_period_status=fiscal_period_status,
            capability_granted=True,
            target_reversible=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Story 11.2 PRIMARY guard — fiscal_periods.status (AD-6 close lock).
    # Closed-period reversal pattern (AC#6(a) + PRD §F11.2):
    # reversal is ONLY permitted when fiscal_periods.status='closed'
    # (4-stage close_sequence_state='confirmed'). The 'closed' period
    # is sealed for direct edits (AD-6 INSERT 거부) — AD-22 reversal
    # is the ONLY edit path. 'open' / 'closing' / 'reversed' are
    # rejected at the authorization layer.
    if fiscal_period_status not in (
        FISCAL_PERIOD_STATUS_ALLOWED | FISCAL_PERIOD_STATUS_REJECTED
    ):
        raise ReversalAuthorizationError(
            message=(
                f"fiscal_period_status {fiscal_period_status!r} is not in "
                f"the known set "
                f"({sorted(FISCAL_PERIOD_STATUS_ALLOWED | FISCAL_PERIOD_STATUS_REJECTED)})"
            ),
            error_code=ERROR_CODE_INVALID_PERIOD_STATUS,
            target_event_id=target_event.event_id,
        )
    if fiscal_period_status in FISCAL_PERIOD_STATUS_REJECTED:
        return ReversalAuthorizationResult(
            authorized=False,
            reject_reason_ko=M11_REJECT_LOCKED_KO,
            period_status=period_status,
            fiscal_period_status=fiscal_period_status,
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
        fiscal_period_status=fiscal_period_status,
        capability_granted=True,
        target_reversible=True,
        actor_id=actor_id,
        tenant_id=tenant_id,
    )


__all__ = [
    "AUTHORIZABLE_TARGET_EVENT_TYPES",
    "ERROR_CODE_INVALID_PERIOD_STATUS",
    "ERROR_CODE_NO_CAPABILITY",
    "ERROR_CODE_TARGET_NOT_REVERSIBLE",
    "ERROR_CODE_NON_UUID_ACTOR",
    "ERROR_CODE_NON_UUID_TENANT",
    "FISCAL_PERIOD_STATUS_ALLOWED",
    "FISCAL_PERIOD_STATUS_REJECTED",
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
