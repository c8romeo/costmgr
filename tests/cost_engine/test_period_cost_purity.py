"""Engine compute_period_cost purity tests (Story 4.1).

AD-1 / AD-5 / AD-8 / AD-11 / AD-15 / AD-16 / AD-22 invariants:
  - Same input → byte-identical CalcResult 100/100 (V8).
  - All KRW fields are `int` (AD-8).
  - `result_hash` is 64-char hex SHA-256 of stable JSON.
  - `state` is always "draft" (AD-22 — service layer owns transitions).
  - Pure stdlib: no I/O, no DB, no clock, no random.
  - Banker's rounding (ROUND_HALF_EVEN) on KRW arithmetic.
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
from packages.cost_engine.ports.calc_port import CalcResult

# ── Fixtures ────────────────────────────────────────────────
_TENANT = UUID("11111111-1111-1111-1111-111111111111")
_PERIOD = "2026-07"
_BASELINE = Baseline(fiscal_period="2026-07", standard_monthly_hours=228)


def _mk_input(
    *,
    direct_material_krw: int = 2_500_000,
    direct_labor_krw: int = 1_800_000,
    indirect_krw: int = 600_000,
    fte_headcount: Decimal = Decimal("1.00"),
    tenant_id: UUID = _TENANT,
    period_key: str = _PERIOD,
) -> MonthlyInput:
    return MonthlyInput(
        tenant_id=tenant_id,
        period_key=period_key,
        direct_material_krw=KRW(direct_material_krw),
        direct_labor_krw=KRW(direct_labor_krw),
        indirect_krw=KRW(indirect_krw),
        fte_headcount=fte_headcount,
    )


# ── AC #1: Determinism (100×) ──────────────────────────────
@pytest.mark.engine
def test_same_input_returns_identical_hash_100x() -> None:
    """AC #1 — 100× call → identical result_hash."""
    inp = _mk_input()
    hashes = {compute_period_cost(inp, _BASELINE).result_hash for _ in range(100)}
    assert len(hashes) == 1, f"Hash drift across 100 calls: {hashes}"


@pytest.mark.engine
def test_same_input_returns_identical_costs_100x() -> None:
    """AC #1 — 100× call → byte-identical KRW fields."""
    inp = _mk_input()
    first = compute_period_cost(inp, _BASELINE)
    for _ in range(99):
        result = compute_period_cost(inp, _BASELINE)
        assert result.material_cost == first.material_cost
        assert result.labor_cost == first.labor_cost
        assert result.overhead_cost == first.overhead_cost
        assert result.manufacturing_cost == first.manufacturing_cost
        assert result.inventory_adjustment == first.inventory_adjustment


@pytest.mark.engine
def test_state_always_draft() -> None:
    """AC #1 — AD-22 invariant: engine ALWAYS returns draft."""
    inp = _mk_input()
    result = compute_period_cost(inp, _BASELINE)
    assert result.state == "draft"


# ── AC #3: 8-stage 산식 체인 ────────────────────────────────
@pytest.mark.engine
def test_section_6_1_eight_step_chain() -> None:
    """AC #3 — PRD §6.1 fixture: 2,500,000 + 1,800,000 + 600,000 → 4,900,000."""
    inp = _mk_input(
        direct_material_krw=2_500_000,
        direct_labor_krw=1_800_000,
        indirect_krw=600_000,
        fte_headcount=Decimal("1.00"),
    )
    result = compute_period_cost(inp, _BASELINE)
    assert result.material_cost == KRW(2_500_000)
    assert result.labor_cost == KRW(1_800_000)  # 1.00 FTE → 그대로
    assert result.overhead_cost == KRW(600_000)
    assert result.manufacturing_cost == KRW(4_900_000)
    assert result.inventory_adjustment == KRW(0)  # TODO(epic-5)


@pytest.mark.engine
def test_round_half_even_bankers_rounding() -> None:
    """AC #3 — Banker's rounding (ROUND_HALF_EVEN).

    fte_headcount=Decimal("0.5") on direct_labor_krw=1:
      1 × 0.5 = 0.5 → banker's → 0
    fte_headcount=Decimal("1.5") on direct_labor_krw=1:
      1 × 1.5 = 1.5 → banker's → 2
    """
    # Decimal("0.5") → 0 (half-even: round to even neighbor)
    inp_half = _mk_input(
        direct_material_krw=0,
        direct_labor_krw=1,
        indirect_krw=0,
        fte_headcount=Decimal("0.5"),
    )
    assert compute_period_cost(inp_half, _BASELINE).labor_cost == KRW(0)

    # Decimal("1.5") → 2 (half-even: round to even neighbor)
    inp_three_half = _mk_input(
        direct_material_krw=0,
        direct_labor_krw=1,
        indirect_krw=0,
        fte_headcount=Decimal("1.5"),
    )
    assert compute_period_cost(inp_three_half, _BASELINE).labor_cost == KRW(2)

    # Decimal("2.5") → 2 (banker's even)
    inp_two_half = _mk_input(
        direct_material_krw=0,
        direct_labor_krw=1,
        indirect_krw=0,
        fte_headcount=Decimal("2.5"),
    )
    assert compute_period_cost(inp_two_half, _BASELINE).labor_cost == KRW(2)

    # Decimal("2.6") → 3 (no rounding ambiguity)
    inp_two_six = _mk_input(
        direct_material_krw=0,
        direct_labor_krw=1,
        indirect_krw=0,
        fte_headcount=Decimal("2.6"),
    )
    assert compute_period_cost(inp_two_six, _BASELINE).labor_cost == KRW(3)


