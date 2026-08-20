"""packages.services.m8_budget.budget_pre_standard_serializers — Story 8.3 thin JSON serializers.

Pure-Python JSON-safe serializers for `PreStandardCost` frozen dataclass
+ `FiscalPeriodSnapshot` ORM row → JSON envelope. Decimal-as-string
(AD-8 monetary precision parity) + UTF-8 Korean SSOT labels (NFR18 ko-KR MVP lock).

CR 11-3 D-2 ALLOWED_SERVICE_SUBMODULES sweep — `m8_budget.budget_pre_standard_serializers`
registered in `tests/architecture/test_api_calls_only_ports.py` (T3 wire).
"""

from __future__ import annotations

from packages.cost_engine.budget_pre_standard import PreStandardCost


def serialize_abcd_disabled_badge_wrapper(
    badge: object,
) -> dict[str, object]:
    """Serialize A×B×C×D 회색 배지 placeholder → JSON-safe dict.

    Thin re-export wrapper around the 8-2 `serialize_abcd_disabled_badge`
    to keep imports flat from `budget_pre_standard_pdf_helpers`.
    """
    # Lazy import to avoid module-load circular (8-2 + 8-3 serializers
    # are siblings under packages.services.m8_budget).
    from packages.services.m8_budget.budget_variance_serializers import (
        serialize_abcd_disabled_badge as _serialize,
    )
    return _serialize(badge)  # type: ignore[arg-type]


def serialize_pre_standard_cost(
    pre_standard_cost: PreStandardCost,
) -> dict[str, object]:
    """Serialize `PreStandardCost` → JSON-safe dict (PRD §F8.3 + AD-15).

    AD-15 §1 cross-language parity with TS mirror
    `apps/web/lib/m8-budget-pre-standard.ts:PreStandardCostSerialized`.

    JSON-safe format:
      - Decimal → str (AD-8 monetary precision, KRW integer)
      - period_key → str (AD-24 virtual `YYYY-MM#B<n>`)
      - scenario_index → int (1차 MVP = 1)
      - engine_type → str (Literal "budget")
    """
    return {
        "material_cost": str(pre_standard_cost.material_cost),
        "labor_cost": str(pre_standard_cost.labor_cost),
        "overhead_cost": str(pre_standard_cost.overhead_cost),
        "manufacturing_cost": str(pre_standard_cost.manufacturing_cost),
        "period_key": str(pre_standard_cost.period_key),
        "scenario_index": int(pre_standard_cost.scenario_index),
        "engine_type": str(pre_standard_cost.engine_type),
    }


def serialize_pre_standard_snapshot(
    pre_standard_cost: PreStandardCost,
    *,
    inventory_adjustment: int,
    result_hash: str,
    state: str,
    created_at_kst: str,
) -> dict[str, object]:
    """Serialize pre-standard snapshot (PRD §F8.3 + AD-22 ledger append-only).

    Composed of:
      - `PreStandardCost` (pure kernel fields)
      - `inventory_adjustment` (BigInteger, default 0)
      - `result_hash` (sha256:64-hex V8 determinism)
      - `state` ('verified' initial, M11 close → 'committed')
      - `created_at_kst` (ISO 8601 KST timestamp)

    AD-15 §1 cross-language parity with TS mirror
    `apps/web/lib/m8-budget-pre-standard.ts:BudgetPreStandardSnapshotSerialized`.
    """
    payload = serialize_pre_standard_cost(pre_standard_cost)
    payload["inventory_adjustment"] = int(inventory_adjustment)
    payload["result_hash"] = str(result_hash)
    payload["state"] = str(state)
    payload["created_at_kst"] = str(created_at_kst)
    return payload


def serialize_pre_standard_pdf_metadata(
    pre_standard_cost: PreStandardCost,
    *,
    period_key: str,
    scenario_index: int,
    generated_at_kst: str,
) -> dict[str, object]:
    """Serialize pre-standard PDF metadata (Epic 6 M5 reuse + §9 #20 format).

    Mirrors `packages.services.m4_inventory.closing_pdf_export.build_closing_pdf_metadata`
    for the pre-standard cost envelope.
    """
    return {
        "report_code": "BUDGET_PRE_STANDARD",
        "title": "예산 사전 표준원가 명세서",
        "period_key": str(period_key),
        "scenario_index": int(scenario_index),
        "material_cost": str(pre_standard_cost.material_cost),
        "labor_cost": str(pre_standard_cost.labor_cost),
        "overhead_cost": str(pre_standard_cost.overhead_cost),
        "manufacturing_cost": str(pre_standard_cost.manufacturing_cost),
        "engine_type": str(pre_standard_cost.engine_type),
        "generated_at_kst": str(generated_at_kst),
        "pdf_format": "A4 portrait + KRW integer + ko-KR only (NFR18)",
    }


__all__ = [
    "serialize_abcd_disabled_badge_wrapper",
    "serialize_pre_standard_cost",
    "serialize_pre_standard_snapshot",
    "serialize_pre_standard_pdf_metadata",
]
