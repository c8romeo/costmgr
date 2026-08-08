"""packages.services.m11_close.reversal_corrected — Story 11.1 pure kernel #2.

AD-22 corrected row constructor for reversal sequence. When a ledger
event is reversed and a *new* corrected value is needed (OQ1 cj-style
default — same period; OQ2 cj-style default — optional corrected_qty
input), this kernel builds a second *new* row sharing the same
`correction_group_id` as the sign-negating row.

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO DB, NO clock, NO
random. Caller passes actor_id + trace_id explicitly. Decimal arithmetic
uses banker's rounding (ROUND_HALF_EVEN) at QTY_QUANTUM = NUMERIC(18,4)
to keep parity with the TS mirror (`apps/web/lib/m11-reversal.ts`).

Drift between Python and TS is caught by
`tests/integration/test_m11_reversal_label_consistency.py`.

PRD §F11.3 AC ↔ ledger invariants:
- "corrected row INSERT (correction_group_id share)" — this kernel
- "재무 효과 0 수렴" — corrected row + negating row share correction_group_id;
  their qty sum must equal target.qty (sign-negating + correction = original effect)
- "(tenant_id, reverses_event_id) unique" — corrected row's
  `reverses_event_id` equals `target_event.event_id` so the unique
  constraint blocks re-correction of the same target

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-reversal.ts`.
"""

from __future__ import annotations

import re
import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Final, NamedTuple

from packages.services.m2_input.inventory_projection import QTY_QUANTUM
from packages.services.m4_inventory.ledger import (
    ERROR_CODE_QTY_MUST_BE_DECIMAL,
    InventoryLedgerEvent,
)
from packages.services.m11_close.reversal_negating import (
    ERROR_CODE_EMPTY_TARGET_EVENT,
    ERROR_CODE_INVALID_CORRECTION_GROUP_ID,
    ERROR_CODE_NON_UUID_ACTOR_ID,
    ERROR_CODE_NON_UUID_TRACE_ID,
)

# ── Constants ────────────────────────────────────────────────
REVERSAL_CORRECTED_EVENT_TYPE: Final[str] = "reversal_corrected"

# Error codes — pure-kernel domain semantics.
ERROR_CODE_INCONSISTENT_CORRECTION_GROUP: Final[str] = "INCONSISTENT_CORRECTION_GROUP_ID"
ERROR_CODE_MISSING_CORRECTED_QTY: Final[str] = "MISSING_CORRECTED_QTY"
ERROR_CODE_MISSING_CORRECTED_PERIOD_KEY: Final[str] = "MISSING_CORRECTED_PERIOD_KEY"

# AD-24 typed period-key pattern.
_PERIOD_KEY_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^\d{4}-(0[1-9]|1[0-2])$"
)

# Korean constants — AD-15 §11 SSOT.
M11_CORRECTED_BUILT_KO: Final[str] = "역분개 정정 row 생성 완료"
M11_CORRECTED_SKIPPED_KO: Final[str] = "정정 수량 미입력 — sign-negating만 emit"
M11_INCONSISTENT_CORRECTION_GROUP_KO: Final[str] = (
    "정정 row의 correction_group_id가 sign-negating row와 일치하지 않습니다"
)
M11_INVALID_CORRECTED_PERIOD_KEY_KO: Final[str] = (
    "정정 기간 키가 'YYYY-MM' AD-24 형식에 맞지 않습니다"
)


# ── Typed exception ──────────────────────────────────────────
class ReversalCorrectedBuildError(Exception):
    """Pure-kernel corrected row construction violation.

    Distinct from service-layer `ReversalRejectedError`. NO HTTP mapping;
    service layer wraps with envelope details.

    Service-layer dispatch uses `err.error_code` (stable Literal).
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = ERROR_CODE_INCONSISTENT_CORRECTION_GROUP,
        target_event_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.target_event_id = target_event_id


# ── ReversalCorrectedEvent NamedTuple ────────────────────────
class ReversalCorrectedEvent(NamedTuple):
    """Immutable corrected row shape — built by `build_reversal_corrected_event`.

    Mirrors `InventoryLedgerEvent` (5-2 wire) but `event_type` is locked
    to `reversal_corrected`. The corrected row's `reverses_event_id` is
    the *original* target event_id (NOT the negating row), so the
    `(tenant_id, reverses_event_id)` UNIQUE constraint (Alembic 0015)
    blocks re-correction of the same target.

    `qty` is the user-corrected value (NOT sign-flipped).
    `period_key` is the period the corrected row belongs to (may equal
    `target_event.period_key` for same-period correction, or differ if
    the correction targets a different period).
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


