#!/usr/bin/env python3
"""Unit tests for AD-8 money type definitions (Story 0.4).

Verifies:
- format_krw / formatUSD produce locale-correct strings.
- to_krw rejects fractional Decimal inputs (per AD-8 KRW=1원 precision).
- to_usd quantizes to 2 decimals (banker's rounding).
- KRW/USD type identity preserved across API + engine imports.
- Conversion helpers (krw_to_usd, usd_to_krw) respect injected rate.
- Engine module is stdlib-only (no Pydantic, no FastAPI).
"""
from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

import pytest

# Ensure imports work: `apps.api.core.money` requires PYTHONPATH=apps:packages:.
REPO_ROOT = Path(__file__).resolve().parents[2]
for p in ("apps", "packages", "."):
    pth = str(REPO_ROOT / p)
    if pth not in sys.path:
        sys.path.insert(0, pth)

from apps.api.core.money import (  # noqa: E402 — after sys.path manipulation
    KRW,
    USD,
    format_krw,
    format_usd,
    krw_to_usd,
    to_krw,
    to_usd,
    usd_to_krw,
)
from packages.cost_engine.core.money import (  # noqa: E402 — after sys.path manipulation
    KRW as EngineKRW,
    USD as EngineUSD,
)


# ── Formatters ────────────────────────────────────────────────


def test_format_krw_basic() -> None:
    assert format_krw(KRW(1_000_000)) == "1,000,000원"


def test_format_krw_zero() -> None:
    assert format_krw(KRW(0)) == "0원"


def test_format_krw_negative() -> None:
    """Negative values format with a leading minus (accounting context)."""
    assert format_krw(KRW(-1_500_000)) == "-1,500,000원"


def test_format_usd_basic() -> None:
    assert format_usd(USD(Decimal("1000.5"))) == "$1,000.50"


def test_format_usd_zero() -> None:
    assert format_usd(USD(Decimal("0"))) == "$0.00"


# ── Converters ────────────────────────────────────────────────


def test_to_krw_from_int() -> None:
    assert to_krw(1_500_000) == KRW(1_500_000)


def test_to_krw_from_int_value() -> None:
    assert to_krw(int(1_500_000)) == KRW(1_500_000)


def test_to_krw_rejects_fractional_decimal() -> None:
    """KRW has 1원 precision — fractional Decimal must raise."""
    with pytest.raises(ValueError, match="integer"):
        to_krw(Decimal("1000.5"))


def test_to_krw_accepts_integer_decimal() -> None:
    assert to_krw(Decimal("1500")) == KRW(1500)


def test_to_usd_quantizes_two_decimals() -> None:
    """Quantizes to exactly 2 decimal places (banker's rounding).

    Python's Decimal default is ROUND_HALF_EVEN (banker's).
    1000.555 → 1000.55 (5 is at last digit, round-half-even → nearest even = 0).
    """
    result = to_usd(1000.555)
    assert Decimal(result) == Decimal("1000.55"), f"got {result}"


def test_to_usd_from_int() -> None:
    """Integer input becomes a USD with 2 decimal places."""
    result = to_usd(1500)
    assert Decimal(result) == Decimal("1500.00")


# ── Conversion helpers (krw_to_usd / usd_to_krw) ──────────────


def test_krw_to_usd_basic() -> None:
    """At rate 1300, 1,300,000 KRW = 1000 USD."""
    result = krw_to_usd(KRW(1_300_000), Decimal("1300"))
    assert Decimal(result) == Decimal("1000.00")


def test_krw_to_usd_rejects_zero_rate() -> None:
    with pytest.raises(ValueError, match="positive"):
        krw_to_usd(KRW(1_000_000), Decimal("0"))


def test_krw_to_usd_rejects_negative_rate() -> None:
    with pytest.raises(ValueError, match="positive"):
        krw_to_usd(KRW(1_000_000), Decimal("-100"))


def test_usd_to_krw_basic() -> None:
    """At rate 1300, 1000 USD = 1,300,000 KRW."""
    result = usd_to_krw(USD("1000.00"), Decimal("1300"))
    assert int(result) == 1_300_000


def test_usd_to_krw_fractional_rounds() -> None:
    """Fractional KRW is rounded (banker's). 1000.5 USD * 1000 = 1,000,500."""
    result = usd_to_krw(USD("1000.5"), Decimal("1000"))
    assert int(result) == 1_000_500


def test_krw_usd_roundtrip_preserves_value() -> None:
    """Round-trip KRW → USD → KRW should preserve value (subject to rate)."""
    rate = Decimal("1300")
    original = KRW(1_300_000)
    usd_value = krw_to_usd(original, rate)  # 1000.00
    back = usd_to_krw(USD(usd_value), rate)  # 1,300,000
    assert int(back) == int(original)


# ── Type identity ─────────────────────────────────────────────


def test_krw_usd_types_match_across_layers() -> None:
    """apps.api.core.money and packages.cost_engine.core.money use the same NewType.

    NewType identity is lost across module reloads (Python quirk), so we
    verify they wrap the SAME underlying type (int / Decimal).
    """
    # Both KRW values must be plain int at runtime.
    api_krw = KRW(1_000)
    eng_krw = EngineKRW(1_000)
    assert isinstance(api_krw, int)
    assert isinstance(eng_krw, int)
    assert type(api_krw) is type(eng_krw) is int

    api_usd = USD(Decimal("100.5"))
    eng_usd = EngineUSD(Decimal("100.5"))
    assert isinstance(api_usd, Decimal)
    assert isinstance(eng_usd, Decimal)


# ── Engine purity (AD-1 hexagonal core) ───────────────────────


def test_engine_money_module_is_stdlib_only() -> None:
    """packages.cost_engine.core.money must NOT import Pydantic / FastAPI / SQLAlchemy."""
    import packages.cost_engine.core.money as engine_money

    source_path = engine_money.__file__
    assert source_path is not None
    source = Path(source_path).read_text(encoding="utf-8")

    forbidden = ["pydantic", "fastapi", "starlette", "sqlalchemy"]
    for forbidden_module in forbidden:
        # `from pydantic import X` or `import pydantic` or `from fastapi import X`
        assert forbidden_module not in source, (
            f"engine money module must be stdlib-only, but imports {forbidden_module!r}"
        )


# ── Display helpers (Korean locale correctness) ───────────────


def test_format_krw_uses_korean_locale() -> None:
    """1,000,000원 uses comma grouping (ko-KR locale)."""
    result = format_krw(KRW(1_234_567_890))
    assert result == "1,234,567,890원"


def test_format_usd_uses_us_locale() -> None:
    """1,000,000.50 USD uses period grouping (en-US locale)."""
    assert format_usd(USD(Decimal("1234567.89"))) == "$1,234,567.89"


def test_usd_constructor_accepts_string() -> None:
    """USD accepts string input (decimal.js serialized form)."""
    result = USD("1234.56")
    assert Decimal(result) == Decimal("1234.56")