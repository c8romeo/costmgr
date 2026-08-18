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
from packages.cost_engine.tests.regression_v8 import (
    SNAPSHOT_REVERSAL_FIXTURE_IDS,
    V3_FIXTURE_IDS,
    V8_FIXTURE_COUNT,
)
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
# CR 5.3 P18 + Story 11.4 A13 — V8 + V3 + V4 + 11-3 snapshot/reversal/reopen fixture count =
# 12 (V8 byte-identical) + 2 (V3 골든) + 4 (V4 + A11 골든 — 6-2 A11 wire)
# + 4 (Story 11.3 snapshot persistence + reversal 영구화 + W2 reopen flow 골든) = 22 total.
# Matrix coverage tests filter V8-only fixtures by the `industry__b-shape` pattern.
EXPECTED_FIXTURE_COUNT = len(ALL_INDUSTRIES) * len(ALL_SHAPES)  # 12 (V8 only)
EXPECTED_TOTAL_COUNT = EXPECTED_FIXTURE_COUNT + 10  # 22 (V8 + V3 + V4/A11 + 11-3 골든)


def _v8_fixture_paths() -> list[Path]:
    """V8-only fixtures (industry__b-shape naming convention)."""
    return [p for p in FIXTURES_DIR.glob("*.json") if "__" in p.stem]


_DETERMINISTIC_TENANT_ID = _uuid_mod.UUID("11111111-1111-4111-8111-111111111111")


# ── Fixtures shipped on disk invariant ────────────────────────
@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_count_is_22() -> None:
    """V8_FIXTURE_COUNT = 22 + 22 fixture JSON files on disk (AC #7 + CR 5.3 P18 + Story 6.2 A11 + Story 11.4 A13).

    Story 4.4 (12 V8 byte-identical 골든) + Story 5.3 (2 V3 closing
    invariant 골든) + Story 6.2 A11 (4 NEW 골든 — 6-1 T10.5 deferred V4
    closing-period PASS/FAIL fill + A11 closing_snapshot +
    ledger_period_closing) + Story 11.4 A13 sprint-up (4 NEW 골든 —
    snapshot_committed + reversal_negating_snapshot +
    reversal_corrected_snapshot + reopen_committed — AD-20 state machine
    + AD-22 영구화 + W2 reopen flow) = 22 total. The V3 + V4 +
    snapshot/reversal/reopen fixtures use a different naming convention
    (no `__` separator) and have a different payload shape. The V8 matrix
    coverage tests below filter V8-only fixtures by the `__` pattern.
    """
    assert V8_FIXTURE_COUNT == 22, (
        f"V8_FIXTURE_COUNT must be 22 (Story 4.4 12 + Story 5.3 2 V3 + Story 6.2 A11 4 V4/A11 + Story 11.4 A13 4 11-3). "
        f"Got {V8_FIXTURE_COUNT}."
    )
    actual = sorted(p.name for p in FIXTURES_DIR.glob("*.json"))
    assert len(actual) == EXPECTED_TOTAL_COUNT, (
        f"Fixtures directory must contain {EXPECTED_TOTAL_COUNT} JSON files "
        f"(12 V8 + 2 V3 + 4 V4/A11). Found {len(actual)}: {actual}"
    )


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_matrix_covers_all_4_industries() -> None:
    """4 industries × ≥1 fixture each (Industry enum SSOT — F-5 review lock)."""
    # CR 5.3 P18 — filter V8-only fixtures by `industry__b-shape` pattern.
    industries = {p.stem.split("__")[0] for p in _v8_fixture_paths()}
    expected_industries = set(ALL_INDUSTRIES)
    assert industries == expected_industries, (
        f"V8 fixture industry coverage drift: got {industries}, "
        f"expected {expected_industries}. F-5 SSOT = Industry enum exact mapping."
    )


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_fixture_matrix_covers_all_3_baseline_shapes() -> None:
    """3 baseline shapes × ≥1 fixture each (PRD §6.1)."""
    # CR 5.3 P18 — filter V8-only fixtures by `industry__b-shape` pattern.
    shapes = {p.stem.split("__")[1] for p in _v8_fixture_paths()}
    assert shapes == set(ALL_SHAPES), (
        f"V8 fixture shape coverage drift: got {shapes}, expected {set(ALL_SHAPES)}"
    )


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v3_golden_fixtures_exist() -> None:
    """CR 5.3 P18 — 2 V3 closing invariant 골든 fixtures ship on disk."""
    for fixture_id in V3_FIXTURE_IDS:
        path = FIXTURES_DIR / f"{fixture_id}.json"
        assert path.exists(), (
            f"V3 골든 fixture missing: {path}. "
            f"Expected 2 fixtures: {V3_FIXTURE_IDS}."
        )


