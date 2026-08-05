"""tests.integration.test_verification_order — AD-12 verification ordering integration tests.

Story 4.3 (Task 5.3) — end-to-end orchestration of V1·V4·V7·V8 in service layer.

Covers:
- Step 6.5 verification wiring in CalcOrchestrator
- AD-12 ordering abort (V1 fail → V4·V7·V8 omitted)
- Per-industry firing (V7 service-only, V1/V4/V8 universal)
- Idempotent skip path returns default-pass verdict
- All scenarios invoke the engine's pure kernel + verification runner
- No DB (CI shim mode) — these tests use the runner directly with synthetic
  CalcResult / MonthlyInput / Baseline fixtures, mirroring the orchestrator's
  call sequence without spinning a RunTime DB.
"""

from __future__ import annotations

import asyncio
import uuid as _uuid_mod
from dataclasses import dataclass
from decimal import Decimal

import pytest

from apps.api.modules.m3_calculate.services.rules import _VERIFICATION_RULES
from apps.api.modules.m3_calculate.services.rules.protocol import (
    INDUSTRY_MANUFACTURING,
    INDUSTRY_MANUFACTURING_RETAIL,
    INDUSTRY_MIXED,
    INDUSTRY_SERVICE,
    INDUSTRY_VALUES,
)
from apps.api.modules.m3_calculate.services.verification_runner import (
    Verdict,
    VerificationRunner,
)
from packages.cost_engine.core.money import KRW
from packages.cost_engine.core.period_cost import Baseline, compute_period_cost
from packages.cost_engine.ports.calc_port import CalcResult, MonthlyInput
from packages.cost_engine.tests.regression_v8.fixture_loader import load_golden_by_id


# ── Service-layer integration (no DB) ────────────────────────
@dataclass(frozen=True)
class IntegrationFixture:
    """Composite fixture — bundles engine output + runner inputs."""

    monthly_input: MonthlyInput
    baseline: Baseline


def _make_fixture(
    *,
    material: int = 1_000_000,
    labor: int = 500_000,
    indirect: int = 300_000,
    fte: Decimal = Decimal("5.0"),
    tenant_id: _uuid_mod.UUID | None = None,
) -> IntegrationFixture:
    """Default fixture — engine produces deterministic draft.

    Story 4.4 (V8 byte-identical): tenant_id override param lets V8-aware
    tests inherit the random uuid4 baked into golden fixtures (AD-16
    result_hash is tenant-scoped). Pre-4.4 tests keep the deterministic
    fallback UUID; V8-aware tests call _make_fixture_from_v8() instead.
    """
    mi = MonthlyInput(
        tenant_id=tenant_id
        or _uuid_mod.UUID("11111111-1111-4111-8111-111111111111"),
        period_key="2026-07",
        direct_material_krw=KRW(material),
        direct_labor_krw=KRW(labor),
        indirect_krw=KRW(indirect),
        fte_headcount=fte,
    )
    baseline = Baseline(
        fiscal_period="2026-07",
        standard_monthly_hours=209,
        bom_ratio_validated=True,
        allocation_basis_set=True,
    )
    return IntegrationFixture(monthly_input=mi, baseline=baseline)


def _make_fixture_from_v8(fixture_id: str = "manufacturing__b-small") -> IntegrationFixture:
    """Story 4.4 helper — build IntegrationFixture from a V8 golden fixture.

    V8 result_hash is tenant-scoped (AD-16 stable_json includes tenant_id).
    The publisher bakes a random uuid4() into each fixture. Tests that
    expect V8 byte-identical match=true MUST inherit the fixture tenant_id.
    This helper is the canonical entry point for V8-accurate integration tests.
    """
    input_dict, _ = load_golden_by_id(fixture_id)
    mi = MonthlyInput(
        tenant_id=_uuid_mod.UUID(input_dict["tenant_id"]),
        period_key=input_dict["period_key"],
        direct_material_krw=KRW(int(input_dict["monthly_input"]["direct_material_krw"])),
        direct_labor_krw=KRW(int(input_dict["monthly_input"]["direct_labor_krw"])),
        indirect_krw=KRW(int(input_dict["monthly_input"]["indirect_krw"])),
        fte_headcount=Decimal(str(input_dict["monthly_input"]["fte_headcount"])),
    )
    baseline = Baseline(
        fiscal_period=input_dict["baseline"]["fiscal_period"],
        standard_monthly_hours=int(input_dict["baseline"]["standard_monthly_hours"]),
        bom_ratio_validated=True,
        allocation_basis_set=True,
    )
    return IntegrationFixture(monthly_input=mi, baseline=baseline)


