"""packages.services.m4_inventory.closing_guard — Story 5.3 pure kernel.

Closing inventory ≥ 0 invariant check (PRD §F4.2 + §V3).

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m4_inventory/services/closing_guard_service.py`
  (T4 service layer — evaluate_closing_guard + request_close_attempt)
- `apps/api/modules/m6_verification/services/closing_invariant_verifier.py`
  (T5 V3 slot fill — verify_v3_closing_invariant)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, no DB, no clock,
no random. Drift between Python and TS caught by
`tests/integration/test_closing_guard_label_consistency.py` (NEW 5-3).

Korean error message SSOT (AD-15 §11):
- `NEGATIVE_CLOSING_INVENTORY_KO` mirrors
  `apps/web/lib/closing-guard.ts::formatNegativeClosingBannerKo`.

Layering (AD-11):
- Pure helpers in `packages/services/m4_inventory/`
- Mirrored TS projection at `apps/web/lib/closing-guard.ts`
- Drift caught by `tests/integration/test_closing_guard_label_consistency.py`

PRD §6.2 수불부 invariant:
- closing = opening + inbound - outbound (QTY_QUANTUM, ROUND_HALF_EVEN)
- closing MUST be ≥ 0 for ALL inventory-tracked products (PRD §V3).
- Negative closing = NEGATIVE_CLOSING → 마감 차단 (PRD §F4.2).
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, NamedTuple

from packages.services.m2_input.inventory_math import QTY_QUANTUM
from packages.services.m4_inventory.ledger import InventoryLedgerEvent

# ── Constants ────────────────────────────────────────────────
# Korean message SSOT (AD-15 §11 parity with TS
# `formatNegativeClosingBannerKo`). Drift caught by integration test.
NEGATIVE_CLOSING_INVENTORY_KO: Final[str] = "기말재고 음수: 마감 불가"

# Closing invariant classification 3 codes (PRD §F4.2 + §V3).
INVARIANT_CODE_CLOSING_OK: Final[str] = "CLOSING_OK"
INVARIANT_CODE_NEGATIVE_CLOSING: Final[str] = "NEGATIVE_CLOSING"
INVARIANT_CODE_EMPTY_PERIOD: Final[str] = "EMPTY_PERIOD"

INVARIANT_CODES: Final[frozenset[str]] = frozenset(
    {
        INVARIANT_CODE_CLOSING_OK,
        INVARIANT_CODE_NEGATIVE_CLOSING,
        INVARIANT_CODE_EMPTY_PERIOD,
    }
)


# ── ClosingInvariant ─────────────────────────────────────────
class ClosingInvariant(NamedTuple):
    """Pure-data closing invariant classification result.

    AD-15: snake_case field names. Mirrored to TS `ClosingInvariant`.

    - `code`: INVARIANT_CODE_CLOSING_OK / NEGATIVE_CLOSING / EMPTY_PERIOD.
    - `negative_products`: dict[product_id → qty Decimal] of products
      with closing < 0 (empty when CLOSING_OK or EMPTY_PERIOD).
    - `closing_per_product`: dict[product_id → qty Decimal] of ALL
      product closings in the period (empty when EMPTY_PERIOD).
    - `guard_enabled`: True (5-3 spec — service-only tenant gets
      `guard_enabled=False` from `ClosingGuardService`).
    """

    code: str
    negative_products: dict[uuid.UUID, Decimal]
    closing_per_product: dict[uuid.UUID, Decimal]
    guard_enabled: bool


# ── ClosingGuardError ─────────────────────────────────────────
class ClosingGuardError(Exception):
    """Pure-kernel closing guard domain error.

    Distinct from service-layer typed exceptions (which carry HTTP
    envelope + audit-first semantics). This exception is raised by the
    pure kernel when invariants are violated at the domain level (e.g.
    non-finite Decimal, unknown invariant code, invalid guard_enabled).
    NO HTTP mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "CLOSING_GUARD_ERROR",
        period_key: str | None = None,
        product_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.period_key = period_key
        self.product_id = product_id


# ── compute_closing_balance_per_product ──────────────────────
def compute_closing_balance_per_product(
    ledger_events: list[InventoryLedgerEvent],
) -> dict[uuid.UUID, Decimal]:
    """Compute closing balance per product from inventory_ledger events.

    SIGN-NEUTRAL aggregate per AD-22 + 5-2 schema: outbound events carry
    NEGATIVE qty at write-time (per P2 review fix preserved), so a plain
    `SUM(qty)` per product yields the closing balance. This is the SSOT
    read path replacing the Epic 3.3 inline projection (Epic 4 close-out
    A3 cj-style 결정).

    Args:
        ledger_events: All events for the period. May be empty.
            Caller is responsible for filtering by tenant_id + period_key
            (service layer owns RLS predicate + AD-3 filter).

    Returns:
        dict[product_id → closing Decimal] with each qty quantized to
        QTY_QUANTUM via ROUND_HALF_EVEN (CR 0-4 lesson).

    Raises:
        ClosingGuardError: If any qty is non-finite (NaN / Infinity).
    """
    bucket: dict[uuid.UUID, Decimal] = {}
    for event in ledger_events:
        if event.qty is None:
            continue  # non-quantitative events (closing_snapshot)
        if not event.qty.is_finite():
            raise ClosingGuardError(
                message=(
                    f"inventory_ledger event {event.event_id} has non-finite " f"qty {event.qty!r}"
                ),
                error_code="NON_FINITE_QTY",
                product_id=event.product_id,
            )
        bucket[event.product_id] = bucket.get(event.product_id, Decimal("0")) + event.qty
    return {pid: qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN) for pid, qty in bucket.items()}


