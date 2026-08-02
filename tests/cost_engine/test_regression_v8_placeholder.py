"""V8 regression contract placeholder test (Story 4.1 — T5).

This file pins the V8 regression contract shape. Story 4.4 will:
  - Drop actual golden fixtures into `packages/cost_engine/tests/regression_v8/fixtures/`.
  - Write `tests/regression_v8/test_regression_v8_fixtures.py` for the
    real fixture-driven golden comparison.

Until then, this test file enforces:
  1. The V8 contract constants exist (V8_INPUT_SCHEMA, V8_GOLDEN_OUTPUT_STRUCTURE,
     V8_BANKER_ROUNDING, V8_FIXTURE_COUNT).
  2. The schemas are well-formed (required keys, types).
  3. The compute_period_cost output would structurally satisfy V8_GOLDEN_OUTPUT_STRUCTURE.
  4. banker_round_krw() helper matches the engine's rounding policy.

The contract test MUST remain green after Story 4.4 fills the fixtures.
The only thing that should change is `V8_FIXTURE_COUNT > 0`.
"""

from __future__ import annotations

import re
from decimal import Decimal
from uuid import UUID

import pytest

from packages.cost_engine import (
    KRW,
    Baseline,
    MonthlyInput,
    compute_period_cost,
)
from packages.cost_engine.tests.regression_v8 import (
    V8_BANKER_ROUNDING,
    V8_FIXTURE_COUNT,
    V8_GOLDEN_OUTPUT_STRUCTURE,
    V8_INPUT_SCHEMA,
    V8GoldenOutput,
    V8Input,
    banker_round_krw,
)


# ── Contract surface ─────────────────────────────────────────
@pytest.mark.engine
def test_v8_input_schema_required_keys() -> None:
    """V8 input schema must demand fixture_id, tenant_id, period_key, monthly_input, baseline."""
    assert V8_INPUT_SCHEMA["type"] == "object"
    assert set(V8_INPUT_SCHEMA["required"]) == {
        "fixture_id",
        "tenant_id",
        "period_key",
        "monthly_input",
        "baseline",
    }


@pytest.mark.engine
def test_v8_input_schema_period_key_pattern_matches_engine() -> None:
    """V8 period_key regex must match the engine's `_PERIOD_KEY_PATTERN`."""
    pattern = V8_INPUT_SCHEMA["properties"]["period_key"]["pattern"]
    assert pattern == r"^\d{4}-(0[1-9]|1[0-2])$"


@pytest.mark.engine
def test_v8_golden_output_required_keys_match_calcresult() -> None:
    """V8 golden output mirrors CalcResult fields exactly."""
    required = set(V8_GOLDEN_OUTPUT_STRUCTURE["required"])
    assert required == {
        "material_cost",
        "labor_cost",
        "overhead_cost",
        "manufacturing_cost",
        "inventory_adjustment",
        "result_hash",
        "state",
    }


@pytest.mark.engine
def test_v8_golden_output_state_is_draft_only() -> None:
    """V8 only captures `state='draft'` (AD-22 — engine invariant)."""
    assert V8_GOLDEN_OUTPUT_STRUCTURE["properties"]["state"]["const"] == "draft"


@pytest.mark.engine
def test_v8_golden_output_result_hash_format() -> None:
    """V8 result_hash regex must demand 64-char hex."""
    pattern = V8_GOLDEN_OUTPUT_STRUCTURE["properties"]["result_hash"]["pattern"]
    assert pattern == r"^[0-9a-f]{64}$"


@pytest.mark.engine
def test_v8_banker_rounding_policy() -> None:
    """V8 documents banker's rounding as the policy."""
    assert V8_BANKER_ROUNDING == "ROUND_HALF_EVEN"