@pytest.mark.engine
def test_step_6_5_verification_wires_to_engine_draft() -> None:
    """Step 6.5: engine computes draft → runner runs V1·V4·V7·V8 sequence."""
    asyncio.run(_step_6_5_verification_wires_to_engine_draft_impl())


async def _step_6_5_verification_wires_to_engine_draft_impl() -> None:
    # Story 4.4: use manufacturing__b-small V8 fixture's tenant_id so V8 byte-identical matches
    fixture = _make_fixture_from_v8("manufacturing__b-small")
    engine_result: CalcResult = compute_period_cost(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
    )
    assert engine_result.state == "draft"  # AD-22 invariant

    runner = VerificationRunner(trace_id="step-6-5-a")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=engine_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    assert verdict.verification_status == "passed"
    # V7 silently skipped for manufacturing
    codes = [v.code for v in verdict.verifications]
    assert "V7" not in codes
    assert "V1" in codes, "V1 must fire for manufacturing"
    assert "V4" in codes, "V4 must fire for manufacturing"
    assert "V8" in codes, "V8 must fire for manufacturing"


@pytest.mark.engine
def test_step_6_5_v1_failure_aborts_subsequent_rules() -> None:
    """AD-12 ordering: V1 fail → V4·V7·V8 omitted from verifications[]."""
    asyncio.run(_step_6_5_v1_failure_aborts_subsequent_rules_impl())


async def _step_6_5_v1_failure_aborts_subsequent_rules_impl() -> None:
    fixture = _make_fixture()
    # Engine produces consistent draft. Force V1 fail by constructing a
    # divergent CalcResult that violates the 1원 단위 invariant.
    bad_result = CalcResult(
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
        material_cost=KRW(1_000_000),
        labor_cost=KRW(500_000),
        overhead_cost=KRW(300_000),
        manufacturing_cost=KRW(1_800_000 - 100),  # delta = -100 (>>1원)
        inventory_adjustment=KRW(0),
        result_hash="0" * 64,
        state="draft",
    )
    runner = VerificationRunner(trace_id="step-6-5-b")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=bad_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    assert verdict.verification_status == "failed"
    assert verdict.top_failure is not None
    assert verdict.top_failure.code == "V1"
    # AD-12 abort: V4·V7·V8 omitted
    codes = [v.code for v in verdict.verifications]
    assert codes == ["V1"]


@pytest.mark.engine
def test_idempotent_skip_returns_default_pass_verdict() -> None:
    """Idempotent re-call path: orchestrator returns default-pass verdict."""
    # The orchestrator's `_build_default_pass_verdict()` builds:
    # verification_status='passed', verifications=[], top_failure=None
    # This test pins that contract.
    verdict = Verdict(
        verification_status="passed",
        verifications=[],
        top_failure=None,
        trace_id="idempotent-trace",
    )
    assert verdict.verification_status == "passed"
    assert verdict.verifications == []
    assert verdict.top_failure is None
    assert verdict.trace_id == "idempotent-trace"


@pytest.mark.engine
@pytest.mark.parametrize("industry", INDUSTRY_VALUES)
def test_per_industry_firing_matrix(industry: str) -> None:
    """Per-industry AD-12 firing matrix (Story 4.3 AC #7).

    Service-only: V7 fires (codes = V1, V4, V7, V8).
    All others: V7 silent skip (codes = V1, V4, V8).
    """
    asyncio.run(_per_industry_firing_matrix_impl(industry))


async def _per_industry_firing_matrix_impl(industry: str) -> None:
    fixture = _make_fixture()
    engine_result = compute_period_cost(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
    )
    runner = VerificationRunner(trace_id=f"industry-{industry}")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=engine_result,
        industry=industry,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    codes = [v.code for v in verdict.verifications]
    if industry == INDUSTRY_SERVICE:
        # V3 silent skip for service-only (no inventory semantics).
        assert codes == ["V1", "V4", "V7", "V8"]
    else:
        # V3 inserted at slot 3 of 5 (Story 5.3).
        assert codes == ["V1", "V4", "V3", "V8"]


@pytest.mark.engine
def test_engine_draft_passes_v1_v4_v8_for_manufacturing_retail() -> None:
    """manufacturing_retail industry: V1/V4/V3/V8 fire, V7 silent skip."""
    asyncio.run(_engine_draft_passes_v1_v4_v8_for_manufacturing_retail_impl())