# ── classify_closing_invariant ───────────────────────────────
def classify_closing_invariant(
    closing_per_product: dict[uuid.UUID, Decimal],
) -> ClosingInvariant:
    """Classify the closing invariant per PRD §V3 + §F4.2.

    Classification rules:
    - `closing_per_product` empty → EMPTY_PERIOD (no events at all).
    - Any closing < 0 → NEGATIVE_CLOSING (with negative_products populated).
    - All closing ≥ 0 → CLOSING_OK.

    Args:
        closing_per_product: from `compute_closing_balance_per_product`.

    Returns:
        `ClosingInvariant` NamedTuple with code + negative_products +
        closing_per_product + guard_enabled=True (caller adjusts
        guard_enabled per industry check).
    """
    if not closing_per_product:
        return ClosingInvariant(
            code=INVARIANT_CODE_EMPTY_PERIOD,
            negative_products={},
            closing_per_product={},
            guard_enabled=True,
        )

    negative_products: dict[uuid.UUID, Decimal] = {}
    for pid, qty in closing_per_product.items():
        if qty < Decimal("0"):
            negative_products[pid] = qty

    if negative_products:
        return ClosingInvariant(
            code=INVARIANT_CODE_NEGATIVE_CLOSING,
            negative_products=_sort_dict_by_qty(negative_products),
            closing_per_product=closing_per_product,
            guard_enabled=True,
        )

    return ClosingInvariant(
        code=INVARIANT_CODE_CLOSING_OK,
        negative_products={},
        closing_per_product=closing_per_product,
        guard_enabled=True,
    )


# ── is_close_blocked ─────────────────────────────────────────
def is_close_blocked(invariant: ClosingInvariant) -> bool:
    """Return True iff `invariant.code == NEGATIVE_CLOSING`.

    Single source of truth for the close-time gate (PRD §F4.2).
    Mirrors TS `shouldDisableCloseButton`.
    """
    return invariant.code == INVARIANT_CODE_NEGATIVE_CLOSING


# ── format_negative_closing_banner_ko ────────────────────────
def format_negative_closing_banner_ko(
    invariant: ClosingInvariant,
    *,
    product_name_lookup: dict[uuid.UUID, str] | None = None,
) -> str:
    """Build the Korean red-banner message for the closing-guard UI.

    Mirrors TS `formatNegativeClosingBannerKo` for AD-15 §11 parity.
    Returns `NEGATIVE_CLOSING_INVENTORY_KO` for empty negative_products
    (defensive — caller should not invoke this branch for CLOSING_OK).

    Args:
        invariant: from `classify_closing_invariant`. Must be
            NEGATIVE_CLOSING for meaningful output.
        product_name_lookup: Optional mapping product_id → product_name
            for human-readable display. None → use product_id_str.

    Returns:
        Korean message string. Example:
        "기말재고 음수: 마감 불가 (원자재 X -5개)"
    """
    if invariant.code != INVARIANT_CODE_NEGATIVE_CLOSING:
        return NEGATIVE_CLOSING_INVENTORY_KO

    # Top offender by severity ASC (qty ASC — same as Story 3.3
    # top_n_severity sort). Top 1 = worst.
    if not invariant.negative_products:
        return NEGATIVE_CLOSING_INVENTORY_KO
    sorted_negatives = sorted(invariant.negative_products.items(), key=lambda x: x[1])
    top_pid, top_qty = sorted_negatives[0]
    label = (product_name_lookup or {}).get(top_pid) or _format_uuid_label(top_pid)
    return f"{NEGATIVE_CLOSING_INVENTORY_KO}: {label} {top_qty}개 → 마감 불가"


# ── Internal helpers ─────────────────────────────────────────
def _sort_dict_by_qty(
    items: dict[uuid.UUID, Decimal],
) -> dict[uuid.UUID, Decimal]:
    """Sort dict by Decimal value ASC (severity sort, deterministic)."""
    return dict(sorted(items.items(), key=lambda x: x[1]))


def _format_uuid_label(pid: uuid.UUID) -> str:
    """Format product UUID as short label for banner display."""
    return f"product-{str(pid)[:8]}"


__all__ = [
    "INVARIANT_CODE_CLOSING_OK",
    "INVARIANT_CODE_EMPTY_PERIOD",
    "INVARIANT_CODE_NEGATIVE_CLOSING",
    "INVARIANT_CODES",
    "NEGATIVE_CLOSING_INVENTORY_KO",
    "ClosingGuardError",
    "ClosingInvariant",
    "classify_closing_invariant",
    "compute_closing_balance_per_product",
    "format_negative_closing_banner_ko",
    "is_close_blocked",
]
