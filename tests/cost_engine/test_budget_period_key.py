"""tests.cost_engine.test_budget_period_key — Story 8.1 pure kernel tests.

Tests for `packages.cost_engine.budget_period_key`:
- `derive_budget_period_key`: real_period_key + scenario_index → virtual period_key
  - 정상범위 + 3종 edge cases (real_period_key invalid / scenario_index <= 0 / scenario_index > 1)
- `parse_virtual_budget_period_key`: virtual period_key → BudgetPeriodKeyParts
  - 정상범위 + 2종 edge cases (real fiscal key 거부 / scenario_index > 1 거부)
- `validate_scenario_uniqueness`: existing_count → None / ScenarioLimitExceededError
  - 0건 허용 + 1건 거부 + N건 거부
- `compute_budget_scenario_hash`: BudgetScenario → sha256 digest
  - 결정론 + frozen=True enforcement
- 100회 determinism (byte-identical hash)
- AD-24 §6.2 pattern enforcement
"""

from __future__ import annotations

import dataclasses

import pytest

from packages.cost_engine.budget_period_key import (
    MVP_MAX_SCENARIOS_PER_TENANT,
    MVP_SCENARIO_INDEX,
    SCENARIO_HASH_PREFIX,
    SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO,
    BudgetPeriodKeyParts,
    BudgetScenario,
    InvalidVirtualBudgetPeriodKeyError,
    ScenarioLimitExceededError,
    compute_budget_scenario_hash,
    derive_budget_period_key,
    parse_virtual_budget_period_key,
    validate_scenario_uniqueness,
)


# ── Constants ────────────────────────────────────────────────
def test_mvp_constants():
    """MVP constants match Story 8.1 spec §F8.1 + §15 NON-GOAL #2."""
    assert MVP_SCENARIO_INDEX == 1
    assert MVP_MAX_SCENARIOS_PER_TENANT == 1
    assert (
        SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO
        == "1차 MVP는 시나리오 1개만 지원합니다 (2차 예정)"
    )
    assert SCENARIO_HASH_PREFIX == "sha256:"


# ── derive_budget_period_key — happy path ────────────────────
def test_derive_budget_period_key_default():
    """Default scenario_index=1 — 1차 MVP only."""
    result = derive_budget_period_key(real_period_key="2026-07")
    assert result == "2026-07#B1"


def test_derive_budget_period_key_explicit_one():
    """Explicit scenario_index=1 (MVP 한도 경계)."""
    result = derive_budget_period_key(
        real_period_key="2026-07", scenario_index=1
    )
    assert result == "2026-07#B1"


def test_derive_budget_period_key_all_valid_months():
    """All valid months (01-12) produce deterministic virtual keys."""
    for month in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
        result = derive_budget_period_key(real_period_key=f"2026-{month}")
        assert result == f"2026-{month}#B1"


def test_derive_budget_period_key_100x_determinism():
    """100회 동일 입력 → 100회 byte-identical 결과 (V8 회귀 가능)."""
    expected = "2026-07#B1"
    for _ in range(100):
        assert derive_budget_period_key(real_period_key="2026-07") == expected


# ── derive_budget_period_key — edge cases ────────────────────
def test_derive_budget_period_key_invalid_real_period_key_raises():
    """Invalid real_period_key pattern → ValueError."""
    with pytest.raises(ValueError, match="real_period_key must match YYYY-MM"):
        derive_budget_period_key(real_period_key="2026-13")


def test_derive_budget_period_key_invalid_month_00():
    """Invalid month 00 → ValueError."""
    with pytest.raises(ValueError, match="real_period_key must match YYYY-MM"):
        derive_budget_period_key(real_period_key="2026-00")


def test_derive_budget_period_key_invalid_year_format():
    """4자리 연도 아닌 경우 → ValueError."""
    with pytest.raises(ValueError, match="real_period_key must match YYYY-MM"):
        derive_budget_period_key(real_period_key="26-07")


def test_derive_budget_period_key_scenario_index_zero_raises():
    """scenario_index=0 → ValueError."""
    with pytest.raises(ValueError, match="scenario_index must be >= 1"):
        derive_budget_period_key(real_period_key="2026-07", scenario_index=0)


def test_derive_budget_period_key_scenario_index_negative_raises():
    """scenario_index=-1 → ValueError."""
    with pytest.raises(ValueError, match="scenario_index must be >= 1"):
        derive_budget_period_key(real_period_key="2026-07", scenario_index=-1)