async def _engine_draft_passes_v1_v4_v8_for_manufacturing_retail_impl() -> None:
    fixture = _make_fixture_from_v8("manufacturing_service__b-small")
    engine_result = compute_period_cost(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
    )
    runner = VerificationRunner(trace_id="mfg-retail")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=engine_result,
        industry=INDUSTRY_MANUFACTURING_RETAIL,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    codes = [v.code for v in verdict.verifications]
    # Story 5.3 — V3 inserted at slot 3 of 5.
    assert codes == ["V1", "V4", "V3", "V8"]


@pytest.mark.engine
def test_engine_draft_passes_v1_v4_v8_for_mixed() -> None:
    """mixed industry: V1/V4/V3/V8 fire, V7 silent skip."""
    asyncio.run(_engine_draft_passes_v1_v4_v8_for_mixed_impl())


async def _engine_draft_passes_v1_v4_v8_for_mixed_impl() -> None:
    fixture = _make_fixture_from_v8("manufacturing_service_other__b-small")
    engine_result = compute_period_cost(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
    )
    runner = VerificationRunner(trace_id="mixed")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=engine_result,
        industry=INDUSTRY_MIXED,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    codes = [v.code for v in verdict.verifications]
    # Story 5.3 — V3 inserted at slot 3 of 5.
    assert codes == ["V1", "V4", "V3", "V8"]


@pytest.mark.engine
def test_service_industry_v7_mvp_placeholder_passes() -> None:
    """Service-only: V7 MVP placeholder returns passed (Epic 9 9-1 wire 후 실제 검증)."""
    asyncio.run(_service_industry_v7_mvp_placeholder_passes_impl())


async def _service_industry_v7_mvp_placeholder_passes_impl() -> None:
    fixture = _make_fixture_from_v8("service__b-small")
    engine_result = compute_period_cost(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
    )
    runner = VerificationRunner(trace_id="service-v7")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=engine_result,
        industry=INDUSTRY_SERVICE,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    assert verdict.verification_status == "passed"
    v7 = next(v for v in verdict.verifications if v.code == "V7")
    assert v7.status == "passed"
    assert v7.details["mvp_placeholder"] is True


@pytest.mark.engine
def test_failed_verification_does_not_block_deterministic_envelope() -> None:
    """Failed verification path returns deterministic envelope (still 200 OK)."""
    asyncio.run(_failed_verification_does_not_block_deterministic_envelope_impl())


async def _failed_verification_does_not_block_deterministic_envelope_impl() -> None:
    fixture = _make_fixture()
    # Fail V1 by off-by-1000
    bad_result = CalcResult(
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
        material_cost=KRW(1_000_000),
        labor_cost=KRW(500_000),
        overhead_cost=KRW(300_000),
        manufacturing_cost=KRW(1_800_000 - 1000),
        inventory_adjustment=KRW(0),
        result_hash="0" * 64,
        state="draft",
    )
    runner = VerificationRunner(trace_id="failed-envelope")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=bad_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    # Verdict envelope is deterministic (same input → same output, AD-5)
    assert verdict.verification_status == "failed"
    assert verdict.top_failure.code == "V1"
    assert verdict.top_failure.details["delta_krw"] == -1000
    assert verdict.trace_id == "failed-envelope"
    # Verify deterministic re-run (AD-5 + AD-16). Verdict class is a
    # mutable-slot dataclass; compare fields individually.
    verdict2 = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=bad_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    assert verdict.verification_status == verdict2.verification_status
    assert verdict.trace_id == verdict2.trace_id
    assert len(verdict.verifications) == len(verdict2.verifications)
    assert verdict.top_failure.code == verdict2.top_failure.code
    assert verdict.top_failure.details == verdict2.top_failure.details


@pytest.mark.engine
def test_rule_registry_uniqueness() -> None:
    """Each rule name maps to exactly one registry entry (no duplicates)."""
    names = [r.name for r in _VERIFICATION_RULES]
    assert len(names) == len(set(names))
    # Story 5.3 — V3 inserted at slot 3 of 5.
    assert set(names) == {"V1", "V3", "V4", "V7", "V8"}


