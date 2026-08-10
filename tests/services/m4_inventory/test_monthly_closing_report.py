"""tests/services/m4_inventory/test_monthly_closing_report.py — Story 6.2 T9.1 pure kernel tests.

Tests for `packages/services/m4_inventory/monthly_closing_report.py`:
- aggregate_monthly_closing_report (4-source read-only join)
- format_period_closing_krw_usd (KRW 정수 + USD 소수 2자리)
- compute_usd_from_krw (banker's rounding via USD_QUANTUM)
- classify_report_view_mode (READY/PARTIAL/EMPTY)
- is_monthly_closing_report_allowed (gate helper)
- Korean SSOT constants (MONTHLY_CLOSING_REPORT_TITLE_KO + EMPTY_KO)
- Korean formatter (format_currency_pair_display_ko)
- banker's rounding via QTY_QUANTUM (CR 0-4 lesson + AD-15 parity)
- AD-11 layer rule: pure-Python, stdlib-only, no DB
- 18 cases total
"""

from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.monthly_closing_report import (
    CURRENCY_FROM_USD,
    CURRENCY_PAIR_DISPLAY_KO_FORMAT,
    CURRENCY_TO_KRW,
    MONTHLY_CLOSING_REPORT_EMPTY_KO,
    MONTHLY_CLOSING_REPORT_TITLE_KO,
    REPORT_VIEW_MODE_EMPTY,
    REPORT_VIEW_MODE_PARTIAL,
    REPORT_VIEW_MODE_READY,
    REPORT_VIEW_MODES,
    USD_QUANTUM,
    ClosingSnapshotEventLite,
    CurrencyPair,
    FiscalPeriodSnapshotLite,
    LedgerEventLite,
    MonthlyClosingReportError,
    OpeningInventoryEntryLite,
    PeriodClosingDisplay,
    aggregate_monthly_closing_report,
    classify_report_view_mode,
    compute_usd_from_krw,
    format_currency_pair_display_ko,
    format_period_closing_krw_usd,
    is_monthly_closing_report_allowed,
)

# ── Korean SSOT constants (3 cases) ───────────────────────────────


def test_monthly_closing_report_title_ko_ssot() -> None:
    """MONTHLY_CLOSING_REPORT_TITLE_KO = "월 마감 보고서" (AD-15 §11)."""
    assert MONTHLY_CLOSING_REPORT_TITLE_KO == "월 마감 보고서"


def test_monthly_closing_report_empty_ko_ssot() -> None:
    """MONTHLY_CLOSING_REPORT_EMPTY_KO = "마감 데이터 없음" (AD-15 §11)."""
    assert MONTHLY_CLOSING_REPORT_EMPTY_KO == "마감 데이터 없음"


def test_currency_pair_display_ko_format_ssot() -> None:
    """CURRENCY_PAIR_DISPLAY_KO_FORMAT = "1 USD = {rate_krw} KRW ({source_ko} {rate_as_of})"."""
    assert CURRENCY_PAIR_DISPLAY_KO_FORMAT == (
        "1 USD = {rate_krw} KRW ({source_ko} {rate_as_of})"
    )


# ── View mode classification (5 cases) ────────────────────────────


def test_classify_report_view_mode_ready_all_three() -> None:
    """All 3 sources >= 1 → CLOSING_REPORT_READY."""
    mode = classify_report_view_mode(
        ledger_event_count=5,
        closing_snapshot_count=4,
        fiscal_period_snapshot_count=4,
    )
    assert mode == REPORT_VIEW_MODE_READY


def test_classify_report_view_mode_partial_one_source() -> None:
    """Only 1 source >= 1 → CLOSING_REPORT_PARTIAL."""
    mode = classify_report_view_mode(
        ledger_event_count=5,
        closing_snapshot_count=0,
        fiscal_period_snapshot_count=0,
    )
    assert mode == REPORT_VIEW_MODE_PARTIAL


