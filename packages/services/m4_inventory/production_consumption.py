"""packages.services.m4_inventory.production_consumption — Story 5.3 W1 pure kernel.

BOM-aware reconciliation of production stream ledger events.

Pure-Python, stdlib-only helpers consumed by:
- `apps/api/modules/m4_inventory/services/closing_guard_service.py`
  (T4 service layer — emit_production_ledger_events dispatch)

AD-1 / AD-5 / AD-11 binding: pure-Python, stdlib-only, no DB, no clock,
no random. Drift between Python and TS caught by
`tests/integration/test_production_consumption_label_consistency.py` (NEW 5-3).

Story 5.2 deferral #9 resolved in 5-3:
- 5-2 commit shipped single-emit (production_output_inbound only).
- 5-3 wires BOM-aware emit:
  - production_output_inbound (output product qty, 양수)
  - production_material_consumption events (per child material, 음수)

BOM matrix SSOT:
- `apps/api/modules/m1_baseline/services/bom_service.py` (Story 2.2)
- 100% invariant (SUM(ratio)=100) — pure kernel trusts BOM data.
- consumption qty = production_row.product_qty * child.ratio / Decimal(100)

Fallback when BOM is missing or incomplete:
- Single production_output_inbound event + single adjustment_positive
  event for material consumption (BOM not yet defined → operator TODO).
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Final, TypedDict

from packages.services.m2_input.inventory_projection import QTY_QUANTUM

# ── Constants ────────────────────────────────────────────────
# Korean message SSOT (AD-15 §11 parity).
INCOMPLETE_BOM_FALLBACK_REASON_KO: Final[str] = (
    "BOM 미정의 또는 부분 정의 — material consumption 기록 보류"
)

# Event_type discriminators (5-2 wire — 11-value whitelist).
EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND: Final[str] = "production_output_inbound"
EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION: Final[str] = "production_material_consumption"
EVENT_TYPE_ADJUSTMENT_POSITIVE: Final[str] = "adjustment_positive"

# Ratio is a percentage (PRD §6.2 — BOM ratio as % of output).
RATIO_PERCENT_DENOMINATOR: Final[Decimal] = Decimal("100")


# ── TypedDict shapes ─────────────────────────────────────────
class ProductionRowLike(TypedDict):
    """Duck-type for monthly_input_rows stream='production' row.

    Pure-kernel interface — service layer maps SQLAlchemy ORM row to
    this TypedDict before dispatch.
    """

    product_id: str  # UUID string for JSON-friendliness
    product_qty: str  # Decimal string (PRD §6.2 NUMERIC(18,4))
    period_key: str
    trace_id: str  # UUID string


class BomChild(TypedDict):
    """Per-child BOM line item.

    Story 2.2 BOM matrix schema:
    - parent_product_id + child_product_id + ratio (NUMERIC(7,4) %).
    """

    child_product_id: str  # UUID string
    ratio: str  # Decimal string — percentage (e.g. "33.3333" = 33.3333%)


class BomMatrixLike(TypedDict):
    """Duck-type for BOM matrix (Story 2.2 schema).

    `children` list carries per-child ratio. Empty children → BOM
    incomplete → fallback path.
    """

    parent_product_id: str  # UUID string
    children: list[BomChild]


class ComputedLedgerEvent(TypedDict):
    """Computed ledger event shape (ready for `LedgerService.append_event`).

    Mirrors `InventoryLedgerEvent` (5-2 schema) but as TypedDict (the
    service layer instantiates the NamedTuple after dispatch).
    """

    event_type: str
    product_id: str
    qty: str  # Decimal string — banker's rounding applied
    metadata: dict[str, Any]


# ── ProductionConsumptionError ────────────────────────────────
class ProductionConsumptionError(Exception):
    """Pure-kernel BOM reconciliation error.

    Distinct from service-layer typed exceptions. Raised when
    internal invariants fail (e.g. malformed Decimal, BOM ratio
    out of range, production qty non-positive).
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "PRODUCTION_CONSUMPTION_ERROR",
        product_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.product_id = product_id