@pytest.mark.engine
def test_v8_fixture_count_now_12_in_story_4_4() -> None:
    """Story 4.4 fills V8_FIXTURE_COUNT = 12 (4 industries × 3 baseline shapes).

    Story 4.1 baseline was 0 (placeholder-only contract). Story 4.4 writes
    the 12 fixture JSONs into `packages/cost_engine/tests/regression_v8/fixtures/`
    and the constant must reflect that — this is the CR 1.1 forward-lock
    for the V8 fill marker (cr-4-3-lessons F-4 STORY_4_4_FILL_POINT).
    """
    assert V8_FIXTURE_COUNT == 12

    from pathlib import Path

    fixtures_dir = (
        Path(__file__).parents[2]
        / "packages"
        / "cost_engine"
        / "tests"
        / "regression_v8"
        / "fixtures"
    )
    actual_files = sorted(p.name for p in fixtures_dir.glob("*.json"))
    assert len(actual_files) == 12, (
        f"V8 fixtures directory must contain 12 JSON files (4 industries × 3 baseline shapes). "
        f"Found {len(actual_files)}: {actual_files}"
    )


# ── Helper parity with engine ────────────────────────────────
@pytest.mark.engine
def test_banker_round_krw_matches_engine_policy() -> None:
    """The helper's rounding must match the engine's _QUANTIZE_KRW + ROUND_HALF_EVEN.

    Spot-check the four edge cases the engine handles:
      Decimal("0.5") → 0
      Decimal("1.5") → 2
      Decimal("2.5") → 2
      Decimal("2.6") → 3
    """
    assert banker_round_krw(Decimal("0.5")) == 0
    assert banker_round_krw(Decimal("1.5")) == 2
    assert banker_round_krw(Decimal("2.5")) == 2
    assert banker_round_krw(Decimal("2.6")) == 3


# ── Compute output shape matches V8 contract ────────────────
@pytest.mark.engine
def test_compute_period_cost_output_satisfies_v8_contract() -> None:
    """ALU output (compute_period_cost) MUST satisfy V8_GOLDEN_OUTPUT_STRUCTURE.

    This is the most important contract test: any future change to
    CalcResult that would break V8 golden comparison fails here, before
    Story 4.4 even creates a fixture.
    """
    inp = MonthlyInput(
        tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
        period_key="2026-07",
        direct_material_krw=KRW(2_500_000),
        direct_labor_krw=KRW(1_800_000),
        indirect_krw=KRW(600_000),
        fte_headcount=Decimal("1.00"),
    )
    baseline = Baseline(fiscal_period="2026-07", standard_monthly_hours=228)
    result = compute_period_cost(inp, baseline)

    # V8-compatible snapshot
    snap: V8GoldenOutput = {
        "material_cost": result.material_cost,
        "labor_cost": result.labor_cost,
        "overhead_cost": result.overhead_cost,
        "manufacturing_cost": result.manufacturing_cost,
        "inventory_adjustment": result.inventory_adjustment,
        "result_hash": result.result_hash,
        "state": result.state,
    }

    # Type checks
    assert isinstance(snap["material_cost"], int)
    assert isinstance(snap["labor_cost"], int)
    assert isinstance(snap["overhead_cost"], int)
    assert isinstance(snap["manufacturing_cost"], int)
    assert isinstance(snap["inventory_adjustment"], int)
    assert re.match(r"^[0-9a-f]{64}$", snap["result_hash"])
    assert snap["state"] == "draft"

    # V8 manufactured_cost = material + labor + overhead (sum invariant)
    assert snap["manufacturing_cost"] == (
        snap["material_cost"] + snap["labor_cost"] + snap["overhead_cost"]
    )


@pytest.mark.engine
def test_v8_input_typeddict_keys() -> None:
    """V8Input TypedDict must expose the contract fields."""
    sample: V8Input = {
        "fixture_id": "food-service-001",
        "fixture_version": "1.0.0",
        "tenant_id": UUID("11111111-1111-1111-1111-111111111111"),
        "period_key": "2026-07",
        "monthly_input": {},
        "baseline": {},
    }
    assert sample["fixture_id"] == "food-service-001"
    assert sample["period_key"] == "2026-07"
