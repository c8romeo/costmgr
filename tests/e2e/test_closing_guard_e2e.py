"""tests.e2e.test_closing_guard_e2e — Story 5.3 end-to-end smoke test.

Verifies the full closing-guard pure-kernel pipeline using only the
pure kernels in `packages.services.m4_inventory.closing_guard` —
no DB or async infrastructure required.

Acceptance scenarios:
1. Negative closing exists in ledger aggregate → code=NEGATIVE_CLOSING + is_blocked=True
2. All closing >= 0 → code=CLOSING_OK + is_blocked=False
3. Empty ledger → code=EMPTY_PERIOD + is_blocked=False
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from packages.services.m4_inventory.closing_guard import (
    INVARIANT_CODE_CLOSING_OK,
    INVARIANT_CODE_EMPTY_PERIOD,
    INVARIANT_CODE_NEGATIVE_CLOSING,
    NEGATIVE_CLOSING_INVENTORY_KO,
    classify_closing_invariant,
    compute_closing_balance_per_product,
    format_negative_closing_banner_ko,
    is_close_blocked,
)
from packages.services.m4_inventory.ledger import InventoryLedgerEvent


def _evt(product_id, qty, event_id=None) -> InventoryLedgerEvent:
    """Build a minimal InventoryLedgerEvent for testing.

    Actual NamedTuple fields:
    event_id, tenant_id, product_id, period_key, event_type, qty, trace_id,
    reverses_event_id, correction_group_id, payload
    """
    return InventoryLedgerEvent(
        event_id=event_id or uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        product_id=product_id,
        period_key="2026-07",
        event_type="purchase_inbound",
        qty=qty,
        trace_id=uuid.uuid4(),
        reverses_event_id=None,
        correction_group_id=None,
        payload={},
    )


def test_e2e_closing_guard_full_flow_smoke():
    """End-to-end smoke: evaluate → block-on-negative → banner formatted."""
    tenant_id = uuid.uuid4()

    # 1. Seed ledger events — one product over-consumed
    pid_overconsumed = uuid.uuid4()
    pid_ok = uuid.uuid4()
    events = [
        # pid_overconsumed: inbound 10 → outbound -15 → closing -5 (negative)
        _evt(pid_overconsumed, Decimal("10.0"), event_id=uuid.uuid4()),
        _evt(pid_overconsumed, Decimal("-15.0"), event_id=uuid.uuid4()),
        # pid_ok: only inbound
        _evt(pid_ok, Decimal("50.0"), event_id=uuid.uuid4()),
    ]

    # 2. Compute closing + classify
    closing = compute_closing_balance_per_product(events)
    assert closing[pid_overconsumed] == Decimal("-5.0000")
    assert closing[pid_ok] == Decimal("50.0000")

    invariant = classify_closing_invariant(closing)
    assert invariant.code == INVARIANT_CODE_NEGATIVE_CLOSING
    assert is_close_blocked(invariant) is True

    # 3. Format banner
    banner = format_negative_closing_banner_ko(invariant)
    assert banner.startswith(NEGATIVE_CLOSING_INVENTORY_KO)
    assert "마감 불가" in banner


def test_e2e_closing_ok_path():
    """End-to-end smoke — closing all positive → OK, no block."""
    pid = uuid.uuid4()
    events = [
        _evt(pid, Decimal("100.0")),
    ]

    closing = compute_closing_balance_per_product(events)
    invariant = classify_closing_invariant(closing)
    assert invariant.code == INVARIANT_CODE_CLOSING_OK
    assert is_close_blocked(invariant) is False


def test_e2e_empty_period_skip_path():
    """End-to-end smoke — empty ledger → EMPTY_PERIOD, no block."""
    closing = compute_closing_balance_per_product([])
    invariant = classify_closing_invariant(closing)
    assert invariant.code == INVARIANT_CODE_EMPTY_PERIOD
    assert is_close_blocked(invariant) is False
