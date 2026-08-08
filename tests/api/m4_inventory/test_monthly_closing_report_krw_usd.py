"""tests/api/m4_inventory/test_monthly_closing_report_krw_usd.py — Story 6.2 T9.6 KRW/USD tests.

Tests for AD-8 monetary types + PRD §F5.2 KRW/USD dual display:
- KRW = BIGINT (정수)
- USD = NUMERIC(18,2) (소수 2자리)
- 환율 injection (tenant_settings.baseline.currency_pair.usd_krw_rate)
- banker's rounding via USD_QUANTUM (CR 0-4 lesson)
- 6 cases total

Pure-kernel only — no DB / async infrastructure required.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.services.m4_inventory.monthly_closing_report import (
    CURRENCY_FROM_USD,
    CURRENCY_TO_KRW,
    USD_QUANTUM,
    CurrencyPair,
    compute_usd_from_krw,
    format_currency_pair_display_ko,
    format_period_closing_krw_usd,
)


# ── USD conversion (3 cases) ─────────────────────────────────────


def test_krw_to_usd_basic_1320() -> None:
    """KRW 1,320,000 / rate 1,320 = USD 1,000.00 (PRD §F5.2 example)."""
    usd = compute_usd_from_krw(Decimal("1320000"), exchange_rate=Decimal("1320"))
    assert usd == Decimal("1000.00")


def test_krw_to_usd_bankers_rounding_half_even() -> None:
    """USD 1.005 → 1.00 (ROUND_HALF_EVEN precision)."""
    # KRW 1005 / rate 1000 = USD 1.005 → quantize to 1.00 (ROUND_HALF_EVEN)
    usd = compute_usd_from_krw(Decimal("1005"), exchange_rate=Decimal("1000"))
    assert usd == Decimal("1.00")


def test_krw_to_usd_decimal_rate_1320_5() -> None:
    """KRW 1,320,000 / rate 1,320.5 = USD 999.62 (banker's rounding precision)."""
    usd = compute_usd_from_krw(
        Decimal("1320000"), exchange_rate=Decimal("1320.5")
    )
    # 1320000 / 1320.5 = 999.6195... → round to 999.62
    assert usd == Decimal("999.62")


# ── Dual display formatter (3 cases) ────────────────────────────


def test_format_period_closing_krw_usd_korean_bank() -> None:
    """format_period_closing_krw_usd → PeriodClosingDisplay (KRW + USD)."""
    pair = CurrencyPair(
        from_currency=CURRENCY_FROM_USD,
        to_currency=CURRENCY_TO_KRW,
        rate=Decimal("1320"),
        rate_source_ko="한국은행",
        rate_as_of="2026-07-25",
    )
    display = format_period_closing_krw_usd(
        Decimal("1320000"), currency_pair=pair
    )
    assert display.amount_krw == Decimal("1320000")
    assert display.amount_usd == Decimal("1000.00")


def test_format_currency_pair_display_ko_korean_bank() -> None:
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


def test_usd_quantum_two_decimals_constant() -> None:
    """USD_QUANTUM = Decimal('0.01') (NUMERIC(18,2) AD-8 SSOT)."""
    assert USD_QUANTUM == Decimal("0.01")
    assert CURRENCY_FROM_USD == "USD"
    assert CURRENCY_TO_KRW == "KRW"