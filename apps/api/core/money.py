"""apps.api.core.money — AD-8 monetary types for the FastAPI side.

This module re-exports the canonical KRW/USD types from the engine so that
API code uses the same type identity (and `isinstance` / NewType semantics)
as the calculation layer.

Source of truth: `packages.cost_engine.core.money` (pure stdlib).
This file is allowed to import Pydantic / FastAPI if needed in the future
(stub Pydantic helpers live below for that purpose).

AD-8 summary:
  - KRW  ↔ DB `BIGINT`, Python `int`, 1원 precision.
  - USD  ↔ DB `NUMERIC(18,2)`, Python `Decimal`, 2-decimal precision.
  - `float` is forbidden in cost paths.
"""

from __future__ import annotations

from decimal import Decimal
from typing import NewType

# Re-export from the canonical engine. This is the type API surface.
# Importing from `packages.cost_engine.core.money` directly would couple the
# API to engine internals; the re-export keeps the boundary clean (AD-1).
from packages.cost_engine.core.money import (  # noqa: F401 — re-export
    KRW,
    USD,
    Money,
    format_krw,
    format_usd,
    to_krw,
    to_usd,
)

__all__ = [
    "KRW",
    "USD",
    "Money",
    "to_krw",
    "to_usd",
    "format_krw",
    "format_usd",
    "krw_to_usd",
    "usd_to_krw",
]


def krw_to_usd(krw: KRW, rate: Decimal) -> USD:
    """Convert KRW to USD using an injected exchange rate (AD-9).

    The rate is *not* hardcoded — callers must inject it from a market
    data source (Story 6.2 KRW/USD dual display). For tests, use a fixed
    rate to keep results deterministic.

    Args:
        krw: KRW integer value (1원 precision).
        rate: KRW per 1 USD — e.g. Decimal("1300.50") means 1 USD = 1,300.50 KRW.

    Returns:
        USD with 2-decimal precision (banker's rounding).
    """
    if rate <= 0:
        raise ValueError(f"krw_to_usd: rate must be positive, got {rate}")
    usd_value = (Decimal(int(krw)) / rate).quantize(Decimal("0.01"))
    return USD(usd_value)


def usd_to_krw(usd: USD, rate: Decimal) -> KRW:
    """Convert USD to KRW using an injected exchange rate (AD-9).

    Inverse of `krw_to_usd`. Same rate semantics.

    Returns:
        KRW with 1원 precision. Fractional KRW (e.g. 1.7원) is rounded
        using banker's rounding (ROUND_HALF_EVEN) — see Decimal.quantize.
    """
    if rate <= 0:
        raise ValueError(f"usd_to_krw: rate must be positive, got {rate}")
    krw_value = (Decimal(usd) * rate).quantize(Decimal("1"))
    return KRW(int(krw_value))


# Convenience: NewType aliases for Pydantic-typed API responses (AD-15).
# These are the SAME runtime types as KRW/USD — NewType is a static-only marker.
KRWField = NewType("KRWField", int)  # for Pydantic `Field` declarations
USDField = NewType("USDField", Decimal)  # for Pydantic `Field` declarations
