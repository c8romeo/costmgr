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
from packages.cost_engine.budget_variance import (
    ABCD_DISABLED_LABEL,
    ABCD_DISABLED_NOTE,
    ABCD_DISABLED_TOOLTIP,
    SEVERITY_THRESHOLD_CRITICAL_PCT,
    SEVERITY_THRESHOLD_WARNING_PCT,
    VARIANCE_HASH_PREFIX,
    VARIANCE_PCT_QUANTUM,
    ABCDDisabledBadge,
    Variance,
    VarianceRow,
    compute_abcd_disabled_badge,
    compute_variance,
    compute_variance_color,
    compute_variance_hash,
)
from packages.cost_engine.core.money import KRW, USD
from packages.cost_engine.core.period_cost import (
    Baseline,
    compute_period_cost,
)
from packages.cost_engine.cvp import (
    FIXED_COST_DELTA_PCT_BOUNDS,
    OPERATING_RATE_DELTA_PCT_BOUNDS,
    PRICE_DELTA_PCT_BOUNDS,
    BEPResult,
    CVPBaseline,
    CVPDelta,
    CVPInvalidInputError,
    CVPResult,
    TargetProfitResult,
    apply_delta,
    compute_bep,
    compute_bep_hash,
    compute_target_profit,
    simulate_cvp,
)
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput
from packages.cost_engine.projection import (
    PROJECTION_COST_INFLATION_RATE_MAX_PCT,
    PROJECTION_COST_INFLATION_RATE_MIN_PCT,
    PROJECTION_HASH_PREFIX,
    InvalidProjectionMonthError,
    NextMonthProjection,
    ProjectionBaselineNotFoundError,
    ProjectionInputs,
    ProjectionInvalidInputError,
    compute_after_tax_income,
    compute_interest_expense,
    compute_projection_hash,
    project_next_month,
)

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
    # Story 7.1 CVP/BEP pure kernel
    "compute_bep",
    "compute_target_profit",
    "apply_delta",
    "simulate_cvp",
    "compute_bep_hash",
    "BEPResult",
    "TargetProfitResult",
    "CVPBaseline",
    "CVPDelta",
    "CVPResult",
    "CVPInvalidInputError",
    "PRICE_DELTA_PCT_BOUNDS",
    "FIXED_COST_DELTA_PCT_BOUNDS",
    "OPERATING_RATE_DELTA_PCT_BOUNDS",
    # Story 7.2 Next-Month Projection pure kernel
    "compute_interest_expense",
    "compute_after_tax_income",
    "project_next_month",
    "compute_projection_hash",
    "ProjectionInputs",
    "NextMonthProjection",
    "ProjectionInvalidInputError",
    "InvalidProjectionMonthError",
    "ProjectionBaselineNotFoundError",
    "PROJECTION_HASH_PREFIX",
    "PROJECTION_COST_INFLATION_RATE_MIN_PCT",
    "PROJECTION_COST_INFLATION_RATE_MAX_PCT",
    # Story 8.2 Budget Variance pure kernel
    "compute_variance",
    "compute_variance_color",
    "compute_variance_hash",
    "compute_abcd_disabled_badge",
    "Variance",
    "VarianceRow",
    "ABCDDisabledBadge",
    "SEVERITY_THRESHOLD_WARNING_PCT",
    "SEVERITY_THRESHOLD_CRITICAL_PCT",
    "VARIANCE_PCT_QUANTUM",
    "VARIANCE_HASH_PREFIX",
    "ABCD_DISABLED_LABEL",
    "ABCD_DISABLED_TOOLTIP",
    "ABCD_DISABLED_NOTE",
]
