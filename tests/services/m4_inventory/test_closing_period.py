"""tests/services/m4_inventory/test_closing_period.py — Story 6.1 pure kernel tests.

Tests for `packages/services/m4_inventory/closing_period.py`:
- compute_closing_snapshot (per-product closing qty materialize)
- classify_closing_period_status (CLOSING_READY/BLOCKED/ALREADY_CLOSED/EMPTY_PERIOD)
- is_closing_period_allowed
- Korean SSOT constants (CLOSING_PERIOD_CONFIRMATION_KO / BLOCKED_KO)
- banker's rounding via QTY_QUANTUM (CR 0-4 lesson + AD-15 parity)
- AD-11 layer rule: pure-Python, stdlib-only, no DB

Subset of the 18 cases from spec §T10.1 — full set deferred to follow-up
session (T10.3 carry).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.closing_period import (
    CLOSING_PERIOD_BLOCKED_KO,
    CLOSING_PERIOD_CONFIRMATION_KO,
    CLOSING_PERIOD_STATUS_ALREADY_CLOSED,
    CLOSING_PERIOD_STATUS_BLOCKED,
    CLOSING_PERIOD_STATUS_EMPTY_PERIOD,
    CLOSING_PERIOD_STATUS_READY,
    ClosingPeriodError,
    ClosingPeriodResult,
    ClosingSnapshotEntry,
    classify_closing_period_status,
    compute_closing_snapshot,
    format_closing_period_blocked_ko,
    format_closing_period_confirmation_ko,
    is_closing_period_allowed,
)


# ── classify_closing_period_status (5 cases) ───────────────────────


def test_classify_closing_period_status_ready_invariant_ok() -> None:
    """Invariant OK + ledger events >= 1 → CLOSING_READY."""
    closing = {uuid.uuid4(): Decimal("10.5"), uuid.uuid4(): Decimal("3")}
    status = classify_closing_period_status(
        closing, ledger_event_count=5, is_already_closed=False
    )
    assert status == CLOSING_PERIOD_STATUS_READY


def test_classify_closing_period_status_blocked_negative_closing() -> None:
    """One product closing < 0 → CLOSING_BLOCKED (invariant NEGATIVE_CLOSING)."""
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    closing = {p1: Decimal("5"), p2: Decimal("-2")}
    status = classify_closing_period_status(
        closing, ledger_event_count=3, is_already_closed=False
    )
    assert status == CLOSING_PERIOD_STATUS_BLOCKED


def test_classify_closing_period_status_empty_period_zero_events() -> None:
    """ledger events 0건 → EMPTY_PERIOD regardless of opening carry chain.

    Spec §AC #4: opening_inventory auto-carry populates closing_per_product
    from prev period, but the period itself has 0 events → still EMPTY_PERIOD.
    The kernel priority 2 fix (CR 6-1 R4 patch D1) decouples EMPTY_PERIOD
    from the opening-carry map.
    """
    closing = {uuid.uuid4(): Decimal("10")}
    status = classify_closing_period_status(
        closing, ledger_event_count=0, is_already_closed=False
    )
    assert status == CLOSING_PERIOD_STATUS_EMPTY_PERIOD


def test_classify_closing_period_status_already_closed_priority() -> None:
    """Priority 1: is_already_closed=True → ALREADY_CLOSED (idempotent no-op)."""
    closing = {uuid.uuid4(): Decimal("5")}
    status = classify_closing_period_status(
        closing, ledger_event_count=10, is_already_closed=True
    )
    assert status == CLOSING_PERIOD_STATUS_ALREADY_CLOSED


def test_classify_closing_period_status_empty_dict_and_zero_events() -> None:
    """closing dict empty + ledger_event_count=0 → EMPTY_PERIOD."""
    status = classify_closing_period_status(
        {}, ledger_event_count=0, is_already_closed=False
    )
    assert status == CLOSING_PERIOD_STATUS_EMPTY_PERIOD


# ── classify_closing_period_status: priority order (3 cases) ─────


def test_classify_closing_period_status_already_beats_blocked() -> None:
    """Priority 1 (ALREADY_CLOSED) wins even if invariant violated."""
    closing = {uuid.uuid4(): Decimal("-5")}
    status = classify_closing_period_status(
        closing, ledger_event_count=1, is_already_closed=True
    )
    assert status == CLOSING_PERIOD_STATUS_ALREADY_CLOSED


def test_classify_closing_period_status_empty_beats_blocked() -> None:
    """Priority 2 (EMPTY_PERIOD): closing empty + events 0 → EMPTY_PERIOD, NOT blocked."""
    status = classify_closing_period_status(
        {}, ledger_event_count=0, is_already_closed=False
    )
    assert status == CLOSING_PERIOD_STATUS_EMPTY_PERIOD


def test_classify_closing_period_status_negative_ledger_event_count_raises() -> None:
    """Negative ledger_event_count → ClosingPeriodError (defense-in-depth)."""
    closing = {uuid.uuid4(): Decimal("5")}
    with pytest.raises(ClosingPeriodError) as exc_info:
        classify_closing_period_status(
            closing, ledger_event_count=-1, is_already_closed=False
        )
    assert exc_info.value.error_code == "NEGATIVE_LEDGER_EVENT_COUNT"


# ── is_closing_period_allowed (3 cases) ────────────────────────────


def test_is_closing_period_allowed_ready() -> None:
    assert is_closing_period_allowed(CLOSING_PERIOD_STATUS_READY) is True


def test_is_closing_period_allowed_blocked() -> None:
    assert is_closing_period_allowed(CLOSING_PERIOD_STATUS_BLOCKED) is False


def test_is_closing_period_allowed_already_closed_and_empty() -> None:
    assert is_closing_period_allowed(CLOSING_PERIOD_STATUS_ALREADY_CLOSED) is False
    assert is_closing_period_allowed(CLOSING_PERIOD_STATUS_EMPTY_PERIOD) is False


# ── is_closing_period_allowed: unknown status raises (1 case) ─────


def test_is_closing_period_allowed_unknown_status_raises() -> None:
    """Unknown status code → ClosingPeriodError (defense-in-depth)."""
    with pytest.raises(ClosingPeriodError) as exc_info:
        is_closing_period_allowed("UNKNOWN_CODE")
    assert exc_info.value.error_code == "INVALID_CLOSING_PERIOD_STATUS"


# ── Korean SSOT constants (2 cases) ────────────────────────────────


def test_closing_period_confirmation_ko_constant_parity() -> None:
    """CLOSING_PERIOD_CONFIRMATION_KO mirrors TS `formatClosingPeriodConfirmationKo`."""
    assert CLOSING_PERIOD_CONFIRMATION_KO == "월 마감 확정: 기말재고 snapshot 저장"


def test_closing_period_blocked_ko_constant_parity() -> None:
    """CLOSING_PERIOD_BLOCKED_KO mirrors TS `formatClosingPeriodBlockedKo`."""
    assert CLOSING_PERIOD_BLOCKED_KO == "마감 차단: 기말재고 음수"


# ── format helpers (4 cases) ───────────────────────────────────────


def test_format_closing_period_confirmation_ko_ready() -> None:
    result = ClosingPeriodResult(
        status=CLOSING_PERIOD_STATUS_READY,
        allowed=True,
        closing_per_product={uuid.uuid4(): Decimal("100")},
        closing_snapshot_count=0,
        ledger_event_count=10,
        period_key="2026-07",
    )
    assert format_closing_period_confirmation_ko(result) == CLOSING_PERIOD_CONFIRMATION_KO


def test_format_closing_period_confirmation_ko_not_ready_returns_empty() -> None:
    """Status != CLOSING_READY → empty string (UI dispatches based on status)."""
    result = ClosingPeriodResult(
        status=CLOSING_PERIOD_STATUS_BLOCKED,
        allowed=False,
        closing_per_product={uuid.uuid4(): Decimal("-3")},
        closing_snapshot_count=0,
        ledger_event_count=2,
        period_key="2026-07",
    )
    assert format_closing_period_confirmation_ko(result) == ""


def test_format_closing_period_blocked_ko_blocked() -> None:
    result = ClosingPeriodResult(
        status=CLOSING_PERIOD_STATUS_BLOCKED,
        allowed=False,
        closing_per_product={uuid.uuid4(): Decimal("-3")},
        closing_snapshot_count=0,
        ledger_event_count=2,
        period_key="2026-07",
    )
    assert format_closing_period_blocked_ko(result) == CLOSING_PERIOD_BLOCKED_KO


def test_format_closing_period_blocked_ko_not_blocked_returns_empty() -> None:
    """Status != CLOSING_BLOCKED → empty string."""
    result = ClosingPeriodResult(
        status=CLOSING_PERIOD_STATUS_READY,
        allowed=True,
        closing_per_product={uuid.uuid4(): Decimal("5")},
        closing_snapshot_count=0,
        ledger_event_count=2,
        period_key="2026-07",
    )
    assert format_closing_period_blocked_ko(result) == ""


# ── compute_closing_snapshot (4 cases) ─────────────────────────────


def test_compute_closing_snapshot_per_product() -> None:
    """Per product 1 ClosingSnapshotEntry."""
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    closing = {p1: Decimal("5"), p2: Decimal("3")}
    entries = compute_closing_snapshot(
        closing,
        period_key="2026-07",
        finalized_at="2026-08-07T12:00:00Z",
    )
    assert len(entries) == 2
    assert all(isinstance(e, ClosingSnapshotEntry) for e in entries)
    qty_map = {e.product_id: e.closing_qty for e in entries}
    assert qty_map[p1] == Decimal("5")
    assert qty_map[p2] == Decimal("3")


def test_compute_closing_snapshot_empty() -> None:
    """Empty closing dict → empty list (EMPTY_PERIOD case)."""
    entries = compute_closing_snapshot(
        {},
        period_key="2026-07",
        finalized_at="2026-08-07T12:00:00Z",
    )
    assert entries == []


def test_compute_closing_snapshot_bankers_rounding() -> None:
    """QTY_QUANTUM banker's rounding via ROUND_HALF_EVEN (CR 0-4 lesson).

    QTY_QUANTUM = Decimal('0.0001') (4 decimals).
    0.00555 at 4 decimals → 0.0056 (banker's rounds half-up at the
    5th decimal — 0.00555 is closer to 0.0056 than 0.0055).
    """
    p1 = uuid.uuid4()
    closing = {p1: Decimal("0.00555")}
    entries = compute_closing_snapshot(
        closing,
        period_key="2026-07",
        finalized_at="2026-08-07T12:00:00Z",
    )
    assert entries[0].closing_qty == Decimal("0.0056")


def test_compute_closing_snapshot_bankers_rounding_half_even() -> None:
    """True ROUND_HALF_EVEN: 0.00005 → 0.0000 (round to even)."""
    p1 = uuid.uuid4()
    closing = {p1: Decimal("0.00005")}
    entries = compute_closing_snapshot(
        closing,
        period_key="2026-07",
        finalized_at="2026-08-07T12:00:00Z",
    )
    assert entries[0].closing_qty == Decimal("0.0000")


def test_compute_closing_snapshot_bankers_rounding_half_even_to_2() -> None:
    """ROUND_HALF_EVEN: 0.00015 → 0.0002 (round to even — 2 is even)."""
    p1 = uuid.uuid4()
    closing = {p1: Decimal("0.00015")}
    entries = compute_closing_snapshot(
        closing,
        period_key="2026-07",
        finalized_at="2026-08-07T12:00:00Z",
    )
    assert entries[0].closing_qty == Decimal("0.0002")


def test_compute_closing_snapshot_deterministic_ordering() -> None:
    """Sort by product_id for deterministic V8 byte-identical parity."""
    p1, p2, p3 = (uuid.uuid4() for _ in range(3))
    # Pass in non-sorted order
    closing = {p3: Decimal("3"), p1: Decimal("1"), p2: Decimal("2")}
    entries = compute_closing_snapshot(
        closing,
        period_key="2026-07",
        finalized_at="2026-08-07T12:00:00Z",
    )
    sorted_product_ids = sorted([p1, p2, p3])
    assert [e.product_id for e in entries] == sorted_product_ids


# ── compute_closing_snapshot: error paths (2 cases) ──────────────


def test_compute_closing_snapshot_non_decimal_qty_raises() -> None:
    """Non-Decimal qty → ClosingPeriodError(QTY_MUST_BE_DECIMAL)."""
    closing = {uuid.uuid4(): 5}  # int, not Decimal
    with pytest.raises(ClosingPeriodError) as exc_info:
        compute_closing_snapshot(
            closing,
            period_key="2026-07",
            finalized_at="2026-08-07T12:00:00Z",
        )
    assert exc_info.value.error_code == "QTY_MUST_BE_DECIMAL"


def test_compute_closing_snapshot_non_finite_qty_raises() -> None:
    """Non-finite Decimal (NaN/Infinity) → ClosingPeriodError(NON_FINITE_QTY)."""
    closing = {uuid.uuid4(): Decimal("NaN")}
    with pytest.raises(ClosingPeriodError) as exc_info:
        compute_closing_snapshot(
            closing,
            period_key="2026-07",
            finalized_at="2026-08-07T12:00:00Z",
        )
    assert exc_info.value.error_code == "NON_FINITE_QTY"


# ── ClosingPeriodError (1 case) ───────────────────────────────────


def test_closing_period_error_typed_exception() -> None:
    """ClosingPeriodError carries message + error_code + period_key + tenant_id."""
    err = ClosingPeriodError(
        message="test message",
        error_code="TEST_CODE",
        period_key="2026-07",
        tenant_id=uuid.uuid4(),
    )
    assert isinstance(err, Exception)
    assert str(err) == "test message"
    assert err.error_code == "TEST_CODE"
    assert err.period_key == "2026-07"
    assert err.tenant_id is not None


# ── ClosingSnapshotEntry shape (1 case) ────────────────────────────


def test_closing_snapshot_entry_namedtuple_shape() -> None:
    """ClosingSnapshotEntry has 3 fields: product_id, closing_qty, finalized_at."""
    p = uuid.uuid4()
    entry = ClosingSnapshotEntry(
        product_id=p,
        closing_qty=Decimal("5"),
        finalized_at="2026-08-07T12:00:00Z",
    )
    assert entry.product_id == p
    assert entry.closing_qty == Decimal("5")
    assert entry.finalized_at == "2026-08-07T12:00:00Z"


# ── Status code SSOT (1 case) ──────────────────────────────────────


def test_closing_period_statuses_frozenset_completeness() -> None:
    """All 4 status codes are in the SSOT frozenset."""
    expected = {
        CLOSING_PERIOD_STATUS_READY,
        CLOSING_PERIOD_STATUS_BLOCKED,
        CLOSING_PERIOD_STATUS_ALREADY_CLOSED,
        CLOSING_PERIOD_STATUS_EMPTY_PERIOD,
    }
    from packages.services.m4_inventory.closing_period import (
        CLOSING_PERIOD_STATUSES,
    )

    assert CLOSING_PERIOD_STATUSES == expected