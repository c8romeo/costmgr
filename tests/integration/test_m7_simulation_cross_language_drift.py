"""tests.integration.test_m7_simulation_cross_language_drift — Story 7.1.

CR 12-5 D-13 cross-language drift detector pattern (AD-15 §11 SSOT
parity with TS mirror `apps/web/lib/m7-simulation-cvp.ts`).

The TS mirror is NOT imported here — that would require a Node test
runner. Instead, this drift detector verifies the Python pure kernel
(`packages.cost_engine.cvp`) exposes the right behavior that the TS
mirror must replicate. The actual TS mirror parity is verified by
`apps/web/__tests__/lib/m7-simulation-cvp.test.ts` (vitest).

This file focuses on:
- Python pure kernel cross-language contract (constants, edge cases,
  quantize behavior) that the TS mirror MUST satisfy.
- Korean SSOT parity (ko-KR.json `cvp_simulation` namespace registered
  — CR 11-4 D-002 + 12-1 P-015).
- No external state mutation (read-only operation).
"""

from __future__ import annotations

import json
import re
from decimal import Decimal
from pathlib import Path

import pytest

from packages.cost_engine import compute_bep as _compute_bep_pub
from packages.cost_engine.cvp import (
    CVPInvalidInputError,
    DEFAULT_OPERATING_RATE,
    DEFAULT_TARGET_PROFIT,
    FIXED_COST_DELTA_PCT_BOUNDS,
    OPERATING_RATE_DELTA_PCT_BOUNDS,
    OPERATING_RATE_MAX,
    OPERATING_RATE_MIN,
    PRICE_DELTA_PCT_BOUNDS,
    apply_delta,
    compute_bep,
    compute_bep_hash,
    simulate_cvp,
)


# ── Cross-language contract: bounds ───────────────────────────
def test_price_delta_pct_bounds_ts_parity():
    """TS mirror PRICE_DELTA_PCT_BOUNDS MUST be [-0.5, 0.5] (ko-KR PRD §F7.1)."""
    assert (Decimal("-0.5"), Decimal("0.5")) == PRICE_DELTA_PCT_BOUNDS


def test_fixed_cost_delta_pct_bounds_ts_parity():
    """TS mirror FIXED_COST_DELTA_PCT_BOUNDS MUST be [-0.3, 0.3]."""
    assert (Decimal("-0.3"), Decimal("0.3")) == FIXED_COST_DELTA_PCT_BOUNDS


def test_operating_rate_bounds_ts_parity():
    """TS mirror OPERATING_RATE_MIN/MAX MUST be 0.5/1.5."""
    assert Decimal("0.5") == OPERATING_RATE_MIN
    assert Decimal("1.5") == OPERATING_RATE_MAX
    assert (Decimal("-0.5"), Decimal("0.5")) == OPERATING_RATE_DELTA_PCT_BOUNDS


def test_default_operating_rate_ts_parity():
    """TS mirror DEFAULT_OPERATING_RATE MUST be 1.0."""
    assert Decimal("1.0") == DEFAULT_OPERATING_RATE


def test_default_target_profit_ts_parity():
    """TS mirror DEFAULT_TARGET_PROFIT MUST be 0."""
    assert Decimal("0") == DEFAULT_TARGET_PROFIT


