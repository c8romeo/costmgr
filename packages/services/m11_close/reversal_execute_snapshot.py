"""packages.services.m11_close.reversal_execute_snapshot — Story 11.3 pure kernel.

AD-22 reversal 영구화 (committed → reversed transition).

This kernel validates the AD-22 reversal pair construction — the
sign-negating row + corrected row that the 11-1 wire emits as part of
the reversal sequence. Story 11.3 adds a NEW constraint: the
underlying fiscal_period_snapshots row must be in state='committed'
(the 3-tier guard introduced alongside M11 owner wire).

AD-20 state machine context:
  draft → verified → committed → reversed
                                ^^^^^^^^^
                                AD-22 영구화

AD-1 / AD-11 binding: pure-Python, stdlib-only, NO DB, NO clock, NO
random. Service layer passes all inputs explicitly.

Korean constants — AD-15 §11 SSOT. Mirrored verbatim in
`apps/web/lib/m11-snapshot.ts`.

Story 11.3 wire — 3-tier guard:
1. monthly_input_periods.status — 11-1 SSOT (open/closed allowed)
2. fiscal_periods.status — 11-2 PRIMARY (closed only)
3. fiscal_period_snapshots.state — 11-3 NEW (committed only — the
   AD-20 state machine guarantees a snapshot exists and is sealed
   BEFORE reversal is attempted)
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# AD-20 3-tier guard — fiscal_period_snapshots.state must be 'committed'.
# Per AD-22 영구화 contract (PRD §F11.3): reversal operates on a
# sealed snapshot. A 'verified' snapshot has not yet been committed
# (the V1·V4·V7·V8 verifiers have passed but the owner has not yet
# sealed it as immutable summary record). A 'reversed' snapshot has
# already been reversed — re-reversal would corrupt the audit trail.
SNAPSHOT_STATE_REQUIRED: Final[frozenset[str]] = frozenset({"committed"})
SNAPSHOT_STATE_REJECTED_DRAFT: Final[frozenset[str]] = frozenset({"draft"})
SNAPSHOT_STATE_REJECTED_VERIFIED: Final[frozenset[str]] = frozenset({"verified"})
SNAPSHOT_STATE_REJECTED_REVERSED: Final[frozenset[str]] = frozenset({"reversed"})

# Banker's rounding parity — QTY_QUANTUM = NUMERIC(18, 4) (CR 0-4).
QTY_QUANTUM: Final[Decimal] = Decimal("0.0001")

# Error codes — pure-kernel domain semantics.
ERROR_CODE_INVALID_INPUT: Final[str] = "INVALID_REVERSAL_INPUT"
ERROR_CODE_INVALID_SNAPSHOT_STATE: Final[str] = "INVALID_SNAPSHOT_STATE"
ERROR_CODE_INSUFFICIENT_QTY: Final[str] = "INSUFFICIENT_QTY_FOR_NEGATING"

# Korean constants — AD-15 §11 SSOT.
REVERSAL_EXECUTE_OK_KO: Final[str] = "스냅샷 역분개 완료"
REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO: Final[str] = (
    "스냅샷 상태가 커밋 상태가 아닙니다 — 역분개 불가"
)


# ── Typed exception ──────────────────────────────────────────
class ReversalExecuteSnapshotError(Exception):
    """Pure-kernel reversal 영구화 violation.

    Distinct from service-layer `ReversalSnapshotMismatchError`. NO
    HTTP mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str,
        snapshot_id: uuid.UUID | None = None,
        snapshot_state: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.snapshot_id = snapshot_id
        self.snapshot_state = snapshot_state


# ── NegatingRowSpec + CorrectedRowSpec ──────────────────────
class NegatingRowSpec(NamedTuple):
    """Specification for the sign-negating row (AD-22 step 5).

    The negating row is a NEW inventory_ledger row with qty = -target.qty.
    It points back to the original via reverses_event_id and shares
    correction_group_id with the corrected row (if any).
    """

    tenant_id: uuid.UUID
    product_id: uuid.UUID
    period_key: str
    event_type: str  # 'reversal_negating'
    negating_qty: Decimal  # absolute value, positive
    reverses_event_id: uuid.UUID
    correction_group_id: uuid.UUID
    actor_id: uuid.UUID
    trace_id: str


class CorrectedRowSpec(NamedTuple):
    """Specification for the corrected row (AD-22 step 6 — optional).

    The corrected row is a NEW inventory_ledger row with the corrected
    qty (qty = corrected_qty). It shares correction_group_id with the
    negating row. Optional — only emitted when corrected_qty is set.
    """

    tenant_id: uuid.UUID
    product_id: uuid.UUID
    period_key: str
    event_type: str  # 'reversal_corrected'
    corrected_qty: Decimal
    correction_group_id: uuid.UUID
    actor_id: uuid.UUID
    trace_id: str


