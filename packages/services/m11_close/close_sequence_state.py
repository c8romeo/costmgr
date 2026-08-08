"""packages.services.m11_close.close_sequence_state — Story 11.2 pure kernel.

AD-6 close lock PRIMARY guard. Computes the 4-stage close sequence
state from completion timestamps, and gates AD-6 INSERT refusal
("rows bounded by `fiscal_periods.status='closed'` reject business-data
INSERTs except AD-22 reversal/correction events").

Per AD-1 / AD-11: pure-Python, stdlib-only, NO DB, NO clock, NO random.

Korean constants — AD-15 §11 SSOT.
"""

from __future__ import annotations

from datetime import datetime
from typing import Final, Literal, NamedTuple

# ── Constants ────────────────────────────────────────────────
CloseSequenceState = Literal[
    "divisions", "manufacturing", "abc", "common", "confirmed"
]
TargetTable = Literal[
    "monthly_input_periods",
    "monthly_input_rows",
    "inventory_ledger",
    "fiscal_period_snapshots",
]
TargetEventType = Literal[
    "opening_carried",
    "purchase_inbound",
    "sales_outbound",
    "production_output_inbound",
    "production_material_consumption",
    "adjustment_positive",
    "adjustment_negative",
    "closing_snapshot",
    "reversal_negating",
    "reversal_corrected",
]

# AD-22 reversal/correction events are EXPLICITLY allowed past the
# close lock (Architecture Spine §AD-6 Rule — exception clause).
REVERSAL_TARGET_EVENT_TYPES: Final[frozenset[str]] = frozenset(
    {"reversal_negating", "reversal_corrected"}
)

# Tables that participate in the AD-6 close lock (business-data INSERTs).
AD6_LOCKED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "monthly_input_periods",
        "monthly_input_rows",
        "inventory_ledger",
        "fiscal_period_snapshots",
    }
)

ERROR_CODE_INVALID_INPUT: Final[str] = "INVALID_INPUT"


# ── Typed exception ──────────────────────────────────────────
class CloseSequenceStateError(Exception):
    """Pure-kernel computation violation.

    Distinct from service-layer typed exceptions. NO HTTP mapping.
    """

    def __init__(self, *, message: str, error_code: str = ERROR_CODE_INVALID_INPUT) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


# ── compute_close_sequence_state ─────────────────────────────
def compute_close_sequence_state(
    *,
    divisions_completed_at: datetime | None,
    manufacturing_completed_at: datetime | None,
    abc_completed_at: datetime | None,
    common_completed_at: datetime | None,
    closed_at: datetime | None,
) -> CloseSequenceState:
    """Return the close_sequence_state string given step timestamps.

    Logic:
        0 steps  → 'divisions'  (initial state)
        1 step   → 'manufacturing'
        2 steps  → 'abc'
        3 steps  → 'common'
        4 steps + closed_at populated → 'confirmed'
        4 steps + closed_at NULL     → 'common' (4 stages done, not
            yet confirmed — awaiting confirm_close_sequence call)
    """
    completed_count = sum(
        ts is not None
        for ts in (
            divisions_completed_at,
            manufacturing_completed_at,
            abc_completed_at,
            common_completed_at,
        )
    )
    if completed_count == 0:
        return "divisions"
    if completed_count == 1:
        return "manufacturing"
    if completed_count == 2:
        return "abc"
    if completed_count == 3:
        return "common"
    # 4 steps done.
    if closed_at is not None:
        return "confirmed"
    return "common"


# ── check_ad6_insert_allowed ─────────────────────────────────
class Ad6InsertGuardResult(NamedTuple):
    """Guard verdict for AD-6 INSERT refusal."""

    allowed: bool
    reject_reason_ko: str | None
    guard_type: Literal["ALLOWED", "CLOSED_LOCK", "REVERSAL_EXCEPTION"]


def check_ad6_insert_allowed(
    *,
    close_sequence_state: str,
    target_table: str,
    target_event_type: str,
) -> Ad6InsertGuardResult:
    """Decide whether an INSERT is permitted under AD-6 close lock.

    Rules (Architecture Spine §AD-6):
        - close_sequence_state='confirmed' → business-data INSERTs
          (monthly_input_periods, monthly_input_rows,
          inventory_ledger, fiscal_period_snapshots) are BLOCKED.
        - AD-22 reversal/correction events (reversal_negating,
          reversal_corrected) are EXPLICITLY allowed past the lock
          (PRD §F11.2 / Architecture Spine §AD-6 exception clause).
        - close_sequence_state NOT 'confirmed' → INSERTs allowed.

    Returns:
        Ad6InsertGuardResult with `allowed` flag + `reject_reason_ko`
        (Korean SSOT) + `guard_type` discriminator.

    Raises:
        CloseSequenceStateError: on invalid input shape.
    """
    if close_sequence_state not in (
        "divisions",
        "manufacturing",
        "abc",
        "common",
        "confirmed",
    ):
        raise CloseSequenceStateError(
            message=(
                f"close_sequence_state {close_sequence_state!r} is not "
                f"a known state"
            )
        )

    # Non-confirmed state → allow (no lock active yet).
    if close_sequence_state != "confirmed":
        return Ad6InsertGuardResult(
            allowed=True,
            reject_reason_ko=None,
            guard_type="ALLOWED",
        )

    # Confirmed state → AD-6 lock active.
    # AD-22 reversal/correction events pass through explicitly.
    if target_event_type in REVERSAL_TARGET_EVENT_TYPES:
        return Ad6InsertGuardResult(
            allowed=True,
            reject_reason_ko=None,
            guard_type="REVERSAL_EXCEPTION",
        )

    # Business-data tables in 'confirmed' state → BLOCKED.
    if target_table in AD6_LOCKED_TABLES:
        return Ad6InsertGuardResult(
            allowed=False,
            reject_reason_ko="마감이 확정되어 입력이 거부됩니다 (AD-6)",
            guard_type="CLOSED_LOCK",
        )

    # Tables not in AD-6 lock set (e.g., audit_logs, verification_log,
    # reversal_log) are allowed even in 'confirmed' state — these are
    # bookkeeping tables, not business-data.
    return Ad6InsertGuardResult(
        allowed=True,
        reject_reason_ko=None,
        guard_type="ALLOWED",
    )


__all__ = [
    "AD6_LOCKED_TABLES",
    "Ad6InsertGuardResult",
    "CloseSequenceState",
    "CloseSequenceStateError",
    "ERROR_CODE_INVALID_INPUT",
    "REVERSAL_TARGET_EVENT_TYPES",
    "TargetEventType",
    "TargetTable",
    "check_ad6_insert_allowed",
    "compute_close_sequence_state",
]