# ── Cross-language contract: edge cases ───────────────────────
def test_compute_bep_unit_price_equal_variable_cost_raises():
    """TS mirror MUST raise the same error when unit_price == unit_variable_cost."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_bep(
            fixed_cost=Decimal("10000000"),
            unit_variable_cost=Decimal("10000"),
            unit_price=Decimal("10000"),
        )
    assert exc_info.value.code == "unit_price_must_exceed_variable_cost"


def test_compute_bep_negative_fixed_cost_raises():
    """TS mirror MUST raise the same error when fixed_cost < 0."""
    with pytest.raises(CVPInvalidInputError) as exc_info:
        compute_bep(
            fixed_cost=Decimal("-1000"),
            unit_variable_cost=Decimal("6000"),
            unit_price=Decimal("10000"),
        )
    assert exc_info.value.code == "fixed_cost_must_be_non_negative"


def test_apply_delta_baseline_not_mutated():
    """TS mirror `applyDeltaTS` MUST NOT mutate the baseline."""
    from packages.cost_engine.cvp import CVPBaseline, CVPDelta

    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    original_unit_price = baseline.unit_price
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.1"))
    apply_delta(baseline, delta)
    assert baseline.unit_price == original_unit_price


# ── Cross-language contract: determinism ─────────────────────
def test_compute_bep_hash_byte_identical_50x():
    """50회 동일 입력 → 50회 byte-identical sha256 digest (TS mirror contract)."""
    result = compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    expected = compute_bep_hash(result)
    for _ in range(50):
        assert compute_bep_hash(result) == expected


# ── ko-KR.json SSOT registry (CR 11-4 D-002 + 12-1 P-015) ─────
@pytest.mark.parametrize(
    "namespace_key",
    [
        "page_title",
        "page_subtitle",
        "sliders_title",
        "results_title",
        "slider_unit_price",
        "slider_unit_variable_cost",
        "slider_fixed_cost",
        "slider_operating_rate",
        "card_bep_quantity",
        "card_bep_revenue",
        "card_target_profit",
        "card_contribution_margin_ratio",
        "reset_button",
        "baseline_not_found_message",
        "invalid_delta_message",
    ],
)
def test_ko_kr_json_cvp_simulation_namespace_exists(namespace_key: str):
    """ko-KR.json SSOT — `cvp_simulation` namespace MUST contain 15 keys."""
    ko_kr_path = Path(__file__).resolve().parents[2] / "apps" / "web" / "messages" / "ko-KR.json"
    data = json.loads(ko_kr_path.read_text(encoding="utf-8"))
    assert "cvp_simulation" in data, "cvp_simulation namespace missing in ko-KR.json"
    assert namespace_key in data["cvp_simulation"], (
        f"cvp_simulation.{namespace_key} missing in ko-KR.json"
    )


def test_ko_kr_json_no_duplicate_cvp_simulation_namespace():
    """ko-KR.json MUST have exactly ONE `cvp_simulation` namespace (CR 11-4 D-002)."""
    ko_kr_path = Path(__file__).resolve().parents[2] / "apps" / "web" / "messages" / "ko-KR.json"
    raw = ko_kr_path.read_text(encoding="utf-8")
    # Count occurrences of `"cvp_simulation":` (top-level key only).
    matches = re.findall(r'^\s*"cvp_simulation":\s*\{', raw, flags=re.MULTILINE)
    assert len(matches) == 1, (
        f"cvp_simulation namespace declared {len(matches)} times in ko-KR.json "
        f"(CR 11-4 D-002 violation — must be exactly 1)"
    )


# ── No external state mutation (read-only operation) ─────────
def test_simulate_cvp_does_not_mutate_baseline():
    """simulate_cvp MUST NOT mutate baseline (frozen=True + copy semantics)."""
    from packages.cost_engine.cvp import CVPBaseline, CVPDelta

    baseline = CVPBaseline(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    original = (
        baseline.fixed_cost,
        baseline.unit_variable_cost,
        baseline.unit_price,
    )
    delta = CVPDelta(unit_price_delta_pct=Decimal("0.1"))
    simulate_cvp(baseline=baseline, delta=delta)
    assert (baseline.fixed_cost, baseline.unit_variable_cost, baseline.unit_price) == original


def test_compute_bep_no_io_side_effects():
    """compute_bep MUST NOT touch sys.modules, no DB imports."""
    import sys

    sys_modules_before = set(sys.modules.keys())
    compute_bep(
        fixed_cost=Decimal("10000000"),
        unit_variable_cost=Decimal("6000"),
        unit_price=Decimal("10000"),
    )
    new_modules = set(sys.modules.keys()) - sys_modules_before
    forbidden = {"sqlalchemy", "psycopg", "asyncpg", "pydantic", "fastapi"}
    violations = [m for m in new_modules if any(m.startswith(f) for f in forbidden)]
    assert not violations, f"compute_bep pulled in forbidden modules: {violations}"


# ── Cross-language vector parity (Python pure kernel) ─────────
# Vectors that the TS mirror MUST replicate. Tested via Python here;
# TS mirror is exercised by `m7-simulation-cvp.test.ts` (vitest).
@pytest.mark.parametrize(
    ("fixed_cost", "unit_variable_cost", "unit_price", "expected_bep_quantity"),
    [
        (Decimal("10000000"), Decimal("6000"), Decimal("10000"), Decimal("2500.00")),
        (Decimal("5000000"), Decimal("7000"), Decimal("10000"), Decimal("1666.67")),
        (Decimal("0"), Decimal("6000"), Decimal("10000"), Decimal("0.00")),
        (Decimal("3000000"), Decimal("5000"), Decimal("8000"), Decimal("1000.00")),
    ],
)
def test_compute_bep_vector_parity(
    fixed_cost: Decimal,
    unit_variable_cost: Decimal,
    unit_price: Decimal,
    expected_bep_quantity: Decimal,
):
    """Vector parity for TS mirror — Python results MUST match expected."""
    result = compute_bep(
        fixed_cost=fixed_cost,
        unit_variable_cost=unit_variable_cost,
        unit_price=unit_price,
    )
    assert result.bep_quantity == expected_bep_quantity


def test_pub_api_compute_bep_exported():
    """`compute_bep` MUST be exported from packages.cost_engine (cross-language SSOT)."""
    assert _compute_bep_pub is compute_bep