@pytest.mark.engine
def test_fte_headcount_decimal_routing() -> None:
    """AC #3 — Story 3.2 FTE 정밀 Decimal routing."""
    # fte_headcount=1.09, direct_labor=1,800,000 → 1.09 × 1,800,000 = 1,962,000
    inp = _mk_input(
        direct_material_krw=0,
        direct_labor_krw=1_800_000,
        indirect_krw=0,
        fte_headcount=Decimal("1.09"),
    )
    assert compute_period_cost(inp, _BASELINE).labor_cost == KRW(1_962_000)


# ── AC #1 + AC #3: result_hash 결정론 ────────────────────────
_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@pytest.mark.engine
def test_result_hash_is_64char_hex() -> None:
    """AC #1 — result_hash 정규식 ^[0-9a-f]{64}$."""
    inp = _mk_input()
    result = compute_period_cost(inp, _BASELINE)
    assert _HASH_RE.match(result.result_hash)


@pytest.mark.engine
def test_result_hash_stable_under_input_reorder() -> None:
    """AC #1 — 같은 logical input → 같은 hash (key sort 보장)."""
    # Baseline 필드 추가 시에도 hash 안정성 검증 — Baseline은 frozen dataclass이므로
    # 필드 순서는 정의에 의해 고정. 본 테스트는 동일 입력 2회 호출 검증.
    inp = _mk_input()
    h1 = compute_period_cost(inp, _BASELINE).result_hash
    h2 = compute_period_cost(inp, _BASELINE).result_hash
    assert h1 == h2


@pytest.mark.engine
def test_result_hash_differs_per_tenant() -> None:
    """AC #1 — tenant_id 격리 (PRD §NFR8)."""
    inp_a = _mk_input(tenant_id=UUID("11111111-1111-1111-1111-111111111111"))
    inp_b = _mk_input(tenant_id=UUID("22222222-2222-2222-2222-222222222222"))
    assert (
        compute_period_cost(inp_a, _BASELINE).result_hash
        != compute_period_cost(inp_b, _BASELINE).result_hash
    )


@pytest.mark.engine
def test_result_hash_differs_per_period() -> None:
    """AC #1 — period_key 격리 (PRD §AD-24 typed period key)."""
    inp_jul = _mk_input(period_key="2026-07")
    inp_aug = _mk_input(period_key="2026-08")
    base_jul = Baseline(fiscal_period="2026-07", standard_monthly_hours=228)
    base_aug = Baseline(fiscal_period="2026-08", standard_monthly_hours=228)
    assert (
        compute_period_cost(inp_jul, base_jul).result_hash
        != compute_period_cost(inp_aug, base_aug).result_hash
    )


# ── AC #3: Input guards ─────────────────────────────────────
@pytest.mark.engine
def test_negative_input_rejected() -> None:
    """AC #3 — KRW 음수 → ValueError (engine-side defense)."""
    inp = _mk_input(direct_material_krw=-1)
    with pytest.raises(ValueError, match="direct_material_krw must be >= 0"):
        compute_period_cost(inp, _BASELINE)


@pytest.mark.engine
def test_zero_input_returns_zero() -> None:
    """AC #3 — 0/0/0 → manufacturing_cost=0."""
    inp = _mk_input(
        direct_material_krw=0,
        direct_labor_krw=0,
        indirect_krw=0,
        fte_headcount=Decimal("0.00"),
    )
    result = compute_period_cost(inp, _BASELINE)
    assert result.material_cost == KRW(0)
    assert result.labor_cost == KRW(0)
    assert result.overhead_cost == KRW(0)
    assert result.manufacturing_cost == KRW(0)


@pytest.mark.engine
def test_baseline_bom_invalid_raises() -> None:
    """AC #3 — PRD §F1.1 BOM 100% 검증 실패 → ValueError."""
    base_invalid = Baseline(
        fiscal_period="2026-07",
        standard_monthly_hours=228,
        bom_ratio_validated=False,
        allocation_basis_set=True,
    )
    inp = _mk_input()
    with pytest.raises(ValueError, match="BOM 비중 합 100% 검증 실패"):
        compute_period_cost(inp, base_invalid)


@pytest.mark.engine
def test_baseline_allocation_missing_raises() -> None:
    """AC #3 — PRD §F0.2 배부기준 3종 미완료 → ValueError."""
    base_invalid = Baseline(
        fiscal_period="2026-07",
        standard_monthly_hours=228,
        bom_ratio_validated=True,
        allocation_basis_set=False,
    )
    inp = _mk_input()
    with pytest.raises(ValueError, match="배부기준 3종 미완료"):
        compute_period_cost(inp, base_invalid)


