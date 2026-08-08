"""packages.services.m11_close.reversal_negating — Story 11.1 pure kernel #1.

AD-22 sign-negating row constructor for reversal sequence. When a ledger
event is reversed, this kernel builds a *new* row with `qty = -target.qty`
(AD-22 sign-negating invariant) + `reverses_event_id` link + optional
`correction_group_id` share + `reversal_of_period_key = target.period_key`
(AD-24 typed). The original row never changes (AD-2 append-only).

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO DB, NO clock, NO
random. Caller passes actor_id + trace_id explicitly. Decimal arithmetic
uses banker's rounding (ROUND_HALF_EVEN) at QTY_QUANTUM = NUMERIC(18,4)
to keep parity with the TS mirror (`apps/web/lib/m11-reversal.ts`) and
the closing_snapshot ledger column precision.

Drift between Python and TS is caught by
`tests/integration/test_m11_reversal_label_consistency.py`.

PRD §F11.3 AC ↔ ledger invariants:
- "부호 반전 row 1개 INSERT" — reversal_negating INSERT 1 row
- "원본 row 변경 없음" — append-only (handled at DB trigger, 5-2 wire)
- "재무 효과 0 수렴" — sign-negating qty = -target.qty (this kernel)
- "(tenant_id, reverses_event_id) unique" — Alembic 0015 PARTIAL UNIQUE

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-reversal.ts`.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Final, NamedTuple

from packages.services.m2_input.inventory_projection import QTY_QUANTUM
from packages.services.m4_inventory.ledger import (
    ERROR_CODE_INVALID_EVENT_TYPE,
    ERROR_CODE_QTY_MUST_BE_DECIMAL,
    InventoryLedgerEvent,
)

# ── Constants ────────────────────────────────────────────────
# Sign-negating row uses the same 11-value event_type whitelist as the
# parent kernel (5-2 wire). The `reversal_negating` value lives in
# `INVENTORY_LEDGER_EVENT_TYPES` (story 5.2).
REVERSAL_NEGATING_EVENT_TYPE: Final[str] = "reversal_negating"

# Error codes — pure-kernel domain semantics. Stable Literals; service
# layer dispatches via `err.error_code` NOT substring matching
# (CR review 2026-08-04 lesson).
ERROR_CODE_EMPTY_TARGET_EVENT: Final[str] = "EMPTY_TARGET_EVENT"
ERROR_CODE_INVALID_CORRECTION_GROUP_ID: Final[str] = "INVALID_CORRECTION_GROUP_ID"
ERROR_CODE_NON_UUID_ACTOR_ID: Final[str] = "NON_UUID_ACTOR_ID"
ERROR_CODE_NON_UUID_TRACE_ID: Final[str] = "NON_UUID_TRACE_ID"
ERROR_CODE_NON_STR_REASON: Final[str] = "NON_STR_REASON"
ERROR_CODE_EMPTY_REASON: Final[str] = "EMPTY_REASON"
ERROR_CODE_SELF_REVERSAL: Final[str] = "SELF_REVERSAL_REJECTED"
ERROR_CODE_TARGET_NOT_REVERSIBLE: Final[str] = "TARGET_NOT_REVERSIBLE"
ERROR_CODE_INVALID_REVERSAL_OF_PERIOD_KEY: Final[str] = "INVALID_REVERSAL_OF_PERIOD_KEY"
ERROR_CODE_QTY_SIGN_INCOHERENT: Final[str] = "QTY_SIGN_INCOHERENT"

# Korean constants — AD-15 §11 SSOT (mirrored verbatim in TS).
M11_AUTHORIZE_KO: Final[str] = "M11 모듈 권한 OK"
M11_NEGATING_BUILT_KO: Final[str] = "역분개 부호 반전 row 생성 완료"
M11_SELF_REVERSAL_REJECTED_KO: Final[str] = "이미 역분개된 행은 재역분개 불가"
M11_TARGET_NOT_REVERSIBLE_KO: Final[str] = (
    "이 이벤트 타입은 역분개 대상이 아닙니다"
)

# Reversible event_types — anything that carries a qty term and was
# emitted from monthly input / carry chain / production / closing
# snapshot can be reversed. Self-reversal (reversal_negating /
# reversal_corrected → reversal) is rejected at validate_reversal_negating_constraints.
REVERSIBLE_TARGET_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {
        "opening_carried",
        "opening_carried_stale_overwrite",
        "purchase_inbound",
        "sales_outbound",
        "production_output_inbound",
        "production_material_consumption",
        "adjustment_positive",
        "adjustment_negative",
        "closing_snapshot",
    }
)


# ── Typed exception (pure-kernel domain semantics) ───────────
class ReversalNegatingBuildError(Exception):
    """Pure-kernel sign-negating row construction violation.

    Distinct from service-layer `ReversalRejectedError` (which carries
    HTTP envelope + audit-first semantics). NO HTTP mapping; service
    layer wraps with envelope details.

    Service-layer dispatch uses `err.error_code` (stable Literal) NOT
    `err.message` substring matching.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = ERROR_CODE_EMPTY_TARGET_EVENT,
        target_event_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.target_event_id = target_event_id