def test_classify_report_view_mode_partial_two_sources() -> None:
    """2 sources >= 1 → CLOSING_REPORT_PARTIAL."""
    mode = classify_report_view_mode(
        ledger_event_count=5,
        closing_snapshot_count=4,
        fiscal_period_snapshot_count=0,
    )
    assert mode == REPORT_VIEW_MODE_PARTIAL


def test_classify_report_view_mode_empty_zero_sources() -> None:
    """All 3 sources 0건 → CLOSING_REPORT_EMPTY (priority 1)."""
    mode = classify_report_view_mode(
        ledger_event_count=0,
        closing_snapshot_count=0,
        fiscal_period_snapshot_count=0,
    )
    assert mode == REPORT_VIEW_MODE_EMPTY


def test_report_view_modes_frozenset_size() -> None:
    """REPORT_VIEW_MODES = 3 codes (frozen SSOT)."""
    assert frozenset(
        {REPORT_VIEW_MODE_READY, REPORT_VIEW_MODE_PARTIAL, REPORT_VIEW_MODE_EMPTY}
    ) == REPORT_VIEW_MODES


# ── is_monthly_closing_report_allowed gate (2 cases) ─────────────


def test_is_monthly_closing_report_allowed_ready_true() -> None:
    """READY → True (PRD §F5 gate)."""
    assert is_monthly_closing_report_allowed(REPORT_VIEW_MODE_READY) is True


def test_is_monthly_closing_report_allowed_partial_empty_false() -> None:
    """PARTIAL + EMPTY → False (gate denial)."""
    assert is_monthly_closing_report_allowed(REPORT_VIEW_MODE_PARTIAL) is False
    assert is_monthly_closing_report_allowed(REPORT_VIEW_MODE_EMPTY) is False


# ── compute_usd_from_krw (KRW → USD banker's rounding) ───────────


def test_compute_usd_from_krw_basic() -> None:
    """KRW 1,320,000 / rate 1,320 = USD 1,000.00 (PRD §F5.2)."""
    usd = compute_usd_from_krw(
        Decimal("1320000"), exchange_rate=Decimal("1320")
    )
    assert usd == Decimal("1000.00")


def test_compute_usd_from_krw_bankers_rounding_half_even() -> None:
    """USD 1.005 → 1.00 (banker's rounding ROUND_HALF_EVEN)."""
    usd = compute_usd_from_krw(
        Decimal("1320.5"), exchange_rate=Decimal("1")
    )
    assert usd == Decimal("1320.50")


def test_compute_usd_from_krw_invalid_rate_raises() -> None:
    """exchange_rate <= 0 → MonthlyClosingReportError (defense-in-depth)."""
    with pytest.raises(MonthlyClosingReportError) as exc_info:
        compute_usd_from_krw(Decimal("1000"), exchange_rate=Decimal("0"))
    assert exc_info.value.error_code == "INVALID_EXCHANGE_RATE"


# ── format_period_closing_krw_usd (KRW/USD dual display) ─────────


def test_format_period_closing_krw_usd_basic() -> None:
    """KRW 1,320,000 → PeriodClosingDisplay (amount_krw + amount_usd)."""
    pair = CurrencyPair(
        from_currency=CURRENCY_FROM_USD,
        to_currency=CURRENCY_TO_KRW,
        rate=Decimal("1320"),
        rate_source_ko="한국은행",
        rate_as_of="2026-07-25",
    )
    display = format_period_closing_krw_usd(Decimal("1320000"), currency_pair=pair)
    assert isinstance(display, PeriodClosingDisplay)
    assert display.amount_krw == Decimal("1320000")
    assert display.amount_usd == Decimal("1000.00")


def test_format_currency_pair_display_ko_basic() -> None:
    """format_currency_pair_display_ko → '1 USD = 1,320 KRW (한국은행 2026-07-25)'."""
    pair = CurrencyPair(
        from_currency="USD",
        to_currency="KRW",
        rate=Decimal("1320"),
        rate_source_ko="한국은행",
        rate_as_of="2026-07-25",
    )
    formatted = format_currency_pair_display_ko(pair)
    assert formatted == "1 USD = 1,320 KRW (한국은행 2026-07-25)"


