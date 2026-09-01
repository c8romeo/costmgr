"""packages.services.m4_inventory.closing_period — Story 6.1 pure kernel.

Closing period service = closing 시점 ledger aggregate 영구화 + closing_snapshot
ledger event emit 진입점 (PRD §F4.3 + §F5 + §V4 + §A11 3-layer defense).

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m4_inventory/services/closing_period_service.py`
  (T3 service layer — ClosingPeriodService.evaluate_closing_period +
  confirm_closing_period + get_closing_period_audit_trail)
- `apps/api/modules/m6_verification/services/closing_period_snapshot_verifier.py`
  (T4 V4 slot fill — verify_v4_closing_period_consistency)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, no DB, no clock,
no random. Drift between Python and TS caught by
`tests/integration/test_closing_period_label_consistency.py` (NEW 6-1).

Closing period status classification (PRD §F4.3):
- CLOSING_READY: invariant OK + ledger events >= 1 → 마감 확정 가능
- CLOSING_BLOCKED: invariant NEGATIVE_CLOSING → 마감 차단
- ALREADY_CLOSED: monthly_input_periods.status='closed' → idempotent no-op skip
- EMPTY_PERIOD: ledger events 0건 → 마감 불가

Korean message SSOT (AD-15 §11):
- `CLOSING_PERIOD_CONFIRMATION_KO` mirrors
  `apps/web/lib/closing-period.ts::formatClosingPeriodConfirmationKo`.
- `CLOSING_PERIOD_BLOCKED_KO` mirrors
  `apps/web/lib/closing-period.ts::formatClosingPeriodBlockedKo`.

Layering (AD-11):
- Pure helpers in `packages/services/m4_inventory/`
- Mirrored TS projection at `apps/web/lib/closing-period.ts`
- Drift caught by `tests/integration/test_closing_period_label_consistency.py`

PRD §6.2 수불부 invariant:
- closing = opening + inbound - outbound (QTY_QUANTUM, ROUND_HALF_EVEN)
- closing MUST be ≥ 0 for ALL inventory-tracked products (PRD §V3)
- closing_snapshot ledger event = per-product closing balance materialize
  (AD-2 append-only + 5-2 wire 진입점 + Epic 11 reversal entrypoint)

A8 inline projection deprecation timeline:
- 6-1 wire 시점: inline projection 보존 (1 epic maintenance window 진행 중)
- Epic 6 close-out 시점에 fold-in vs deprecate 결정 필수
  (PRD §F4.3 closing_period service = AD-2 ledger aggregate SSOT)
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, NamedTuple

from packages.services.m2_input.inventory_math import QTY_QUANTUM

# ── Constants ────────────────────────────────────────────────
# Korean message SSOT (AD-15 §11 parity with TS
# `formatClosingPeriodConfirmationKo` + `formatClosingPeriodBlockedKo`).
# Drift caught by integration test
# `tests/integration/test_closing_period_label_consistency.py`.
CLOSING_PERIOD_CONFIRMATION_KO: Final[str] = "월 마감 확정: 기말재고 snapshot 저장"
CLOSING_PERIOD_BLOCKED_KO: Final[str] = "마감 차단: 기말재고 음수"

# Closing period status classification 4 codes (PRD §F4.3 + §V4 + §A11).
CLOSING_PERIOD_STATUS_READY: Final[str] = "CLOSING_READY"
CLOSING_PERIOD_STATUS_BLOCKED: Final[str] = "CLOSING_BLOCKED"
CLOSING_PERIOD_STATUS_ALREADY_CLOSED: Final[str] = "ALREADY_CLOSED"
CLOSING_PERIOD_STATUS_EMPTY_PERIOD: Final[str] = "EMPTY_PERIOD"

CLOSING_PERIOD_STATUSES: Final[frozenset[str]] = frozenset(
    {
        CLOSING_PERIOD_STATUS_READY,
        CLOSING_PERIOD_STATUS_BLOCKED,
        CLOSING_PERIOD_STATUS_ALREADY_CLOSED,
        CLOSING_PERIOD_STATUS_EMPTY_PERIOD,
    }
)


# ── ClosingPeriodError ─────────────────────────────────────────
class ClosingPeriodError(Exception):
    """Pure-kernel closing period domain error.

    Distinct from service-layer typed exceptions (which carry HTTP
    envelope + audit-first semantics). This exception is raised by the
    pure kernel when invariants are violated at the domain level (e.g.
    invalid period_key, unknown status code, non-finite qty).
    NO HTTP mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "CLOSING_PERIOD_ERROR",
        period_key: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.period_key = period_key
        self.tenant_id = tenant_id


# ── ClosingSnapshotEntry ─────────────────────────────────────
class ClosingSnapshotEntry(NamedTuple):
    """Pure-data closing snapshot ledger entry (per-product).

    AD-15: snake_case field names. Mirrors TS
    `apps/web/lib/l2-input-inventory-ledger.ts::ClosingSnapshotEvent`.

    `closing_qty` is the per-product closing balance (Decimal, quantized
    to QTY_QUANTUM via ROUND_HALF_EVEN — CR 0-4 lesson). `finalized_at`
    is the ISO-8601 UTC timestamp string passed by the caller (AD-5:
    pure kernel has no clock).

    Each entry maps to ONE inventory_ledger row with
    `event_type='closing_snapshot'` (5-2 11-value whitelist). Per
    product 1 row = N rows total per period_key.
    """

    product_id: uuid.UUID
    closing_qty: Decimal
    finalized_at: str  # ISO-8601 UTC