# ── ReversalNegatingEvent NamedTuple ─────────────────────────
class ReversalNegatingEvent(NamedTuple):
    """Immutable sign-negating row shape — built by `build_reversal_negating_event`.

    Mirrors `InventoryLedgerEvent` (5-2 wire) but `event_type` is locked
    to `reversal_negating`. Original event_id is preserved in
    `reverses_event_id` for AD-22 traceability.

    `qty` is always present (sign-negating of a quantitative event).
    `period_key` of the new row equals `target_event.period_key` (PRD
    §F11.3 default — same-period reversal).

    `reversal_of_period_key` is the original event's period_key (may
    differ if corrected row crosses periods).
    """

    event_id: uuid.UUID
    tenant_id: uuid.UUID
    product_id: uuid.UUID
    period_key: str
    event_type: str
    qty: Decimal
    trace_id: uuid.UUID
    reverses_event_id: uuid.UUID
    correction_group_id: uuid.UUID
    reversal_of_period_key: str
    actor_id: uuid.UUID
    payload: dict[str, Any]


# ── build_reversal_negating_event ────────────────────────────
def build_reversal_negating_event(
    *,
    target_event: InventoryLedgerEvent,
    reason: str,
    actor_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    trace_id: uuid.UUID,
    event_id: uuid.UUID | None = None,
) -> ReversalNegatingEvent:
    """Build a sign-negating row mirroring `target_event` with qty = -target.qty.

    AD-22 sequence step 1: the original row's qty is sign-flipped to
    produce a *new* row. `(tenant_id, reverses_event_id)` unique
    constraint (Alembic 0015 `uq_inventory_ledger_reverses_event_id`)
    prevents re-reversal of the same target.

    Args:
        target_event: Original InventoryLedgerEvent row to reverse.
            Must be in REVERSIBLE_TARGET_EVENT_TYPES.
        reason: Free-text user-provided justification (Korean SSOT — AD-15).
        actor_id: UUID of the reversal initiator (audit-first attribution).
        correction_group_id: UUID linking this negating row with its
            optional corrected row (single correction_group_id per
            reversal sequence).
        trace_id: UUID for end-to-end request correlation.
        event_id: Optional pre-minted UUID for the new row (service
            layer usually mints via uuid7()). Defaults to uuid4() — but
            service layer should override to maintain AD-15 v7 identity.

    Returns:
        ReversalNegatingEvent NamedTuple ready for INSERT.

    Raises:
        ReversalNegatingBuildError: On any shape / sign violation.
    """
    if target_event is None:
        raise ReversalNegatingBuildError(
            message="target_event must not be None",
            error_code=ERROR_CODE_EMPTY_TARGET_EVENT,
        )
    if not isinstance(actor_id, uuid.UUID):
        raise ReversalNegatingBuildError(
            message=f"actor_id must be UUID, got {type(actor_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_ACTOR_ID,
        )
    if not isinstance(trace_id, uuid.UUID):
        raise ReversalNegatingBuildError(
            message=f"trace_id must be UUID, got {type(trace_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_TRACE_ID,
        )
    if not isinstance(correction_group_id, uuid.UUID):
        raise ReversalNegatingBuildError(
            message=(
                f"correction_group_id must be UUID, got "
                f"{type(correction_group_id).__name__!r}"
            ),
            error_code=ERROR_CODE_INVALID_CORRECTION_GROUP_ID,
        )
    if not isinstance(reason, str):
        raise ReversalNegatingBuildError(
            message=f"reason must be str, got {type(reason).__name__!r}",
            error_code=ERROR_CODE_NON_STR_REASON,
        )
    if not reason:
        raise ReversalNegatingBuildError(
            message="reason must be non-empty (audit-first attribution)",
            error_code=ERROR_CODE_EMPTY_REASON,
        )

    # Defense-in-depth: target_event must be reversible.
    validate_reversal_negating_constraints(target_event)

    if target_event.qty is None:
        raise ReversalNegatingBuildError(
            message=(
                f"target_event {target_event.event_id} has None qty — "
                f"sign-negating requires non-None qty (PRD §6.2 inventory eq)"
            ),
            error_code="QTY_REQUIRED",
            target_event_id=target_event.event_id,
        )
    if not isinstance(target_event.qty, Decimal):
        raise ReversalNegatingBuildError(
            message=(
                f"target_event.qty must be Decimal, got "
                f"{type(target_event.qty).__name__!r}"
            ),
            error_code=ERROR_CODE_QTY_MUST_BE_DECIMAL,
            target_event_id=target_event.event_id,
        )

    # Sign flip + banker's rounding to QTY_QUANTUM (NUMERIC(18,4)).
    # CR 0-4 lesson: banker's rounding parity TS/Python.
    negating_qty = (-target_event.qty).quantize(
        QTY_QUANTUM, rounding=ROUND_HALF_EVEN
    )

    # Self-reversal prevention — defense-in-depth on top of the
    # REVERSIBLE_TARGET_EVENT_TYPES check.
    if target_event.event_type in ("reversal_negating", "reversal_corrected"):
        # Should already be rejected by validate_reversal_negating_constraints,
        # but explicit re-check keeps the message specific.
        raise ReversalNegatingBuildError(
            message=(
                f"target_event {target_event.event_id} is itself a reversal "
                f"({target_event.event_type!r}); self-reversal is rejected"
            ),
            error_code=ERROR_CODE_SELF_REVERSAL,
            target_event_id=target_event.event_id,
        )

    # Sign coherence: sign-negating qty must be the opposite sign of
    # target.qty (or both zero). AD-22 sign-negating invariant.
    # Normalize -0.0000 → 0.0000 for sign check (banker's rounding quirk).
    if target_event.qty != Decimal("0") and (
        (target_event.qty > 0 and negating_qty > 0)
        or (target_event.qty < 0 and negating_qty < 0)
    ):
        raise ReversalNegatingBuildError(
            message=(
                f"sign flip violated: target.qty={target_event.qty!s} → "
                f"negating.qty={negating_qty!s}; expected opposite sign"
            ),
            error_code=ERROR_CODE_QTY_SIGN_INCOHERENT,
            target_event_id=target_event.event_id,
        )

    new_event_id = event_id if event_id is not None else uuid.uuid4()

    return ReversalNegatingEvent(
        event_id=new_event_id,
        tenant_id=target_event.tenant_id,
        product_id=target_event.product_id,
        period_key=target_event.period_key,
        event_type=REVERSAL_NEGATING_EVENT_TYPE,
        qty=negating_qty,
        trace_id=trace_id,
        reverses_event_id=target_event.event_id,
        correction_group_id=correction_group_id,
        reversal_of_period_key=target_event.period_key,
        actor_id=actor_id,
        payload={
            "reason": reason,
            "source": "reversal_request",
            "target_event_id": str(target_event.event_id),
            "actor_id": str(actor_id),
            "trace_id": str(trace_id),
        },
    )


