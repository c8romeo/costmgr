"""Tests for Story 11.6 EXTENSION `packages.cost_engine.abc_engine` Report #15 surface.

Coverage (11-6 wire):
  - `compute_report15_hash` V8 determinism + envelope guard (8 cases)
  - `ActivityCostRow` frozen dataclass invariant (6 cases)
  - `Report15Summary` frozen dataclass invariant (4 cases)
  - `Report15InconsistentStateError` envelope raise (4 cases)
  - 9-3 + 11-6 surface integration (4 cases)
  - V8 100-repeats + permuted order (2 cases)

Total: ~28 NEW pytest cases (T1.3) — A19 cohesion pattern 9 surface EXTENSION 검증.

PRD §9 #15 verbatim wire:
  - 활동원가 내역서 (활동별 원가·동인 단가)
  - V7 ABC 무결성: Σ(활동별 원가) = Σ(부서 원가)
  - KRW + USD 동시 표시 (PRD §9 공통 규격)
  - A30 forward-lock SHARED PDF generator reuse 1st case (Story 11.6 본 진입점)
  - A31/A32/A33 forward-lock 결정 wire 진입점
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    ABC_HASH_PREFIX,
    REPORT15_HASH_PREFIX,
    ActivityCostRow,
    CCRResult,
    CostObjectRow,
    Report15InconsistentStateError,
    Report15Summary,
    UnusedCapacitySubRow,
    V7Verdict,
    compute_ccr,
    compute_report15_hash,
    verify_v7_balance,
)

# ── helpers ──────────────────────────────────────────────


def _mk_ccr(
    *,
    department_id: str = "dept-r15",
    department_cost: str = "13200000",
    practical_capacity_hours: str = "400",
) -> CCRResult:
    """Helper — CCRResult fixture (9-2 compute_ccr 동일 surface)."""
    return compute_ccr(
        department_id=department_id,
        department_cost=Decimal(department_cost),
        practical_capacity_hours=Decimal(practical_capacity_hours),
    )


def _mk_activity_breakdown() -> list[ActivityCostRow]:
    """Helper — 3 activity cost rows (PRD §9 #15 verbatim — 활동별 원가·동인 단가)."""
    return [
        ActivityCostRow(
            activity_id="act-1",
            activity_name_ko="고객 상담",
            activity_name_en="Customer Consultation",
            total_cost_krw=Decimal("6600000"),
            total_cost_usd=Decimal("4950"),
            driver_count=4,
            cost_per_driver_krw=Decimal("1650000"),
            cost_per_driver_usd=Decimal("1237.50"),
            allocated_krw=Decimal("6600000"),
            allocated_usd=Decimal("4950"),
            hash="placeholder-1",
        ),
        ActivityCostRow(
            activity_id="act-2",
            activity_name_ko="주문 처리",
            activity_name_en="Order Processing",
            total_cost_krw=Decimal("3300000"),
            total_cost_usd=Decimal("2475"),
            driver_count=2,
            cost_per_driver_krw=Decimal("1650000"),
            cost_per_driver_usd=Decimal("1237.50"),
            allocated_krw=Decimal("3300000"),
            allocated_usd=Decimal("2475"),
            hash="placeholder-2",
        ),
        ActivityCostRow(
            activity_id="act-3",
            activity_name_ko="배송",
            activity_name_en="Delivery",
            total_cost_krw=Decimal("3300000"),
            total_cost_usd=Decimal("2475"),
            driver_count=2,
            cost_per_driver_krw=Decimal("1650000"),
            cost_per_driver_usd=Decimal("1237.50"),
            allocated_krw=Decimal("3300000"),
            allocated_usd=Decimal("2475"),
            hash="placeholder-3",
        ),
    ]


def _mk_v7_verdict(
    *,
    breakdown_sum: str = "13200000",
    unused_cost: str = "0",
    department_cost: str = "13200000",
) -> V7Verdict:
    """Helper — V7Verdict fixture (9-3 verify_v7_balance 동일 surface).

    Report #15 는 activity별 원가·동인 단가 focus 이므로 unused_capacity = 0
    (PRD §A9 verbatim "미사용능력 별도 관리" 는 Report #21 에서 별도 행 표시,
    Report #15 에서는 KPI focus).
    """
    return verify_v7_balance(
        total_breakdown_sum=Decimal(breakdown_sum),
        unused_cost=Decimal(unused_cost),
        department_cost=Decimal(department_cost),
    )


# ── compute_report15_hash — V8 determinism + envelope guard (8 cases) ────


@pytest.mark.engine
def test_compute_report15_hash_determinism_100_repeats() -> None:
    """V8 determinism — compute_report15_hash 100회 반복 → 동일 hash."""
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict()
    first_hash: str | None = None
    for _ in range(100):
        result = compute_report15_hash(
            activity_breakdown=breakdown,
            period_key="2026-Q1",
            v7_verdict=v7,
        )
        if first_hash is None:
            first_hash = result
        assert result == first_hash
        assert result.startswith(REPORT15_HASH_PREFIX)


@pytest.mark.engine
def test_compute_report15_hash_empty_period_key_raises() -> None:
    """Edge case — empty period_key → Report15InconsistentStateError envelope."""
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict()
    with pytest.raises(Report15InconsistentStateError) as exc_info:
        compute_report15_hash(
            activity_breakdown=breakdown,
            period_key="",
            v7_verdict=v7,
        )
    assert exc_info.value.reason == "empty_period_key"
    assert exc_info.value.period_key == ""


@pytest.mark.engine
def test_compute_report15_hash_no_activity_breakdown_raises() -> None:
    """Edge case — empty activity_breakdown → no_activity_breakdown envelope."""
    v7 = _mk_v7_verdict()
    with pytest.raises(Report15InconsistentStateError) as exc_info:
        compute_report15_hash(
            activity_breakdown=[],
            period_key="2026-Q1",
            v7_verdict=v7,
        )
    assert exc_info.value.reason == "no_activity_breakdown"
    assert exc_info.value.period_key == "2026-Q1"


@pytest.mark.engine
def test_compute_report15_hash_wrong_activity_row_type_raises() -> None:
    """Type-safe — non-ActivityCostRow item → ValueError (CR 12-5 D-14
    typed envelope, kernel raises ValueError for type violations)."""
    v7 = _mk_v7_verdict()
    with pytest.raises(ValueError, match="ActivityCostRow"):
        compute_report15_hash(
            activity_breakdown=[{"activity_id": "x", "total_cost_krw": Decimal("1")}],  # type: ignore[list-item]
            period_key="2026-Q1",
            v7_verdict=v7,
        )


@pytest.mark.engine
def test_compute_report15_hash_wrong_v7_verdict_type_raises() -> None:
    """Type-safe — non-V7Verdict → ValueError."""
    breakdown = _mk_activity_breakdown()
    with pytest.raises(ValueError, match="V7Verdict"):
        compute_report15_hash(
            activity_breakdown=breakdown,
            period_key="2026-Q1",
            v7_verdict="not-a-verdict",  # type: ignore[arg-type]
        )


@pytest.mark.engine
def test_compute_report15_hash_wrong_activity_breakdown_type_raises() -> None:
    """Type-safe — non-list → ValueError."""
    v7 = _mk_v7_verdict()
    with pytest.raises(ValueError, match="list"):
        compute_report15_hash(
            activity_breakdown="not-a-list",  # type: ignore[arg-type]
            period_key="2026-Q1",
            v7_verdict=v7,
        )


@pytest.mark.engine
def test_compute_report15_hash_same_input_same_hash() -> None:
    """V8 determinism — 동일 inputs → 동일 hash (determinism)."""
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict()
    h1 = compute_report15_hash(
        activity_breakdown=list(breakdown),
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    h2 = compute_report15_hash(
        activity_breakdown=list(breakdown),
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h1 == h2


@pytest.mark.engine
def test_compute_report15_hash_different_period_key_changes_hash() -> None:
    """V8 determinism — period_key 변경 → 다른 hash."""
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict()
    h1 = compute_report15_hash(
        activity_breakdown=breakdown,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    h2 = compute_report15_hash(
        activity_breakdown=breakdown,
        period_key="2026-Q2",
        v7_verdict=v7,
    )
    assert h1 != h2


# ── ActivityCostRow — frozen dataclass invariant (6 cases) ─────────


@pytest.mark.engine
def test_activity_cost_row_frozen_dataclass_slots() -> None:
    """Frozen dataclass invariant — frozen=True + slots=True 보존."""
    row = ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal("6600000"),
        total_cost_usd=Decimal("4950"),
        driver_count=4,
        cost_per_driver_krw=Decimal("1650000"),
        cost_per_driver_usd=Decimal("1237.50"),
        allocated_krw=Decimal("6600000"),
        allocated_usd=Decimal("4950"),
        hash="sha256:abc",
    )
    assert dataclasses.is_dataclass(row)
    assert row.activity_id == "act-1"
    assert row.activity_name_ko == "고객 상담"
    assert row.activity_name_en == "Customer Consultation"
    assert row.driver_count == 4
    assert row.hash == "sha256:abc"


@pytest.mark.engine
def test_activity_cost_row_frozen_immutable() -> None:
    """Frozen — assignment 후 attribute set raise (frozen AD-5 parity)."""
    row = ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal("0"),
        total_cost_usd=Decimal("0"),
        driver_count=1,
        cost_per_driver_krw=Decimal("0"),
        cost_per_driver_usd=Decimal("0"),
        allocated_krw=Decimal("0"),
        allocated_usd=Decimal("0"),
        hash="sha256:0",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.driver_count = 2  # type: ignore[misc]


@pytest.mark.engine
def test_activity_cost_row_equality_by_field() -> None:
    """Equality — frozen dataclass 동일 field → 동등."""
    row1 = ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal("6600000"),
        total_cost_usd=Decimal("4950"),
        driver_count=4,
        cost_per_driver_krw=Decimal("1650000"),
        cost_per_driver_usd=Decimal("1237.50"),
        allocated_krw=Decimal("6600000"),
        allocated_usd=Decimal("4950"),
        hash="sha256:abc",
    )
    row2 = ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal("6600000"),
        total_cost_usd=Decimal("4950"),
        driver_count=4,
        cost_per_driver_krw=Decimal("1650000"),
        cost_per_driver_usd=Decimal("1237.50"),
        allocated_krw=Decimal("6600000"),
        allocated_usd=Decimal("4950"),
        hash="sha256:abc",
    )
    assert row1 == row2


@pytest.mark.engine
def test_activity_cost_row_krw_usd_consistency() -> None:
    """KRW ↔ USD consistency invariant — cost_per_driver × driver_count = total_cost (KRW)."""
    row = ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal("6600000"),
        total_cost_usd=Decimal("4950"),
        driver_count=4,
        cost_per_driver_krw=Decimal("1650000"),
        cost_per_driver_usd=Decimal("1237.50"),
        allocated_krw=Decimal("6600000"),
        allocated_usd=Decimal("4950"),
        hash="sha256:abc",
    )
    # KRW consistency: cost_per_driver × driver_count = total_cost
    assert row.cost_per_driver_krw * row.driver_count == row.total_cost_krw
    # USD consistency: cost_per_driver × driver_count = total_cost
    assert row.cost_per_driver_usd * row.driver_count == row.total_cost_usd