# ── ClosingPeriodResult ────────────────────────────────────────
class ClosingPeriodResult(NamedTuple):
    """Pure-data closing period evaluation result.

    Mirrors TS `apps/web/lib/closing-period.ts::ClosingPeriodState`.

    - `status`: One of CLOSING_PERIOD_STATUSES 4 codes.
    - `allowed`: True iff status == CLOSING_READY (PRD §F4.3 gate).
    - `closing_per_product`: dict[product_id → closing_qty] Decimal
      per product (empty when EMPTY_PERIOD).
    - `closing_snapshot_count`: number of closing_snapshot ledger
      events already in inventory_ledger (0 for first confirm).
    - `ledger_event_count`: total inventory_ledger event count for the
      period (includes purchase_inbound + sales_outbound + production
      etc. — NOT closing_snapshot).
    - `period_key`: 'YYYY-MM' AD-24 typed.
    """

    status: str
    allowed: bool
    closing_per_product: dict[uuid.UUID, Decimal]
    closing_snapshot_count: int
    ledger_event_count: int
    period_key: str


# ── compute_closing_snapshot ──────────────────────────────────
def compute_closing_snapshot(
    closing_per_product: dict[uuid.UUID, Decimal],
    *,
    period_key: str,
    finalized_at: str,
) -> list[ClosingSnapshotEntry]:
    """Build per-product closing_snapshot ledger entries.

    Pure kernel — takes closing_per_product (from 5-3
    `compute_closing_balance_per_product` result) + caller-provided
    period_key + finalized_at, returns list of ClosingSnapshotEntry
    ready for 5-2 `LedgerService.append_event(event_type='closing_snapshot', ...)`.

    AD-15 §11 banker's rounding (CR 0-4 lesson): each closing_qty is
    quantized to QTY_QUANTUM via ROUND_HALF_EVEN. Cross-language parity
    with TS Decimal.set scale parity.

    Args:
        closing_per_product: dict[product_id → closing_qty Decimal]
            from 5-3 closing_guard pure kernel. Empty when EMPTY_PERIOD.
        period_key: 'YYYY-MM' AD-24 typed period key (caller-validated).
        finalized_at: ISO-8601 UTC timestamp string (service layer
            owns datetime.now(UTC); AD-5 pure kernel no clock).

    Returns:
        list[ClosingSnapshotEntry] — 1 entry per product. Empty list
        when closing_per_product is empty (EMPTY_PERIOD case).

    Raises:
        ClosingPeriodError: If any closing_qty is non-finite
            (NaN/Infinity) — caught at compute_closing_balance_per_product
            call site, defense-in-depth here.
    """
    entries: list[ClosingSnapshotEntry] = []
    for product_id, closing_qty in closing_per_product.items():
        if not isinstance(closing_qty, Decimal):
            raise ClosingPeriodError(
                message=(
                    f"closing_qty must be Decimal, got "
                    f"{type(closing_qty).__name__!r} for product_id={product_id}"
                ),
                error_code="QTY_MUST_BE_DECIMAL",
                period_key=period_key,
            )
        if not closing_qty.is_finite():
            raise ClosingPeriodError(
                message=(
                    f"closing_qty is non-finite {closing_qty!r} " f"for product_id={product_id}"
                ),
                error_code="NON_FINITE_QTY",
                period_key=period_key,
            )
        quantized = closing_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
        entries.append(
            ClosingSnapshotEntry(
                product_id=product_id,
                closing_qty=quantized,
                finalized_at=finalized_at,
            )
        )
    # Sort by product_id for deterministic ordering (V8 byte-identical
    # fixture parity + audit payload reproducibility).
    entries.sort(key=lambda e: e.product_id)
    return entries


