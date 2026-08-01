"""packages.services.m2_input.inventory_projection — Story 3.3 inventory projection.

Pure-Python, stdlib-only module. NO DB, NO clock, NO random. AD-1 / AD-5
binding: this is the canonical inventory-projection kernel consumed by
`apps/api/modules/m2_input/services/monthly_input_service.py` AND
mirrored by `apps/web/lib/l2-input-warnings.ts` (drift caught by
`tests/integration/test_m2_input_label_consistency.py`).

The module answers:
- "Given a previous period's closing balances, what is the opening
  balance for a product in the current period?" → `compute_opening_inventory`
- "What is the closing balance given opening + inbound + outbound?"
  → `compute_closing_inventory` (PRD §6.2 수불 공식)
- "Given a list of mixed-stream monthly input rows, what is the per-product
  inventory projection?" → `build_inventory_projection`
  - `sales` rows → outbound (PRD §6.2 판매 = 출고)
  - `purchases` rows → inbound (PRD §6.2 구매 = 매입)
  - `production` rows → inbound (output product_qty only — input material
    consumption is Epic 5 ledger territory; see `TODO(epic-5)` marker)

PRD §6.2 수불부: 기초 + 구입 − 생산출고 = 기말
- opening = monthly_input_periods.opening_inventory JSONB (MVP default 0)
- inbound = purchases + production output
- outbound = sales (production input material consumption = Epic 5)

MVP limitation (deferred to Epic 5):
- Material consumption when production occurs: not tracked in 3.3
- Cumulative across periods: prev_period_closing → current_period_opening
  is auto-carried by Epic 5 Story 5-1 (TODO(epic-5) marker below)

AD-8 monetary parity: qty is `Decimal` (NUMERIC(18,4)). Not a monetary
amount, but inherits the same drift-prevention discipline.

AD-15 cross-language parity: snake_case Python ↔ camelCase TS.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Final, NamedTuple, Protocol


# ── Constants ────────────────────────────────────────────────
# PRD §6.2 inventory-tracked product types.
# - `material`     — 원재료 (raw material)
# - `semi_product` — 반제품 (work-in-progress)
# - `product`      — 완제품 (finished goods)
# Excluded: `service` (consulting, no stock), `merchandise` (Epic 5 separate)
INVENTORY_PRODUCT_TYPES: Final[frozenset[str]] = frozenset(
    {"material", "semi_product", "product"}
)

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


# ── ERP / Inventory source marker (Epic 5 stub) ─────────────
# TODO(epic-5): When Epic 5 Story 5-1 (opening auto-carry) + 5-2
# (append-only ledger) ships, this module will read from
# `inventory_ledger` instead of `monthly_input_rows`. The inline
# projection is the MVP source-of-truth. Mirrors Story 2.3's
# `LEDGER_REFERENCE_QUERY_STUB` pattern.
LEDGER_REFERENCE_QUERY_STUB: Final[str] = ""


# ── Row protocol (avoids SQLAlchemy dependency in pure tests) ─
class _RowLike(Protocol):
    """Duck type for `MonthlyInputRow` (pure interface, no DB import).

    The pure kernel only reads `stream`, `product_id`, `qty`,
    `product_type`. SQLAlchemy ORM rows satisfy this protocol
    structurally (Story 3.1 + 3.2 schema).
    """

    stream: str
    product_id: uuid.UUID | None
    qty: Decimal | None
    product_type: str


# ── compute_opening_inventory ────────────────────────────────
def compute_opening_inventory(
    prev_period_projection: dict[uuid.UUID, Decimal] | None,
    product_id: uuid.UUID,
) -> Decimal:
    """Return the opening inventory for `product_id` in the current period.

    Cj-style default: if the previous period has no record for this
    product, opening is 0. (MVP — Epic 5 Story 5-1 will auto-carry
    closing balances from the previous period.)

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


# ── build_inventory_projection ───────────────────────────────
def build_inventory_projection(
    rows: list[_RowLike],
    opening_balance: dict[uuid.UUID, Decimal] | None,
) -> list[InventoryMovement]:
    """Build per-product inventory movement list for a period.

    Stream mapping (PRD §6.2):
    - `sales` → outbound (qty)
    - `purchases` → inbound (qty)
    - `production` → inbound (output product_qty; input material
      consumption is Epic 5 ledger territory)
    - `orders`, `expenses`, `labor` → ignored (no inventory impact)

    Filter: only rows whose `product_type` is in
    `INVENTORY_PRODUCT_TYPES` are tracked. `service` / `merchandise`
    products are excluded.

    Args:
        rows: monthly input rows (any object with .stream, .product_id,
            .qty, .product_type attributes).
        opening_balance: Optional dict mapping product_id → opening
            qty (from `monthly_input_periods.opening_inventory JSONB`,
            or service layer fallback to 0).

    Returns:
        List of `InventoryMovement` (one per product). Products with
        all-zero qty contributions are omitted.

    TODO(epic-5): replace with `inventory_ledger` read when Epic 5
    5-1+5-2 ships. The columns/products set remains the same.
    """
    # product_id → running aggregate
    bucket: dict[uuid.UUID, dict[str, Decimal]] = {}

    for row in rows:
        if row.product_id is None or row.qty is None:
            continue  # labor / expenses / no-FK rows
        if row.product_type not in INVENTORY_PRODUCT_TYPES:
            continue  # service / merchandise / unknown
        pid = row.product_id
        qty = row.qty
        if qty == 0:
            continue

        slot = bucket.setdefault(
            pid,
            {"inbound": Decimal("0"), "outbound": Decimal("0")},
        )

        if row.stream == "sales":
            slot["outbound"] += qty
        elif row.stream == "purchases":
            slot["inbound"] += qty
        elif row.stream == "production":
            # Output product_qty → inbound (MVP).
            # Input material consumption → Epic 5 ledger (TODO(epic-5)).
            slot["inbound"] += qty
        # orders / expenses / labor → skip

    # Compose InventoryMovement list (sorted by product_id for deterministic
    # output — supports AC #8 sort + cross-language parity tests).
    out: list[InventoryMovement] = []
    for pid in sorted(bucket.keys(), key=str):
        slot = bucket[pid]
        opening = (
            (opening_balance or {}).get(pid, Decimal("0"))
        )
        out.append(
            InventoryMovement(
                product_id=pid,
                opening_qty=opening.quantize(
                    QTY_QUANTUM, rounding=ROUND_HALF_EVEN
                ),
                inbound_qty=slot["inbound"].quantize(
                    QTY_QUANTUM, rounding=ROUND_HALF_EVEN
                ),
                outbound_qty=slot["outbound"].quantize(
                    QTY_QUANTUM, rounding=ROUND_HALF_EVEN
                ),
            )
        )
    return out
