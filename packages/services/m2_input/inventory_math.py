"""packages.services.m2_input.inventory_math — inventory math primitives.

Pure-Python, stdlib-only module. NO DB, NO clock, NO random. AD-1 / AD-5
binding: this is the canonical inventory-math kernel consumed by
`apps/api/modules/m2_input/services/monthly_input_service.py`,
`apps/api/modules/m4_inventory/services/opening_carry_service.py`, and
the carry chain in `packages/services/m2_input/opening_carry.py`.

History (A19 carry-over sprint, 2026-08-15):
- This module is the post-deprecation home of the math surface that
  used to live in `packages/services/m2_input/inventory_projection.py`.
- `build_inventory_projection` (Epic 3.3 inline aggregation) and the
  `LEDGER_REFERENCE_QUERY_STUB` deprecation marker were REMOVED here
  per Epic 6 close-out retro §7 A19 — the ledger (Epic 5 5-2
  `inventory_ledger` table + `LedgerService.query_period_closing_all`)
  is the SSOT for inventory projection.
- Carry-chain call sites in `opening_carry_service.py` continue to use
  `compute_closing_inventory` + `QTY_QUANTUM` for the deterministic
  banker's-rounding math; this kernel preserves that contract.

The module answers:
- "What inventory product types are tracked?" → `INVENTORY_PRODUCT_TYPES`
- "What is the NUMERIC(18,4) quantum for qty?" → `QTY_QUANTUM`
- "What is the per-product movement aggregate?" → `InventoryMovement`
- "Given a previous period's closing balances, what is the opening
  balance for a product in the current period?" → `compute_opening_inventory`
- "What is the closing balance given opening + inbound + outbound?"
  → `compute_closing_inventory` (PRD §6.2 수불 공식)

PRD §6.2 수불부: 기초 + 구입 − 생산출고 = 기말
- opening = monthly_input_periods.opening_inventory JSONB (auto-carried)
- inbound = purchases + production output
- outbound = sales
- closing = opening + inbound - outbound (QTY_QUANTUM, ROUND_HALF_EVEN)

AD-8 monetary parity: qty is `Decimal` (NUMERIC(18,4)). Not a monetary
amount, but inherits the same drift-prevention discipline.

AD-15 cross-language parity: snake_case Python ↔ camelCase TS.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# PRD §6.2 inventory-tracked product types.
# - `material`     — 원재료 (raw material)
# - `semi_product` — 반제품 (work-in-progress)
# - `product`      — 완제품 (finished goods)
# Excluded: `service` (consulting, no stock), `merchandise` (Epic 5 separate)
INVENTORY_PRODUCT_TYPES: Final[frozenset[str]] = frozenset({"material", "semi_product", "product"})

# Decimal quantization for qty — NUMERIC(18,4) per PRD §6.1.
QTY_QUANTUM: Final[Decimal] = Decimal("0.0001")


# ── InventoryMovement ────────────────────────────────────────
class InventoryMovement(NamedTuple):
    """Per-product inventory aggregate for a single period.

    Aggregated across all rows of the period (sales + purchases +
    production output) for a single product. The closing_qty is NOT
    stored here — it's computed on demand by `compute_closing_inventory`
    so the kernel stays consistent with PRD §6.2's 수불 공식.

    AD-15: snake_case field names.
    """

    product_id: uuid.UUID
    opening_qty: Decimal
    inbound_qty: Decimal
    outbound_qty: Decimal


# ── compute_opening_inventory ────────────────────────────────
def compute_opening_inventory(
    prev_period_projection: dict[uuid.UUID, Decimal] | None,
    product_id: uuid.UUID,
) -> Decimal:
    """Return the opening inventory for `product_id` in the current period.

    Cj-style default: if the previous period has no record for this
    product, opening is 0.

    Args:
        prev_period_projection: dict mapping product_id → closing
            qty from the previous period. None / empty → 0 for all.
        product_id: The product to look up.

    Returns:
        Decimal opening balance (>= 0). Zero if unknown.
    """
    if not prev_period_projection:
        return Decimal("0")
    return prev_period_projection.get(product_id, Decimal("0"))


# ── compute_closing_inventory ────────────────────────────────
def compute_closing_inventory(
    opening: Decimal,
    inbound: Decimal,
    outbound: Decimal,
) -> Decimal:
    """PRD §6.2 수불 공식: closing = opening + inbound − outbound.

    Args:
        opening: 기초재고 (>= 0).
        inbound: 입고 합 (purchases + production output).
        outbound: 출고 합 (sales).

    Returns:
        Decimal 기말재고. May be negative (PRD §V3 fire signal — caller
        MUST surface as NEGATIVE_CLOSING_INVENTORY warning).
    """
    closing = opening + inbound - outbound
    return closing.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