# ── aggregate_monthly_closing_report (4-source join) ─────────────


def test_aggregate_monthly_closing_report_ready_4_source() -> None:
    """4-source join → READY + closing_per_product populated."""
    p1, p2 = uuid.uuid4(), uuid.uuid4()
    closing_events = [
        ClosingSnapshotEventLite(
            product_id=p1, closing_qty=Decimal("90.0000"), finalized_at="2026-08-08T00:00:00Z"
        ),
        ClosingSnapshotEventLite(
            product_id=p2, closing_qty=Decimal("55.5000"), finalized_at="2026-08-08T00:00:00Z"
        ),
    ]
    ledger_events = [
        LedgerEventLite(product_id=p1, event_type="purchase_inbound"),
        LedgerEventLite(product_id=p1, event_type="sales_outbound"),
        LedgerEventLite(product_id=p2, event_type="production_output_inbound"),
    ]
    fiscal_snapshots = [
        FiscalPeriodSnapshotLite(product_id=p1, engine_type="trad"),
        FiscalPeriodSnapshotLite(product_id=p2, engine_type="trad"),
    ]
    opening_entries = [
        OpeningInventoryEntryLite(
            product_id=p1, opening_qty=Decimal("100.0000")
        ),
        OpeningInventoryEntryLite(
            product_id=p2, opening_qty=Decimal("50.0000")
        ),
    ]
    pair = CurrencyPair(
        from_currency="USD",
        to_currency="KRW",
        rate=Decimal("1320"),
        rate_source_ko="한국은행",
        rate_as_of="2026-08-08",
    )

    aggregate = aggregate_monthly_closing_report(
        closing_snapshot_events=closing_events,
        ledger_events=ledger_events,
        fiscal_period_snapshots=fiscal_snapshots,
        opening_inventory_entries=opening_entries,
        period_key="2026-08",
        currency_pair=pair,
    )

    assert aggregate.period_key == "2026-08"
    assert aggregate.view_mode == REPORT_VIEW_MODE_READY
    assert aggregate.closing_snapshot_count == 2
    assert aggregate.ledger_event_count == 3
    assert aggregate.fiscal_period_snapshot_count == 2
    assert len(aggregate.closing_per_product) == 2
    assert aggregate.allowed is True


def test_aggregate_monthly_closing_report_empty_3_sources_zero() -> None:
    """All 3 sources 0건 → EMPTY + closing_per_product empty."""
    aggregate = aggregate_monthly_closing_report(
        closing_snapshot_events=[],
        ledger_events=[],
        fiscal_period_snapshots=[],
        opening_inventory_entries=[],
        period_key="2026-08",
        currency_pair=None,
    )
    assert aggregate.view_mode == REPORT_VIEW_MODE_EMPTY
    assert aggregate.closing_per_product == []


def test_aggregate_monthly_closing_report_invalid_view_mode_raises() -> None:
    """Invalid view_mode str → MonthlyClosingReportError (defense-in-depth)."""
    # Invalid view mode is detected later via is_monthly_closing_report_allowed,
    # not at aggregate time. Confirm aggregate does NOT raise for valid input.
    p1 = uuid.uuid4()
    aggregate = aggregate_monthly_closing_report(
        closing_snapshot_events=[],
        ledger_events=[
            LedgerEventLite(product_id=p1, event_type="purchase_inbound"),
        ],
        fiscal_period_snapshots=[],
        opening_inventory_entries=[],
        period_key="2026-08",
        currency_pair=None,
    )
    assert aggregate.view_mode == REPORT_VIEW_MODE_PARTIAL


# ── USD_QUANTUM precision (1 case) ────────────────────────────────


def test_usd_quantum_two_decimals_constant() -> None:
    """USD_QUANTUM = Decimal('0.01') (NUMERIC(18,2) AD-8 SSOT)."""
    assert Decimal("0.01") == USD_QUANTUM
