"""packages.services.m8_budget.budget_period_key_serializers — Story 8.1 thin JSON serializers.

Pure-Python JSON-safe serializers for `BudgetScenario` + `BudgetPeriodKeyParts`
frozen dataclasses. Decimal-as-string (AD-8 monetary precision parity) +
UUID-as-string (AD-15 §1 cross-language parity with TS mirror).

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m8_budget` registered in
`tests/architecture/test_api_calls_only_ports.py` (T7 wire).
"""

from __future__ import annotations

from packages.cost_engine.budget_period_key import (
    BudgetPeriodKeyParts,
    BudgetScenario,
)


def serialize_budget_scenario(scenario: BudgetScenario) -> dict[str, str | int]:
    """Serialize `BudgetScenario` → JSON-safe dict (Decimal-as-string + UUID-as-string).

    AD-15 §1 + AD-8 cross-language parity with TS mirror
    `apps/web/lib/m8-budget-scenario.ts:serializeBudgetScenarioTS`.
    """
    return {
        "id": str(scenario.id),
        "tenant_id": str(scenario.tenant_id),
        "period_key": str(scenario.period_key),
        "real_period_key": str(scenario.real_period_key),
        "scenario_index": int(scenario.scenario_index),
        "created_by": str(scenario.created_by),
        "created_at_kst": str(scenario.created_at_kst),
    }


def serialize_budget_period_key_parts(
    parts: BudgetPeriodKeyParts,
) -> dict[str, str | int]:
    """Serialize `BudgetPeriodKeyParts` → JSON-safe dict."""
    return {
        "real_period_key": str(parts.real_period_key),
        "scenario_index": int(parts.scenario_index),
        "scenario_suffix": str(parts.scenario_suffix),
    }


__all__ = [
    "serialize_budget_scenario",
    "serialize_budget_period_key_parts",
]