# ── compute_production_consumption_events ────────────────────
def compute_production_consumption_events(
    *,
    production_row: ProductionRowLike,
    bom: BomMatrixLike | None,
) -> list[ComputedLedgerEvent]:
    """BOM-aware reconciliation of production row → ledger events.

    Story 5.2 deferral #9 wire (5-3 spec 본문 T3). Each production
    row INSERT in `monthly_input_service.save_row` (stream='production')
    produces:
    - Exactly 1 `production_output_inbound` event (output product qty).
    - If BOM is defined + complete:
      - N `production_material_consumption` events (one per child).
    - If BOM is None OR children empty:
      - 1 `adjustment_positive` event for material consumption
        (incomplete BOM 기록 — operator TODO marker).

    Args:
        production_row: Duck-typed production row (product_id UUID
            string + product_qty Decimal string + period_key + trace_id).
        bom: Duck-typed BOM matrix (parent_product_id UUID string +
            children list with ratio). None → fallback path.

    Returns:
        List of ComputedLedgerEvent TypedDicts (1 output + N consumption
        OR 1 output + 1 adjustment_positive). Sorted deterministically
        by event_type + product_id (CR 4-3 lesson).

    Raises:
        ProductionConsumptionError: On malformed input (non-positive
            qty, BOM ratio out of [0, 100], non-finite Decimal).
    """
    # Validate production row
    product_id = _parse_uuid(production_row["product_id"], field="product_id")
    product_qty = _parse_qty(production_row["product_qty"], field="product_qty", min_zero=True)
    if product_qty <= Decimal("0"):
        raise ProductionConsumptionError(
            message=(f"production row product_qty must be > 0, got {product_qty}"),
            error_code="NON_POSITIVE_PRODUCT_QTY",
            product_id=product_id,
        )

    output_event = ComputedLedgerEvent(
        event_type=EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND,
        product_id=str(product_id),
        qty=_format_qty(product_qty),
        metadata={
            "period_key": production_row["period_key"],
            "trace_id": production_row["trace_id"],
        },
    )

    bom_events = _compute_bom_events(
        production_row=production_row,
        bom=bom,
        output_product_id=product_id,
        output_qty=product_qty,
    )

    # Deterministic sort: output first, then by event_type + product_id
    events = [output_event] + bom_events
    events.sort(
        key=lambda e: (
            0 if e["event_type"] == EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND else 1,
            e["event_type"],
            e["product_id"],
        )
    )
    return events


# ── Internal helpers ─────────────────────────────────────────
def _compute_bom_events(
    *,
    production_row: ProductionRowLike,
    bom: BomMatrixLike | None,
    output_product_id: uuid.UUID,
    output_qty: Decimal,
) -> list[ComputedLedgerEvent]:
    """Compute material consumption events (or fallback adjustment)."""
    if bom is None or not bom.get("children"):
        return [
            ComputedLedgerEvent(
                event_type=EVENT_TYPE_ADJUSTMENT_POSITIVE,
                product_id=str(output_product_id),
                qty=_format_qty(output_qty),
                metadata={
                    "period_key": production_row["period_key"],
                    "trace_id": production_row["trace_id"],
                    "fallback_reason_ko": INCOMPLETE_BOM_FALLBACK_REASON_KO,
                    "bom_status": "missing_or_empty",
                },
            )
        ]

    events: list[ComputedLedgerEvent] = []
    for child in bom["children"]:
        child_pid = _parse_uuid(child["child_product_id"], field="child_product_id")
        ratio = _parse_qty(child["ratio"], field="ratio", min_zero=True)
        if ratio < Decimal("0") or ratio > RATIO_PERCENT_DENOMINATOR:
            raise ProductionConsumptionError(
                message=(f"BOM child ratio {ratio} out of range [0, 100]"),
                error_code="BOM_RATIO_OUT_OF_RANGE",
                product_id=output_product_id,
            )

        # consumption qty = output_qty * ratio / 100
        # NEGATIVE for material consumption (outbound for material).
        consumption_qty = -(output_qty * ratio / RATIO_PERCENT_DENOMINATOR)
        consumption_qty = consumption_qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)

        events.append(
            ComputedLedgerEvent(
                event_type=EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION,
                product_id=str(child_pid),
                qty=_format_qty(consumption_qty),
                metadata={
                    "period_key": production_row["period_key"],
                    "trace_id": production_row["trace_id"],
                    "parent_product_id": str(output_product_id),
                    "ratio": _format_qty(ratio),
                },
            )
        )
    return events


def _parse_uuid(value: str, *, field: str) -> uuid.UUID:
    """Parse UUID string with error wrapping."""
    try:
        return uuid.UUID(value)
    except (ValueError, TypeError) as err:
        raise ProductionConsumptionError(
            message=f"{field} must be UUID string, got {value!r}",
            error_code="INVALID_UUID",
        ) from err


def _parse_qty(value: str, *, field: str, min_zero: bool) -> Decimal:
    """Parse Decimal string with error wrapping."""
    try:
        qty = Decimal(value)
    except (ValueError, TypeError, ArithmeticError) as err:
        raise ProductionConsumptionError(
            message=f"{field} must be Decimal string, got {value!r}",
            error_code="INVALID_QTY",
        ) from err
    if not qty.is_finite():
        raise ProductionConsumptionError(
            message=f"{field} must be finite Decimal, got {value!r}",
            error_code="NON_FINITE_QTY",
        )
    if min_zero and qty < Decimal("0"):
        raise ProductionConsumptionError(
            message=f"{field} must be >= 0, got {value!r}",
            error_code="NEGATIVE_QTY",
        )
    return qty


def _format_qty(qty: Decimal) -> str:
    """Format Decimal to AD-8 banker's rounding string."""
    quantized = qty.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)
    return f"{quantized:f}"


__all__ = [
    "EVENT_TYPE_ADJUSTMENT_POSITIVE",
    "EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION",
    "EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND",
    "INCOMPLETE_BOM_FALLBACK_REASON_KO",
    "RATIO_PERCENT_DENOMINATOR",
    "BomChild",
    "BomMatrixLike",
    "ComputedLedgerEvent",
    "ProductionConsumptionError",
    "ProductionRowLike",
    "compute_production_consumption_events",
]
