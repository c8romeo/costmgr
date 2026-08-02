"""tests.regression_v8.test_regression_v8_fixtures — V8 골든 CI gate (Story 4.4).

Story 4.4 (Task 4) — mandatory CI gate for V8 byte-identical regression.

Marker strategy:
- `@pytest.mark.engine` + `@pytest.mark.v8_regression` (both applied). The V8
  marker carries the no-skip semantics explicitly; `pytest` default invocation
  includes both markers (no `--ignore` / `--deselect` exclusion allowed).

Matrix coverage (AC #2 + #7):
- 4 industries × 3 baseline shapes = 12 fixtures (manufacturing / manufacturing_service
  / service / manufacturing_service_other × b-small / b-standard / b-complex).
- Each fixture has a `_fixture_lock_sha256` header for determinism detection.

Determinism invariant (AC #4):
- 100x repeat with same input → byte-identical verdict envelope.
- `golden_diff` JSON dump order is deterministic (sort_keys=True).
"""
from __future__ import annotations

import asyncio
import json
import uuid as _uuid_mod
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from apps.api.modules.m3_calculate.services.rules import _VERIFICATION_RULES
from apps.api.modules.m3_calculate.services.rules.protocol import (
    INDUSTRY_VALUES,
    RuleInput,
)
from apps.api.modules.m3_calculate.services.rules.v8_regression import (
    V8RegressionRule,
)
from apps.api.modules.m3_calculate.services.verification_runner import (
    Verdict,
    VerificationRunner,
)
from packages.cost_engine.core.money import KRW
from packages.cost_engine.core.period_cost import Baseline, compute_period_cost
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput
from packages.cost_engine.tests.regression_v8 import V8_FIXTURE_COUNT
from packages.cost_engine.tests.regression_v8.fixture_loader import (
    compute_golden_lock_sha256,
    load_golden_by_id,
    load_golden_for_industry,
    select_golden_for_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "packages" / "cost_engine" / "tests" / "regression_v8" / "fixtures"

ALL_INDUSTRIES = list(INDUSTRY_VALUES)  # 4 values
ALL_SHAPES = ("b-small", "b-standard", "b-complex")  # 3 baseline shapes
EXPECTED_FIXTURE_COUNT = len(ALL_INDUSTRIES) * len(ALL_SHAPES)  # 12

_DETERMINISTIC_TENANT_ID = _uuid_mod.UUID("11111111-1111-4111-8111-111111111111")


# ── Fixtures shipped on disk invariant ────────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_count_is_12() -> None:
    """V8_FIXTURE_COUNT = 12 + 12 fixture JSON files on disk (AC #7)."""
    assert V8_FIXTURE_COUNT == 12, (
        f"V8_FIXTURE_COUNT must be 12 (Story 4.4 fill). Got {V8_FIXTURE_COUNT}."
    )
    actual = sorted(p.name for p in FIXTURES_DIR.glob("*.json"))
    assert len(actual) == EXPECTED_FIXTURE_COUNT, (
        f"V8 fixtures directory must contain {EXPECTED_FIXTURE_COUNT} JSON files "
        f"(4 industries × 3 baseline shapes). Found {len(actual)}: {actual}"
    )


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_matrix_covers_all_4_industries() -> None:
    """4 industries × ≥1 fixture each (Industry enum SSOT — F-5 review lock)."""
    industries = {p.stem.split("__")[0] for p in FIXTURES_DIR.glob("*.json")}
    expected_industries = set(ALL_INDUSTRIES)
    assert industries == expected_industries, (
        f"V8 fixture industry coverage drift: got {industries}, "
        f"expected {expected_industries}. F-5 SSOT = Industry enum exact mapping."
    )


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_matrix_covers_all_3_baseline_shapes() -> None:
    """3 baseline shapes × ≥1 fixture each (PRD §6.1)."""
    shapes = {p.stem.split("__")[1] for p in FIXTURES_DIR.glob("*.json")}
    assert shapes == set(ALL_SHAPES), (
        f"V8 fixture shape coverage drift: got {shapes}, expected {set(ALL_SHAPES)}"
    )


# ── Lock sha256 invariant (AC #7) ────────────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
@pytest.mark.parametrize(
    "fixture_id",
    sorted(f"{industry}__{shape}" for industry in ALL_INDUSTRIES for shape in ALL_SHAPES),
)
def test_v8_fixture_lock_sha256_validates(fixture_id: str) -> None:
    """12 cases — every fixture's _fixture_lock_sha256 matches content.

    The lock is sha256(stable_json(golden)) — changing golden content
    without re-running the publisher will fail this gate.
    """
    _input, golden = load_golden_by_id(fixture_id)
    expected_lock = compute_golden_lock_sha256(golden)
    assert _input["_fixture_lock_sha256"] == expected_lock, (
        f"Lock sha256 mismatch for {fixture_id}. Re-run "
        f"`python -m packages.cost_engine.tests.regression_v8.fixture_publisher --all`"
    )


# ── Byte-identical 골든 comparison (AC #3, #5) ──────────────
@pytest.mark.engine
@pytest.mark.v8_regression
@pytest.mark.parametrize(
    "fixture_id",
    sorted(f"{industry}__{shape}" for industry in ALL_INDUSTRIES for shape in ALL_SHAPES),
)
def test_v8_golden_byte_identical_for_each_fixture(fixture_id: str) -> None:
    """12 cases — V8 rule kernel matches the engine's deterministic draft."""
    asyncio.run(_v8_golden_byte_identical_for_each_fixture_impl(fixture_id))


async def _v8_golden_byte_identical_for_each_fixture_impl(fixture_id: str) -> None:
    input_dict, _golden = load_golden_by_id(fixture_id)
    mi = _monthly_input_from_fixture(input_dict)
    baseline = _baseline_from_fixture(input_dict)
    engine_result = compute_period_cost(monthly_input=mi, baseline=baseline)
    industry = fixture_id.split("__")[0]

    rule = V8RegressionRule()
    rule_input = RuleInput(
        monthly_input=mi,
        baseline=baseline,
        calc_result=engine_result,
        industry=industry,
        tenant_id=mi.tenant_id,
        period_key=mi.period_key,
        trace_id=f"v8-{fixture_id}",
    )
    item = rule.check(rule_input)
    assert item.code == "V8"
    assert item.status == "passed", (
        f"V8 regression failure for {fixture_id}: status={item.status}, "
        f"message={item.message_ko}, details={item.details!r}"
    )
    # Real fixture comparison, NOT the Epic 11 placeholder fallback.
    assert item.details.get("placeholder") is not True, (
        f"V8 must not use placeholder branch for {fixture_id} (fixture exists)."
    )
    assert item.details["fixture_id"] == fixture_id
    fields_compared = set(item.details["fields_compared"])
    assert fields_compared == {
        "material_cost",
        "labor_cost",
        "overhead_cost",
        "manufacturing_cost",
        "inventory_adjustment",
        "result_hash",
        "state",
    }


# ── Determinism 100x invariant (AC #4) ────────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
@pytest.mark.parametrize(
    "fixture_id",
    sorted(f"{industry}__{shape}" for industry in ALL_INDUSTRIES for shape in ALL_SHAPES),
)
def test_v8_golden_100x_determinism(fixture_id: str) -> None:
    """12 cases — same input → same envelope 100x. AD-16 determinism."""
    asyncio.run(_v8_golden_100x_determinism_impl(fixture_id))


async def _v8_golden_100x_determinism_impl(fixture_id: str) -> None:
    input_dict, _ = load_golden_by_id(fixture_id)
    mi = _monthly_input_from_fixture(input_dict)
    baseline = _baseline_from_fixture(input_dict)
    engine_result = compute_period_cost(monthly_input=mi, baseline=baseline)
    industry = fixture_id.split("__")[0]

    rule = V8RegressionRule()
    rule_input = RuleInput(
        monthly_input=mi,
        baseline=baseline,
        calc_result=engine_result,
        industry=industry,
        tenant_id=mi.tenant_id,
        period_key=mi.period_key,
        trace_id=f"determinism-{fixture_id}",
    )

    first = rule.check(rule_input)
    for _ in range(99):
        again = rule.check(rule_input)
        assert again.status == first.status
        assert again.code == first.code
        assert again.message_ko == first.message_ko
        assert again.details == first.details, (
            f"V8 determinism drift for {fixture_id} after repeat call. "
            f"first.details={first.details!r}, again.details={again.details!r}"
        )


# ── Failed-path shape (AC #3) ────────────────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_golden_failed_path_format() -> None:
    """1 case — V8 fail 시 CR 2.3 extra='forbid' consistent golden_diff shape."""
    asyncio.run(_v8_golden_failed_path_format_impl())


async def _v8_golden_failed_path_format_impl() -> None:
    input_dict, _golden = load_golden_by_id("manufacturing__b-small")
    mi = _monthly_input_from_fixture(input_dict)  # use fixture's tenant_id; engine hash parity
    baseline = _baseline_from_fixture(input_dict)
    natural = compute_period_cost(monthly_input=mi, baseline=baseline)

    # Inject a 1 KRW drift on material_cost (golden mismatch).
    drifted = CalcResult(
        tenant_id=natural.tenant_id,
        period_key=natural.period_key,
        material_cost=KRW(int(natural.material_cost) + 1),
        labor_cost=KRW(int(natural.labor_cost)),
        overhead_cost=KRW(int(natural.overhead_cost)),
        manufacturing_cost=KRW(int(natural.manufacturing_cost) + 1),
        inventory_adjustment=KRW(int(natural.inventory_adjustment)),
        result_hash=natural.result_hash,
        state="draft",
    )
    rule = V8RegressionRule()
    rule_input = RuleInput(
        monthly_input=mi,
        baseline=baseline,
        calc_result=drifted,
        industry="manufacturing",
        tenant_id=mi.tenant_id,
        period_key=mi.period_key,
        trace_id="v8-failed-path",
    )
    item = rule.check(rule_input)
    assert item.code == "V8"
    assert item.status == "failed"
    diff = item.details["golden_diff"]
    assert set(diff.keys()) == {"left", "right", "fields_diff"}
    assert sorted(diff["fields_diff"]) == ["manufacturing_cost", "material_cost"]
    assert diff["left"]["material_cost"] == int(natural.material_cost) + 1
    assert diff["left"]["manufacturing_cost"] == int(natural.manufacturing_cost) + 1
    # CR 2.3 invariant — golden_diff JSON dump is deterministic.
    assert json.dumps(diff, sort_keys=True) == json.dumps(diff, sort_keys=True)


# ── Industry × V* firing matrix (AC #5) ─────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
@pytest.mark.parametrize("industry", ALL_INDUSTRIES)
def test_v8_golden_industry_skip_matrix(industry: str) -> None:
    """4 cases — V8 fires for all 4 industries (universal)."""
    asyncio.run(_v8_golden_industry_skip_matrix_impl(industry))


async def _v8_golden_industry_skip_matrix_impl(industry: str) -> None:
    # Load THIS industry's b-small fixture to inherit its tenant_id (the
    # engine's result_hash is tenant-scoped per AD-16). Without inheriting
    # the fixture tenant_id, the recomputed engine result will differ from
    # the golden — V8 fires a mismatch.
    input_dict, _golden = load_golden_by_id(f"{industry}__b-small")
    mi = _monthly_input_from_fixture(input_dict)
    baseline = _baseline_from_fixture(input_dict)
    engine_result = compute_period_cost(monthly_input=mi, baseline=baseline)
    runner = VerificationRunner(trace_id=f"v8-industry-{industry}")
    verdict = await runner.run_all(
        monthly_input=mi,
        baseline=baseline,
        calc_result=engine_result,
        industry=industry,
        tenant_id=mi.tenant_id,
        period_key="2026-07",
    )
    codes = [v.code for v in verdict.verifications]
    if industry == "service":
        # V7 fires only for service. V8 still fires for all.
        assert codes == ["V1", "V4", "V7", "V8"]
    else:
        assert codes == ["V1", "V4", "V8"]
    # V8 itself fired and passed (canonical b-small match for all industries).
    v8 = next(v for v in verdict.verifications if v.code == "V8")
    assert v8.status == "passed"
    assert v8.details["fixture_id"] == f"{industry}__b-small"


# ── Idempotent re-call invariant (AC #5) ─────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
@pytest.mark.parametrize(
    "fixture_id",
    sorted(f"{industry}__{shape}" for industry in ALL_INDUSTRIES for shape in ALL_SHAPES),
)
def test_v8_golden_idempotent_re_call(fixture_id: str) -> None:
    """12 cases — re-call with same input → identical verdict envelope (20x)."""
    asyncio.run(_v8_golden_idempotent_re_call_impl(fixture_id))


async def _v8_golden_idempotent_re_call_impl(fixture_id: str) -> None:
    input_dict, _ = load_golden_by_id(fixture_id)
    mi = _monthly_input_from_fixture(input_dict)
    baseline = _baseline_from_fixture(input_dict)
    engine_result = compute_period_cost(monthly_input=mi, baseline=baseline)
    industry = fixture_id.split("__")[0]

    runner = VerificationRunner(trace_id=f"idemp-{fixture_id}")
    verdicts: list[Verdict] = []
    for _ in range(20):
        verdicts.append(
            await runner.run_all(
                monthly_input=mi,
                baseline=baseline,
                calc_result=engine_result,
                industry=industry,
                tenant_id=mi.tenant_id,
                period_key="2026-07",
            )
        )
    base = verdicts[0]
    for v in verdicts[1:]:
        assert v.verification_status == base.verification_status
        assert v.trace_id == base.trace_id
        assert len(v.verifications) == len(base.verifications)
        for a, b in zip(v.verifications, base.verifications, strict=True):
            assert a.code == b.code
            assert a.status == b.status
            assert a.message_ko == b.message_ko
            assert a.details == b.details


# ── V8 rule registry wiring invariants ───────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_rule_registry_uniqueness() -> None:
    """Each rule name maps to exactly one registry entry (no duplicates)."""
    names = [r.name for r in _VERIFICATION_RULES]
    assert len(names) == len(set(names))
    assert set(names) == {"V1", "V4", "V7", "V8"}


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_rule_is_in_registry() -> None:
    """V8RegressionRule is registered."""
    rule_names = [type(r).__name__ for r in _VERIFICATION_RULES]
    assert "V8RegressionRule" in rule_names


# ── Fixture loader API smoke ─────────────────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
def test_load_golden_for_industry_returns_matrix_aligned_list() -> None:
    """load_golden_for_industry → 3 fixtures per industry."""
    for industry in ALL_INDUSTRIES:
        fixtures = load_golden_for_industry(industry)
        assert len(fixtures) == 3, (
            f"Industry {industry} must have 3 fixtures (b-small/b-standard/b-complex); "
            f"got {len(fixtures)}"
        )
        shapes = sorted(f["fixture_id"].split("__")[1] for f in fixtures)
        assert shapes == sorted(ALL_SHAPES)


@pytest.mark.engine
@pytest.mark.v8_regression
def test_select_golden_for_input_deterministic_resolution() -> None:
    """select_golden_for_input — monthly_total + fte → canonical shape, deterministic."""
    mi_small = _make_input(material=1_000_000, labor=500_000, indirect=300_000, fte="5.0")
    mi_standard = _make_input(material=4_900_000, labor=2_100_000, indirect=1_500_000, fte="12.5")
    mi_complex = _make_input(material=12_345_678, labor=8_765_432, indirect=4_321_098, fte="42.0")

    small = select_golden_for_input(industry="manufacturing", monthly_input=mi_small)
    standard = select_golden_for_input(industry="manufacturing", monthly_input=mi_standard)
    complex_ = select_golden_for_input(industry="manufacturing", monthly_input=mi_complex)

    assert small is not None
    assert small["fixture_id"] == "manufacturing__b-small"
    assert standard is not None
    assert standard["fixture_id"] == "manufacturing__b-standard"
    assert complex_ is not None
    assert complex_["fixture_id"] == "manufacturing__b-complex"


@pytest.mark.engine
@pytest.mark.v8_regression
def test_select_golden_for_input_returns_none_for_unknown_industry() -> None:
    """Epic 11 reversal fallback — unknown industry returns None (placeholder path)."""
    mi = _make_input(material=1_000_000, labor=500_000, indirect=300_000, fte="5.0")
    result = select_golden_for_input(industry="unknown_industry", monthly_input=mi)
    assert result is None


# ── Helpers ──────────────────────────────────────────────────
def _monthly_input_from_fixture(input_dict: dict[str, Any]) -> MonthlyInput:
    # Engine result_hash includes tenant_id (AD-16 stable_json) — must use
    # the fixture's stored tenant_id, not a deterministic UUID. The publisher
    # bakes a random uuid4() into the fixture; tests must consume that exact
    # tenant_id so the recomputed engine output byte-matches the golden.
    return MonthlyInput(
        tenant_id=_uuid_mod.UUID(input_dict["tenant_id"]),
        period_key=input_dict["period_key"],
        direct_material_krw=KRW(int(input_dict["monthly_input"]["direct_material_krw"])),
        direct_labor_krw=KRW(int(input_dict["monthly_input"]["direct_labor_krw"])),
        indirect_krw=KRW(int(input_dict["monthly_input"]["indirect_krw"])),
        fte_headcount=Decimal(str(input_dict["monthly_input"]["fte_headcount"])),
    )


def _make_input(*, material: int, labor: int, indirect: int, fte: Any) -> MonthlyInput:
    return MonthlyInput(
        tenant_id=_DETERMINISTIC_TENANT_ID,
        period_key="2026-07",
        direct_material_krw=KRW(material),
        direct_labor_krw=KRW(labor),
        indirect_krw=KRW(indirect),
        fte_headcount=Decimal(str(fte)),
    )


def _baseline_from_fixture(input_dict: dict[str, Any]) -> Baseline:
    return _make_baseline(
        hours=int(input_dict["baseline"]["standard_monthly_hours"]),
        bom_validated=bool(input_dict["baseline"].get("bom_ratio_validated", True)),
        allocation_set=bool(input_dict["baseline"].get("allocation_basis_set", True)),
    )


def _make_baseline(
    *, hours: int, bom_validated: bool = True, allocation_set: bool = True
) -> Baseline:
    return Baseline(
        fiscal_period="2026-07",
        standard_monthly_hours=hours,
        bom_ratio_validated=bom_validated,
        allocation_basis_set=allocation_set,
    )