def test_derive_budget_period_key_scenario_index_two_raises():
    """scenario_index=2 (1차 MVP 한도 초과) → ValueError."""
    with pytest.raises(ValueError, match="MVP supports scenario_index=1 only"):
        derive_budget_period_key(real_period_key="2026-07", scenario_index=2)


def test_derive_budget_period_key_non_string_raises():
    """real_period_key not str → ValueError."""
    with pytest.raises(ValueError, match="real_period_key must be str"):
        derive_budget_period_key(real_period_key=202607)  # type: ignore[arg-type]


def test_derive_budget_period_key_non_int_scenario_index_raises():
    """scenario_index not int → ValueError."""
    with pytest.raises(ValueError, match="scenario_index must be int"):
        derive_budget_period_key(real_period_key="2026-07", scenario_index="1")  # type: ignore[arg-type]


# ── parse_virtual_budget_period_key — happy path ─────────────
def test_parse_virtual_budget_period_key_default():
    """Normal virtual period_key → BudgetPeriodKeyParts."""
    result = parse_virtual_budget_period_key(period_key="2026-07#B1")
    assert result == BudgetPeriodKeyParts(
        real_period_key="2026-07",
        scenario_index=1,
        scenario_suffix="#B1",
    )


def test_parse_virtual_budget_period_key_all_months():
    """All valid months parse correctly."""
    for month in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
        result = parse_virtual_budget_period_key(period_key=f"2026-{month}#B1")
        assert result.real_period_key == f"2026-{month}"
        assert result.scenario_index == 1
        assert result.scenario_suffix == "#B1"


# ── parse_virtual_budget_period_key — edge cases ─────────────
def test_parse_virtual_budget_period_key_real_fiscal_raises():
    """Real fiscal key (`2026-07`) → ValueError (M8 virtual only)."""
    with pytest.raises(ValueError, match="period_key must match YYYY-MM#B<n>"):
        parse_virtual_budget_period_key(period_key="2026-07")


def test_parse_virtual_budget_period_key_malformed_raises():
    """Malformed period_key → ValueError."""
    with pytest.raises(ValueError, match="period_key must match YYYY-MM#B<n>"):
        parse_virtual_budget_period_key(period_key="not-a-period-key")


def test_parse_virtual_budget_period_key_scenario_zero_raises():
    """scenario_index=0 → ValueError (pattern rejects)."""
    with pytest.raises(ValueError, match="period_key must match YYYY-MM#B<n>"):
        parse_virtual_budget_period_key(period_key="2026-07#B0")


def test_parse_virtual_budget_period_key_scenario_two_raises():
    """scenario_index=2 (1차 MVP 한도) → ValueError."""
    with pytest.raises(ValueError, match="MVP supports scenario_index=1 only"):
        parse_virtual_budget_period_key(period_key="2026-07#B2")


def test_parse_virtual_budget_period_key_non_string_raises():
    """period_key not str → ValueError."""
    with pytest.raises(ValueError, match="period_key must be str"):
        parse_virtual_budget_period_key(period_key=202607)  # type: ignore[arg-type]


# ── validate_scenario_uniqueness ─────────────────────────────
def test_validate_scenario_uniqueness_zero_count():
    """existing_count=0 → return None (1st scenario 허용)."""
    assert validate_scenario_uniqueness(existing_count=0) is None


def test_validate_scenario_uniqueness_one_count_raises():
    """existing_count=1 → ScenarioLimitExceededError."""
    with pytest.raises(ScenarioLimitExceededError) as exc_info:
        validate_scenario_uniqueness(existing_count=1)
    assert exc_info.value.message == SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO
    assert exc_info.value.existing_count == 1


def test_validate_scenario_uniqueness_two_count_raises():
    """existing_count=2 → ScenarioLimitExceededError (defense-in-depth)."""
    with pytest.raises(ScenarioLimitExceededError) as exc_info:
        validate_scenario_uniqueness(existing_count=2)
    assert exc_info.value.existing_count == 2


def test_validate_scenario_uniqueness_negative_count_raises():
    """existing_count=-1 → ValueError (defense-in-depth)."""
    with pytest.raises(ValueError, match="existing_count must be >= 0"):
        validate_scenario_uniqueness(existing_count=-1)