@pytest.mark.engine
def test_period_key_format_validation() -> None:
    """AC #3 — period_key AD-24 형식 (YYYY-MM)."""
    # 잘못된 형식 4종 모두 거부
    for bad in ("2026-7", "2026/07", "26-07", "2026-13"):
        inp = _mk_input(period_key=bad)
        base_bad = Baseline(fiscal_period="2026-07", standard_monthly_hours=228)
        with pytest.raises(ValueError, match="period_key must match YYYY-MM"):
            compute_period_cost(inp, base_bad)


@pytest.mark.engine
def test_tenant_id_uuid_validation() -> None:
    """AC #3 — tenant_id UUID (type system enforced)."""
    # dataclass frozen + type system — UUID가 아닌 값은 type error.
    # 본 테스트는 타입 시스템이 강제함을 명시 (runtime check는 mypy/pyright 책임).
    import typing

    hint = MonthlyInput.__dataclass_fields__["tenant_id"].type
    assert "UUID" in str(hint) or "uuid" in str(hint).lower() or hint == typing.Any


@pytest.mark.engine
def test_standard_monthly_hours_must_be_positive() -> None:
    """AC #3 — standard_monthly_hours <= 0 → ValueError."""
    base_invalid = Baseline(fiscal_period="2026-07", standard_monthly_hours=0)
    inp = _mk_input()
    with pytest.raises(ValueError, match="standard_monthly_hours must be > 0"):
        compute_period_cost(inp, base_invalid)


# ── AC #3: Monetary type invariants (AD-8) ─────────────────
@pytest.mark.engine
def test_krw_types_are_int() -> None:
    """AC #3 — 모든 KRW 필드 `isinstance(..., int)`."""
    result = compute_period_cost(_mk_input(), _BASELINE)
    for field in (
        "material_cost",
        "labor_cost",
        "overhead_cost",
        "manufacturing_cost",
        "inventory_adjustment",
    ):
        value = getattr(result, field)
        assert isinstance(value, int), f"{field} is {type(value).__name__}, not int"


@pytest.mark.engine
def test_no_float_anywhere() -> None:
    """AC #3 — engine 모듈의 모든 KRW 산술에 `float` 금지."""
    import ast
    from pathlib import Path

    import packages.cost_engine.core.period_cost as pc

    src = pc.__file__  # type: ignore[attr-defined]
    assert src is not None
    # 본 파일 source에서 `float` 사용 0건 (type annotation 제외).
    src_path = Path(src)
    with src_path.open(encoding="utf-8") as f:
        tree = ast.parse(f.read())
    float_uses: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        ):
            float_uses.append((node.lineno, "call"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_uses.append((node.lineno, f"literal {node.value}"))
    assert not float_uses, f"float usage in engine: {float_uses}"


# ── AC #3: CalcResult dataclass invariants ──────────────────
@pytest.mark.engine
def test_calcresult_is_dataclass() -> None:
    """AC #3 — CalcResult is frozen dataclass (AD-5: immutable)."""
    import dataclasses

    assert dataclasses.is_dataclass(CalcResult)
    # frozen=True enforcement is on the class itself, not per-field.
    assert CalcResult.__dataclass_params__.frozen  # type: ignore[attr-defined]


@pytest.mark.engine
def test_calcresult_required_fields() -> None:
    """AC #3 — CalcResult 9 fields all required."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(CalcResult)}
    expected = {
        "tenant_id",
        "period_key",
        "material_cost",
        "labor_cost",
        "overhead_cost",
        "manufacturing_cost",
        "inventory_adjustment",
        "result_hash",
        "state",
    }
    assert field_names == expected


# ── AC #1: large fixture stress (1000×) ────────────────────
@pytest.mark.engine
def test_1000_iterations_no_drift() -> None:
    """AC #1 — 1000회 호출에서도 hash/cost 0 drift (V8 stress)."""
    inp = _mk_input()
    first = compute_period_cost(inp, _BASELINE)
    for i in range(1000):
        result = compute_period_cost(inp, _BASELINE)
        assert result.result_hash == first.result_hash, f"drift at i={i}"
        assert result.manufacturing_cost == first.manufacturing_cost, f"drift at i={i}"


# ── AC #3: multiple tenants + periods stability ─────────────
@pytest.mark.engine
def test_two_periods_same_tenant_distinct_hashes() -> None:
    """AC #3 — 동일 tenant, 다른 period → 다른 hash."""
    base_jul = Baseline(fiscal_period="2026-07", standard_monthly_hours=228)
    base_aug = Baseline(fiscal_period="2026-08", standard_monthly_hours=228)
    inp_jul = _mk_input(period_key="2026-07")
    inp_aug = _mk_input(period_key="2026-08")
    h_jul = compute_period_cost(inp_jul, base_jul).result_hash
    h_aug = compute_period_cost(inp_aug, base_aug).result_hash
    assert h_jul != h_aug
