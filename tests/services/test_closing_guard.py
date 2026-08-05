"""tests.services.test_closing_guard — Story 5.3 pure closing_guard kernel tests.

Tests for `packages.services.m4_inventory.closing_guard`:
- compute_closing_balance_per_product (SIGN-NEUTRAL aggregate)
- classify_closing_invariant (3 codes: CLOSING_OK / NEGATIVE_CLOSING / EMPTY_PERIOD)
- is_close_blocked (single source of truth)
- format_negative_closing_banner_ko (Korean message SSOT)
- ClosingInvariant NamedTuple shape

AD-11 layer rule: pure-Python, stdlib-only, no DB, no clock, no random.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.closing_guard import (
    INVARIANT_CODE_CLOSING_OK,
    INVARIANT_CODE_EMPTY_PERIOD,
    INVARIANT_CODE_NEGATIVE_CLOSING,
    INVARIANT_CODES,
    NEGATIVE_CLOSING_INVENTORY_KO,
    ClosingGuardError,
    ClosingInvariant,
    classify_closing_invariant,
    compute_closing_balance_per_product,
    format_negative_closing_banner_ko,
    is_close_blocked,
)
from packages.services.m4_inventory.ledger import InventoryLedgerEvent


# ── Constants ──────────────────────────────────────────────────
def test_constants():
    """3 invariant codes match Story 5.3 spec."""
    assert NEGATIVE_CLOSING_INVENTORY_KO == "기말재고 음수: 마감 불가"
    assert INVARIANT_CODES == frozenset(
        {INVARIANT_CODE_CLOSING_OK, INVARIANT_CODE_NEGATIVE_CLOSING, INVARIANT_CODE_EMPTY_PERIOD}
    )


# ── compute_closing_balance_per_product ─────────────────────────
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


def test_compute_closing_empty():
    """Empty events → empty dict."""
    assert compute_closing_balance_per_product([]) == {}


def test_compute_closing_sign_neutral():
    """Outbound events carry negative qty at write-time (per P2 review fix);
    plain SUM(qty) per product yields the closing balance.
    """
    pid_a = uuid.uuid4()
    pid_b = uuid.uuid4()
    events = [
        _evt(pid_a, Decimal("100.0")),   # inbound
        _evt(pid_a, Decimal("-30.0")),   # outbound (negative at write-time)
        _evt(pid_b, Decimal("50.0")),    # inbound
        _evt(pid_b, Decimal("-50.0")),   # outbound (full consume)
    ]
    closing = compute_closing_balance_per_product(events)
    assert closing[pid_a] == Decimal("70.0000")  # banker's rounding
    assert closing[pid_b] == Decimal("0.0000")


def test_compute_closing_skip_none_qty():
    """Events with qty=None (e.g. closing_snapshot) are skipped."""
    pid = uuid.uuid4()
    events = [
        _evt(pid, Decimal("100.0")),
        _evt(pid, None),  # closing_snapshot
    ]
    closing = compute_closing_balance_per_product(events)
    assert closing[pid] == Decimal("100.0000")


def test_compute_closing_non_finite_raises():
    """Non-finite qty → ClosingGuardError."""
    pid = uuid.uuid4()
    events = [_evt(pid, Decimal("NaN"))]
    with pytest.raises(ClosingGuardError) as exc_info:
        compute_closing_balance_per_product(events)
    assert exc_info.value.error_code == "NON_FINITE_QTY"


# ── classify_closing_invariant ──────────────────────────────────
def test_classify_empty_period():
    """Empty closing dict → EMPTY_PERIOD."""
    invariant = classify_closing_invariant({})
    assert invariant.code == INVARIANT_CODE_EMPTY_PERIOD
    assert invariant.negative_products == {}
    assert invariant.closing_per_product == {}
    assert invariant.guard_enabled is True


def test_classify_closing_ok():
    """All closings >= 0 → CLOSING_OK."""
    pid_a = uuid.uuid4()
    pid_b = uuid.uuid4()
    closing = {pid_a: Decimal("100.0"), pid_b: Decimal("0.0")}
    invariant = classify_closing_invariant(closing)
    assert invariant.code == INVARIANT_CODE_CLOSING_OK
    assert invariant.negative_products == {}
    assert invariant.guard_enabled is True


def test_classify_negative_closing():
    """At least one closing < 0 → NEGATIVE_CLOSING."""
    pid_ok = uuid.uuid4()
    pid_neg = uuid.uuid4()
    closing = {pid_ok: Decimal("50.0"), pid_neg: Decimal("-5.0")}
    invariant = classify_closing_invariant(closing)
    assert invariant.code == INVARIANT_CODE_NEGATIVE_CLOSING
    assert invariant.negative_products == {pid_neg: Decimal("-5.0000")}
    assert invariant.guard_enabled is True


def test_classify_zero_closing_ok():
    """Closing exactly 0 → CLOSING_OK (>= 0 inclusive)."""
    pid = uuid.uuid4()
    closing = {pid: Decimal("0.0")}
    invariant = classify_closing_invariant(closing)
    assert invariant.code == INVARIANT_CODE_CLOSING_OK


# ── is_close_blocked ───────────────────────────────────────────
def test_is_close_blocked_only_on_negative():
    """Close blocked ONLY when NEGATIVE_CLOSING."""
    inv_neg = classify_closing_invariant({uuid.uuid4(): Decimal("-1.0")})
    inv_ok = classify_closing_invariant({uuid.uuid4(): Decimal("0.0")})
    inv_empty = classify_closing_invariant({})
    assert is_close_blocked(inv_neg) is True
    assert is_close_blocked(inv_ok) is False
    assert is_close_blocked(inv_empty) is False


# ── format_negative_closing_banner_ko ──────────────────────────
def test_format_banner_empty_negative():
    """Defensive — empty negative_products returns base message."""
    invariant = classify_closing_invariant({uuid.uuid4(): Decimal("-1.0")})
    # Manually clear negatives (defensive test)
    invariant = invariant._replace(negative_products={})
    banner = format_negative_closing_banner_ko(invariant)
    assert banner == NEGATIVE_CLOSING_INVENTORY_KO


def test_format_banner_includes_top_offender():
    """Banner includes top offender's product_id + closing_qty."""
    pid_top = uuid.uuid4()
    pid_other = uuid.uuid4()
    closing = {
        pid_top: Decimal("-10.0"),  # most severe (lowest)
        pid_other: Decimal("-1.0"),
    }
    invariant = classify_closing_invariant(closing)
    banner = format_negative_closing_banner_ko(invariant)
    assert NEGATIVE_CLOSING_INVENTORY_KO in banner
    # The Decimal qty is formatted via f-string → preserves trailing zeros (e.g. "-10.0개")
    assert "-10" in banner
    assert "개" in banner
    assert "마감 불가" in banner


def test_format_banner_with_product_name_lookup():
    """product_name_lookup overrides UUID short label."""
    pid = uuid.uuid4()
    invariant = classify_closing_invariant({pid: Decimal("-5.0")})
    banner = format_negative_closing_banner_ko(
        invariant, product_name_lookup={pid: "원자재 A"}
    )
    assert "원자재 A" in banner


def test_format_banner_non_negative_returns_base():
    """CLOSING_OK → returns base message (defensive)."""
    invariant = classify_closing_invariant({uuid.uuid4(): Decimal("50.0")})
    banner = format_negative_closing_banner_ko(invariant)
    assert banner == NEGATIVE_CLOSING_INVENTORY_KO


# ── ClosingInvariant NamedTuple shape ──────────────────────────
def test_closing_invariant_fields():
    """ClosingInvariant has 4 fields per Story 5.3 spec."""
    fields = {"code", "negative_products", "closing_per_product", "guard_enabled"}
    assert set(ClosingInvariant._fields) == fields