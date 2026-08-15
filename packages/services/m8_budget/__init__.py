"""packages.services.m8_budget — Story 8.1 thin serializers layer.

Pure re-export of `packages.cost_engine.budget_period_key` + thin
JSON-safe serializers (`Decimal-as-string`, UUID-as-string).

AD-15 §11 cross-language parity with TS mirror
(`apps/web/lib/m8-budget-scenario.ts` — `deriveBudgetPeriodKeyTS`).
"""

from packages.services.m8_budget.budget_period_key_serializers import (
    serialize_budget_period_key_parts,
    serialize_budget_scenario,
)

__all__ = [
    "serialize_budget_scenario",
    "serialize_budget_period_key_parts",
]
