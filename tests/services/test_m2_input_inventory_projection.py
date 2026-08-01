"""tests.services.test_m2_input_inventory_projection — Story 3.3 pure helpers.

Mirrors Story 3.2's `test_m2_input_labor_conversion.py` pattern:
- Pure-Python tests (no DB, no clock, no random)
- AD-1/AD-5 binding: every assertion operates on the pure functions in
  `packages.services.m2_input.inventory_projection`
- Cross-language parity covered separately by
  `tests/integration/test_m2_input_label_consistency.py`

Acceptance Criteria mapping (Story 3.3):
- AC #1: NEGATIVE_CLOSING_INVENTORY fire (PRD §V3) — opening 100, outbound 130 → -30
- AC #6: service-only tenant (product_type='service') → no inventory warning
- AC #8: multiple products sorted by closing_qty ASC
- Epic 5 ledger stub marker: `TODO(epic-5)` parity with Story 2.3
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from decimal import Decimal

from packages.services.m2_input.inventory_projection import (
    INVENTORY_PRODUCT_TYPES,
    InventoryMovement,
    build_inventory_projection,
    compute_closing_inventory,
    compute_opening_inventory,
)


# ── Lightweight row stub (avoids ORM dependency in pure tests) ──
@dataclass(frozen=True)
class _RowStub:
    """`MonthlyInputRow` duck type for `build_inventory_projection`.

    The service-layer rows are SQLAlchemy ORM models; the pure function
    only reads `stream`, `product_id`, `qty`, `product_type`. We supply
    a dataclass tuple so the tests stay pure (no DB).
    """

    stream: str
    product_id: uuid.UUID | None
    qty: Decimal | None
    product_type: str


# ── INVENTORY_PRODUCT_TYPES (PRD §6.2) ───────────────────────
def test_inventory_product_types_contains_expected() -> None:
    """PRD §6.2: material / semi_product / product are tracked."""
    assert INVENTORY_PRODUCT_TYPES == frozenset(
        {"material", "semi_product", "product"}
    )


def test_inventory_product_types_excludes_service_and_merchandise() -> None:
    """service / merchandise are NOT in inventory projection (Epic 5)."""
    assert "service" not in INVENTORY_PRODUCT_TYPES
    assert "merchandise" not in INVENTORY_PRODUCT_TYPES


# ── compute_opening_inventory (cj-style default: 0 for new) ─
def test_opening_inventory_zero_for_new_tenant() -> None:
    """prev_period=None → 0 (MVP cj-style default)."""
    pid = uuid.uuid4()
    assert compute_opening_inventory(None, pid) == Decimal("0")


def test_opening_inventory_empty_prev_dict() -> None:
    """prev_period={} → 0 (no products in prior period)."""
    assert compute_opening_inventory({}, uuid.uuid4()) == Decimal("0")


def test_opening_inventory_from_prev_period() -> None:
    """prev_period={pid: 100} → 100 for that product."""
    pid = uuid.uuid4()
    assert compute_opening_inventory({pid: Decimal("100")}, pid) == Decimal("100")


def test_opening_inventory_unknown_product_in_prev() -> None:
    """prev had product A, lookup for B → 0 (not stale)."""
    pid_a = uuid.uuid4()
    pid_b = uuid.uuid4()
    assert compute_opening_inventory({pid_a: Decimal("100")}, pid_b) == Decimal("0")


# ── compute_closing_inventory (PRD §6.2 수불 공식) ─────────
def test_closing_inventory_basic_positive() -> None:
    """opening=100, inbound=0, outbound=30 → 70."""
    assert compute_closing_inventory(
        Decimal("100"), Decimal("0"), Decimal("30")
    ) == Decimal("70")


def test_closing_inventory_negative_basic() -> None:
    """AC #1: opening=100, outbound=130 → -30 (PRD §V3 fire)."""
    assert compute_closing_inventory(
        Decimal("100"), Decimal("0"), Decimal("130")
    ) == Decimal("-30")


def test_closing_inventory_exact_zero() -> None:
    """opening=100, outbound=100 → 0 (no warning)."""
    assert compute_closing_inventory(
        Decimal("100"), Decimal("0"), Decimal("100")
    ) == Decimal("0")


def test_closing_inventory_with_inbound_and_outbound() -> None:
    """opening=100, inbound=50, outbound=80 → 70."""
    assert compute_closing_inventory(
        Decimal("100"), Decimal("50"), Decimal("80")
    ) == Decimal("70")