# ── ReversalExecuteSnapshotResult ───────────────────────────
class ReversalExecuteSnapshotResult(NamedTuple):
    """Pure-kernel decision for AD-22 영구화 (committed → reversed)."""

    authorized: bool
    snapshot_state: str
    correction_group_id: uuid.UUID
    target_event_id: uuid.UUID
    negating_qty: Decimal  # absolute value of the negating row qty
    corrected_qty: Decimal | None
    tenant_id: uuid.UUID
    actor_id: uuid.UUID


# ── validate_reversal_execute_snapshot ─────────────────────
def validate_reversal_execute_snapshot(
    *,
    tenant_id: uuid.UUID,
    target_event_id: uuid.UUID,
    snapshot_id: uuid.UUID,
    snapshot_state: str,
    target_qty: Decimal,
    corrected_qty: Decimal | None,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
) -> ReversalExecuteSnapshotResult:
    """Validate AD-22 영구화: committed snapshot → reversed state.

    Story 11.3 PRIMARY. The reversal 영구화 (영구화 = 영구화 = 영구 보존)
    is the FINAL step in the AD-22 reversal sequence. It transitions
    fiscal_period_snapshots.state from 'committed' to 'reversed' and
    emits the sign-negating + corrected row pair.

    Args:
        tenant_id: Owning tenant (audit attribution).
        target_event_id: The inventory_ledger.event_id being reversed.
        snapshot_id: The fiscal_period_snapshots.snapshot_id (must be
            in state='committed').
        snapshot_state: The snapshot's current state — one of
            'draft' / 'verified' / 'committed' / 'reversed'.
        target_qty: The target event's qty (positive Decimal). The
            negating row's qty will be -target_qty.
        corrected_qty: Optional corrected qty (AD-22 step 6). If
            None, only the negating row is emitted.
        correction_group_id: Minted by the caller (11-1 wire: uuid7
            fallback to uuid4). Links the negating + corrected rows.
        actor_id: UUID of the reversal initiator.

    Returns:
        ReversalExecuteSnapshotResult with `authorized` flag +
        `negating_qty` (the absolute value the service layer will
        insert as qty=-negating_qty) + `corrected_qty` (or None).

    Raises:
        ReversalExecuteSnapshotError: On invalid input shape
            (non-UUID tenant/actor/snapshot, invalid snapshot_state,
            negative target_qty, negative corrected_qty).
    """
    if not isinstance(tenant_id, uuid.UUID):
        raise ReversalExecuteSnapshotError(
            message=f"tenant_id must be UUID, got {type(tenant_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(target_event_id, uuid.UUID):
        raise ReversalExecuteSnapshotError(
            message=f"target_event_id must be UUID, got {type(target_event_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(snapshot_id, uuid.UUID):
        raise ReversalExecuteSnapshotError(
            message=f"snapshot_id must be UUID, got {type(snapshot_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(correction_group_id, uuid.UUID):
        raise ReversalExecuteSnapshotError(
            message=f"correction_group_id must be UUID, got {type(correction_group_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(actor_id, uuid.UUID):
        raise ReversalExecuteSnapshotError(
            message=f"actor_id must be UUID, got {type(actor_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(target_qty, Decimal):
        raise ReversalExecuteSnapshotError(
            message=f"target_qty must be Decimal, got {type(target_qty).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if target_qty < Decimal("0"):
        raise ReversalExecuteSnapshotError(
            message=(
                f"target_qty must be non-negative, got {target_qty!r}"
            ),
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if corrected_qty is not None:
        if not isinstance(corrected_qty, Decimal):
            raise ReversalExecuteSnapshotError(
                message=f"corrected_qty must be Decimal or None, got {type(corrected_qty).__name__!r}",
                error_code=ERROR_CODE_INVALID_INPUT,
            )
        if corrected_qty < Decimal("0"):
            raise ReversalExecuteSnapshotError(
                message=(
                    f"corrected_qty must be non-negative, got {corrected_qty!r}"
                ),
                error_code=ERROR_CODE_INVALID_INPUT,
            )

    if snapshot_state not in (
        SNAPSHOT_STATE_REQUIRED
        | SNAPSHOT_STATE_REJECTED_DRAFT
        | SNAPSHOT_STATE_REJECTED_VERIFIED
        | SNAPSHOT_STATE_REJECTED_REVERSED
    ):
        raise ReversalExecuteSnapshotError(
            message=(
                f"snapshot_state {snapshot_state!r} is not in the known "
                f"AD-20 lifecycle "
                f"({sorted(SNAPSHOT_STATE_REQUIRED | SNAPSHOT_STATE_REJECTED_DRAFT | SNAPSHOT_STATE_REJECTED_VERIFIED | SNAPSHOT_STATE_REJECTED_REVERSED)})"
            ),
            error_code=ERROR_CODE_INVALID_SNAPSHOT_STATE,
            snapshot_id=snapshot_id,
            snapshot_state=snapshot_state,
        )

    # Snapshot must be in 'committed' state for reversal 영구화.
    if snapshot_state not in SNAPSHOT_STATE_REQUIRED:
        return ReversalExecuteSnapshotResult(
            authorized=False,
            snapshot_state=snapshot_state,
            correction_group_id=correction_group_id,
            target_event_id=target_event_id,
            negating_qty=Decimal("0"),
            corrected_qty=corrected_qty,
            tenant_id=tenant_id,
            actor_id=actor_id,
        )

    # Authorized: state='committed' → reversed transition.
    return ReversalExecuteSnapshotResult(
        authorized=True,
        snapshot_state=snapshot_state,
        correction_group_id=correction_group_id,
        target_event_id=target_event_id,
        negating_qty=target_qty,  # absolute value (sign applied at INSERT)
        corrected_qty=corrected_qty,
        tenant_id=tenant_id,
        actor_id=actor_id,
    )


# ── build_negating_row_spec ─────────────────────────────────
def build_negating_row_spec(
    *,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    period_key: str,
    target_qty: Decimal,
    target_event_id: uuid.UUID,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> NegatingRowSpec:
    """Build the AD-22 sign-negating row specification.

    The qty value is the absolute value of target_qty; the service
    layer applies the negative sign at INSERT time. This keeps the
    pure-kernel math in non-negative space (defense-in-depth).
    """
    if not isinstance(tenant_id, uuid.UUID):
        raise ReversalExecuteSnapshotError(
            message=f"tenant_id must be UUID, got {type(tenant_id).__name__!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )
    if not isinstance(target_qty, Decimal) or target_qty < Decimal("0"):
        raise ReversalExecuteSnapshotError(
            message=f"target_qty must be non-negative Decimal, got {target_qty!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )

    return NegatingRowSpec(
        tenant_id=tenant_id,
        product_id=product_id,
        period_key=period_key,
        event_type="reversal_negating",
        negating_qty=target_qty,
        reverses_event_id=target_event_id,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
        trace_id=trace_id,
    )


# ── build_corrected_row_spec ───────────────────────────────
def build_corrected_row_spec(
    *,
    tenant_id: uuid.UUID,
    product_id: uuid.UUID,
    period_key: str,
    corrected_qty: Decimal,
    correction_group_id: uuid.UUID,
    actor_id: uuid.UUID,
    trace_id: str,
) -> CorrectedRowSpec:
    """Build the AD-22 corrected row specification (optional step 6)."""
    if not isinstance(corrected_qty, Decimal) or corrected_qty < Decimal("0"):
        raise ReversalExecuteSnapshotError(
            message=f"corrected_qty must be non-negative Decimal, got {corrected_qty!r}",
            error_code=ERROR_CODE_INVALID_INPUT,
        )

    return CorrectedRowSpec(
        tenant_id=tenant_id,
        product_id=product_id,
        period_key=period_key,
        event_type="reversal_corrected",
        corrected_qty=corrected_qty,
        correction_group_id=correction_group_id,
        actor_id=actor_id,
        trace_id=trace_id,
    )


__all__ = [
    "ERROR_CODE_INSUFFICIENT_QTY",
    "ERROR_CODE_INVALID_INPUT",
    "ERROR_CODE_INVALID_SNAPSHOT_STATE",
    "QTY_QUANTUM",
    "REVERSAL_EXECUTE_INVALID_SNAPSHOT_KO",
    "REVERSAL_EXECUTE_OK_KO",
    "SNAPSHOT_STATE_REJECTED_DRAFT",
    "SNAPSHOT_STATE_REJECTED_REVERSED",
    "SNAPSHOT_STATE_REJECTED_VERIFIED",
    "SNAPSHOT_STATE_REQUIRED",
    "CorrectedRowSpec",
    "NegatingRowSpec",
    "ReversalExecuteSnapshotError",
    "ReversalExecuteSnapshotResult",
    "build_corrected_row_spec",
    "build_negating_row_spec",
    "validate_reversal_execute_snapshot",
]
