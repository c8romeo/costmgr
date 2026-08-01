"""tests.services.test_m2_input_completion — pure-function tests for stream_completion.

Story 3.1 — Task 1.

These tests have NO DB, NO web, NO clock dependency. They verify:
- 6-stream labels match PRD §8.M2(b)
- Industry → visible-streams map (service hides production)
- compute_stream_completion pure function (yellow dot decision)
- is_all_streams_complete aggregate gate
- STREAM_ORDER is stable (UI ordering regression guard)

Per AD-5 / AD-15: tests live alongside the canonical domain code and run
under `pytest tests/services/`. Drift between Python + TS mirror is
caught by `tests/integration/test_m2_input_label_consistency.py`.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from packages.services.m0_onboarding.industry_menu import Industry
from packages.services.m2_input.stream_completion import (
    STREAM_LABELS_KO,
    STREAM_ORDER,
    STREAMS_FOR_INDUSTRY,
    compute_stream_completion,
    is_all_streams_complete,
)


# ───────────────────────────────────────────────────────────────
# Industry → streams visibility (AC #1, #6)
# ───────────────────────────────────────────────────────────────
def test_streams_for_manufacturing_returns_six_streams() -> None:
    """제조업은 6 stream 모두 노출 (orders, production, sales, purchases, expenses, labor)."""
    streams = STREAMS_FOR_INDUSTRY[Industry.MANUFACTURING]
    assert len(streams) == 6
    assert streams == frozenset(
        {"orders", "production", "sales", "purchases", "expenses", "labor"}
    )


def test_streams_for_service_returns_five_streams_no_production() -> None:
    """서비스업은 5 stream (production hidden). PRD §8.M2(b)."""
    streams = STREAMS_FOR_INDUSTRY[Industry.SERVICE]
    assert len(streams) == 5
    assert "production" not in streams
    assert streams == frozenset(
        {"orders", "sales", "purchases", "expenses", "labor"}
    )


def test_streams_for_manufacturing_service_returns_six() -> None:
    """제조+서비스 겸영은 6 stream 모두 노출."""
    streams = STREAMS_FOR_INDUSTRY[Industry.MANUFACTURING_SERVICE]
    assert len(streams) == 6
    assert "production" in streams


def test_streams_for_manufacturing_service_other_returns_six() -> None:
    """제조+서비스+기타도 6 stream 모두 노출."""
    streams = STREAMS_FOR_INDUSTRY[Industry.MANUFACTURING_SERVICE_OTHER]
    assert len(streams) == 6
    assert "production" in streams


def test_streams_for_industry_is_complete_map() -> None:
    """모든 Industry enum 값이 STREAMS_FOR_INDUSTRY에 매핑되어 있어야 함."""
    for industry in Industry:
        assert industry in STREAMS_FOR_INDUSTRY
        assert len(STREAMS_FOR_INDUSTRY[industry]) >= 5  # 최소 5 stream 보장


# ───────────────────────────────────────────────────────────────
# STREAM_LABELS_KO (AC #1)
# ───────────────────────────────────────────────────────────────
def test_stream_labels_match_prd_section_8_m2_b() -> None:
    """PRD §8.M2(b) 한국어 라벨 정확 일치 — 회귀 방지."""
    assert STREAM_LABELS_KO == {
        "orders": "주문",
        "production": "생산",
        "sales": "판매",
        "purchases": "구매",
        "expenses": "경비",
        "labor": "인원",
    }


def test_stream_order_matches_prd_tab_order() -> None:
    """PRD §8.M2(b) 탭 순서: 주문 → 생산 → 판매 → 구매 → 경비 → 인원."""
    assert STREAM_ORDER == (
        "orders",
        "production",
        "sales",
        "purchases",
        "expenses",
        "labor",
    )


# ───────────────────────────────────────────────────────────────
# compute_stream_completion (AC #3)
# ───────────────────────────────────────────────────────────────
def test_compute_stream_completion_empty_all_false() -> None:
    """row counts가 모두 0 → 모든 visible stream completed=False (노란 점)."""
    status = compute_stream_completion(Industry.MANUFACTURING, rows_by_stream={})
    assert status.is_complete is False
    for stream, st in status.streams.items():
        assert st.completed is False
        assert st.row_count == 0


def test_compute_stream_completion_orders_present_only() -> None:
    """orders에만 row가 있으면 orders만 completed=True, 나머지 False."""
    status = compute_stream_completion(
        Industry.MANUFACTURING, rows_by_stream={"orders": 3}
    )
    assert status.streams["orders"].completed is True
    assert status.streams["orders"].row_count == 3
    assert status.streams["production"].completed is False
    assert status.is_complete is False
    # missing list는 PRD 순서대로 — orders 직후 production이 첫 미완료
    assert status.missing[0] == "생산"


def test_compute_stream_completion_all_present_for_manufacturing() -> None:
    """제조업 — 6 stream 모두 ≥1 row → is_complete=True."""
    rows = {s: 1 for s in STREAM_ORDER}
    status = compute_stream_completion(Industry.MANUFACTURING, rows_by_stream=rows)
    assert status.is_complete is True
    assert status.missing == []
    for stream, st in status.streams.items():
        assert st.completed is True
        assert st.row_count == 1


def test_compute_stream_completion_service_no_production_key() -> None:
    """서비스업은 production 키가 결과 dict에 없음 (capability_mask 차집합)."""
    rows = {"orders": 1, "sales": 1, "purchases": 1, "expenses": 1, "labor": 1}
    status = compute_stream_completion(Industry.SERVICE, rows_by_stream=rows)
    assert "production" not in status.streams
    assert status.is_complete is True
    assert status.capability_mask == ["expenses", "labor", "orders", "purchases", "sales"]


def test_compute_stream_completion_service_excludes_production_from_missing() -> None:
    """서비스업에서 production은 missing list에 포함 안 됨 (업종 외)."""
    status = compute_stream_completion(Industry.SERVICE, rows_by_stream={})
    assert "생산" not in status.missing
    # 5개 missing label만
    assert len(status.missing) == 5


def test_compute_stream_completion_unknown_industry_defaults_to_service() -> None:
    """인식 불가 industry → SERVICE (most restrictive) 폴백."""
    status = compute_stream_completion("unknown", rows_by_stream={})
    # production hidden
    assert "production" not in status.streams


def test_compute_stream_completion_none_rows_treated_as_empty() -> None:
    """None rows_by_stream → empty dict 폴백 (defensive)."""
    status = compute_stream_completion(Industry.MANUFACTURING, rows_by_stream=None)
    assert status.is_complete is False
    assert all(not s.completed for s in status.streams.values())


def test_compute_stream_completion_capability_mask_sorted_for_ui() -> None:
    """capability_mask는 정렬된 stream 이름 리스트 (UI 일관성)."""
    status = compute_stream_completion(
        Industry.MANUFACTURING, rows_by_stream={"orders": 1}
    )
    assert status.capability_mask == sorted(STREAMS_FOR_INDUSTRY[Industry.MANUFACTURING])


# ───────────────────────────────────────────────────────────────
# is_all_streams_complete (AC #3 [계산] 게이트)
# ───────────────────────────────────────────────────────────────
def test_is_all_streams_complete_manufacturing_with_production_all_present() -> None:
    """제조업 + 6 stream 모두 row 있음 → True."""
    rows = {s: 1 for s in STREAM_ORDER}
    assert is_all_streams_complete(Industry.MANUFACTURING, rows) is True


def test_is_all_streams_complete_service_no_production_key_returns_true() -> None:
    """서비스업 row dict에 production key 없음 → True (업종 외)."""
    rows = {"orders": 1, "sales": 1, "purchases": 1, "expenses": 1, "labor": 1}
    assert is_all_streams_complete(Industry.SERVICE, rows) is True


def test_is_all_streams_complete_labor_zero_rows_returns_false() -> None:
    """인원 stream에 row 0개 → False (가장 흔한 미완료 케이스)."""
    rows = {s: 1 for s in STREAM_ORDER if s != "labor"}
    assert is_all_streams_complete(Industry.MANUFACTURING, rows) is False


@pytest.mark.parametrize(
    "industry, expected_count",
    [
        (Industry.MANUFACTURING, 6),
        (Industry.SERVICE, 5),
        (Industry.MANUFACTURING_SERVICE, 6),
        (Industry.MANUFACTURING_SERVICE_OTHER, 6),
    ],
)
def test_visible_streams_count_per_industry(
    industry: Industry, expected_count: int
) -> None:
    """industry별 visible stream 수 (PRD §8.M2(b) 매트릭스)."""
    visible = STREAMS_FOR_INDUSTRY[industry]
    assert len(visible) == expected_count


# ───────────────────────────────────────────────────────────────
# Story 3.2 — FTE display pay_type branching (Task 6.2)
# ───────────────────────────────────────────────────────────────
from packages.services.m2_input.labor_conversion import (
    DEFAULT_PAYROLL,
    PayType,
    PayrollSettings,
    build_fte_display,
)


def test_fte_display_pay_type_monthly_uses_basis() -> None:
    """AC #2 — pay_type='monthly' uses basis 환산
    (1명 × 2_500_000 = 2_500_000 NOT 0).
    """
    display = build_fte_display(
        pay_type=PayType.MONTHLY,
        workers=1,
        days_per_worker=None,
        daily_wage_krw=None,
        monthly_salary_basis_krw=2_500_000,
        overtime_krw=0,
        welfare_krw=0,
        bonus_krw=0,
        retirement_reserve_krw=0,
        company_burden_rate=Decimal("0.115"),
        payroll=DEFAULT_PAYROLL,
        source_rows=1,
    )
    assert display.pay_type == PayType.MONTHLY
    assert display.fte_headcount == Decimal("1.00")
    assert display.fte_wage_krw == 2_500_000
    assert display.source_rows == 1
    # Breakdown should be populated for monthly mode
    assert display.breakdown is not None
    assert display.breakdown["base_krw"] == 2_500_000


def test_fte_display_pay_type_daily_uses_direct_wage() -> None:
    """AC #1 — pay_type='daily' uses direct sum
    (3명 × 8일 × 150_000 = 3_600_000 NOT 1.09 × 2_500_000).
    """
    display = build_fte_display(
        pay_type=PayType.DAILY,
        workers=3,
        days_per_worker=8,
        daily_wage_krw=150_000,
        monthly_salary_basis_krw=None,
        overtime_krw=0,
        welfare_krw=0,
        bonus_krw=0,
        retirement_reserve_krw=0,
        company_burden_rate=DEFAULT_PAYROLL.company_burden_rate,
        payroll=DEFAULT_PAYROLL,
        source_rows=1,
    )
    assert display.pay_type == PayType.DAILY
    assert display.fte_headcount == Decimal("1.09")  # 3*8/22
    assert display.fte_wage_krw == 3_600_000  # direct sum, NOT 2_725_000
    assert display.breakdown is None  # daily mode has no breakdown


def test_fte_display_zero_workers_all_zeros() -> None:
    """Edge — workers=0 → fte=Decimal("0.00"), wage=0 across all modes."""
    display = build_fte_display(
        pay_type=PayType.MONTHLY,
        workers=0,
        days_per_worker=None,
        daily_wage_krw=None,
        monthly_salary_basis_krw=2_500_000,
        overtime_krw=0,
        welfare_krw=0,
        bonus_krw=0,
        retirement_reserve_krw=0,
        company_burden_rate=Decimal("0.115"),
        payroll=DEFAULT_PAYROLL,
        source_rows=1,
    )
    assert display.fte_headcount == Decimal("0.00")
    assert display.fte_wage_krw == 0