# ── validate_reversal_negating_constraints ───────────────────
def validate_reversal_negating_constraints(target_event: InventoryLedgerEvent) -> None:
    """Defense-in-depth check that target_event is eligible for reversal.

    AD-22 sequence gate. Reversal must NOT target:
    - another reversal_negating / reversal_corrected (self-reversal)
    - any non-whitelisted event_type (defense-in-depth even though the
      parent kernel already validates event_type on INSERT)

    Raises:
        ReversalNegatingBuildError: With one of:
        - ERROR_CODE_SELF_REVERSAL (event_type is reversal_negating / corrected)
        - ERROR_CODE_TARGET_NOT_REVERSIBLE (event_type not in whitelist)
        - propagated from parent `validate_event_type` for unknown types
    """
    if target_event is None:
        raise ReversalNegatingBuildError(
            message="target_event must not be None",
            error_code=ERROR_CODE_EMPTY_TARGET_EVENT,
        )
    if not isinstance(target_event, InventoryLedgerEvent):
        raise ReversalNegatingBuildError(
            message=(
                f"target_event must be InventoryLedgerEvent, got "
                f"{type(target_event).__name__!r}"
            ),
            error_code=ERROR_CODE_INVALID_EVENT_TYPE,
        )

    if target_event.event_type in ("reversal_negating", "reversal_corrected"):
        raise ReversalNegatingBuildError(
            message=(
                f"target_event {target_event.event_id} is itself a reversal "
                f"({target_event.event_type!r}); self-reversal is rejected"
            ),
            error_code=ERROR_CODE_SELF_REVERSAL,
            target_event_id=target_event.event_id,
        )

    if target_event.event_type not in REVERSIBLE_TARGET_EVENT_TYPES:
        raise ReversalNegatingBuildError(
            message=(
                f"target_event.event_type {target_event.event_type!r} is not "
                f"reversible. Reversible types: {sorted(REVERSIBLE_TARGET_EVENT_TYPES)}"
            ),
            error_code=ERROR_CODE_TARGET_NOT_REVERSIBLE,
            target_event_id=target_event.event_id,
        )


__all__ = [
    "ERROR_CODE_EMPTY_TARGET_EVENT",
    "ERROR_CODE_INVALID_CORRECTION_GROUP_ID",
    "ERROR_CODE_NON_UUID_ACTOR_ID",
    "ERROR_CODE_NON_UUID_TRACE_ID",
    "ERROR_CODE_NON_STR_REASON",
    "ERROR_CODE_EMPTY_REASON",
    "ERROR_CODE_SELF_REVERSAL",
    "ERROR_CODE_TARGET_NOT_REVERSIBLE",
    "ERROR_CODE_INVALID_REVERSAL_OF_PERIOD_KEY",
    "ERROR_CODE_QTY_SIGN_INCOHERENT",
    "M11_AUTHORIZE_KO",
    "M11_NEGATING_BUILT_KO",
    "M11_SELF_REVERSAL_REJECTED_KO",
    "M11_TARGET_NOT_REVERSIBLE_KO",
    "REVERSAL_NEGATING_EVENT_TYPE",
    "REVERSIBLE_TARGET_EVENT_TYPES",
    "ReversalNegatingBuildError",
    "ReversalNegatingEvent",
    "build_reversal_negating_event",
    "validate_reversal_negating_constraints",
]