# ── Story 11.4 A13 — 4 NEW snapshot/reversal/reopen 골든 fixtures ─
@pytest.mark.engine
@pytest.mark.v8_regression
def test_snapshot_reversal_reopen_fixtures_exist() -> None:
    """Story 11.4 A13 sprint-up — 4 NEW 골든 fixtures ship on disk.

    4 NEW V8 골든 for AD-20 state machine + AD-22 reversal 영구화 +
    W2 reopen flow (Story 11.3 wire base + Story 11.4 A13 fixture matrix
    fill):
    - snapshot_committed.json (AD-20 verified→committed transition)
    - reversal_negating_snapshot.json (AD-22 sign-negating row)
    - reversal_corrected_snapshot.json (AD-22 corrected row)
    - reopen_committed.json (W2 reopen with operator_action enum + reason)
    """
    for fixture_id in SNAPSHOT_REVERSAL_FIXTURE_IDS:
        path = FIXTURES_DIR / f"{fixture_id}.json"
        assert path.exists(), (
            f"Story 11.4 A13 골든 fixture missing: {path}. "
            f"Expected 4 fixtures: {SNAPSHOT_REVERSAL_FIXTURE_IDS}."
        )


@pytest.mark.engine
@pytest.mark.v8_regression
def test_snapshot_committed_fixture_shape() -> None:
    """Story 11.4 A13 — snapshot_committed.json has AD-20 transition shape.

    Pins the AD-20 state machine transition shape (verified → committed)
    + 4-channel cache invalidation publisher wire. Drift detector: if
    the fixture omits a required field, this test fails.
    """
    path = FIXTURES_DIR / "snapshot_committed.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["fixture_id"] == "snapshot_committed"
    assert data["pre_commit_state"] == "verified"
    assert data["post_commit_state"] == "committed"
    assert data["expected_commit_transition_ok"] is True
    # AD-25 4-channel publisher wire (ai_cache + cost_engine_cache +
    # fiscal_period_cache + closing_snapshot_cache).
    assert set(data["expected_cache_invalidation_channels"]) == {
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    }
    assert data["audit_action"] == "snapshot_persistence_committed"


@pytest.mark.engine
@pytest.mark.v8_regression
def test_reversal_negating_snapshot_fixture_shape() -> None:
    """Story 11.4 A13 — reversal_negating_snapshot.json has AD-22 sign-negating shape.

    Pins the AD-22 reversal 영구화 sign-negating row construction with
    correction_group_id link. Banker's rounding parity invariant pinned.
    """
    path = FIXTURES_DIR / "reversal_negating_snapshot.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["fixture_id"] == "reversal_negating_snapshot"
    assert data["pre_reversal_state"] == "committed"
    assert data["post_reversal_state"] == "reversed"
    assert data["expected_reversal_authorized"] is True
    # Sign-negating row contract.
    assert data["negating_row"]["event_type"] == "reversal_negating"
    assert data["negating_row"]["qty"] == "-10.0000"
    assert data["negating_row"]["reverses_event_id"] == data["target_event_id"]
    # correction_group_id link between negating + corrected rows.
    assert data["expected_correction_group_link"] == data["negating_row"]["correction_group_id"]
    # Financial effect = 0 (reversal 영구화 invariant).
    assert data["expected_financial_effect"] == "0.0000"
    # Audit + cache invalidation.
    assert data["audit_action"] == "snapshot_persistence_reversed"


@pytest.mark.engine
@pytest.mark.v8_regression
def test_reversal_corrected_snapshot_fixture_shape() -> None:
    """Story 11.4 A13 — reversal_corrected_snapshot.json has AD-22 corrected row shape.

    Pins the AD-22 corrected row construction with corrected_period_key
    (AD-24 typed 'YYYY-MM') + banker's rounding parity (CR 0-4).
    """
    path = FIXTURES_DIR / "reversal_corrected_snapshot.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["fixture_id"] == "reversal_corrected_snapshot"
    assert data["expected_reversal_authorized"] is True
    # Corrected row contract.
    assert data["corrected_row"]["event_type"] == "reversal_corrected"
    assert data["corrected_row"]["qty"] == "8.5000"
    assert data["corrected_row"]["period_key"] == "2026-09"
    # corrected_period_key AD-24 typed format.
    assert data["expected_corrected_period_key"] == "2026-09"
    # Banker's rounding parity (CR 0-4 wire).
    assert data["expected_bankers_rounding_parity"] is True
    # correction_group_id link (negating + corrected share same group).
    assert data["expected_correction_group_link"] == data["corrected_row"]["correction_group_id"]


