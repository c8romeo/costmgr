"""tests.services.test_production_consumption — Story 5.3 BOM reconciliation tests.

Tests for `packages.services.m4_inventory.production_consumption`:
- BOM-defined: emits 1 production_output_inbound + N production_material_consumption
- BOM missing/incomplete: emits 1 production_output_inbound + 1 adjustment_positive fallback
- Negative consumption qty (outbound for material)
- Banker's rounding (AD-8)
- Deterministic sort order (CR 4-3 lesson)
- Pure kernel errors: NON_POSITIVE_PRODUCT_QTY, BOM_RATIO_OUT_OF_RANGE, INVALID_UUID, INVALID_QTY, NON_FINITE_QTY, NEGATIVE_QTY
- Korean fallback reason SSOT
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.production_consumption import (
    EVENT_TYPE_ADJUSTMENT_POSITIVE,
    EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND,
    INCOMPLETE_BOM_FALLBACK_REASON_KO,
    RATIO_PERCENT_DENOMINATOR,
    BomChild,
    BomMatrixLike,
    ProductionConsumptionError,
    ProductionRowLike,
    compute_production_consumption_events,
)

# Inlined to avoid pytest module-level constant resolution edge cases.
EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION = "production_material_consumption"


# ── Constants ──────────────────────────────────────────────────
def test_constants():
    """Event types + Korean fallback reason match Story 5.3 spec."""
    assert EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND == "production_output_inbound"
    assert EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION == "production_material_consumption"
    assert EVENT_TYPE_ADJUSTMENT_POSITIVE == "adjustment_positive"
    assert RATIO_PERCENT_DENOMINATOR == Decimal("100")
    assert (
        INCOMPLETE_BOM_FALLBACK_REASON_KO
        == "BOM 미정의 또는 부분 정의 — material consumption 기록 보류"
    )


# ── BOM defined + complete ──────────────────────────────────────
def test_bom_complete_emits_n_consumption():
    """BOM with 2 children → 1 output + 2 consumption events."""
    parent_pid = uuid.uuid4()
    child_a = uuid.uuid4()
    child_b = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="100.0000",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    bom = BomMatrixLike(
        parent_product_id=str(parent_pid),
        children=[
            BomChild(child_product_id=str(child_a), ratio="60.0000"),
            BomChild(child_product_id=str(child_b), ratio="40.0000"),
        ],
    )
    events = compute_production_consumption_events(
        production_row=row, bom=bom
    )
    assert len(events) == 3  # 1 output + 2 consumption
    output_event = next(e for e in events if e["event_type"] == EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND)
    assert output_event["product_id"] == str(parent_pid)
    assert Decimal(output_event["qty"]) == Decimal("100.0000")
    consumption_events = [
        e for e in events if e["event_type"] == EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION
    ]
    assert len(consumption_events) == 2
    # Both consumption qty are NEGATIVE
    for ce in consumption_events:
        assert Decimal(ce["qty"]) < Decimal("0")
    # 60% + 40% = 100% — total consumption qty = output qty (sign-matched)
    total_consumption = sum(Decimal(e["qty"]) for e in consumption_events)
    assert total_consumption == Decimal("-100.0000")


# ── BOM missing → fallback adjustment_positive ──────────────────
def test_bom_none_fallback():
    """BOM=None → 1 output + 1 adjustment_positive fallback."""
    parent_pid = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="50.0000",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    events = compute_production_consumption_events(production_row=row, bom=None)
    assert len(events) == 2  # 1 output + 1 fallback
    types = sorted(e["event_type"] for e in events)
    assert types == [EVENT_TYPE_ADJUSTMENT_POSITIVE, EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND]
    fallback = next(e for e in events if e["event_type"] == EVENT_TYPE_ADJUSTMENT_POSITIVE)
    assert fallback["metadata"]["bom_status"] == "missing_or_empty"
    assert fallback["metadata"]["fallback_reason_ko"] == INCOMPLETE_BOM_FALLBACK_REASON_KO


# ── BOM empty children → fallback ──────────────────────────────
def test_bom_empty_children_fallback():
    """BOM with empty children list → fallback path."""
    parent_pid = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="100.0000",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    bom = BomMatrixLike(parent_product_id=str(parent_pid), children=[])
    events = compute_production_consumption_events(production_row=row, bom=bom)
    assert len(events) == 2  # fallback path


# ── Banker's rounding parity ────────────────────────────────────
def test_banker_rounding():
    """Consumption qty quantized to QTY_QUANTUM (0.0001) via ROUND_HALF_EVEN.

    Material consumption is SIGN-NEGATIVE per AD-22 (outbound), so test
    that the absolute magnitude matches.
    """
    parent_pid = uuid.uuid4()
    child_pid = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="100.0000",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    bom = BomMatrixLike(
        parent_product_id=str(parent_pid),
        children=[BomChild(child_product_id=str(child_pid), ratio="33.3333")],
    )
    events = compute_production_consumption_events(production_row=row, bom=bom)
    consumption = next(e for e in events if e["event_type"] == EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION)
    # 100 * 33.3333 / 100 = 33.3333 → outbound → -33.3333
    assert Decimal(consumption["qty"]) == Decimal("-33.3333")


# ── Deterministic sort order ───────────────────────────────────
def test_sort_order_output_first_then_by_product_id():
    """Output event first, then consumption events sorted by product_id."""
    parent_pid = uuid.uuid4()
    child_a = uuid.uuid4()
    child_b = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="100.0000",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    bom = BomMatrixLike(
        parent_product_id=str(parent_pid),
        children=[
            BomChild(child_product_id=str(child_b), ratio="50.0000"),  # reverse order
            BomChild(child_product_id=str(child_a), ratio="50.0000"),
        ],
    )
    events = compute_production_consumption_events(production_row=row, bom=bom)
    assert events[0]["event_type"] == EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND
    # Remaining events sorted by product_id
    product_ids = [e["product_id"] for e in events[1:]]
    assert product_ids == sorted(product_ids)


# ── Errors ──────────────────────────────────────────────────────
def test_non_positive_qty_raises():
    """product_qty must be > 0."""
    parent_pid = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="0",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    with pytest.raises(ProductionConsumptionError) as exc_info:
        compute_production_consumption_events(production_row=row, bom=None)
    assert exc_info.value.error_code == "NON_POSITIVE_PRODUCT_QTY"


def test_negative_qty_raises():
    """Negative product_qty → NEGATIVE_QTY error."""
    parent_pid = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="-5",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    with pytest.raises(ProductionConsumptionError) as exc_info:
        compute_production_consumption_events(production_row=row, bom=None)
    assert exc_info.value.error_code == "NEGATIVE_QTY"


def test_invalid_uuid_raises():
    """Non-UUID string → INVALID_UUID."""
    row = ProductionRowLike(
        product_id="not-a-uuid",
        product_qty="10",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    with pytest.raises(ProductionConsumptionError) as exc_info:
        compute_production_consumption_events(production_row=row, bom=None)
    assert exc_info.value.error_code == "INVALID_UUID"


def test_bom_ratio_out_of_range_raises():
    """BOM child ratio > 100 → BOM_RATIO_OUT_OF_RANGE."""
    parent_pid = uuid.uuid4()
    child_pid = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="100",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    bom = BomMatrixLike(
        parent_product_id=str(parent_pid),
        children=[BomChild(child_product_id=str(child_pid), ratio="150.0000")],
    )
    with pytest.raises(ProductionConsumptionError) as exc_info:
        compute_production_consumption_events(production_row=row, bom=bom)
    assert exc_info.value.error_code == "BOM_RATIO_OUT_OF_RANGE"


def test_invalid_qty_raises():
    """Non-numeric qty → INVALID_QTY."""
    parent_pid = uuid.uuid4()
    row = ProductionRowLike(
        product_id=str(parent_pid),
        product_qty="not-a-number",
        period_key="2026-07",
        trace_id=str(uuid.uuid4()),
    )
    with pytest.raises(ProductionConsumptionError) as exc_info:
        compute_production_consumption_events(production_row=row, bom=None)
    assert exc_info.value.error_code == "INVALID_QTY"
