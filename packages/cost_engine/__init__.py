"""bizup cost engine — pure Python hexagonal core.

AD-1:  Hexagonal core. Pure domain logic; ports for inbound/outbound; adapters at boundary.
AD-5:  Engine purity — no I/O, no DB, no clock, no randomness, no global state, no logs.
AD-11: Dependency direction — `core` may NOT import `adapters`. Enforced by import-linter.

This package is the source of truth for the 1원 reconciliation (V8 regression).

Public API (Story 4.1):
  - compute_period_cost(monthly_input, baseline) -> CalcResult (pure kernel)
  - MonthlyInput / CalcResult / Baseline dataclasses
  - KRW / USD NewType monetary primitives
"""

from packages.cost_engine.core.money import KRW, USD
from packages.cost_engine.core.period_cost import (
    Baseline,
    compute_period_cost,
)
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput

__all__ = [
    # Pure kernel
    "compute_period_cost",
    "Baseline",
    # I/O dataclasses
    "MonthlyInput",
    "CalcResult",
    # Monetary primitives
    "KRW",
    "USD",
]
