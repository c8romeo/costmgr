"""Engine money type sanity tests (AD-8)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.cost_engine.core.money import (
    KRW,
    USD,
    format_krw,
    format_usd,
    to_krw,
    to_usd,
)


@pytest.mark.engine
def test_krw_to_int() -> None:
    assert to_krw(1000) == 1000
    assert isinstance(to_krw(1000), int)


@pytest.mark.engine
def test_krw_rejects_fractional_decimal() -> None:
    with pytest.raises(ValueError):
        to_krw(Decimal("1000.5"))


@pytest.mark.engine
def test_usd_quantizes_to_two_decimals() -> None:
    assert to_usd(Decimal("1000.555")) == Decimal("1000.56")  # banker's rounding via quantize
    assert to_usd(1000) == Decimal("1000.00")


@pytest.mark.engine
def test_format_krw_ko_locale() -> None:
    assert format_krw(KRW(1_000_000)) == "1,000,000원"
    assert format_krw(KRW(0)) == "0원"


@pytest.mark.engine
def test_format_usd_two_decimals() -> None:
    assert format_usd(USD(Decimal("1000.50"))) == "$1,000.50"
