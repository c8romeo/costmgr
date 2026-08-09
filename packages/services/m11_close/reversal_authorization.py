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
- snapshot_state (Story 11.3 NEW — fiscal_period_snapshots.state must
  be 'committed' for 영구화. AD-20 state machine guarantees a snapshot
  exists and is sealed BEFORE reversal is attempted. Optional with
  default 'committed' to preserve 11-1/11-2 backward compatibility.)

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

Story 11.3 wire (3-tier guard) — AD-20 state machine 영구화 gate:
- REVERSAL 영구화 (committed → reversed) requires
  fiscal_period_snapshots.state='committed'. A 'verified' snapshot has
  not yet been committed (the V1·V4·V7·V8 verifiers have passed but
  the owner has not yet sealed it as immutable summary record). A
  'reversed' snapshot has already been reversed — re-reversal would
  corrupt the audit trail.
- This adds a 3rd guard layer ON TOP of:
  1. monthly_input_periods.status — 11-1 SSOT (open/closed allowed)
  2. fiscal_periods.status — 11-2 PRIMARY (closed only)
  3. fiscal_period_snapshots.state — 11-3 NEW (committed only — AD-20)
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

# 11-3 EXTENSION — fiscal_period_snapshots.state (AD-20 state machine)
# 3rd-tier guard layer. AD-22 영구화 requires the underlying snapshot
# to be in state='committed' (PRD §F11.2 — snapshot must be sealed as
# immutable summary record BEFORE reversal 영구화 is attempted). A
# 'verified' snapshot has passed V1·V4·V7·V8 verifiers but has not yet
# been committed; a 'reversed' snapshot has already been reversed.
# Default 'committed' preserves 11-1/11-2 backward compatibility — the
# 11-1 reversal_request path uses reversal REQUEST (not 영구화), which
# only requires the snapshot to eventually be committed before execute.
SNAPSHOT_STATE_ALLOWED: Final[frozenset[str]] = frozenset({"committed"})
SNAPSHOT_STATE_REJECTED: Final[frozenset[str]] = frozenset(
    {"draft", "verified", "reversed"}
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
# 11-3 NEW — snapshot state guard
ERROR_CODE_INVALID_SNAPSHOT_STATE: Final[str] = "INVALID_SNAPSHOT_STATE"

# Korean constants — AD-15 §11 SSOT. Mirrored verbatim in TS.
M11_AUTHORIZE_KO: Final[str] = "M11 모듈 권한 OK"
M11_REJECT_LOCKED_KO: Final[str] = "잠긴 기간 — 역분개 불가"
M11_REJECT_NO_CAPABILITY_KO: Final[str] = "역분개 권한 미보유"
M11_REJECT_TARGET_NOT_REVERSIBLE_KO: Final[str] = (
    "이 이벤트 타입은 역분개 대상이 아닙니다"
)
# 11-3 NEW — snapshot state guard Korean SSOT
M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO: Final[str] = (
    "스냅샷이 커밋 상태가 아닙니다 — 영구화 역분개 불가"
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

    Story 11.3 wire: extends with `snapshot_state` to capture the THIRD
    guard layer (AD-20 state machine 영구화 gate). The 3-tier guard
    guarantees that reversal 영구화 only operates on a snapshot that
    has been sealed as immutable summary record (state='committed').
    """

    authorized: bool
    reject_reason_ko: str | None
    period_status: str  # "open" | "closed" | "locked"
    fiscal_period_status: str  # "open" | "closing" | "closed" | "reversed"
    snapshot_state: str  # 11-3 NEW — "draft" | "verified" | "committed" | "reversed"
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
    snapshot_state: str = "committed",
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

    Story 11.3 wire — 3rd-tier guard:
      3. `snapshot_state` (fiscal_period_snapshots.state — 11-3 NEW):
         must be "committed" for reversal 영구화 (PRD §F11.2). Optional
         with default "committed" — the 11-1 reversal REQUEST path does
         not require the snapshot to be committed yet (the snapshot is
         committed as part of the post-confirm consistency step in the
         close sequence). The 11-3 reversal EXECUTE path passes the
         actual snapshot state. "draft" / "verified" / "reversed" are
         rejected at the authorization layer.

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
        snapshot_state: `fiscal_period_snapshots.state` snapshot — must
            be "committed" for 영구화 (Story 11.3 NEW 3rd-tier guard).
            Defaults to "committed" for 11-1/11-2 backward compatibility.

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
            snapshot_state=snapshot_state,
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
            snapshot_state=snapshot_state,
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
            snapshot_state=snapshot_state,
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
            snapshot_state=snapshot_state,
            capability_granted=True,
            target_reversible=True,
            actor_id=actor_id,
            tenant_id=tenant_id,
        )

    # Story 11.3 NEW — 3rd-tier guard: fiscal_period_snapshots.state
    # (AD-20 state machine 영구화 gate). Reversal 영구화 (the EXECUTE
    # path, not the REQUEST path) requires the underlying snapshot to
    # be in state='committed'. The 11-1 reversal REQUEST path uses the
    # default 'committed' (backward-compat). The 11-3 reversal EXECUTE
    # path passes the actual snapshot_state fetched from the DB.
    if snapshot_state not in (
        SNAPSHOT_STATE_ALLOWED | SNAPSHOT_STATE_REJECTED
    ):
        raise ReversalAuthorizationError(
            message=(
                f"snapshot_state {snapshot_state!r} is not in the known "
                f"AD-20 lifecycle set "
                f"({sorted(SNAPSHOT_STATE_ALLOWED | SNAPSHOT_STATE_REJECTED)})"
            ),
            error_code=ERROR_CODE_INVALID_SNAPSHOT_STATE,
            target_event_id=target_event.event_id,
        )
    if snapshot_state in SNAPSHOT_STATE_REJECTED:
        return ReversalAuthorizationResult(
            authorized=False,
            reject_reason_ko=M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO,
            period_status=period_status,
            fiscal_period_status=fiscal_period_status,
            snapshot_state=snapshot_state,
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
        snapshot_state=snapshot_state,
        capability_granted=True,
        target_reversible=True,
        actor_id=actor_id,
        tenant_id=tenant_id,
    )


__all__ = [
    "AUTHORIZABLE_TARGET_EVENT_TYPES",
    "ERROR_CODE_INVALID_PERIOD_STATUS",
    "ERROR_CODE_INVALID_SNAPSHOT_STATE",
    "ERROR_CODE_NO_CAPABILITY",
    "ERROR_CODE_TARGET_NOT_REVERSIBLE",
    "ERROR_CODE_NON_UUID_ACTOR",
    "ERROR_CODE_NON_UUID_TENANT",
    "FISCAL_PERIOD_STATUS_ALLOWED",
    "FISCAL_PERIOD_STATUS_REJECTED",
    "M11_AUTHORIZE_KO",
    "M11_REJECT_LOCKED_KO",
    "M11_REJECT_NO_CAPABILITY_KO",
    "M11_REJECT_SNAPSHOT_NOT_COMMITTED_KO",
    "M11_REJECT_TARGET_NOT_REVERSIBLE_KO",
    "PERIOD_STATUS_ALLOWED",
    "PERIOD_STATUS_REJECTED",
    "ReversalAuthorizationError",
    "ReversalAuthorizationResult",
    "SNAPSHOT_STATE_ALLOWED",
    "SNAPSHOT_STATE_REJECTED",
    "authorize_reversal",
]