# ── classify_closing_period_status ────────────────────────────
def classify_closing_period_status(
    closing_per_product: dict[uuid.UUID, Decimal],
    *,
    ledger_event_count: int,
    is_already_closed: bool,
) -> str:
    """Classify the closing period status per PRD §F4.3 + §V4 + §A11.

    Classification rules (in priority order):
    1. `is_already_closed=True` → ALREADY_CLOSED (idempotent no-op skip).
    2. `ledger_event_count == 0` → EMPTY_PERIOD (no events at all in this
       period, regardless of opening carry chain populating
       `closing_per_product` from prev period).
    3. Any closing < 0 → CLOSING_BLOCKED (PRD §F4.2 invariant violation,
       5-3 closing_guard service dispatched NEGATIVE_CLOSING_INVENTORY).
    4. All closing >= 0 AND ledger_event_count >= 1 → CLOSING_READY
       (마감 확정 가능 — confirm_closing_period dispatch entry).

    Args:
        closing_per_product: dict[product_id → closing_qty] from 5-3
            `compute_closing_balance_per_product`.
        ledger_event_count: total inventory_ledger event count for the
            period (excludes closing_snapshot to avoid double-counting).
        is_already_closed: True iff
            `monthly_input_periods.status == 'closed'` (service layer
            reads AD-6 fiscal-period close lock).

    Returns:
        str — one of CLOSING_PERIOD_STATUSES 4 codes.

    Raises:
        ClosingPeriodError: If ledger_event_count is negative
            (defense-in-depth — caller should never pass < 0).
    """
    if ledger_event_count < 0:
        raise ClosingPeriodError(
            message=(f"ledger_event_count must be >= 0, got {ledger_event_count!r}"),
            error_code="NEGATIVE_LEDGER_EVENT_COUNT",
        )

    # Priority 1: already closed → idempotent no-op
    if is_already_closed:
        return CLOSING_PERIOD_STATUS_ALREADY_CLOSED

    # Priority 2: empty period (ledger_event_count == 0 regardless of
    # opening carry chain populating closing_per_product)
    if ledger_event_count == 0:
        return CLOSING_PERIOD_STATUS_EMPTY_PERIOD

    # Priority 3: invariant violation (PRD §V3)
    for qty in closing_per_product.values():
        if qty < Decimal("0"):
            return CLOSING_PERIOD_STATUS_BLOCKED

    # Priority 4: ready to confirm
    return CLOSING_PERIOD_STATUS_READY


# ── is_closing_period_allowed ─────────────────────────────────
def is_closing_period_allowed(status: str) -> bool:
    """Return True iff `status == CLOSING_PERIOD_STATUS_READY`.

    Single source of truth for the close-time gate (PRD §F4.3).
    Mirrors TS `isClosingPeriodAllowed` in `apps/web/lib/closing-period.ts`.

    Args:
        status: One of CLOSING_PERIOD_STATUSES 4 codes.

    Returns:
        bool — True iff status is CLOSING_READY.

    Raises:
        ClosingPeriodError: If status is not in CLOSING_PERIOD_STATUSES
            (defense-in-depth — caller must classify first).
    """
    if status not in CLOSING_PERIOD_STATUSES:
        raise ClosingPeriodError(
            message=(
                f"closing period status {status!r} is not in the 4-code "
                f"set. Accepted: {sorted(CLOSING_PERIOD_STATUSES)}"
            ),
            error_code="INVALID_CLOSING_PERIOD_STATUS",
        )
    return status == CLOSING_PERIOD_STATUS_READY


# ── format_closing_period_confirmation_ko ─────────────────────
def format_closing_period_confirmation_ko(result: ClosingPeriodResult) -> str:
    """Build the Korean confirmation message for the closing-period UI.

    Mirrors TS `formatClosingPeriodConfirmationKo` for AD-15 §11 parity.

    Args:
        result: from service layer (wraps pure-kernel classification
            + ledger aggregate). Must be status=CLOSING_READY.

    Returns:
        str — Korean message SSOT. Empty when status != CLOSING_READY
            (caller must dispatch UI based on status code, not message).

    Examples:
        >>> result = ClosingPeriodResult(
        ...     status=CLOSING_PERIOD_STATUS_READY,
        ...     allowed=True,
        ...     closing_per_product={UUID(...): Decimal("100")},
        ...     closing_snapshot_count=0,
        ...     ledger_event_count=10,
        ...     period_key="2026-07",
        ... )
        >>> format_closing_period_confirmation_ko(result)
        '월 마감 확정: 기말재고 snapshot 저장'
    """
    if result.status != CLOSING_PERIOD_STATUS_READY:
        return ""
    return CLOSING_PERIOD_CONFIRMATION_KO


# ── format_closing_period_blocked_ko ──────────────────────────
def format_closing_period_blocked_ko(result: ClosingPeriodResult) -> str:
    """Build the Korean blocked-banner message for the closing-period UI.

    Mirrors TS `formatClosingPeriodBlockedKo` for AD-15 §11 parity.

    Args:
        result: from service layer. Must be status=CLOSING_BLOCKED.

    Returns:
        str — Korean message SSOT. Empty when status != CLOSING_BLOCKED.
    """
    if result.status != CLOSING_PERIOD_STATUS_BLOCKED:
        return ""
    return CLOSING_PERIOD_BLOCKED_KO


__all__ = [
    "CLOSING_PERIOD_BLOCKED_KO",
    "CLOSING_PERIOD_CONFIRMATION_KO",
    "CLOSING_PERIOD_STATUS_ALREADY_CLOSED",
    "CLOSING_PERIOD_STATUS_BLOCKED",
    "CLOSING_PERIOD_STATUS_EMPTY_PERIOD",
    "CLOSING_PERIOD_STATUS_READY",
    "CLOSING_PERIOD_STATUSES",
    "ClosingPeriodError",
    "ClosingPeriodResult",
    "ClosingSnapshotEntry",
    "classify_closing_period_status",
    "compute_closing_snapshot",
    "format_closing_period_blocked_ko",
    "format_closing_period_confirmation_ko",
    "is_closing_period_allowed",
]