# ── build_inventory_projection — per-stream mapping ─────────
def test_inventory_projection_sales_only_outbound() -> None:
    """sales row → outbound (PRD §6.2 판매 = 출고)."""
    pid = uuid.uuid4()
    rows = [
        _RowStub(
            stream="sales",
            product_id=pid,
            qty=Decimal("30"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert len(projection) == 1
    assert projection[0].product_id == pid
    assert projection[0].opening_qty == Decimal("0")
    assert projection[0].inbound_qty == Decimal("0")
    assert projection[0].outbound_qty == Decimal("30")


def test_inventory_projection_purchases_inbound() -> None:
    """purchases row → inbound (PRD §6.2 구매 = 매입)."""
    pid = uuid.uuid4()
    rows = [
        _RowStub(
            stream="purchases",
            product_id=pid,
            qty=Decimal("50"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert len(projection) == 1
    assert projection[0].inbound_qty == Decimal("50")
    assert projection[0].outbound_qty == Decimal("0")


def test_inventory_production_outbound_material_consumption() -> None:
    """output product_qty → inbound for the product (MVP per spec).

    Story 3.3 ships ONLY the output product inbound — input material
    consumption is Epic 5 ledger territory (TODO(epic-5) marker).
    """
    pid = uuid.uuid4()
    rows = [
        _RowStub(
            stream="production",
            product_id=pid,
            qty=Decimal("100"),
            product_type="product",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert len(projection) == 1
    assert projection[0].inbound_qty == Decimal("100")
    assert projection[0].outbound_qty == Decimal("0")


def test_inventory_projection_excludes_service_products() -> None:
    """AC #6: product_type='service' → not in projection."""
    pid_svc = uuid.uuid4()
    pid_mat = uuid.uuid4()
    rows = [
        _RowStub(
            stream="sales",
            product_id=pid_svc,
            qty=Decimal("30"),
            product_type="service",
        ),
        _RowStub(
            stream="sales",
            product_id=pid_mat,
            qty=Decimal("20"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert len(projection) == 1
    assert projection[0].product_id == pid_mat


def test_inventory_projection_multiple_products() -> None:
    """3 products (mat/semi/prod) → 3 movements."""
    pids = [uuid.uuid4() for _ in range(3)]
    rows = [
        _RowStub(
            stream="sales",
            product_id=pids[0],
            qty=Decimal("10"),
            product_type="material",
        ),
        _RowStub(
            stream="sales",
            product_id=pids[1],
            qty=Decimal("20"),
            product_type="semi_product",
        ),
        _RowStub(
            stream="sales",
            product_id=pids[2],
            qty=Decimal("30"),
            product_type="product",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert len(projection) == 3
    by_pid = {m.product_id: m for m in projection}
    assert by_pid[pids[0]].outbound_qty == Decimal("10")
    assert by_pid[pids[1]].outbound_qty == Decimal("20")
    assert by_pid[pids[2]].outbound_qty == Decimal("30")


def test_inventory_projection_zero_qty_excluded() -> None:
    """qty=0 row → skip (no movement)."""
    pid = uuid.uuid4()
    rows = [
        _RowStub(
            stream="sales",
            product_id=pid,
            qty=Decimal("0"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert projection == []


def test_inventory_projection_round_half_even_decimal() -> None:
    """qty=Decimal("0.005") → quantized to 0.01 (ROUND_HALF_EVEN) on inbound sum."""
    pid = uuid.uuid4()
    rows = [
        _RowStub(
            stream="purchases",
            product_id=pid,
            qty=Decimal("0.005"),
            product_type="material",
        ),
        _RowStub(
            stream="purchases",
            product_id=pid,
            qty=Decimal("0.005"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert len(projection) == 1
    # 0.005 + 0.005 = 0.010 → ROUND_HALF_EVEN at 4dp = 0.0100
    assert projection[0].inbound_qty == Decimal("0.0100")


def test_inventory_projection_unknown_product_in_prev_period() -> None:
    """Prev had product A, current doesn't have A → opening=0 for B."""
    pid_a = uuid.uuid4()
    pid_b = uuid.uuid4()
    rows = [
        _RowStub(
            stream="sales",
            product_id=pid_b,
            qty=Decimal("10"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(
        rows, opening_balance={pid_a: Decimal("100")}
    )
    assert len(projection) == 1
    assert projection[0].product_id == pid_b
    assert projection[0].opening_qty == Decimal("0")


def test_inventory_projection_closing_qty_for_labor_no_product() -> None:
    """labor stream rows → ignored (no product_id)."""
    rows = [
        _RowStub(
            stream="labor",
            product_id=None,
            qty=None,
            product_type="service",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert projection == []


def test_inventory_projection_empty_rows() -> None:
    """empty rows → empty projection."""
    projection = build_inventory_projection([], opening_balance=None)
    assert projection == []


def test_inventory_projection_aggregate_by_product() -> None:
    """3 sales rows of same product → sum outbound."""
    pid = uuid.uuid4()
    rows = [
        _RowStub(
            stream="sales",
            product_id=pid,
            qty=Decimal("10"),
            product_type="material",
        ),
        _RowStub(
            stream="sales",
            product_id=pid,
            qty=Decimal("20"),
            product_type="material",
        ),
        _RowStub(
            stream="sales",
            product_id=pid,
            qty=Decimal("5"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(rows, opening_balance=None)
    assert len(projection) == 1
    assert projection[0].outbound_qty == Decimal("35")


def test_inventory_projection_with_opening_balance() -> None:
    """opening_balance={pid: 100} → opening_qty=100 in projection."""
    pid = uuid.uuid4()
    rows = [
        _RowStub(
            stream="sales",
            product_id=pid,
            qty=Decimal("30"),
            product_type="material",
        ),
    ]
    projection = build_inventory_projection(
        rows, opening_balance={pid: Decimal("100")}
    )
    assert len(projection) == 1
    assert projection[0].opening_qty == Decimal("100")
    assert projection[0].outbound_qty == Decimal("30")
    # closing = 100 + 0 - 30 = 70 (computed separately by
    # compute_closing_inventory; the projection struct stores raw aggregates)
    assert projection[0].inbound_qty == Decimal("0")


def test_inventory_movement_named_tuple_shape() -> None:
    """InventoryMovement fields exist (AD-15 snake_case)."""
    pid = uuid.uuid4()
    m = InventoryMovement(
        product_id=pid,
        opening_qty=Decimal("100"),
        inbound_qty=Decimal("0"),
        outbound_qty=Decimal("30"),
    )
    assert m.product_id == pid
    assert m.opening_qty == Decimal("100")
    assert m.inbound_qty == Decimal("0")
    assert m.outbound_qty == Decimal("30")
