"""Story 5.2 — pure helpers test suite (T1).

Drives the red-green-refactor cycle for
`packages.services.m4_inventory.ledger`. Pure kernel — no DB, no clock,
no random. Determinism + banker's rounding parity enforced (CR 0-4
lesson). Drift between Python and TS caught by
`tests/integration/test_inventory_ledger_label_consistency.py`.
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

import pytest

from packages.services.m4_inventory.ledger import (
    INVENTORY_LEDGER_EVENT_TYPES,
    INVENTORY_LEDGER_QTY_QUANTUM,
    AppendOnlyLedgerError,
    InventoryLedgerEvent,
    PAYLOAD_KEY_CORRECTION_GROUP_ID,
    PAYLOAD_KEY_EVENT_ID,
    PAYLOAD_KEY_EVENT_TYPE,
    PAYLOAD_KEY_METADATA,
    PAYLOAD_KEY_PERIOD_KEY,
    PAYLOAD_KEY_PRODUCT_ID,
    PAYLOAD_KEY_QTY,
    PAYLOAD_KEY_REVERSES_EVENT_ID,
    PAYLOAD_KEY_SOURCE,
    PAYLOAD_KEY_TRACE_ID,
    SOURCE_CARRY_CHAIN,
    SOURCE_CLOSE_SNAPSHOT,
    SOURCE_MANUAL_BACKFILL,
    SOURCE_MONTHLY_INPUT,
    SOURCE_REVERSAL_REQUEST,
    append_only_violation_message,
    build_event_payload,
    validate_event_shape,
    validate_event_type,
)

# ─────────────────────────────────────────────────────────────
# Test data — UUID v7-style fixtures
# ─────────────────────────────────────────────────────────────

TENANT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000001")
EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-000000000002")
TRACE_ID = uuid.UUID("019200a0-0000-7000-8000-000000000003")
PROD_X = uuid.UUID("019200a0-0000-7000-8000-00000000000a")
REVERSES_EVENT_ID = uuid.UUID("019200a0-0000-7000-8000-0000000000ff")
CORRECTION_GROUP_ID = uuid.UUID("019200a0-0000-7000-8000-0000000000ee")


# ─────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────

def test_event_types_11_values_present() -> None:
    """AC #2 + OQ3 cj-style default: 11 event_type values explicit."""
    expected = {
        "opening_carried",
        "opening_carried_stale_overwrite",
        "purchase_inbound",
        "sales_outbound",
        "production_output_inbound",
        "production_material_consumption",
        "adjustment_positive",
        "adjustment_negative",
        "reversal_negating",
        "reversal_corrected",
        "closing_snapshot",
    }
    assert INVENTORY_LEDGER_EVENT_TYPES == frozenset(expected)
    assert len(INVENTORY_LEDGER_EVENT_TYPES) == 11


def test_qty_quantum_matches_engine() -> None:
    """NUMERIC(18,4) quantization (AD-8 monetary types)."""
    assert INVENTORY_LEDGER_QTY_QUANTUM == Decimal("0.0001")


# ─────────────────────────────────────────────────────────────
# validate_event_type
# ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "event_type",
    [
        "opening_carried",
        "opening_carried_stale_overwrite",
        "purchase_inbound",
        "sales_outbound",
        "production_output_inbound",
        "production_material_consumption",
        "adjustment_positive",
        "adjustment_negative",
        "reversal_negating",
        "reversal_corrected",
        "closing_snapshot",
    ],
)
def test_validate_event_type_all_11_pass(event_type: str) -> None:
    """All 11 canonical event_types validate without raising."""
    validate_event_type(event_type)  # no raise


def test_validate_event_type_empty_string_raises() -> None:
    """Empty event_type raises AppendOnlyLedgerError."""
    with pytest.raises(AppendOnlyLedgerError, match="non-empty"):
        validate_event_type("")


def test_validate_event_type_non_string_raises() -> None:
    """Non-string event_type raises AppendOnlyLedgerError."""
    with pytest.raises(AppendOnlyLedgerError, match="must be str"):
        validate_event_type(12345)  # type: ignore[arg-type]


def test_validate_event_type_unknown_value_raises() -> None:
    """Unknown event_type value raises with whitelist message."""
    with pytest.raises(AppendOnlyLedgerError, match="11-value whitelist"):
        validate_event_type("unknown_event_type")


def test_validate_event_type_case_sensitive() -> None:
    """Strict match — case-sensitive (no normalization)."""
    with pytest.raises(AppendOnlyLedgerError, match="11-value whitelist"):
        validate_event_type("OPENING_CARRIED")


# ─────────────────────────────────────────────────────────────
# build_event_payload — quantitative event
# ─────────────────────────────────────────────────────────────

