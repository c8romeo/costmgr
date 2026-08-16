"""packages.services.m8_budget — Story 8.1 + 8.2 thin serializers layer.

Pure re-export of `packages.cost_engine.budget_period_key` + `packages.cost_engine.budget_variance`
+ thin JSON-safe serializers (`Decimal-as-string`, UUID-as-string).

AD-15 §11 cross-language parity with TS mirror
(`apps/web/lib/m8-budget-scenario.ts` — `deriveBudgetPeriodKeyTS` +
`apps/web/lib/m8-budget-variance.ts` — `computeVarianceTS`).
"""

from packages.services.m8_budget.budget_period_key_serializers import (
    serialize_budget_period_key_parts,
    serialize_budget_scenario,
)
from packages.services.m8_budget.budget_variance_pdf_helpers import (
    serialize_budget_variance_pdf_envelope,
)
from packages.services.m8_budget.budget_variance_serializers import (
    serialize_abcd_disabled_badge,
    serialize_variance_row,
    serialize_variance_total,
)

__all__ = [
    "serialize_budget_scenario",
    "serialize_budget_period_key_parts",
    "serialize_variance_row",
    "serialize_variance_total",
    "serialize_abcd_disabled_badge",
    "serialize_budget_variance_pdf_envelope",
]
