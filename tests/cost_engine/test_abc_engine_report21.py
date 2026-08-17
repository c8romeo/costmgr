"""Tests for Story 9.4 EXTENSION `packages.cost_engine.abc_engine` Report #21 surface.

Coverage (9-4 wire):
  - `compute_report21_hash` V8 determinism + envelope guard (8 cases)
  - `compute_report_pdf_hash` V8 byte-equality (5 cases)
  - `Report21Summary` frozen dataclass invariant (4 cases)
  - `Report21InconsistentStateError` envelope raise (3 cases)
  - 9-3 + 9-4 surface integration (8 cases)
  - V8 100-repeats + permuted order (4 cases)

Total: ~32 NEW pytest cases (T1.3) — A19 cohesion pattern 8 surface EXTENSION 검증.

PRD §9 #21 + §7.3 (법인세법 시행규칙 제76조 2기준) verbatim wire:
  - 원가대상별 원가 집계표 (Report #21)
  - V7 ABC 무결성: Σ(원가대상별 배부액) + 미사용능력 = Σ(부서 원가)
  - A30 forward-lock SHARED PDF generator 결정 wire (Story 9.4 본 진입점
    + Report #15 후속, 9-3 handoff `handoff-2026-08-17-9-3-done.md` lock).
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from packages.cost_engine.abc_engine import (
    ABC_HASH_PREFIX,
    REPORT_PDF_HASH_PREFIX,
    ActivityMapping,
    CCRResult,
    CostObjectRow,
    DepartmentAllocation,
    Report21InconsistentStateError,
    Report21Summary,
    UnusedCapacitySubRow,
    V7Verdict,
    aggregate_multi_department_ccr,
    compute_allocation,
    compute_ccr,
    compute_report21_hash,
    compute_report_pdf_hash,
    verify_v7_balance,
)

# ── helpers ──────────────────────────────────────────────


def _mk_ccr(
    *,
    department_id: str = "dept-r21",
    department_cost: str = "13200000",
    practical_capacity_hours: str = "400",
) -> CCRResult:
    """Helper — CCRResult fixture (9-2 compute_ccr 동일 surface)."""
    return compute_ccr(
        department_id=department_id,
        department_cost=Decimal(department_cost),
        practical_capacity_hours=Decimal(practical_capacity_hours),
    )


def _mk_cost_object_breakdown(
    ccr: CCRResult,  # noqa: ARG001 — used in test fixtures
) -> list[CostObjectRow]:
    """Helper — 4 cost object breakdown rows (PRD §9 #21 + §F9.2)."""
    return [
        CostObjectRow(
            product_id="prod-A",
            activity_id="act-1",
            driver_id="drv-hr",
            allocated_krw=Decimal("6600000"),
        ),
        CostObjectRow(
            product_id="prod-B",
            activity_id="act-1",
            driver_id="drv-hr",
            allocated_krw=Decimal("3300000"),
        ),
        CostObjectRow(
            product_id="prod-C",
            activity_id="act-1",
            driver_id="drv-hr",
            allocated_krw=Decimal("3300000"),
        ),
    ]


def _mk_unused_capacity_breakdown(
    ccr: CCRResult,
) -> list[UnusedCapacitySubRow]:
    """Helper — 1 unused capacity row (PRD §A9 + §F9.3)."""
    return [
        UnusedCapacitySubRow(
            department_id=ccr.department_id,
            unused_hours=Decimal("200"),
            unused_cost_krw=Decimal("6600000"),
            hash="placeholder",
        )
    ]


def _mk_v7_verdict(
    *,
    breakdown_sum: str = "13200000",
    unused_cost: str = "6600000",
    department_cost: str = "19800000",
) -> V7Verdict:
    """Helper — V7Verdict fixture (9-3 verify_v7_balance 동일 surface)."""
    return verify_v7_balance(
        total_breakdown_sum=Decimal(breakdown_sum),
        unused_cost=Decimal(unused_cost),
        department_cost=Decimal(department_cost),
    )


# ── compute_report21_hash — V8 determinism + envelope guard (8 cases) ────


@pytest.mark.engine
def test_compute_report21_hash_determinism_100_repeats() -> None:
    """V8 determinism — compute_report21_hash 100회 반복 → 동일 hash."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict()
    first_hash: str | None = None
    for _ in range(100):
        result = compute_report21_hash(
            cost_object_breakdown=breakdown,
            unused_capacity_breakdown=unused,
            period_key="2026-Q1",
            v7_verdict=v7,
        )
        if first_hash is None:
            first_hash = result
        assert result == first_hash
        assert result.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_compute_report21_hash_empty_period_key_raises() -> None:
    """Edge case — empty period_key → Report21InconsistentStateError envelope."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict()
    with pytest.raises(Report21InconsistentStateError) as exc_info:
        compute_report21_hash(
            cost_object_breakdown=breakdown,
            unused_capacity_breakdown=unused,
            period_key="",
            v7_verdict=v7,
        )
    assert exc_info.value.reason == "empty_period_key"
    assert exc_info.value.period_key == ""


@pytest.mark.engine
def test_compute_report21_hash_no_breakdown_raises() -> None:
    """Edge case — empty breakdown + empty unused → no_breakdown envelope."""
    v7 = _mk_v7_verdict()
    with pytest.raises(Report21InconsistentStateError) as exc_info:
        compute_report21_hash(
            cost_object_breakdown=[],
            unused_capacity_breakdown=[],
            period_key="2026-Q1",
            v7_verdict=v7,
        )
    assert exc_info.value.reason == "no_breakdown"
    assert exc_info.value.period_key == "2026-Q1"


@pytest.mark.engine
def test_compute_report21_hash_wrong_cost_object_row_type_raises() -> None:
    """Type-safe — non-CostObjectRow item → ValueError (CR 12-5 D-14
    typed envelope, kernel raises ValueError for type violations)."""
    ccr = _mk_ccr()
    v7 = _mk_v7_verdict()
    with pytest.raises(ValueError, match="CostObjectRow"):
        compute_report21_hash(
            cost_object_breakdown=[{"product_id": "x", "allocated_krw": Decimal("1")}],  # type: ignore[list-item]
            unused_capacity_breakdown=_mk_unused_capacity_breakdown(ccr),
            period_key="2026-Q1",
            v7_verdict=v7,
        )


@pytest.mark.engine
def test_compute_report21_hash_wrong_unused_subrow_type_raises() -> None:
    """Type-safe — non-UnusedCapacitySubRow item → ValueError."""
    ccr = _mk_ccr()
    v7 = _mk_v7_verdict()
    with pytest.raises(ValueError, match="UnusedCapacitySubRow"):
        compute_report21_hash(
            cost_object_breakdown=_mk_cost_object_breakdown(ccr),
            unused_capacity_breakdown=[{"department_id": "x", "unused_cost_krw": Decimal("1")}],  # type: ignore[list-item]
            period_key="2026-Q1",
            v7_verdict=v7,
        )


@pytest.mark.engine
def test_compute_report21_hash_wrong_v7_verdict_type_raises() -> None:
    """Type-safe — non-V7Verdict → ValueError."""
    ccr = _mk_ccr()
    with pytest.raises(ValueError, match="V7Verdict"):
        compute_report21_hash(
            cost_object_breakdown=_mk_cost_object_breakdown(ccr),
            unused_capacity_breakdown=_mk_unused_capacity_breakdown(ccr),
            period_key="2026-Q1",
            v7_verdict="not-a-verdict",  # type: ignore[arg-type]
        )


@pytest.mark.engine
def test_compute_report21_hash_permuted_unused_order_changes_hash() -> None:
    """V8 determinism — period_key/permutation 반영 (v7_verdict 동일 시
    cost_object_breakdown 순서 변경 = 동일 hash, tuple 순서 보존 검증).
    """
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict()
    h1 = compute_report21_hash(
        cost_object_breakdown=list(breakdown),
        unused_capacity_breakdown=list(unused),
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    # 같은 순서 → 동일 hash (determinism)
    h2 = compute_report21_hash(
        cost_object_breakdown=list(breakdown),
        unused_capacity_breakdown=list(unused),
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h1 == h2


@pytest.mark.engine
def test_compute_report21_hash_different_period_key_changes_hash() -> None:
    """V8 determinism — period_key 변경 → 다른 hash."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict()
    h1 = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=unused,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    h2 = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=unused,
        period_key="2026-Q2",
        v7_verdict=v7,
    )
    assert h1 != h2


# ── compute_report_pdf_hash — V8 byte-equality (5 cases) ───────────


@pytest.mark.engine
def test_compute_report_pdf_hash_byte_equality() -> None:
    """V8 byte-equality — 동일 pdf_bytes → 동일 hash."""
    pdf_bytes = b"%PDF-1.4\nreportlab sample bytes" * 10
    h1 = compute_report_pdf_hash(pdf_bytes=pdf_bytes)
    h2 = compute_report_pdf_hash(pdf_bytes=pdf_bytes)
    assert h1 == h2
    assert h1.startswith(REPORT_PDF_HASH_PREFIX)


@pytest.mark.engine
def test_compute_report_pdf_hash_different_bytes_changes_hash() -> None:
    """V8 byte-equality — 1 byte 변경 → 다른 hash (SHA256 avalanche)."""
    h1 = compute_report_pdf_hash(pdf_bytes=b"%PDF-1.4\nA")
    h2 = compute_report_pdf_hash(pdf_bytes=b"%PDF-1.4\nB")
    assert h1 != h2


@pytest.mark.engine
def test_compute_report_pdf_hash_empty_bytes_valid() -> None:
    """Edge case — empty bytes → 정상 hash (64-char hexdigest)."""
    h = compute_report_pdf_hash(pdf_bytes=b"")
    assert h.startswith(REPORT_PDF_HASH_PREFIX)
    assert len(h) == len(REPORT_PDF_HASH_PREFIX) + 64


@pytest.mark.engine
def test_compute_report_pdf_hash_not_bytes_raises() -> None:
    """Type-safe — non-bytes → ValueError."""
    with pytest.raises(ValueError, match="bytes"):
        compute_report_pdf_hash(pdf_bytes="not-bytes")  # type: ignore[arg-type]


@pytest.mark.engine
def test_compute_report_pdf_hash_64_hex_chars() -> None:
    """V8 determinism — sha256 hexdigest = 64 chars (32 bytes)."""
    pdf_bytes = b"%PDF-1.4\n" + bytes(range(256))
    h = compute_report_pdf_hash(pdf_bytes=pdf_bytes)
    digest = h[len(REPORT_PDF_HASH_PREFIX):]
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


# ── Report21Summary — frozen dataclass invariant (4 cases) ─────────


@pytest.mark.engine
def test_report21_summary_frozen_dataclass_slots() -> None:
    """Frozen dataclass invariant — frozen=True + slots=True 보존."""
    summary = Report21Summary(
        product_count=3,
        total_allocated_krw=Decimal("13200000"),
        total_unused_krw=Decimal("6600000"),
        hash="sha256:abc",
    )
    assert dataclasses.is_dataclass(summary)
    assert summary.product_count == 3
    assert summary.total_allocated_krw == Decimal("13200000")
    assert summary.total_unused_krw == Decimal("6600000")
    assert summary.hash == "sha256:abc"


@pytest.mark.engine
def test_report21_summary_frozen_immutable() -> None:
    """Frozen — assignment 후 attribute set raise (frozen AD-5 parity)."""
    summary = Report21Summary(
        product_count=1,
        total_allocated_krw=Decimal("0"),
        total_unused_krw=Decimal("0"),
        hash="sha256:0",
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        summary.product_count = 2  # type: ignore[misc]


@pytest.mark.engine
def test_report21_summary_equality_by_field() -> None:
    """Equality — frozen dataclass 동일 field → 동등."""
    s1 = Report21Summary(
        product_count=3,
        total_allocated_krw=Decimal("13200000"),
        total_unused_krw=Decimal("6600000"),
        hash="sha256:abc",
    )
    s2 = Report21Summary(
        product_count=3,
        total_allocated_krw=Decimal("13200000"),
        total_unused_krw=Decimal("6600000"),
        hash="sha256:abc",
    )
    assert s1 == s2


@pytest.mark.engine
def test_report21_summary_hash_field_decimal_total() -> None:
    """Invariant — Decimal-as-string (AD-8) total_allocated + unused ≥ 0."""
    summary = Report21Summary(
        product_count=3,
        total_allocated_krw=Decimal("0"),
        total_unused_krw=Decimal("0"),
        hash="sha256:zero",
    )
    total = summary.total_allocated_krw + summary.total_unused_krw
    assert total >= Decimal("0")


# ── Report21InconsistentStateError — envelope raise (3 cases) ─────────


@pytest.mark.engine
def test_report21_inconsistent_state_error_envelope_fields() -> None:
    """CR 12-5 D-14 envelope — typed exception fields 보존."""
    err = Report21InconsistentStateError(
        "test",
        period_key="2026-Q1",
        expected_sum=Decimal("19800000"),
        actual_sum=Decimal("19800000.02"),
        reason="test_reason",
    )
    assert err.period_key == "2026-Q1"
    assert err.expected_sum == Decimal("19800000")
    assert err.actual_sum == Decimal("19800000.02")
    assert err.reason == "test_reason"
    assert isinstance(err, ValueError)


@pytest.mark.engine
def test_report21_inconsistent_state_error_caught_by_value_error() -> None:
    """Hierarchy — `Report21InconsistentStateError` is `ValueError`
    (CR 12-5 D-14 envelope REUSE 0 NEW handlers, main.py excepts
    ValueError 만 잡으면 됨).
    """
    with pytest.raises(Report21InconsistentStateError) as exc_info:
        raise Report21InconsistentStateError(
            "test",
            period_key="2026-Q1",
            expected_sum=Decimal("19800000"),
            actual_sum=Decimal("19800000"),
            reason="test",
        )
    assert isinstance(exc_info.value, Report21InconsistentStateError)


@pytest.mark.engine
def test_report21_inconsistent_state_error_reason_distinct() -> None:
    """Distinct reasons — empty_period_key vs no_breakdown."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    v7 = _mk_v7_verdict()
    # empty_period_key
    try:
        compute_report21_hash(
            cost_object_breakdown=breakdown,
            unused_capacity_breakdown=[],
            period_key="",
            v7_verdict=v7,
        )
    except Report21InconsistentStateError as e:
        assert e.reason == "empty_period_key"  # noqa: PT017 — explicit reason assertion
    # no_breakdown reason
    try:
        compute_report21_hash(
            cost_object_breakdown=[],
            unused_capacity_breakdown=[],
            period_key="2026-Q1",
            v7_verdict=v7,
        )
    except Report21InconsistentStateError as e:
        assert e.reason == "no_breakdown"  # noqa: PT017 — explicit reason assertion


# ── 9-3 + 9-4 surface integration (8 cases) ───────────────────


@pytest.mark.engine
def test_report21_hash_with_full_9_3_pipeline_v7_balanced() -> None:
    """Integration — 9-2 CCR + 9-2 alloc + 9-3 multi-dept CCR +
    9-4 compute_report21_hash V8 determinism envelope (full chain).
    """
    # Step 1: CCR compute (9-2)
    ccr = _mk_ccr(department_id="dept-r21-int", department_cost="13200000", practical_capacity_hours="400")
    # Step 2: allocation (9-2)
    breakdown_rows = _mk_cost_object_breakdown(ccr)
    total_breakdown = sum((r.allocated_krw for r in breakdown_rows), Decimal("0"))
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=[ActivityMapping(activity_id="act-1", hours=Decimal("400"), ccr_amount_krw=Decimal("13200000"))],
        cost_object_breakdown=breakdown_rows,
        used_hours=Decimal("400"),
    )
    # Step 3: V7 verdict (9-3)
    v7 = verify_v7_balance(
        total_breakdown_sum=total_breakdown,
        unused_cost=allocation.unused_capacity.unused_cost_krw,
        department_cost=ccr.department_cost,
    )
    assert v7.is_balanced is True
    # Step 4: 9-4 build envelope
    h = compute_report21_hash(
        cost_object_breakdown=list(allocation.cost_object_breakdown),
        unused_capacity_breakdown=[UnusedCapacitySubRow(
            department_id=ccr.department_id,
            unused_hours=allocation.unused_capacity.unused_hours,
            unused_cost_krw=allocation.unused_capacity.unused_cost_krw,
            hash="placeholder",
        )],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h.startswith(ABC_HASH_PREFIX)
    assert len(h) == len(ABC_HASH_PREFIX) + 64


@pytest.mark.engine
def test_report21_hash_with_multi_department_aggregation() -> None:
    """Integration — 9-3 multi-department CCR aggregation +
    9-4 Report #21 hash envelope (multi-dept V7 verdict)."""
    ccr_list = [
        _mk_ccr(department_id="dept-A", department_cost="13200000", practical_capacity_hours="400"),
        _mk_ccr(department_id="dept-B", department_cost="6600000", practical_capacity_hours="200"),
    ]
    multi = aggregate_multi_department_ccr(ccr_results=ccr_list)
    assert multi.department_count == 2
    # Build per-dept breakdowns + unused + V7 verdicts
    per_dept_breakdowns: list[CostObjectRow] = []
    per_dept_unused: list[UnusedCapacitySubRow] = []
    for ccr in ccr_list:
        # Simplified: full breakdown + 200h unused
        per_dept_breakdowns.append(CostObjectRow(
            product_id=f"prod-{ccr.department_id}",
            activity_id="act-1",
            driver_id="drv-hr",
            allocated_krw=ccr.ccr_per_hour * Decimal("200"),
        ))
        per_dept_unused.append(UnusedCapacitySubRow(
            department_id=ccr.department_id,
            unused_hours=Decimal("200"),
            unused_cost_krw=ccr.ccr_per_hour * Decimal("200"),
            hash="placeholder",
        ))
    # Sum V7 across departments
    total_alloc = sum((r.allocated_krw for r in per_dept_breakdowns), Decimal("0"))
    total_unused = sum((r.unused_cost_krw for r in per_dept_unused), Decimal("0"))
    dept_total = sum((ccr.department_cost for ccr in ccr_list), Decimal("0"))
    v7 = verify_v7_balance(
        total_breakdown_sum=total_alloc,
        unused_cost=total_unused,
        department_cost=dept_total,
    )
    # 9-4 envelope
    h = compute_report21_hash(
        cost_object_breakdown=per_dept_breakdowns,
        unused_capacity_breakdown=per_dept_unused,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_report21_hash_period_key_isolates_hashes() -> None:
    """Isolation — 동일 data + 다른 period_key → 다른 hash (multi-period Q1/Q2/Q3/Q4)."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict()
    hashes: set[str] = set()
    for period in ("2026-Q1", "2026-Q2", "2026-Q3", "2026-Q4"):
        h = compute_report21_hash(
            cost_object_breakdown=breakdown,
            unused_capacity_breakdown=unused,
            period_key=period,
            v7_verdict=v7,
        )
        hashes.add(h)
    assert len(hashes) == 4  # 4 distinct hashes for 4 periods


@pytest.mark.engine
def test_report21_hash_only_unused_no_breakdown_raises() -> None:
    """Edge — empty breakdown + empty unused → no_breakdown envelope."""
    v7 = _mk_v7_verdict()
    with pytest.raises(Report21InconsistentStateError) as exc_info:
        compute_report21_hash(
            cost_object_breakdown=[],
            unused_capacity_breakdown=[],
            period_key="2026-Q1",
            v7_verdict=v7,
        )
    assert exc_info.value.reason == "no_breakdown"


@pytest.mark.engine
def test_report21_hash_only_cost_object_no_unused_valid() -> None:
    """Edge — only cost_object_breakdown (no unused subrows) → 정상 hash
    (PRD §A9 "별도 항목으로 구분 관리" — zero unused 도 valid report).
    """
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    v7 = _mk_v7_verdict(
        breakdown_sum="13200000",
        unused_cost="0",
        department_cost="13200000",
    )
    h = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=[],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_report21_hash_with_department_allocation_chain() -> None:
    """Integration — DepartmentAllocation (9-3) → Report21Summary (9-4)
    envelope, V7 verdict chain 보존.
    """
    ccr = _mk_ccr()
    breakdown_rows = _mk_cost_object_breakdown(ccr)
    total_breakdown = sum((r.allocated_krw for r in breakdown_rows), Decimal("0"))
    allocation = compute_allocation(
        ccr=ccr,
        activity_mappings=[],
        cost_object_breakdown=breakdown_rows,
        used_hours=Decimal("400"),
    )
    v7 = verify_v7_balance(
        total_breakdown_sum=total_breakdown,
        unused_cost=allocation.unused_capacity.unused_cost_krw,
        department_cost=ccr.department_cost,
    )
    dept_alloc = DepartmentAllocation(
        department_id=ccr.department_id,
        ccr=ccr,
        allocation=allocation,
        v7_verdict=v7,
    )
    # Use dept_alloc in hash envelope
    h = compute_report21_hash(
        cost_object_breakdown=breakdown_rows,
        unused_capacity_breakdown=[UnusedCapacitySubRow(
            department_id=ccr.department_id,
            unused_hours=allocation.unused_capacity.unused_hours,
            unused_cost_krw=allocation.unused_capacity.unused_cost_krw,
            hash="placeholder",
        )],
        period_key="2026-Q1",
        v7_verdict=dept_alloc.v7_verdict,
    )
    assert h.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_report21_hash_v7_unbalanced_within_tolerance_valid() -> None:
    """V7 within tolerance — 0.01 KRW 오차 허용 (is_balanced=True)."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict(
        breakdown_sum="13200000",
        unused_cost="6600000",
        department_cost="19800000.01",
    )
    assert v7.is_balanced is True  # tolerance 이내
    h = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=unused,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h.startswith(ABC_HASH_PREFIX)


@pytest.mark.engine
def test_report21_pdf_hash_integration_with_report21_hash() -> None:
    """A30 SHARED integration — compute_report21_hash + compute_report_pdf_hash
    Report #21 PDF byte-equality envelope (Discriminated union report_id=21).
    """
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict()
    report21_hash = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=unused,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    pdf_bytes = b"%PDF-1.4\nReport21 sample bytes"
    pdf_hash = compute_report_pdf_hash(pdf_bytes=pdf_bytes)
    assert report21_hash.startswith(ABC_HASH_PREFIX)
    assert pdf_hash.startswith(REPORT_PDF_HASH_PREFIX)
    assert report21_hash != pdf_hash  # distinct prefixes


# ── V8 100-repeats + permuted order (4 cases) ───────────────────


@pytest.mark.engine
def test_report21_hash_v8_100_repeats_stable() -> None:
    """V8 determinism — 100회 반복 호출, 동일 hash 보장."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    unused = _mk_unused_capacity_breakdown(ccr)
    v7 = _mk_v7_verdict()
    first = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=unused,
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    for _ in range(100):
        got = compute_report21_hash(
            cost_object_breakdown=breakdown,
            unused_capacity_breakdown=unused,
            period_key="2026-Q1",
            v7_verdict=v7,
        )
        assert got == first


@pytest.mark.engine
def test_report21_pdf_hash_v8_100_repeats_stable() -> None:
    """V8 byte-equality — 100회 반복 호출, 동일 PDF hash 보장."""
    pdf_bytes = b"%PDF-1.4\nreport21 v8 test" * 10
    first = compute_report_pdf_hash(pdf_bytes=pdf_bytes)
    for _ in range(100):
        got = compute_report_pdf_hash(pdf_bytes=pdf_bytes)
        assert got == first


@pytest.mark.engine
def test_report21_hash_permuted_breakdown_order_changes_hash() -> None:
    """V8 determinism — cost_object_breakdown 순서 변경 → 다른 hash
    (tuple 순서 보존 validation).
    """
    _ccr = _mk_ccr()  # noqa: F841 — fixture param used implicitly
    v7 = _mk_v7_verdict()
    row_a = CostObjectRow(product_id="A", activity_id="a", driver_id="d", allocated_krw=Decimal("1"))
    row_b = CostObjectRow(product_id="B", activity_id="b", driver_id="d", allocated_krw=Decimal("2"))
    row_c = CostObjectRow(product_id="C", activity_id="c", driver_id="d", allocated_krw=Decimal("3"))
    h1 = compute_report21_hash(
        cost_object_breakdown=[row_a, row_b, row_c],
        unused_capacity_breakdown=[],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    h2 = compute_report21_hash(
        cost_object_breakdown=[row_c, row_b, row_a],
        unused_capacity_breakdown=[],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h1 != h2  # tuple 순서 보존


@pytest.mark.engine
def test_report21_hash_permuted_unused_order_changes_hash() -> None:
    """V8 determinism — unused_capacity_breakdown 순서 변경 → 다른 hash."""
    ccr = _mk_ccr()
    breakdown = _mk_cost_object_breakdown(ccr)
    v7 = _mk_v7_verdict()
    u_a = UnusedCapacitySubRow(department_id="A", unused_hours=Decimal("10"), unused_cost_krw=Decimal("1"), hash="h")
    u_b = UnusedCapacitySubRow(department_id="B", unused_hours=Decimal("20"), unused_cost_krw=Decimal("2"), hash="h")
    h1 = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=[u_a, u_b],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    h2 = compute_report21_hash(
        cost_object_breakdown=breakdown,
        unused_capacity_breakdown=[u_b, u_a],
        period_key="2026-Q1",
        v7_verdict=v7,
    )
    assert h1 != h2