def test_validate_scenario_uniqueness_non_int_raises():
    """existing_count not int → ValueError."""
    with pytest.raises(ValueError, match="existing_count must be int"):
        validate_scenario_uniqueness(existing_count="0")  # type: ignore[arg-type]


# ── compute_budget_scenario_hash ─────────────────────────────
def _make_scenario(suffix: str = "") -> BudgetScenario:
    return BudgetScenario(
        id=f"019000000000-0000-7000-8000-000000000001{suffix}",
        tenant_id="019000000000-0000-7000-8000-000000000002",
        period_key="2026-07#B1",
        real_period_key="2026-07",
        scenario_index=1,
        created_by="019000000000-0000-7000-8000-000000000003",
        created_at_kst="2026-07-15T10:30:00+09:00",
    )


def test_compute_budget_scenario_hash_format():
    """Hash format: `sha256:` + 32-char hexdigest."""
    scenario = _make_scenario()
    digest = compute_budget_scenario_hash(scenario=scenario)
    assert digest.startswith("sha256:")
    hex_part = digest[len("sha256:"):]
    assert len(hex_part) == 64  # 32 bytes = 64 hex chars
    int(hex_part, 16)  # 검증: valid hex


def test_compute_budget_scenario_hash_determinism():
    """동일 입력 → 동일 hash (NFR16 determinism)."""
    scenario = _make_scenario()
    h1 = compute_budget_scenario_hash(scenario=scenario)
    h2 = compute_budget_scenario_hash(scenario=scenario)
    assert h1 == h2


def test_compute_budget_scenario_hash_100x_byte_identical():
    """100회 동일 입력 → 100회 byte-identical (V8 회귀 가능)."""
    scenario = _make_scenario()
    expected = compute_budget_scenario_hash(scenario=scenario)
    for _ in range(100):
        assert compute_budget_scenario_hash(scenario=scenario) == expected


def test_compute_budget_scenario_hash_different_input_different_hash():
    """다른 created_at_kst → 다른 hash (변경 감지)."""
    s1 = _make_scenario()
    s2 = dataclasses.replace(s1, created_at_kst="2026-07-15T10:30:01+09:00")
    assert compute_budget_scenario_hash(scenario=s1) != compute_budget_scenario_hash(scenario=s2)


def test_compute_budget_scenario_hash_non_scenario_raises():
    """scenario not BudgetScenario → ValueError."""
    with pytest.raises(ValueError, match="scenario must be BudgetScenario"):
        compute_budget_scenario_hash(scenario={"id": "x"})  # type: ignore[arg-type]


# ── Frozen dataclass enforcement ─────────────────────────────
def test_budget_period_key_parts_is_frozen():
    """BudgetPeriodKeyParts is frozen=True — mutation 시 FrozenInstanceError."""
    parts = parse_virtual_budget_period_key(period_key="2026-07#B1")
    with pytest.raises(dataclasses.FrozenInstanceError):
        parts.real_period_key = "2099-12"  # type: ignore[misc]


def test_budget_scenario_is_frozen():
    """BudgetScenario is frozen=True + slots=True — mutation 시 FrozenInstanceError."""
    scenario = _make_scenario()
    with pytest.raises(dataclasses.FrozenInstanceError):
        scenario.id = "different-id"  # type: ignore[misc]


# ── Cross-function consistency ───────────────────────────────
def test_derive_then_parse_round_trip():
    """derive_budget_period_key → parse_virtual_budget_period_key round-trip."""
    derived = derive_budget_period_key(real_period_key="2026-07")
    parsed = parse_virtual_budget_period_key(period_key=derived)
    assert parsed.real_period_key == "2026-07"
    assert parsed.scenario_index == 1
    assert parsed.scenario_suffix == "#B1"


def test_budget_period_key_parts_exported():
    """Public API export — `BudgetPeriodKeyParts` importable."""
    from packages.cost_engine import BudgetPeriodKeyParts as Exported
    assert Exported is BudgetPeriodKeyParts


def test_budget_scenario_exported():
    """Public API export — `BudgetScenario` importable."""
    from packages.cost_engine import BudgetScenario as Exported
    assert Exported is BudgetScenario


def test_scenario_limit_exceeded_error_exported():
    """Public API export — `ScenarioLimitExceededError` importable."""
    from packages.cost_engine import ScenarioLimitExceededError as Exported
    assert Exported is ScenarioLimitExceededError