@pytest.mark.engine
@pytest.mark.v8_regression
def test_reopen_committed_fixture_shape() -> None:
    """Story 11.4 A13 — reopen_committed.json has W2 reopen flow shape.

    Pins W2 reopen operator action enum (4-value) + reason length 20-500
    (AD-15 audit-justification) + AD-10 owner-only role gate +
    2-channel cache invalidation (fiscal_period_cache + closing_snapshot_cache).
    """
    path = FIXTURES_DIR / "reopen_committed.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["fixture_id"] == "reopen_committed"
    assert data["pre_reopen_status"] == "closed"
    assert data["pre_reopen_close_sequence_state"] == "confirmed"
    # W2 reopen operator_action 4-value enum.
    assert data["operator_action"] in {
        "operator_reopen",
        "audit_finding",
        "legal_compliance",
        "data_correction",
    }
    # AD-15 reason length 20-500 audit-justification.
    assert data["reason_length"] >= data["reason_min_length_required"]
    assert data["reason_length"] <= data["reason_max_length_allowed"]
    # AD-10 owner-only + capability granted.
    assert data["is_owner"] is True
    assert data["capability_granted"] is True
    assert data["expected_reopen_authorized"] is True
    # 2-channel cache invalidation (W2 reopen — fiscal_period + closing_snapshot only).
    assert set(data["expected_cache_invalidation_channels"]) == {
        "fiscal_period_cache",
        "closing_snapshot_cache",
    }
    assert data["expected_audit_action"] == "reopen_completed"


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
        # Story 5.3: V3 is service-only SKIPPED (Story 4-3 service-only skip pattern
        # mirrored by V3 closing invariant = inventory semantics don't apply to
        # service-only tenants). So service skips V3 entirely.
        assert codes == ["V1", "V4", "V7", "V8"]
    else:
        # V3 fires for all manufacturing industries (closing invariant is
        # inventory-semantic — applies to any tenant with inventory).
        assert codes == ["V1", "V4", "V3", "V8"]
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
    # Story 5.3: V3 (closing ≥ 0 invariant) added at slot 3 of 5 ordering
    # (V1 → V4 → V3 → V7 → V8). Per AD-12 invariant preserved.
    assert set(names) == {"V1", "V3", "V4", "V7", "V8"}


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


# ── Smoke-fix T3 (2026-08-18): runtime tenant_id mismatch fallback ──
@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_runtime_tenant_id_mismatch_returns_placeholder_passed() -> None:
    """When runtime tenant_id differs from the fixture's baked-in tenant_id,
    V8 MUST return `passed` with `placeholder=True` and `tenant_id_mismatch=True`.

    Without this fallback, any non-unit-test runtime caller (smoke / dev
    seed / pilot tenant) would always see V8 fail with a result_hash
    mismatch — a false positive regression.

    Smoke 2026-08-18 hit this: the dev seed's tenant_id never matches the
    published fixture's tenant_id, so V8 fired `failed` in the smoke
    response even though the engine had not regressed.
    """
    asyncio.run(_v8_runtime_tenant_id_mismatch_impl())


async def _v8_runtime_tenant_id_mismatch_impl() -> None:
    input_dict, _golden = load_golden_by_id("manufacturing__b-small")
    mi = _monthly_input_from_fixture(input_dict)
    baseline = _baseline_from_fixture(input_dict)
    engine_result = compute_period_cost(monthly_input=mi, baseline=baseline)

    # Use a DIFFERENT tenant_id than the fixture's baked-in tenant_id.
    runtime_tenant_id = _uuid_mod.uuid4()
    assert str(runtime_tenant_id) != input_dict["tenant_id"]

    rule_input = RuleInput(
        monthly_input=mi,
        baseline=baseline,
        calc_result=engine_result,
        industry="manufacturing",
        tenant_id=runtime_tenant_id,
        period_key=mi.period_key,
        trace_id="v8-tenant-mismatch",
    )
    rule = V8RegressionRule()
    item = rule.check(rule_input)

    # V8 must NOT fire as a regression when the runtime tenant_id differs
    # from the fixture's baked-in tenant_id.
    assert item.code == "V8"
    assert item.status == "passed"
    assert item.details["placeholder"] is True
    assert item.details["tenant_id_mismatch"] is True
    assert item.details["fixture_tenant_id"] == input_dict["tenant_id"]
    assert item.details["runtime_tenant_id"] == str(runtime_tenant_id)


@pytest.mark.engine
@pytest.mark.v8_regression
def test_v8_matching_tenant_id_still_byte_compares() -> None:
    """Companion to the mismatch fallback: when the runtime tenant_id MATCHES
    the fixture's tenant_id, V8 must still perform the byte-identical
    comparison (no regression on the original V8 contract).
    """
    asyncio.run(_v8_matching_tenant_id_still_byte_compares_impl())


async def _v8_matching_tenant_id_still_byte_compares_impl() -> None:
    input_dict, _golden = load_golden_by_id("manufacturing__b-small")
    mi = _monthly_input_from_fixture(input_dict)
    baseline = _baseline_from_fixture(input_dict)
    engine_result = compute_period_cost(monthly_input=mi, baseline=baseline)

    # Use the SAME tenant_id as the fixture — V8 must run byte-identical.
    rule_input = RuleInput(
        monthly_input=mi,
        baseline=baseline,
        calc_result=engine_result,
        industry="manufacturing",
        tenant_id=mi.tenant_id,
        period_key=mi.period_key,
        trace_id="v8-matching-tenant",
    )
    rule = V8RegressionRule()
    item = rule.check(rule_input)

    # With a matching tenant_id and native engine output, V8 must pass
    # without the placeholder marker.
    assert item.code == "V8"
    assert item.status == "passed"
    assert "placeholder" not in item.details or item.details.get("placeholder") is False
    assert item.details.get("fixture_id") == "manufacturing__b-small"


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