# ── build_reversal_corrected_event ───────────────────────────
def build_reversal_corrected_event(
    *,
    target_event: InventoryLedgerEvent,
    correction_group_id: uuid.UUID,
    corrected_qty: Decimal | None,
    corrected_period_key: str | None,
    actor_id: uuid.UUID,
    trace_id: uuid.UUID,
    event_id: uuid.UUID | None = None,
) -> ReversalCorrectedEvent | None:
    """Build a corrected row sharing `correction_group_id` with the negating row.

    AD-22 sequence step 2 (optional): if `corrected_qty` and
    `corrected_period_key` are both provided, a corrected row is built
    with `qty = corrected_qty` (NOT sign-flipped — this is the new
    truth). If either is None, returns None — the caller should skip
    the corrected row INSERT.

    AD-15 parity: corrected_qty is quantized to QTY_QUANTUM via
    ROUND_HALF_EVEN.

    Args:
        target_event: Original InventoryLedgerEvent row whose correction
            the new row represents.
        correction_group_id: UUID shared with the sign-negating row.
        corrected_qty: New corrected qty (NOT sign-flipped). None skips.
        corrected_period_key: Period key the corrected row belongs to.
            None skips.
        actor_id: UUID of the reversal initiator.
        trace_id: UUID for end-to-end request correlation.
        event_id: Optional pre-minted UUID for the new row.

    Returns:
        ReversalCorrectedEvent NamedTuple ready for INSERT, or None
        if corrected_qty / corrected_period_key are None.

    Raises:
        ReversalCorrectedBuildError: On shape / correction_group_id /
            period_key mismatch.
    """
    # Skip path — corrected row is optional (PRD §F11.3 spec).
    if corrected_qty is None and corrected_period_key is None:
        return None
    if corrected_qty is None:
        raise ReversalCorrectedBuildError(
            message=(
                "corrected_qty must be provided together with corrected_period_key"
            ),
            error_code=ERROR_CODE_MISSING_CORRECTED_QTY,
            target_event_id=target_event.event_id,
        )
    if corrected_period_key is None:
        raise ReversalCorrectedBuildError(
            message=(
                "corrected_period_key must be provided together with corrected_qty"
            ),
            error_code=ERROR_CODE_MISSING_CORRECTED_PERIOD_KEY,
            target_event_id=target_event.event_id,
        )

    if target_event is None:
        raise ReversalCorrectedBuildError(
            message="target_event must not be None",
            error_code=ERROR_CODE_EMPTY_TARGET_EVENT,
            target_event_id=None,
        )
    if not isinstance(actor_id, uuid.UUID):
        raise ReversalCorrectedBuildError(
            message=f"actor_id must be UUID, got {type(actor_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_ACTOR_ID,
            target_event_id=target_event.event_id,
        )
    if not isinstance(trace_id, uuid.UUID):
        raise ReversalCorrectedBuildError(
            message=f"trace_id must be UUID, got {type(trace_id).__name__!r}",
            error_code=ERROR_CODE_NON_UUID_TRACE_ID,
            target_event_id=target_event.event_id,
        )
    if not isinstance(correction_group_id, uuid.UUID):
        raise ReversalCorrectedBuildError(
            message=(
                f"correction_group_id must be UUID, got "
                f"{type(correction_group_id).__name__!r}"
            ),
            error_code=ERROR_CODE_INVALID_CORRECTION_GROUP_ID,
            target_event_id=target_event.event_id,
        )
    if not isinstance(corrected_qty, Decimal):
        raise ReversalCorrectedBuildError(
            message=(
                f"corrected_qty must be Decimal, got "
                f"{type(corrected_qty).__name__!r}"
            ),
            error_code=ERROR_CODE_QTY_MUST_BE_DECIMAL,
            target_event_id=target_event.event_id,
        )

    # Defense-in-depth: validate constraints (correction_group_id
    # consistency + period_key AD-24 typed pattern).
    validate_reversal_corrected_constraints(
        target_event=target_event,
        correction_group_id=correction_group_id,
        corrected_period_key=corrected_period_key,
    )

    # Banker's rounding parity (CR 0-4).
    quantized_corrected_qty = corrected_qty.quantize(
        QTY_QUANTUM, rounding=ROUND_HALF_EVEN
    )

    new_event_id = event_id if event_id is not None else uuid.uuid4()

    return ReversalCorrectedEvent(
        event_id=new_event_id,
        tenant_id=target_event.tenant_id,
        product_id=target_event.product_id,
        period_key=corrected_period_key,
        event_type=REVERSAL_CORRECTED_EVENT_TYPE,
        qty=quantized_corrected_qty,
        trace_id=trace_id,
        # AD-22 D1 — corrected row does NOT carry `reverses_event_id`.
        # Only the sign-negating row owns `reverses_event_id=target_event.event_id`.
        # The corrected row's link to the target is via `correction_group_id`
        # (shared with the negating row). This prevents the (tenant_id,
        # reverses_event_id) PARTIAL UNIQUE INDEX from blocking a second
        # corrected INSERT on the same target — re-correction is permitted
        # because the corrected row has no `reverses_event_id`.
        reverses_event_id=None,
        correction_group_id=correction_group_id,
        reversal_of_period_key=target_event.period_key,
        actor_id=actor_id,
        payload={
            "source": "reversal_request",
            "corrected_period_key": corrected_period_key,
            "target_event_id": str(target_event.event_id),
            "actor_id": str(actor_id),
            "trace_id": str(trace_id),
        },
    )