def test_build_event_payload_purchase_inbound_shape() -> None:
    """purchase_inbound → full payload with qty serialized as str."""
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="purchase_inbound",
        qty=Decimal("100.0000"),
        trace_id=TRACE_ID,
        source=SOURCE_MONTHLY_INPUT,
    )
    assert payload == {
        PAYLOAD_KEY_EVENT_ID: str(EVENT_ID),
        PAYLOAD_KEY_PRODUCT_ID: str(PROD_X),
        PAYLOAD_KEY_PERIOD_KEY: "2026-08",
        PAYLOAD_KEY_EVENT_TYPE: "purchase_inbound",
        PAYLOAD_KEY_QTY: "100.0000",
        PAYLOAD_KEY_TRACE_ID: str(TRACE_ID),
        PAYLOAD_KEY_SOURCE: SOURCE_MONTHLY_INPUT,
        PAYLOAD_KEY_REVERSES_EVENT_ID: None,
        PAYLOAD_KEY_CORRECTION_GROUP_ID: None,
        PAYLOAD_KEY_METADATA: {},
    }


def test_build_event_payload_with_reversal_fields() -> None:
    """reversal_corrected payload includes reverses_event_id + correction_group_id."""
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="reversal_corrected",
        qty=Decimal("-50.0000"),
        trace_id=TRACE_ID,
        source=SOURCE_REVERSAL_REQUEST,
        reverses_event_id=REVERSES_EVENT_ID,
        correction_group_id=CORRECTION_GROUP_ID,
    )
    assert payload[PAYLOAD_KEY_REVERSES_EVENT_ID] == str(REVERSES_EVENT_ID)
    assert payload[PAYLOAD_KEY_CORRECTION_GROUP_ID] == str(CORRECTION_GROUP_ID)


def test_build_event_payload_with_metadata() -> None:
    """metadata dict round-trips."""
    meta = {"actor_id": "user-123", "trace": "extra-context"}
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="adjustment_positive",
        qty=Decimal("10.0000"),
        trace_id=TRACE_ID,
        source=SOURCE_MANUAL_BACKFILL,
        metadata=meta,
    )
    assert payload[PAYLOAD_KEY_METADATA] == meta


def test_build_event_payload_closing_snapshot_qty_none() -> None:
    """closing_snapshot allows qty=None (OQ2 nullable)."""
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="closing_snapshot",
        qty=None,
        trace_id=TRACE_ID,
        source=SOURCE_CLOSE_SNAPSHOT,
    )
    assert payload[PAYLOAD_KEY_QTY] is None


def test_build_event_payload_invalid_event_type_raises() -> None:
    """Invalid event_type short-circuits before qty check."""
    with pytest.raises(AppendOnlyLedgerError, match="11-value whitelist"):
        build_event_payload(
            event_id=EVENT_ID,
            product_id=PROD_X,
            period_key="2026-08",
            event_type="not_in_whitelist",
            qty=Decimal("10.0000"),
            trace_id=TRACE_ID,
            source=SOURCE_MONTHLY_INPUT,
        )


def test_build_event_payload_invalid_period_key_raises() -> None:
    """M8 budget key format rejected (PRD §6.2 inventory equation is fiscal)."""
    with pytest.raises(AppendOnlyLedgerError, match="YYYY-MM"):
        build_event_payload(
            event_id=EVENT_ID,
            product_id=PROD_X,
            period_key="2026-08#B1",
            event_type="purchase_inbound",
            qty=Decimal("10.0000"),
            trace_id=TRACE_ID,
            source=SOURCE_MONTHLY_INPUT,
        )


def test_build_event_payload_non_quantitative_event_with_qty_quantized() -> None:
    """closing_snapshot with qty=Decimal → auto-quantized to 4dp."""
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="closing_snapshot",
        qty=Decimal("10.00000"),  # 5dp input → kernel quantizes → 4dp output
        trace_id=TRACE_ID,
        source=SOURCE_CLOSE_SNAPSHOT,
    )
    assert payload[PAYLOAD_KEY_QTY] == "10.0000"  # auto-quantized


def test_build_event_payload_quantitative_event_qty_none_raises() -> None:
    """purchase_inbound with qty=None raises (PRD §6.2 qty term required)."""
    with pytest.raises(AppendOnlyLedgerError, match="requires non-None qty"):
        build_event_payload(
            event_id=EVENT_ID,
            product_id=PROD_X,
            period_key="2026-08",
            event_type="purchase_inbound",
            qty=None,
            trace_id=TRACE_ID,
            source=SOURCE_MONTHLY_INPUT,
        )


