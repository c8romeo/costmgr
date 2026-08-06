"""V8 regression fixtures — 1원 단위 golden output contract.

Story 4.1 — T5 — V8 placeholder contract:
  - V8_INPUT_SCHEMA: JSON schema for the regression V8 input fixture.
  - V8_GOLDEN_OUTPUT_STRUCTURE: 1원 단위 golden output snapshot shape.

These are **placeholder-only**. Story 4.4 will fill the actual golden
fixtures (food-service BOM, 3-product matrix). The contract below
defines the boundary so subsequent fixtures do not have to redesign
the schema.

Used in:
  - Story 4.4: actual fixtures (`regression_v8/fixtures/*.json`).
  - Story 4.4: test runner (`tests/regression_v8/test_regression_v8_fixtures.py`).

Pin-related bumps require running V8 (`docs/STACK_PIN.md`). V8 is
0-tolerance KRW — no rounding tolerance.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Final, TypedDict
from uuid import UUID


# ── V8 Input Schema ─────────────────────────────────────────
class V8Input(TypedDict):
    """V8 regression input fixture — feeds compute_period_cost directly.

    Story 4.1 spec: 1 fixture = 1 monthly_input + 1 baseline → 1
    expected CalcResult. The same structural input is used by
    Story 4.4 to generate test goldens for the 8-stage chain.
    """

    fixture_id: str  # slug, e.g. "food-service-001"
    fixture_version: str  # semver, e.g. "1.0.0"
    tenant_id: UUID
    period_key: str  # YYYY-MM (AD-24)
    monthly_input: dict  # MonthlyInput structural shape
    baseline: dict  # Baseline structural shape


# ── V8 Golden Output Structure ───────────────────────────────
class V8GoldenCost(TypedDict):
    """KRW int field — exact match (no rounding tolerance)."""

    value: int
    # field name is materialized by the test runner (material_cost /
    # labor_cost / overhead_cost / manufacturing_cost / inventory_adjustment).


class V8GoldenOutput(TypedDict):
    """V8 golden output snapshot — byte-identical to CalcResult shape.

    V8 captures the full CalcResult (5 KRW int fields + result_hash + state).
    Every value is exact — 0 KRW tolerance. Per the architecture, V8 is
    the only verification layer that mandates 0-tolerance at the engine
    level (V1-V7 are verification surfaces that eventually feed V8).
    """

    material_cost: int
    labor_cost: int
    overhead_cost: int
    manufacturing_cost: int
    inventory_adjustment: int
    result_hash: str  # 64-char hex SHA-256
    state: str  # "draft" (AD-22 — engine never returns other states)


V8_INPUT_SCHEMA: Final[dict] = {
    "type": "object",
    "required": ["fixture_id", "tenant_id", "period_key", "monthly_input", "baseline"],
    "properties": {
        "fixture_id": {"type": "string", "pattern": "^[a-z0-9-]+$"},
        "fixture_version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+$"},
        "tenant_id": {"type": "string", "format": "uuid"},
        "period_key": {"type": "string", "pattern": r"^\d{4}-(0[1-9]|1[0-2])$"},
        "monthly_input": {
            "type": "object",
            "required": [
                "direct_material_krw",
                "direct_labor_krw",
                "indirect_krw",
                "fte_headcount",
            ],
        },
        "baseline": {
            "type": "object",
            "required": ["fiscal_period", "standard_monthly_hours"],
        },
    },
}

V8_GOLDEN_OUTPUT_STRUCTURE: Final[dict] = {
    "type": "object",
    "required": [
        "material_cost",
        "labor_cost",
        "overhead_cost",
        "manufacturing_cost",
        "inventory_adjustment",
        "result_hash",
        "state",
    ],
    "properties": {
        "material_cost": {"type": "integer", "minimum": 0},
        "labor_cost": {"type": "integer", "minimum": 0},
        "overhead_cost": {"type": "integer", "minimum": 0},
        "manufacturing_cost": {"type": "integer", "minimum": 0},
        "inventory_adjustment": {"type": "integer"},
        "result_hash": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
        "state": {"const": "draft"},
    },
}

# Banker's rounding (ROUND_HALF_EVEN) policy used by Story 4.4 when
# it generates goldens. The constant is here so the policy is visible
# at the contract boundary.
V8_BANKER_ROUNDING: Final[str] = "ROUND_HALF_EVEN"

# Story 4.4 populated 12 golden fixtures (4 industries × 3 baseline shapes).
# Story 5.3 added 2 NEW V3 closing invariant 골든 fixtures (PASS + FAIL).
# See `tests/regression_v8/test_regression_v8_fixtures.py` for CI gate.
# CR 5.3 P18 review patch — V8 + V3 fixture count = 12 + 2 = 14.
V8_FIXTURE_COUNT: Final[int] = 14

# V3 closing invariant fixture count (subset of V8_FIXTURE_COUNT).
# These are the 2 NEW V3 골든 fixtures shipped in Story 5.3:
# - v3_closing_pass_manufacturing.json
# - v3_closing_fail_manufacturing.json
# Distinct from the 12 V8 byte-identical regression fixtures (which use
# the `industry__b-shape` naming convention with monthly_input/golden
# payloads). The V3 fixtures use a different shape (industry +
# ledger_aggregate + expected_v3_*) and live in the same fixtures/
# directory for CI discoverability. CR 5.3 P18 review patch.
V3_FIXTURE_COUNT: Final[int] = 2
V3_FIXTURE_IDS: Final[tuple[str, ...]] = (
    "v3_closing_pass_manufacturing",
    "v3_closing_fail_manufacturing",
)


# ── Helper for Story 4.4 fixture generation ─────────────────
def banker_round_krw(value: Decimal) -> int:
    """Banker's rounding on KRW — same policy as the engine uses.

    Exposed here so Story 4.4 fixture builders can compute the golden
    values identically to how the engine computes them. CR 1.1 lesson
    — TS mirror parity (AD-15) requires identical rounding mode.
    """
    return int(value.quantize(Decimal("1"), rounding="ROUND_HALF_EVEN"))
