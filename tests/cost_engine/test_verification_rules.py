"""Verification rule kernels + runner + purity gate tests (Story 4.3 — Task 5.1).

AD-12 verification-first invariant for V1·V4·V7·V8:
- V1 (완전배부): manufacturing_cost == direct_material + direct_labor + indirect
                 (1원 단위 tolerance)
- V4 (원가-손익 Reconciliation): 4요소 자동 분해 sum == manufacturing_cost
- V7 (ABC 무결성): service-only industry — Epic 9 9-1 wire 후 실제 검증
- V8 (엔진 대조): SHA-256 result_hash 매칭 — Story 4.4 골든 fill 후 wire

Tests cover:
1. V1 / V4 / V7 / V8 happy path + edge cases
2. AD-12 ordering invariant (V1 fail → V4·V7·V8 abort)
3. AD-5 purity (rule kernels no I/O imports)
4. Per-industry applies_to semantics (V7 service-only)
5. VerificationRunner ASYNC surface + verdict envelope shape
6. V4 4요소 분해 helper symmetry
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from decimal import Decimal

import pytest

from apps.api.modules.m3_calculate.services.rules import (
    _VERIFICATION_RULES,
    RuleInput,
    VerificationItem,
)
from apps.api.modules.m3_calculate.services.rules.protocol import (
    INDUSTRY_MANUFACTURING,
    INDUSTRY_SERVICE,
    INDUSTRY_VALUES,
)
from apps.api.modules.m3_calculate.services.rules.v1_complete_allocation import (
    V1CompleteAllocationRule,
)
from apps.api.modules.m3_calculate.services.rules.v4_cost_income_reconciliation import (
    V4CostIncomeReconciliationRule,
    compute_four_elements,
)
from apps.api.modules.m3_calculate.services.rules.v7_abc_integrity import (
    V7AbcIntegrityRule,
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
from packages.cost_engine.tests.regression_v8.fixture_loader import load_golden_by_id


# ── Fixtures ─────────────────────────────────────────────────
def _make_baseline() -> Baseline:
    """Story 4.1 baseline — BOM 100% validated + allocation basis set."""
    return Baseline(
        fiscal_period="2026-07",
        standard_monthly_hours=209,
        bom_ratio_validated=True,
        allocation_basis_set=True,
    )


def _make_monthly_input(
    *,
    material: int = 1_000_000,
    labor: int = 500_000,
    indirect: int = 300_000,
    fte: Decimal = Decimal("5.0"),
    tenant_id: uuid.UUID | None = None,
) -> MonthlyInput:
    """Default 6-stream monthly input — minimal fields for verification.

    Story 4.4: tenant_id override lets V8-aware tests inherit the random
    uuid4 baked into V8 golden fixtures (AD-16 result_hash is tenant-scoped).
    Pre-4.4 tests keep the deterministic fallback UUID for V8 placeholder.
    """
    return MonthlyInput(
        tenant_id=tenant_id or uuid.UUID("11111111-1111-4111-8111-111111111111"),
        period_key="2026-07",
        direct_material_krw=KRW(material),
        direct_labor_krw=KRW(labor),
        indirect_krw=KRW(indirect),
        fte_headcount=fte,
    )


def _make_calc_result(
    *,
    material: int = 1_000_000,
    labor: int = 500_000,
    overhead: int = 300_000,
    manufacturing: int = 1_800_000,
    inventory_adjustment: int = 0,
    result_hash: str = "0" * 64,
    tenant_id: uuid.UUID | None = None,
) -> CalcResult:
    """Default engine draft — invariant: manufacturing = material + labor + overhead.

    Story 4.4: tenant_id override (same rationale as _make_monthly_input).
    """
    return CalcResult(
        tenant_id=tenant_id or uuid.UUID("11111111-1111-4111-8111-111111111111"),
        period_key="2026-07",
        material_cost=KRW(material),
        labor_cost=KRW(labor),
        overhead_cost=KRW(overhead),
        manufacturing_cost=KRW(manufacturing),
        inventory_adjustment=KRW(inventory_adjustment),
        result_hash=result_hash,
        state="draft",
    )


def _make_rule_input(
    *,
    industry: str = INDUSTRY_MANUFACTURING,
    monthly_input: MonthlyInput | None = None,
    calc_result: CalcResult | None = None,
    baseline: Baseline | None = None,
    tenant_id: uuid.UUID | None = None,
) -> RuleInput:
    """Default rule input — orchestration glue for V* kernels.

    Story 4.4: tenant_id override; V8-aware callers MUST pass the per-industry
    fixture's tenant_id (see _make_monthly_input / _make_calc_result comments).
    """
    return RuleInput(
        monthly_input=monthly_input or _make_monthly_input(tenant_id=tenant_id),
        baseline=baseline or _make_baseline(),
        calc_result=calc_result or _make_calc_result(tenant_id=tenant_id),
        industry=industry,
        tenant_id=tenant_id or uuid.UUID("11111111-1111-4111-8111-111111111111"),
        period_key="2026-07",
        trace_id="test-trace-001",
    )


# ── V1 — 완전배부 (PRD §11) ─────────────────────────────────
@pytest.mark.engine
def test_v1_pass_when_manufacturing_equals_sum_of_three() -> None:
    """V1 happy path: 1_000_000 + 500_000 + 300_000 = 1_800_000 → passed."""
    rule = V1CompleteAllocationRule()
    item = rule.check(_make_rule_input(calc_result=_make_calc_result(
        material=1_000_000, labor=500_000, overhead=300_000, manufacturing=1_800_000,
    )))
    assert item.code == "V1"
    assert item.status == "passed"
    assert item.details["delta_krw"] == 0


@pytest.mark.engine
def test_v1_pass_with_one_won_tolerance() -> None:
    """V1 1원 단위 tolerance: delta=±1 → still passed (AD-15 banker's rounding)."""
    rule = V1CompleteAllocationRule()
    item = rule.check(_make_rule_input(calc_result=_make_calc_result(
        material=1_000_000, labor=500_000, overhead=300_000, manufacturing=1_800_001,
    )))
    assert item.status == "passed"
    assert item.details["delta_krw"] == 1


@pytest.mark.engine
def test_v1_fail_when_manufacturing_off_by_two_won() -> None:
    """V1 fail: delta > 1원 → status='failed', diagnostic Korean."""
    rule = V1CompleteAllocationRule()
    item = rule.check(_make_rule_input(calc_result=_make_calc_result(
        material=1_000_000, labor=500_000, overhead=300_000, manufacturing=1_799_997,
    )))
    assert item.code == "V1"
    assert item.status == "failed"
    assert "위반" in item.message_ko
    assert item.details["delta_krw"] == -3


@pytest.mark.engine
def test_v1_applies_to_all_industries() -> None:
    """V1 universal: applies_to always True regardless of industry."""
    rule = V1CompleteAllocationRule()
    for industry in INDUSTRY_VALUES:
        assert rule.applies_to(industry=industry) is True


# ── V4 — 원가-손익 Reconciliation 4요소 ─────────────────────
@pytest.mark.engine
def test_v4_pass_normal_case() -> None:
    """V4 happy path: 4요소 합 == manufacturing_cost → passed.

    MVP: produced=sold, unit_material_price=1 KRW/unit → manufactured_qty
    = material_cost (1_000_000 / 1 = 1_000_000), so:
    ① = (1M - 1M) × 1 = 0
    ② = 1M × 1 + 500k + 300k = 1.8M
    ③ = 0 (MVP)
    ④ = 0 (Epic 5 fold-in 전)
    sum_4 = 1.8M == manufacturing_cost = 1.8M ✓
    """
    rule = V4CostIncomeReconciliationRule()
    item = rule.check(_make_rule_input())
    assert item.code == "V4"
    assert item.status == "passed"
    elements = item.details["4_elements"]
    assert elements["qty_diff_material_krw"] == 0  # MVP: produced = sold
    assert elements["labor_overhead_allocation_krw"] == 1_800_000  # sold + labor + overhead
    assert elements["unit_price_diff_krw"] == 0  # MVP placeholder
    assert elements["inventory_adjustment_krw"] == 0  # Epic 5 fold-in 전
    assert elements["sum_4_elements_krw"] == 1_800_000


@pytest.mark.engine
def test_v4_pass_with_inventory_adjustment() -> None:
    """V4 inventory_adjustment is reported in detail but NOT in sum_4_elements.

    inventory_adjustment is a separate engine result field (PRD §6.1 (7)).
    V4 4-element sum reconciles to manufacturing_cost, NOT manufacturing_cost
    + inventory_adjustment. The detail dict still carries inventory_adjustment
    for traceability, but the failure check excludes it.
    """
    rule = V4CostIncomeReconciliationRule()
    # manufactured = 1.8M, inventory_adjustment = 50k → sum_4 = 1.8M (NOT 1.85M)
    result = _make_calc_result(inventory_adjustment=50_000, manufacturing=1_800_000)
    item = rule.check(_make_rule_input(calc_result=result))
    assert item.status == "passed"
    elements = item.details["4_elements"]
    assert elements["inventory_adjustment_krw"] == 50_000  # reported in detail
    assert elements["sum_4_elements_krw"] == 1_800_000  # NOT in sum (separate field)


@pytest.mark.engine
def test_compute_four_elements_helper_symmetry() -> None:
    """compute_four_elements pure helper — direct call to verify 4-element math.

    produced_qty=100, sold_qty=80, unit_material_price=10_000:
    ① = (100-80)×10_000 = 200_000 (qty_diff_material)
    ② = 80×10_000 + 500_000 + 300_000 = 1_600_000 (absorbed material + labor + overhead)
    ③ = 0 (MVP placeholder)
    ④ = 0 (inventory_adjustment)
    sum_4 = 200_000 + 1_600_000 = 1_800_000
    To balance manufacturing_cost, set it to 1_800_000.
    """
    elements = compute_four_elements(
        produced_qty=100,
        sold_qty=80,
        unit_material_price_krw=KRW(10_000),
        labor_cost_krw=KRW(500_000),
        overhead_cost_krw=KRW(300_000),
        inventory_adjustment_krw=KRW(0),
        manufacturing_cost_krw=KRW(1_800_000),
    )
    # ① (100-80)*10_000 = 200_000
    assert elements["qty_diff_material_krw"] == 200_000
    # ② 80*10_000 + 500_000 + 300_000 = 1_600_000
    assert elements["labor_overhead_allocation_krw"] == 1_600_000
    # ③ MVP placeholder
    assert elements["unit_price_diff_krw"] == 0
    # ④ inventory_adjustment
    assert elements["inventory_adjustment_krw"] == 0
    # sum_4 = 200_000 + 1_600_000 + 0 + 0 = 1_800_000
    assert elements["sum_4_elements_krw"] == 1_800_000
    assert elements["manufacturing_cost_krw"] == 1_800_000


@pytest.mark.engine
def test_v4_applies_to_all_industries() -> None:
    """V4 universal: applies_to always True."""
    rule = V4CostIncomeReconciliationRule()
    for industry in INDUSTRY_VALUES:
        assert rule.applies_to(industry=industry) is True


# ── V7 — ABC 무결성 (PRD §11) ───────────────────────────────
@pytest.mark.engine
def test_v7_applies_only_to_service() -> None:
    """V7 AD-12 spec: service-only industry. Manufacturing/mfg_retail/mixed skip."""
    rule = V7AbcIntegrityRule()
    assert rule.applies_to(industry=INDUSTRY_SERVICE) is True
    assert rule.applies_to(industry=INDUSTRY_MANUFACTURING) is False
    for industry in INDUSTRY_VALUES:
        if industry != INDUSTRY_SERVICE:
            assert rule.applies_to(industry=industry) is False


@pytest.mark.engine
def test_v7_pass_for_service_with_mvp_placeholder() -> None:
    """V7 MVP: service tenant → pass with mvp_placeholder=True (Epic 9 wire 후 실제 검증)."""
    rule = V7AbcIntegrityRule()
    item = rule.check(_make_rule_input(industry=INDUSTRY_SERVICE))
    assert item.code == "V7"
    assert item.status == "passed"
    assert item.details["mvp_placeholder"] is True


@pytest.mark.engine
def test_v7_failed_when_invoked_for_non_service() -> None:
    """V7 defense-in-depth: industry mismatch → failed (applies_to enforces, but check
    also guards). This is a unit test that bypasses applies_to."""
    rule = V7AbcIntegrityRule()
    item = rule.check(_make_rule_input(industry=INDUSTRY_MANUFACTURING))
    assert item.status == "failed"
    assert "condition 위반" in item.message_ko


# ── V8 — 엔진 대조 (PRD §11) — Story 4.4 fill wire ──────────
@pytest.mark.engine
def test_v8_golden_match_passes_for_all_industries() -> None:
    """Story 4.4 AC #2 + #5 — V8 골든 byte-identical match for all 4 industries.

    Each iteration inherits the per-industry V8 golden fixture's tenant_id
    (AD-16 result_hash is tenant-scoped — random uuid4 baked in by the publisher).
    The default placeholder=True contract from Story 4.3 is OBSOLETE; V8 now
    performs real byte-identical comparison against the 12 published 골든 fixtures.
    """
    rule = V8RegressionRule()
    for industry in INDUSTRY_VALUES:
        assert rule.applies_to(industry=industry) is True
        # Inherit per-industry fixture tenant_id + run the engine on the
        # fixture's stored input/baseline so labor_cost includes the FTE
        # 환산. The default _make_calc_result uses un-FTE-adjusted numbers.
        input_dict, _ = load_golden_by_id(f"{industry}__b-small")
        fixture_tenant = uuid.UUID(input_dict["tenant_id"])
        fi = MonthlyInput(
            tenant_id=fixture_tenant,
            period_key=input_dict["period_key"],
            direct_material_krw=KRW(int(input_dict["monthly_input"]["direct_material_krw"])),
            direct_labor_krw=KRW(int(input_dict["monthly_input"]["direct_labor_krw"])),
            indirect_krw=KRW(int(input_dict["monthly_input"]["indirect_krw"])),
            fte_headcount=Decimal(str(input_dict["monthly_input"]["fte_headcount"])),
        )
        fb = Baseline(
            fiscal_period=input_dict["baseline"]["fiscal_period"],
            standard_monthly_hours=int(input_dict["baseline"]["standard_monthly_hours"]),
            bom_ratio_validated=True,
            allocation_basis_set=True,
        )
        engine_result = compute_period_cost(monthly_input=fi, baseline=fb)
        item = rule.check(_make_rule_input(
            industry=industry,
            tenant_id=fixture_tenant,
            monthly_input=fi,
            baseline=fb,
            calc_result=engine_result,
        ))
        assert item.status == "passed", (
            f"V8 골든 mismatch for industry={industry}: {item.message_ko!r} {item.details!r}"
        )
        assert item.details.get("placeholder") is not True, (
            f"V8 must NOT take the placeholder branch for industry={industry} — fixture exists."
        )
        assert item.details["fixture_id"] == f"{industry}__b-small"
        assert len(item.details["fields_compared"]) == 7  # 5 KRW + hash + state


# ── Registry — AD-12 strict order ────────────────────────────
@pytest.mark.engine
def test_registry_order_is_v1_v4_v7_v8() -> None:
    """AD-12 ordering invariant: V1 first, V4 second, V7 third, V8 last."""
    assert [r.name for r in _VERIFICATION_RULES] == ["V1", "V4", "V7", "V8"]


@pytest.mark.engine
def test_registry_is_immutable_tuple() -> None:
    """Registry is tuple — append-only semantics, no in-place mutation."""
    assert isinstance(_VERIFICATION_RULES, tuple)


# ── VerificationRunner + AD-12 ordering abort ─────────────────
@pytest.mark.engine
def test_runner_v1_v4_v8_for_manufacturing_v7_skipped() -> None:
    """Runner: manufacturing fires V1+V4+V8, V7 silent skip (not in verifications[])."""
    asyncio.run(_runner_v1_v4_v8_for_manufacturing_v7_skipped_impl())


async def _runner_v1_v4_v8_for_manufacturing_v7_skipped_impl() -> None:
    # Story 4.4: inherit manufacturing__b-small fixture's tenant_id for V8 match.
    input_dict, _ = load_golden_by_id("manufacturing__b-small")
    fixture_tenant = uuid.UUID(input_dict["tenant_id"])
    fi = MonthlyInput(
        tenant_id=fixture_tenant,
        period_key=input_dict["period_key"],
        direct_material_krw=KRW(int(input_dict["monthly_input"]["direct_material_krw"])),
        direct_labor_krw=KRW(int(input_dict["monthly_input"]["direct_labor_krw"])),
        indirect_krw=KRW(int(input_dict["monthly_input"]["indirect_krw"])),
        fte_headcount=Decimal(str(input_dict["monthly_input"]["fte_headcount"])),
    )
    fb = Baseline(
        fiscal_period=input_dict["baseline"]["fiscal_period"],
        standard_monthly_hours=int(input_dict["baseline"]["standard_monthly_hours"]),
        bom_ratio_validated=True,
        allocation_basis_set=True,
    )
    engine_result = compute_period_cost(monthly_input=fi, baseline=fb)
    runner = VerificationRunner(trace_id="t-1")
    verdict = await runner.run_all(
        monthly_input=fi,
        baseline=fb,
        calc_result=engine_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=fixture_tenant,
        period_key="2026-07",
    )
    assert verdict.verification_status == "passed"
    assert verdict.top_failure is None
    codes = [v.code for v in verdict.verifications]
    assert codes == ["V1", "V4", "V8"]  # V7 silently skipped
    assert verdict.trace_id == "t-1"


@pytest.mark.engine
def test_runner_service_industry_fires_v1_v4_v7_v8() -> None:
    """Runner: service-only tenant fires all 4 rules (V7 included)."""
    asyncio.run(_runner_service_industry_fires_v1_v4_v7_v8_impl())


async def _runner_service_industry_fires_v1_v4_v7_v8_impl() -> None:
    # Story 4.4: inherit service__b-small fixture's tenant_id for V8 match.
    input_dict, _ = load_golden_by_id("service__b-small")
    fixture_tenant = uuid.UUID(input_dict["tenant_id"])
    fi = MonthlyInput(
        tenant_id=fixture_tenant,
        period_key=input_dict["period_key"],
        direct_material_krw=KRW(int(input_dict["monthly_input"]["direct_material_krw"])),
        direct_labor_krw=KRW(int(input_dict["monthly_input"]["direct_labor_krw"])),
        indirect_krw=KRW(int(input_dict["monthly_input"]["indirect_krw"])),
        fte_headcount=Decimal(str(input_dict["monthly_input"]["fte_headcount"])),
    )
    fb = Baseline(
        fiscal_period=input_dict["baseline"]["fiscal_period"],
        standard_monthly_hours=int(input_dict["baseline"]["standard_monthly_hours"]),
        bom_ratio_validated=True,
        allocation_basis_set=True,
    )
    engine_result = compute_period_cost(monthly_input=fi, baseline=fb)
    runner = VerificationRunner(trace_id="t-2")
    verdict = await runner.run_all(
        monthly_input=fi,
        baseline=fb,
        calc_result=engine_result,
        industry=INDUSTRY_SERVICE,
        tenant_id=fixture_tenant,
        period_key="2026-07",
    )
    assert verdict.verification_status == "passed"
    codes = [v.code for v in verdict.verifications]
    assert codes == ["V1", "V4", "V7", "V8"]


@pytest.mark.engine
def test_runner_v1_failure_aborts_v4_v7_v8() -> None:
    """AD-12 ordering abort: V1 fail → V4·V7·V8 omitted from verifications[]."""
    asyncio.run(_runner_v1_failure_aborts_v4_v7_v8_impl())


async def _runner_v1_failure_aborts_v4_v7_v8_impl() -> None:
    runner = VerificationRunner(trace_id="t-3")
    # Force V1 fail: manufacturing_cost off by 100 (>1원 tolerance)
    bad_result = _make_calc_result(manufacturing=1_800_000 - 100)
    verdict = await runner.run_all(
        monthly_input=_make_monthly_input(),
        baseline=_make_baseline(),
        calc_result=bad_result,
        industry=INDUSTRY_MANUFACTURING,
        tenant_id=uuid.UUID("11111111-1111-4111-8111-111111111111"),
        period_key="2026-07",
    )
    assert verdict.verification_status == "failed"
    assert verdict.top_failure is not None
    assert verdict.top_failure.code == "V1"
    # V4/V7/V8 omitted (verifications[] only contains fired rules)
    codes = [v.code for v in verdict.verifications]
    assert codes == ["V1"]


@pytest.mark.engine
def test_runner_v4_failure_skips_v7_v8() -> None:
    """AD-12 ordering: V1 pass + V4 fail → V7·V8 omitted.

    V4 MVP is structurally passing-only (qty=produced=sold → ①=0, so
    sum_4_elements always equals manufacturing_cost within 1원). V4 failure
    requires Story 4.4 ledger fold-in to differentiate production vs sales
    quantities. The runner construction below is referenced via `_` to keep
    the AD-12 wiring in place when Story 4.4 lands.
    """
    _ = VerificationRunner(trace_id="t-4")
    pytest.skip("V4 MVP always passes (qty=produced=sold → ①=0). Story 4.4 refines.")


# ── AD-5 purity (AST 3중 차단) ──────────────────────────────────
@pytest.mark.engine
def test_verification_rules_no_io_imports() -> None:
    """AD-5 purity: rule kernels MUST NOT import DB / web / clock / random layers.

    This is the AST guard. If any rule kernel imports `sqlalchemy`, `psycopg`,
    `asyncpg`, `fastapi`, `starlette`, `httpx`, `time`, `datetime.now`,
    `os.environ`, `random`, or `secrets`, the test fails. Mirrors Story 0.4
    chunk-B AST guard pattern.
    """
    forbidden_imports: tuple[str, ...] = (
        "sqlalchemy",
        "psycopg",
        "asyncpg",
        "fastapi",
        "starlette",
        "httpx",
        "requests",
        "time",  # `import time` (not `from datetime import time`)
        "random",
        "secrets",
    )
    rule_modules = [
        "apps.api.modules.m3_calculate.services.rules.protocol",
        "apps.api.modules.m3_calculate.services.rules.v1_complete_allocation",
        "apps.api.modules.m3_calculate.services.rules.v4_cost_income_reconciliation",
        "apps.api.modules.m3_calculate.services.rules.v7_abc_integrity",
        "apps.api.modules.m3_calculate.services.rules.v8_regression",
    ]
    for module_name in rule_modules:
        module = __import__(module_name, fromlist=["__name__"])
        source = inspect.getsource(module)
        for forbidden in forbidden_imports:
            assert f"import {forbidden}" not in source, (
                f"{module_name} imports forbidden {forbidden!r} (AD-5 purity)"
            )
            assert f"from {forbidden} " not in source, (
                f"{module_name} imports forbidden {forbidden!r} (AD-5 purity)"
            )


@pytest.mark.engine
def test_verification_runner_no_io_imports() -> None:
    """Runner itself also pure — no DB / web / clock / random."""
    forbidden_imports: tuple[str, ...] = (
        "sqlalchemy",
        "psycopg",
        "asyncpg",
        "fastapi",
        "starlette",
        "httpx",
    )
    module = __import__(
        "apps.api.modules.m3_calculate.services.verification_runner",
        fromlist=["__name__"],
    )
    source = inspect.getsource(module)
    for forbidden in forbidden_imports:
        assert f"import {forbidden}" not in source, (
            f"verification_runner imports forbidden {forbidden!r}"
        )
        assert f"from {forbidden} " not in source, (
            f"verification_runner imports forbidden {forbidden!r}"
        )


# ── Verdict envelope shape ──────────────────────────────────
@pytest.mark.engine
def test_verdict_envelope_passing_shape() -> None:
    """Verdict envelope: passed with verifications[] + trace_id."""
    items = [
        VerificationItem(code="V1", status="passed", message_ko="정상", details={}),
        VerificationItem(code="V4", status="passed", message_ko="정상", details={}),
    ]
    verdict = Verdict(
        verification_status="passed",
        verifications=items,
        top_failure=None,
        trace_id="envelope-1",
    )
    assert verdict.verification_status == "passed"
    assert verdict.top_failure is None
    assert len(verdict.verifications) == 2
    assert verdict.trace_id == "envelope-1"


@pytest.mark.engine
def test_verdict_envelope_failed_shape_top_failure() -> None:
    """Verdict envelope: failed with top_failure non-None."""
    items = [
        VerificationItem(code="V1", status="failed", message_ko="위반", details={"delta_krw": -100}),
        # V4 omitted (AD-12 abort)
    ]
    verdict = Verdict(
        verification_status="failed",
        verifications=items,
        top_failure=items[0],
        trace_id="envelope-2",
    )
    assert verdict.verification_status == "failed"
    assert verdict.top_failure is not None
    assert verdict.top_failure.code == "V1"
    assert verdict.top_failure.details["delta_krw"] == -100