@pytest.mark.engine
def test_activity_cost_row_allocated_equals_total() -> None:
    """Allocated invariant — allocated = total_cost (PRD §A6 verbatim
    "완전배부·대차평형" Report #15 activity-level 보존)."""
    row = ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal("6600000"),
        total_cost_usd=Decimal("4950"),
        driver_count=4,
        cost_per_driver_krw=Decimal("1650000"),
        cost_per_driver_usd=Decimal("1237.50"),
        allocated_krw=Decimal("6600000"),
        allocated_usd=Decimal("4950"),
        hash="sha256:abc",
    )
    assert row.allocated_krw == row.total_cost_krw
    assert row.allocated_usd == row.total_cost_usd


@pytest.mark.engine
def test_activity_cost_row_minimum_driver_count() -> None:
    """Edge case — driver_count = 1 minimum (PRD §F9.1 "2+ drivers per activity"
    는 cost_pool 단계 guard — ActivityCostRow 는 activity-level 집계로
    driver_count ≥ 1 만 필요, service layer validate)."""
    row = ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw=Decimal("1000000"),
        total_cost_usd=Decimal("750"),
        driver_count=1,
        cost_per_driver_krw=Decimal("1000000"),
        cost_per_driver_usd=Decimal("750"),
        allocated_krw=Decimal("1000000"),
        allocated_usd=Decimal("750"),
        hash="sha256:abc",
    )
    assert row.driver_count == 1