# ── validate_reversal_corrected_constraints ──────────────────
def validate_reversal_corrected_constraints(
    *,
    target_event: InventoryLedgerEvent,
    correction_group_id: uuid.UUID,
    corrected_period_key: str,
    negating_correction_group_id: uuid.UUID | None = None,
) -> None:
    """Defense-in-depth check for corrected row construction.

    AD-22 sequence gate (corrected row side):
    - `correction_group_id` must be a UUID (validated by caller too).
    - `corrected_period_key` must match `^\\d{4}-(0[1-9]|1[0-2])$`
      (AD-24 typed).
    - If `negating_correction_group_id` is provided (service-layer
      cross-check after negating row INSERT), it must match the
      corrected row's `correction_group_id`.

    Raises:
        ReversalCorrectedBuildError: On any constraint violation.
    """
    if target_event is None:
        raise ReversalCorrectedBuildError(
            message="target_event must not be None",
            error_code=ERROR_CODE_EMPTY_TARGET_EVENT,
            target_event_id=None,
        )
    if not isinstance(correction_group_id, uuid.UUID):
        raise ReversalCorrectedBuildError(
            message=(
                f"correction_group_id must be UUID, got "
                f"{type(correction_group_id).__name__!r}"
            ),
            error_code=ERROR_CODE_INVALID_CORRECTION_GROUP_ID,
            target_event_id=target_event.event_id,
        )
    if not isinstance(corrected_period_key, str):
        raise ReversalCorrectedBuildError(
            message=(
                f"corrected_period_key must be str, got "
                f"{type(corrected_period_key).__name__!r}"
            ),
            error_code=ERROR_CODE_INCONSISTENT_CORRECTION_GROUP,
            target_event_id=target_event.event_id,
        )
    if not _PERIOD_KEY_PATTERN.match(corrected_period_key):
        raise ReversalCorrectedBuildError(
            message=(
                f"corrected_period_key {corrected_period_key!r} must match "
                f"'YYYY-MM' AD-24 typed pattern"
            ),
            error_code=ERROR_CODE_INVALID_CORRECTION_GROUP_ID,
            target_event_id=target_event.event_id,
        )
    if negating_correction_group_id is not None and correction_group_id != negating_correction_group_id:
        raise ReversalCorrectedBuildError(
            message=(
                f"corrected row's correction_group_id {correction_group_id!s} "
                f"does not match negating row's "
                f"{negating_correction_group_id!s}"
            ),
            error_code=ERROR_CODE_INCONSISTENT_CORRECTION_GROUP,
            target_event_id=target_event.event_id,
        )


__all__ = [
    "ERROR_CODE_INCONSISTENT_CORRECTION_GROUP",
    "ERROR_CODE_MISSING_CORRECTED_QTY",
    "ERROR_CODE_MISSING_CORRECTED_PERIOD_KEY",
    "ERROR_CODE_INVALID_CORRECTION_GROUP_ID",
    "M11_CORRECTED_BUILT_KO",
    "M11_CORRECTED_SKIPPED_KO",
    "M11_INCONSISTENT_CORRECTION_GROUP_KO",
    "M11_INVALID_CORRECTED_PERIOD_KEY_KO",
    "REVERSAL_CORRECTED_EVENT_TYPE",
    "ReversalCorrectedBuildError",
    "ReversalCorrectedEvent",
    "build_reversal_corrected_event",
    "validate_reversal_corrected_constraints",
]