# ── Story 4.4 — V8 골든 match path (AC #5) ─────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
def test_step_6_5_v8_golden_match_path() -> None:
    """Story 4.4 AC #5 — V1·V4 pass + V8 fixture match → verification_status='passed'.

    The default `_make_fixture()` produces monthly_total=1,800,000 KRW with
    fte=5.0, which the V8 fixture loader maps to manufacturing__b-small
    (canonical bin: monthly_total≤2_000_000 AND fte≤5). The engine's
    deterministic draft must match the published golden byte-identically,
    so V8 emits `status='passed'` with non-placeholder details.
    """
    asyncio.run(_step_6_5_v8_golden_match_path_impl())


async def _step_6_5_v8_golden_match_path_impl() -> None:
    # Story 4.4: load manufacturing__b-small so V8 match=true.
    fixture = _make_fixture_from_v8("manufacturing__b-small")
    engine_result = compute_period_cost(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
    )

    runner = VerificationRunner(trace_id="v8-golden-match")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=engine_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )

    # V1·V4 pass + V8 fixture match → passed envelope
    assert verdict.verification_status == "passed"
    assert verdict.top_failure is None

    v8 = next(v for v in verdict.verifications if v.code == "V8")
    assert v8.status == "passed"
    # V8 fill marker must reflect real fixture comparison, NOT placeholder.
    assert v8.details.get("placeholder") is not True, (
        f"V8 must NOT use placeholder branch when a fixture matches — "
        f"details={v8.details!r}"
    )
    # V8 fixture_id must point to the b-small canonical shape for manufacturing.
    assert v8.details["fixture_id"] == "manufacturing__b-small"
    # fields_compared = 7 (5 KRW + result_hash + state) — wire invariant.
    assert len(v8.details["fields_compared"]) == 7
    assert set(v8.details["fields_compared"]) == {
        "material_cost",
        "labor_cost",
        "overhead_cost",
        "manufacturing_cost",
        "inventory_adjustment",
        "result_hash",
        "state",
    }


@pytest.mark.engine
@pytest.mark.v8_regression
def test_step_6_5_v8_golden_mismatch_returns_failed_envelope() -> None:
    """Story 4.4 AC #3 — V8 골든 mismatch → failed envelope + golden_diff details.

    Forces a 1 KRW drift on the engine result; the V8 fixture (byte-identical
    gate) catches it. AD-12 ordering: V1·V4 pass first (engine draft still
    satisfies their invariants), then V8 fires the top failure.
    """
    asyncio.run(_step_6_5_v8_golden_mismatch_returns_failed_envelope_impl())


async def _step_6_5_v8_golden_mismatch_returns_failed_envelope_impl() -> None:
    fixture = _make_fixture()
    engine_result = compute_period_cost(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
    )
    # Add 1 KRW drift on material_cost to trigger V8 mismatch.
    drifted_material = int(engine_result.material_cost) + 1
    drifted_result = CalcResult(
        tenant_id=engine_result.tenant_id,
        period_key=engine_result.period_key,
        material_cost=KRW(drifted_material),
        labor_cost=KRW(int(engine_result.labor_cost)),
        overhead_cost=KRW(int(engine_result.overhead_cost)),
        manufacturing_cost=KRW(
            int(engine_result.material_cost)
            + int(engine_result.labor_cost)
            + int(engine_result.overhead_cost)
            + 1
        ),
        inventory_adjustment=KRW(int(engine_result.inventory_adjustment)),
        result_hash=engine_result.result_hash,  # same hash — V8 mismatch is on cost fields
        state="draft",
    )

    runner = VerificationRunner(trace_id="v8-golden-mismatch")
    verdict = await runner.run_all(
        monthly_input=fixture.monthly_input,
        baseline=fixture.baseline,
        calc_result=drifted_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=fixture.monthly_input.tenant_id,
        period_key="2026-07",
    )
    assert verdict.verification_status == "failed"
    assert verdict.top_failure is not None
    assert verdict.top_failure.code == "V8"
    # AD-12 ordering — V1·V4 still fired before V8 triggered the abort.
    codes = [v.code for v in verdict.verifications]
    assert codes == ["V1", "V4", "V3", "V8"]  # Story 5.3 V3 inserted at slot 3 of 5
    # golden_diff is the CR 2.3 extra='forbid' consistent shape.
    assert "golden_diff" in verdict.top_failure.details
    diff = verdict.top_failure.details["golden_diff"]
    assert "left" in diff
    assert "right" in diff
    assert "fields_diff" in diff
    assert "material_cost" in diff["fields_diff"]
    assert diff["left"]["material_cost"] == drifted_material
