"""packages.cost_engine.core.money — KRW/USD newtype definitions (pure stdlib).

AD-8: BIGINT for KRW integer, NUMERIC(18,2) for USD; float is forbidden on cost paths.
AD-15: snake_case, no Pydantic inside the engine (adapters may use Pydantic, core may not).

Money type implementations live in:
  - apps/api/core/money.py   (API side — may use Pydantic)
  - apps/web/lib/money.ts    (TS side — bigint + decimal.js)
  - packages/cost_engine/core/money.py  (this file — stdlib only)
"""

from decimal import Decimal
from typing import NewType

# KRW wraps int (BIGINT in DB). 1원 precision.
KRW = NewType("KRW", int)

# USD wraps Decimal (NUMERIC(18,2) in DB). Two-decimal precision.
USD = NewType("USD", Decimal)

Money = KRW | USD


def to_krw(value: int | Decimal) -> KRW:
    """Convert to KRW integer (1원 precision). Reject fractional values."""
    if isinstance(value, Decimal):
        if value != int(value):
            raise ValueError(f"USD→KRW requires integer value, got {value}")
        return KRW(int(value))
    return KRW(int(value))


def to_usd(value: Decimal | int) -> USD:
    """Convert to USD with 2-decimal precision (banker's rounding)."""
    return USD(Decimal(value).quantize(Decimal("0.01")))


def format_krw(krw: KRW) -> str:
    """Format KRW with Korean locale: 1,000,000원."""
    return f"{krw:,}원"


def format_usd(usd: USD) -> str:
    """Format USD with US locale: 1,000.00."""
    return f"${usd:,.2f}"