def test_build_event_payload_qty_not_decimal_raises() -> None:
    """Non-Decimal qty raises (AD-8 monetary types)."""
    with pytest.raises(AppendOnlyLedgerError, match="must be Decimal"):
        build_event_payload(
            event_id=EVENT_ID,
            product_id=PROD_X,
            period_key="2026-08",
            event_type="purchase_inbound",
            qty=100.0,  # type: ignore[arg-type]
            trace_id=TRACE_ID,
            source=SOURCE_MONTHLY_INPUT,
        )


def test_build_event_payload_qty_auto_quantized() -> None:
    """qty with > 4dp precision → auto-quantized via ROUND_HALF_EVEN.

    CR 0-4 lesson: kernel performs the banker's rounding (TS/Python
    ROUND_HALF_EVEN parity) — caller does NOT need to pre-quantize.
    """
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="purchase_inbound",
        qty=Decimal("10.00000"),  # 5dp → 4dp
        trace_id=TRACE_ID,
        source=SOURCE_MONTHLY_INPUT,
    )
    assert payload[PAYLOAD_KEY_QTY] == "10.0000"  # auto-quantized


def test_build_event_payload_invalid_source_raises() -> None:
    """Non-canonical source raises."""
    with pytest.raises(AppendOnlyLedgerError, match="5-canonical set"):
        build_event_payload(
            event_id=EVENT_ID,
            product_id=PROD_X,
            period_key="2026-08",
            event_type="purchase_inbound",
            qty=Decimal("10.0000"),
            trace_id=TRACE_ID,
            source="not_a_source",
        )


# ─────────────────────────────────────────────────────────────
# build_event_payload — banker's rounding parity (CR 0-4 lesson)
# ─────────────────────────────────────────────────────────────

def test_build_event_payload_bankers_rounding_even_4dp() -> None:
    """0.00005 quantized at 4dp via ROUND_HALF_EVEN → 0.0000 (4th=0 even → down)."""
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="purchase_inbound",
        qty=Decimal("0.00005"),
        trace_id=TRACE_ID,
        source=SOURCE_MONTHLY_INPUT,
    )
    assert payload[PAYLOAD_KEY_QTY] == "0.0000"


def test_build_event_payload_bankers_rounding_odd_4dp() -> None:
    """0.00015 quantized at 4dp via ROUND_HALF_EVEN → 0.0002 (4th=1 odd → up)."""
    payload = build_event_payload(
        event_id=EVENT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="purchase_inbound",
        qty=Decimal("0.00015"),
        trace_id=TRACE_ID,
        source=SOURCE_MONTHLY_INPUT,
    )
    assert payload[PAYLOAD_KEY_QTY] == "0.0002"


# ─────────────────────────────────────────────────────────────
# InventoryLedgerEvent NamedTuple + validate_event_shape
# ─────────────────────────────────────────────────────────────

def test_inventory_ledger_event_field_types() -> None:
    """NamedTuple fields mirror SQL column set (AD-15 snake_case)."""
    event = InventoryLedgerEvent(
        event_id=EVENT_ID,
        tenant_id=TENANT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="purchase_inbound",
        qty=Decimal("100.0000"),
        trace_id=TRACE_ID,
        reverses_event_id=None,
        correction_group_id=None,
        payload={"key": "value"},
    )
    assert event.event_id == EVENT_ID
    assert event.tenant_id == TENANT_ID
    assert event.product_id == PROD_X
    assert event.period_key == "2026-08"
    assert event.event_type == "purchase_inbound"
    assert event.qty == Decimal("100.0000")
    assert event.trace_id == TRACE_ID
    assert event.reverses_event_id is None
    assert event.correction_group_id is None
    assert event.payload == {"key": "value"}


def test_validate_event_shape_valid_event_passes() -> None:
    """Valid InventoryLedgerEvent → no raise."""
    event = InventoryLedgerEvent(
        event_id=EVENT_ID,
        tenant_id=TENANT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="sales_outbound",
        qty=Decimal("-30.0000"),
        trace_id=TRACE_ID,
        reverses_event_id=None,
        correction_group_id=None,
        payload={},
    )
    validate_event_shape(event)  # no raise


def test_validate_event_shape_invalid_event_type_raises() -> None:
    """Invalid event_type in NamedTuple raises."""
    event = InventoryLedgerEvent(
        event_id=EVENT_ID,
        tenant_id=TENANT_ID,
        product_id=PROD_X,
        period_key="2026-08",
        event_type="not_canonical",
        qty=Decimal("10.0000"),
        trace_id=TRACE_ID,
        reverses_event_id=None,
        correction_group_id=None,
        payload={},
    )
    with pytest.raises(AppendOnlyLedgerError, match="11-value whitelist"):
        validate_event_shape(event)