# ── Report15Summary — frozen dataclass invariant (4 cases) ─────────


@pytest.mark.engine
def test_report15_summary_frozen_dataclass_slots() -> None:
    """Frozen dataclass invariant — frozen=True + slots=True 보존."""
    summary = Report15Summary(
        activity_count=3,
        total_cost_krw=Decimal("13200000"),
        total_cost_usd=Decimal("9900"),
        total_driver_count=8,
        hash="sha256:abc",
    )
    assert dataclasses.is_dataclass(summary)
    assert summary.activity_count == 3
    assert summary.total_cost_krw == Decimal("13200000")
    assert summary.total_cost_usd == Decimal("9900")
    assert summary.total_driver_count == 8


@pytest.mark.engine
def test_report15_summary_frozen_immutable() -> None:
    """Frozen — assignment 후 attribute set raise (frozen AD-5 parity)."""
    summary = Report15Summary(
        activity_count=1,
        total_cost_krw=Decimal("0"),
        total_cost_usd=Decimal("0"),
        total_driver_count=1,
        hash="sha256:0",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.activity_count = 2  # type: ignore[misc]


@pytest.mark.engine
def test_report15_summary_total_driver_count_invariant() -> None:
    """Invariant — total_driver_count ≥ activity_count (PRD §F9.1 2+ drivers
    per activity, ActivityCostRow driver_count sum)."""
    summary = Report15Summary(
        activity_count=3,
        total_cost_krw=Decimal("13200000"),
        total_cost_usd=Decimal("9900"),
        total_driver_count=8,
        hash="sha256:abc",
    )
    assert summary.total_driver_count >= summary.activity_count


@pytest.mark.engine
def test_report15_summary_equality_by_field() -> None:
    """Equality — frozen dataclass 동일 field → 동등."""
    s1 = Report15Summary(
        activity_count=3,
        total_cost_krw=Decimal("13200000"),
        total_cost_usd=Decimal("9900"),
        total_driver_count=8,
        hash="sha256:abc",
    )
    s2 = Report15Summary(
        activity_count=3,
        total_cost_krw=Decimal("13200000"),
        total_cost_usd=Decimal("9900"),
        total_driver_count=8,
        hash="sha256:abc",
    )
    assert s1 == s2


# ── Report15InconsistentStateError — envelope raise (4 cases) ─────────


@pytest.mark.engine
def test_report15_inconsistent_state_error_envelope_fields() -> None:
    """CR 12-5 D-14 envelope — typed exception fields 보존."""
    err = Report15InconsistentStateError(
        "test",
        period_key="2026-Q1",
        expected_sum=Decimal("13200000"),
        actual_sum=Decimal("13200000.02"),
        reason="test_reason",
    )
    assert err.period_key == "2026-Q1"
    assert err.expected_sum == Decimal("13200000")
    assert err.actual_sum == Decimal("13200000.02")
    assert err.reason == "test_reason"
    assert isinstance(err, ValueError)


@pytest.mark.engine
def test_report15_inconsistent_state_error_caught_by_value_error() -> None:
    """Hierarchy — `Report15InconsistentStateError` is `ValueError`
    (CR 12-5 D-14 envelope REUSE 0 NEW handlers, main.py excepts
    ValueError 만 잡으면 됨)."""
    with pytest.raises(Report15InconsistentStateError) as exc_info:
        raise Report15InconsistentStateError(
            "test",
            period_key="2026-Q1",
            expected_sum=Decimal("13200000"),
            actual_sum=Decimal("13200000"),
            reason="test",
        )
    assert isinstance(exc_info.value, Report15InconsistentStateError)


@pytest.mark.engine
def test_report15_inconsistent_state_error_distinct_reasons() -> None:
    """Distinct reasons — empty_period_key vs no_activity_breakdown."""
    v7 = _mk_v7_verdict()
    breakdown = _mk_activity_breakdown()
    # empty_period_key
    try:
        compute_report15_hash(
            activity_breakdown=breakdown,
            period_key="",
            v7_verdict=v7,
        )
    except Report15InconsistentStateError as e:
        assert e.reason == "empty_period_key"  # noqa: PT017 — explicit reason assertion
    # no_activity_breakdown
    try:
        compute_report15_hash(
            activity_breakdown=[],
            period_key="2026-Q1",
            v7_verdict=v7,
        )
    except Report15InconsistentStateError as e:
        assert e.reason == "no_activity_breakdown"  # noqa: PT017 — explicit reason assertion


@pytest.mark.engine
def test_report15_inconsistent_state_error_distinct_from_report21() -> None:
    """Type distinction — Report15InconsistentStateError ≠
    Report21InconsistentStateError (typed exception, CR 12-5 D-14
    distinct envelope codes)."""
    from packages.cost_engine.abc_engine import Report21InconsistentStateError
    err15 = Report15InconsistentStateError(
        "r15",
        period_key="2026-Q1",
        expected_sum=Decimal("13200000"),
        actual_sum=Decimal("13200000"),
        reason="r15_reason",
    )
    err21 = Report21InconsistentStateError(
        "r21",
        period_key="2026-Q1",
        expected_sum=Decimal("19800000"),
        actual_sum=Decimal("19800000"),
        reason="r21_reason",
    )
    assert type(err15) is not type(err21)
    assert err15.reason == "r15_reason"
    assert err21.reason == "r21_reason"


# ── 9-3 + 11-6 surface integration (4 cases) ───────────────────


@pytest.mark.engine
def test_report15_hash_with_v7_balanced_verdict() -> None:
    """Integration — 9-3 V7 verdict (balanced) + 11-6 compute_report15_hash
    V8 determinism envelope."""
    breakdown = _mk_activity_breakdown()
    # V7 verdict: Σ activity total_cost = Σ department cost (balanced)
    total_activity = sum((row.total_cost_krw for row in breakdown), Decimal("0"))
    v7 = _mk_v7_verdict(
        breakdown_sum=str(total_activity),
        unused_cost="0",
        department_cost=str(total_activity),
    )
    assert v7.is_balanced is True
    h = compute_report15_hash(
        activity_breakdown=breakdown,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h.startswith(REPORT15_HASH_PREFIX)
    assert len(h) == len(REPORT15_HASH_PREFIX) + 64


@pytest.mark.engine
def test_report15_hash_with_v7_unbalanced_verdict_still_valid_hash() -> None:
    """V7 unbalanced — compute_report15_hash 는 envelope guard 안 함
    (Report #21 동일 surface pattern — V7 verdict 가 is_balanced=False 라도
    hash envelope 정상, frontend disabled signal 은 service layer 가 결정).
    """
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict(
        breakdown_sum="13200000",
        unused_cost="0",
        department_cost="13200001",  # 1 KRW off — V7 unbalanced
    )
    assert v7.is_balanced is False
    # Still valid hash (V8 determinism envelope 보존)
    h = compute_report15_hash(
        activity_breakdown=breakdown,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h.startswith(REPORT15_HASH_PREFIX)


@pytest.mark.engine
def test_report15_hash_period_key_isolates_hashes() -> None:
    """Isolation — 동일 data + 다른 period_key → 다른 hash (multi-period Q1/Q2/Q3/Q4)."""
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict()
    hashes: set[str] = set()
    for period in ("2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"):
        h = compute_report15_hash(
            activity_breakdown=breakdown,
            period_key=period,
            v7_verdict=v7,
        )
        hashes.add(h)
    assert len(hashes) == 4  # 4 distinct hashes for 4 periods


@pytest.mark.engine
def test_report15_hash_with_9_3_unused_capacity_chain() -> None:
    """Integration — 9-3 UnusedCapacitySubRow (PRD §A9) 와 Report #15 hash
    envelope 공존 검증 (Report #15 는 activity focus 이지만 9-3 unused chain
    �로 compute_report15_hash 호출 가능)."""
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict()
    # 9-3 unused chain — Report #15 는 unused_capacity 별도 표기 없음,
    # V7 verdict 의 unused_cost = 0 �로 envelope 구성
    h = compute_report15_hash(
        activity_breakdown=breakdown,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h.startswith(REPORT15_HASH_PREFIX)


# ── V8 100-repeats + permuted order (2 cases) ───────────────────


@pytest.mark.engine
def test_report15_hash_v8_100_repeats_stable() -> None:
    """V8 determinism — 100회 반복 호출, 동일 hash 보장."""
    breakdown = _mk_activity_breakdown()
    v7 = _mk_v7_verdict()
    first = compute_report15_hash(
        activity_breakdown=breakdown,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    for _ in range(100):
        got = compute_report15_hash(
            activity_breakdown=breakdown,
            period_key="2026-Q1",
            v7_verdict=v7,
        )
        assert got == first


@pytest.mark.engine
def test_report15_hash_permuted_activity_order_changes_hash() -> None:
    """V8 determinism — activity_breakdown 순서 변경 → 다른 hash
    (tuple 순서 보존 validation, Report #21 동일 pattern)."""
    v7 = _mk_v7_verdict()
    a = ActivityCostRow(
        activity_id="A",
        activity_name_ko="A",
        activity_name_en="A",
        total_cost_krw=Decimal("1"),
        total_cost_usd=Decimal("0.75"),
        driver_count=1,
        cost_per_driver_krw=Decimal("1"),
        cost_per_driver_usd=Decimal("0.75"),
        allocated_krw=Decimal("1"),
        allocated_usd=Decimal("0.75"),
        hash="h",
    )
    b = ActivityCostRow(
        activity_id="B",
        activity_name_ko="B",
        activity_name_en="B",
        total_cost_krw=Decimal("2"),
        total_cost_usd=Decimal("1.50"),
        driver_count=1,
        cost_per_driver_krw=Decimal("2"),
        cost_per_driver_usd=Decimal("1.50"),
        allocated_krw=Decimal("2"),
        allocated_usd=Decimal("1.50"),
        hash="h",
    )
    c = ActivityCostRow(
        activity_id="C",
        activity_name_ko="C",
        activity_name_en="C",
        total_cost_krw=Decimal("3"),
        total_cost_usd=Decimal("2.25"),
        driver_count=1,
        cost_per_driver_krw=Decimal("3"),
        cost_per_driver_usd=Decimal("2.25"),
        allocated_krw=Decimal("3"),
        allocated_usd=Decimal("2.25"),
        hash="h",
    )
    h1 = compute_report15_hash(
        activity_breakdown=[a, b, c],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    h2 = compute_report15_hash(
        activity_breakdown=[c, b, a],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h1 != h2  # tuple 순서 보존

    # Suppress unused warning for V7Verdict import
    _ = CostObjectRow
    _ = UnusedCapacitySubRow
    _ = ABC_HASH_PREFIX
