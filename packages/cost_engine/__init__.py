"""bizup cost engine — pure Python hexagonal core.

AD-1:  Hexagonal core. Pure domain logic; ports for inbound/outbound; adapters at boundary.
AD-5:  Engine purity — no I/O, no DB, no clock, no randomness, no global state, no logs.
AD-11: Dependency direction — `core` may NOT import `adapters`. Enforced by import-linter.

This package is the source of truth for the 1원 reconciliation (V8 regression).

Public API (Story 4.1):
  - compute_period_cost(monthly_input, baseline) -> CalcResult (pure kernel)
  - MonthlyInput / CalcResult / Baseline dataclasses
  - KRW / USD NewType monetary primitives

Public API (Story 8.1):
  - derive_budget_period_key / parse_virtual_budget_period_key / validate_scenario_uniqueness / compute_budget_scenario_hash
  - BudgetPeriodKeyParts / BudgetScenario frozen dataclasses
  - ScenarioLimitExceededError / InvalidVirtualBudgetPeriodKeyError typed exceptions
"""

from packages.cost_engine.budget_period_key import (
    BudgetPeriodKeyParts,
    BudgetScenario,
    InvalidVirtualBudgetPeriodKeyError,
    ScenarioLimitExceededError,
    compute_budget_scenario_hash,
    derive_budget_period_key,
    parse_virtual_budget_period_key,
    validate_scenario_uniqueness,
)
from packages.cost_engine.core.money import KRW, USD
from packages.cost_engine.core.period_cost import (
    Baseline,
    compute_period_cost,
)
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput

__all__ = [
    # Story 4.1 pure kernel
    "compute_period_cost",
    "Baseline",
    # I/O dataclasses
    "MonthlyInput",
    "CalcResult",
    # Monetary primitives
    "KRW",
    "USD",
    # Story 8.1 budget period key pure kernel
    "derive_budget_period_key",
    "parse_virtual_budget_period_key",
    "validate_scenario_uniqueness",
    "compute_budget_scenario_hash",
    "BudgetPeriodKeyParts",
    "BudgetScenario",
    "ScenarioLimitExceededError",
    "InvalidVirtualBudgetPeriodKeyError",
]