def test_validate_event_shape_invalid_period_key_raises() -> None:
    """Invalid period_key format in NamedTuple raises."""
    event = InventoryLedgerEvent(
        event_id=EVENT_ID,
        tenant_id=TENANT_ID,
        product_id=PROD_X,
        period_key="bad-format",
        event_type="purchase_inbound",
        qty=Decimal("10.0000"),
        trace_id=TRACE_ID,
        reverses_event_id=None,
        correction_group_id=None,
        payload={},
    )
    with pytest.raises(AppendOnlyLedgerError, match="YYYY-MM"):
        validate_event_shape(event)


def test_validate_event_shape_non_uuid_product_id_raises() -> None:
    """Non-UUID product_id raises."""
    event = InventoryLedgerEvent(
        event_id=EVENT_ID,
        tenant_id=TENANT_ID,
        product_id="not-a-uuid",  # type: ignore[arg-type]
        period_key="2026-08",
        event_type="purchase_inbound",
        qty=Decimal("10.0000"),
        trace_id=TRACE_ID,
        reverses_event_id=None,
        correction_group_id=None,
        payload={},
    )
    with pytest.raises(AppendOnlyLedgerError, match="product_id must be UUID"):
        validate_event_shape(event)


# ─────────────────────────────────────────────────────────────
# append_only_violation_message
# ─────────────────────────────────────────────────────────────

def test_append_only_violation_message_update() -> None:
    """UPDATE attempt → Korean '수정 불가' message."""
    msg = append_only_violation_message(
        attempted_op="UPDATE",
        event_id=EVENT_ID,
    )
    assert "수정" in msg
    assert str(EVENT_ID) in msg
    assert "원장만 기록" in msg


def test_append_only_violation_message_delete() -> None:
    """DELETE attempt → Korean '삭제 불가' message."""
    msg = append_only_violation_message(
        attempted_op="DELETE",
        event_id=EVENT_ID,
    )
    assert "삭제" in msg
    assert str(EVENT_ID) in msg


def test_append_only_violation_message_with_db_trigger() -> None:
    """DB trigger verbatim copy appended."""
    db_msg = "append-only violation: inventory_ledger table forbids UPDATE/DELETE"
    msg = append_only_violation_message(
        attempted_op="UPDATE",
        event_id=EVENT_ID,
        db_trigger_message=db_msg,
    )
    assert db_msg in msg


def test_append_only_violation_message_unknown_op_passthrough() -> None:
    """Unknown op label passes through verbatim (no normalization)."""
    msg = append_only_violation_message(
        attempted_op="TRUNCATE",
        event_id=EVENT_ID,
    )
    assert "TRUNCATE" in msg


# ─────────────────────────────────────────────────────────────
# Determinism — repeated calls produce byte-identical output
# ─────────────────────────────────────────────────────────────

def test_build_event_payload_idempotent() -> None:
    """Same input 100× → byte-identical output (AD-16 determinism)."""
    kwargs: dict[str, Any] = {
        "event_id": EVENT_ID,
        "product_id": PROD_X,
        "period_key": "2026-08",
        "event_type": "purchase_inbound",
        "qty": Decimal("100.0000"),
        "trace_id": TRACE_ID,
        "source": SOURCE_MONTHLY_INPUT,
    }
    first = build_event_payload(**kwargs)
    for _ in range(100):
        again = build_event_payload(**kwargs)
        assert again == first


# ─────────────────────────────────────────────────────────────
# Constants cross-check
# ─────────────────────────────────────────────────────────────

def test_sources_5_canonical_values() -> None:
    """5 source discriminator values (audit-first payload self-describing)."""
    expected = {
        SOURCE_CARRY_CHAIN,
        SOURCE_MONTHLY_INPUT,
        SOURCE_MANUAL_BACKFILL,
        SOURCE_REVERSAL_REQUEST,
        SOURCE_CLOSE_SNAPSHOT,
    }
    assert expected == {
        "carry_chain",
        "monthly_input",
        "manual_backfill",
        "reversal_request",
        "close_snapshot",
    }


def test_quantum_uses_round_half_even() -> None:
    """CR 0-4 lesson: banker's rounding via ROUND_HALF_EVEN."""
    # Validate the QTY_QUANTUM Decimal is exactly NUMERIC(18,4) precision.
    assert INVENTORY_LEDGER_QTY_QUANTUM.as_tuple().exponent == -4
    # And boundary value: 0.00005 quantized via ROUND_HALF_EVEN → 0.0000.
    quantized = Decimal("0.00005").quantize(
        INVENTORY_LEDGER_QTY_QUANTUM, rounding=ROUND_HALF_EVEN
    )
    assert quantized == Decimal("0.0000")