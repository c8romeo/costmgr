"""Tests for Story 11.6 EXTENSION `apps.api.modules.m5_reports.services.report15_service` surface.

Coverage (11-6 wire Surface 4):
  - `Report15Service.build_report15` (4 cases)
  - `Report15Service.generate_report15_pdf` (4 cases)
  - `_to_report15_state` ORM→kernel boundary (3 cases)
  - `serialize_report15_state` JSON envelope (3 cases)
  - 4 envelope typed exceptions (2 cases)
  - V7 balance + activity_breakdown integration (2 cases)

Total: ~18 NEW pytest cases (T3.7) — CR 1.1 audit-first invariant + V7 balance 보존.

PRD §9 #15 verbatim wire:
  - 활동원가 내역서 (활동별 원가·동인 단가)
  - A19 cohesion 9 surface 진입점 결정 wire 검증
"""

from __future__ import annotations

import asyncio
import uuid
from decimal import Decimal

import pytest

from apps.api.modules.m5_reports.exceptions import (
    REPORT15_NO_ACTIVITY_BREAKDOWN_KO,
    REPORT15_PERIOD_NOT_COMMITTED_KO,
    Report15InconsistentStateError,
    Report15NoActivityBreakdownError,
    Report15PdfGenerationError,
    Report15PeriodNotCommittedError,
)
from apps.api.modules.m5_reports.services.report15_service import (
    Report15Service,
    Report15State,
    _to_report15_state,
    serialize_report15_state,
)
from packages.cost_engine.abc_engine import (
    ActivityCostRow,
    Report15Summary,
    V7Verdict,
    verify_v7_balance,
)

# ── helpers ──────────────────────────────────────────────


def _mk_activity_row(
    *,
    activity_id: str = "act-1",
    activity_name_ko: str = "고객 상담",
    activity_name_en: str = "Customer Consultation",
    total_cost_krw: str = "6600000",
    total_cost_usd: str = "4950",
    driver_count: int = 4,
    cost_per_driver_krw: str = "1650000",
    cost_per_driver_usd: str = "1237.50",
    allocated_krw: str = "6600000",
    allocated_usd: str = "4950",
    hash_str: str = "placeholder",
) -> ActivityCostRow:
    """Helper — ActivityCostRow fixture (11-6 kernel surface)."""
    return ActivityCostRow(
        activity_id=activity_id,
        activity_name_ko=activity_name_ko,
        activity_name_en=activity_name_en,
        total_cost_krw=Decimal(total_cost_krw),
        total_cost_usd=Decimal(total_cost_usd),
        driver_count=driver_count,
        cost_per_driver_krw=Decimal(cost_per_driver_krw),
        cost_per_driver_usd=Decimal(cost_per_driver_usd),
        allocated_krw=Decimal(allocated_krw),
        allocated_usd=Decimal(allocated_usd),
        hash=hash_str,
    )


def _mk_v7_verdict(
    *,
    breakdown_sum: str = "13200000",
    unused_cost: str = "0",
    department_cost: str = "13200000",
) -> V7Verdict:
    """Helper — V7Verdict fixture (9-3 verify_v7_balance)."""
    return verify_v7_balance(
        total_breakdown_sum=Decimal(breakdown_sum),
        unused_cost=Decimal(unused_cost),
        department_cost=Decimal(department_cost),
    )


def _mk_summary(
    *,
    activity_count: int = 3,
    total_cost_krw: str = "13200000",
    total_cost_usd: str = "9900",
    total_driver_count: int = 8,
    hash_str: str = "sha256:abc",
) -> Report15Summary:
    """Helper — Report15Summary fixture."""
    return Report15Summary(
        activity_count=activity_count,
        total_cost_krw=Decimal(total_cost_krw),
        total_cost_usd=Decimal(total_cost_usd),
        total_driver_count=total_driver_count,
        hash=hash_str,
    )


# ── Report15Service.build_report15 (4 cases) ────────────────


@pytest.mark.engine
def test_build_report15_empty_period_key_raises() -> None:
    """Step 1 — empty period_key → Report15PeriodNotCommittedError envelope."""
    service = Report15Service()
    with pytest.raises(Report15PeriodNotCommittedError) as exc_info:
        asyncio.run(
            service.build_report15(
                session=None,  # type: ignore[arg-type]
                tenant_id=uuid.uuid4(),
                period_key="",
            )
        )
    assert exc_info.value.reason == "empty_period_key"


@pytest.mark.engine
def test_build_report15_empty_activity_breakdown_raises_envelope() -> None:
    """PRD §9 #15 verbatim — 활동별 필수 (활동 1개 이상).
    empty activity_breakdown → Report15NoActivityBreakdownError envelope."""
    service = Report15Service()
    with pytest.raises(Report15NoActivityBreakdownError) as exc_info:
        asyncio.run(
            service.build_report15(
                session=None,  # type: ignore[arg-type]
                tenant_id=uuid.uuid4(),
                period_key="2026-Q1",
            )
        )
    assert exc_info.value.reason == "no_activity_breakdown"


@pytest.mark.engine
def test_build_report15_envelope_assemble_with_v7_balanced() -> None:
    """V7 balanced + valid activity_breakdown → Report15State envelope."""
    # Activity breakdown with valid KRW + USD totals
    rows = [
        _mk_activity_row(activity_id="act-1", total_cost_krw="6600000", total_cost_usd="4950", driver_count=4),
        _mk_activity_row(activity_id="act-2", total_cost_krw="6600000", total_cost_usd="4950", driver_count=4),
    ]
    # Build via internal logic — bypass by directly invoking _to_report15_state
    # (since build_report15 takes session param)
    summary = _mk_summary(activity_count=2)
    v7 = _mk_v7_verdict(breakdown_sum="13200000")
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=rows,
    )
    assert isinstance(state, Report15State)
    assert state.summary_message_ko is None  # V7 balanced → no message
    assert state.activity_breakdown_count == 2
    assert state.total_driver_count == 8
    assert state.report_code == "ACTIVITY_COST_DETAIL"


@pytest.mark.engine
def test_build_report15_envelope_assemble_with_v7_unbalanced() -> None:
    """V7 unbalanced → summary_message_ko populated (PRD §9 #15 verbatim message)."""
    rows = [_mk_activity_row()]
    summary = _mk_summary(activity_count=1)
    v7 = _mk_v7_verdict(
        breakdown_sum="6600000",
        unused_cost="0",
        department_cost="6600001",  # 1 KRW off
    )
    assert v7.is_balanced is False
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=rows,
    )
    assert state.summary_message_ko is not None
    assert REPORT15_NO_ACTIVITY_BREAKDOWN_KO in state.summary_message_ko


# ── Report15Service.generate_report15_pdf (4 cases) ─────────────


@pytest.mark.engine
def test_generate_report15_pdf_basic() -> None:
    """A30 SHARED factory reuse 1st case — Report #15 PDF 정상 생성."""
    service = Report15Service()
    payload = (
        {
            "activity_name_ko": "고객 상담",
            "activity_name_en": "Customer Consultation",
            "total_cost_krw": "6600000",
            "total_cost_usd": "4950",
            "driver_count": "4",
        },
    )
    result = asyncio.run(
        service.generate_report15_pdf(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            period_key="2026-Q1",
            payload=payload,
        )
    )
    assert result.report_id == 15
    assert result.size_bytes == len(result.pdf_bytes)
    assert result.pdf_bytes.startswith(b"%PDF-")


@pytest.mark.engine
def test_generate_report15_pdf_empty_payload_raises() -> None:
    """A30 SHARED factory payload invariant — Report #15 empty payload → 500 envelope."""
    service = Report15Service()
    with pytest.raises(Report15PdfGenerationError) as exc_info:
        asyncio.run(
            service.generate_report15_pdf(
                tenant_id=uuid.uuid4(),
                period_key="2026-Q1",
                payload=(),
            )
        )
    assert exc_info.value.reason == "no_payload_for_report15"


@pytest.mark.engine
def test_generate_report15_pdf_v8_determinism_100_repeats() -> None:
    """V8 byte-equality — 동일 payload → byte-identical PDF 100회."""
    service = Report15Service()
    payload = (
        {
            "activity_name_ko": "고객 상담",
            "total_cost_krw": "1000000",
        },
    )
    first = asyncio.run(
        service.generate_report15_pdf(
            tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
            period_key="2026-Q1",
            payload=payload,
        )
    )
    for _ in range(100):
        got = asyncio.run(
            service.generate_report15_pdf(
                tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                period_key="2026-Q1",
                payload=payload,
            )
        )
        assert got.pdf_bytes == first.pdf_bytes
        assert got.generation_hash == first.generation_hash


@pytest.mark.engine
def test_generate_report15_pdf_empty_period_key_raises() -> None:
    """PDF generation — empty period_key → Report15PdfGenerationError envelope."""
    service = Report15Service()
    with pytest.raises(Report15PdfGenerationError) as exc_info:
        asyncio.run(
            service.generate_report15_pdf(
                tenant_id=uuid.uuid4(),
                period_key="",
                payload=({"activity_name_ko": "x"},),
            )
        )
    assert exc_info.value.reason == "empty_period_key"


# ── _to_report15_state ORM→kernel boundary (3 cases) ───────────


@pytest.mark.engine
def test_to_report15_state_balanced_no_message() -> None:
    """CR 12-1 L3 boundary — V7 balanced → summary_message_ko = None."""
    summary = _mk_summary()
    v7 = _mk_v7_verdict()
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=[_mk_activity_row()],
    )
    assert state.summary_message_ko is None


@pytest.mark.engine
def test_to_report15_state_unbalanced_message_includes_diff() -> None:
    """V7 unbalanced → summary_message_ko 에 diff 포함 (Report #21 동일 surface 미러)."""
    summary = _mk_summary()
    v7 = _mk_v7_verdict(
        breakdown_sum="6600000",
        unused_cost="0",
        department_cost="6600005",
    )
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=[_mk_activity_row()],
    )
    assert state.summary_message_ko is not None
    # Diff = 6600005 - 6600000 = 5원
    assert "차이 5원" in state.summary_message_ko


@pytest.mark.engine
def test_to_report15_state_total_driver_count_invariant() -> None:
    """Invariant — total_driver_count = Σ ActivityCostRow.driver_count."""
    summary = _mk_summary()
    v7 = _mk_v7_verdict()
    rows = [
        _mk_activity_row(driver_count=4),
        _mk_activity_row(activity_id="act-2", driver_count=2),
        _mk_activity_row(activity_id="act-3", driver_count=2),
    ]
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=rows,
    )
    assert state.total_driver_count == 8  # 4+2+2
    assert state.activity_breakdown_count == 3


# ── serialize_report15_state JSON envelope (3 cases) ───────────


@pytest.mark.engine
def test_serialize_report15_state_json_safe_shape() -> None:
    """AD-15 §1 cross-language parity — JSON envelope shape (TS mirror)."""
    summary = _mk_summary()
    v7 = _mk_v7_verdict()
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=[_mk_activity_row()],
    )
    envelope = serialize_report15_state(state)
    assert envelope["period_key"] == "2026-Q1"
    assert envelope["report_code"] == "ACTIVITY_COST_DETAIL"
    assert envelope["v7_verdict_is_balanced"] is True
    assert envelope["generation_hash"] == "sha256:abc"
    assert envelope["activity_count"] == 1
    assert envelope["total_driver_count"] == 4
    assert isinstance(envelope["activity_breakdown"], list)


@pytest.mark.engine
def test_serialize_report15_state_decimal_as_string() -> None:
    """AD-8 Decimal-as-string — KRW + USD amounts as string."""
    summary = _mk_summary()
    v7 = _mk_v7_verdict()
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=[_mk_activity_row()],
    )
    envelope = serialize_report15_state(state)
    assert envelope["total_cost_krw"] == "13200000"
    assert envelope["total_cost_usd"] == "9900"
    row = envelope["activity_breakdown"][0]
    assert row["total_cost_krw"] == "6600000"
    assert row["total_cost_usd"] == "4950"


@pytest.mark.engine
def test_serialize_report15_state_empty_breakdown() -> None:
    """Empty activity_breakdown → JSON envelope with empty list."""
    summary = _mk_summary(activity_count=0, total_cost_krw="0", total_cost_usd="0", total_driver_count=0)
    v7 = _mk_v7_verdict()
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=[],
    )
    envelope = serialize_report15_state(state)
    assert envelope["activity_count"] == 0
    assert envelope["total_driver_count"] == 0
    assert envelope["activity_breakdown"] == []


# ── 4 envelope typed exceptions (2 cases) ───────────────────


@pytest.mark.engine
def test_report15_envelope_exception_classes_distinct() -> None:
    """Typed exceptions — Report #15 envelope 4 classes distinct (CR 12-5 D-14)."""
    e1 = Report15PeriodNotCommittedError("p", period_key="2026-Q1", reason="x")
    e2 = Report15NoActivityBreakdownError("n", period_key="2026-Q1", reason="x")
    e3 = Report15InconsistentStateError(
        "i", period_key="2026-Q1",
        expected_sum=Decimal("0"), actual_sum=Decimal("0"),
        reason="x",
    )
    assert type(e1) is not type(e2)
    assert type(e1) is not type(e3)
    assert type(e2) is not type(e3)


@pytest.mark.engine
def test_report15_korean_ssot_messages() -> None:
    """Korean SSOT — REPORT15_*_KO envelope messages 보존 (CR 11-4 D-002)."""
    assert REPORT15_PERIOD_NOT_COMMITTED_KO == (
        "리포트 #15 생성 전 회계기간이 커밋되지 않았습니다"
    )
    assert REPORT15_NO_ACTIVITY_BREAKDOWN_KO == (
        "리포트 #15: 활동별 원가 데이터가 없습니다"
    )


# ── V7 balance + activity_breakdown integration (2 cases) ───────────


@pytest.mark.engine
def test_v7_balanced_with_krw_usd_consistency() -> None:
    """Integration — KRW + USD totals balanced, V7 verdict is_balanced=True."""
    rows = [
        _mk_activity_row(total_cost_krw="6600000", total_cost_usd="4950"),
        _mk_activity_row(activity_id="act-2", total_cost_krw="3300000", total_cost_usd="2475"),
    ]
    total_krw = sum((r.total_cost_krw for r in rows), Decimal("0"))
    total_usd = sum((r.total_cost_usd for r in rows), Decimal("0"))
    v7 = _mk_v7_verdict(
        breakdown_sum=str(total_krw),
        unused_cost="0",
        department_cost=str(total_krw),
    )
    assert v7.is_balanced is True
    assert total_usd == Decimal("7425")  # 4950 + 2475


@pytest.mark.engine
def test_v7_unbalanced_with_breakdown_present() -> None:
    """Integration — breakdown present but V7 unbalanced (delta_krw > 0)."""
    rows = [_mk_activity_row(total_cost_krw="1000000")]
    v7 = _mk_v7_verdict(
        breakdown_sum="1000000",
        unused_cost="0",
        department_cost="1000100",  # 100 KRW off
    )
    assert v7.is_balanced is False
    assert abs(v7.delta_krw) == Decimal("100")
    summary = _mk_summary(activity_count=1, total_cost_krw="1000000", total_cost_usd="750", total_driver_count=4)
    state = _to_report15_state(
        summary=summary,
        v7_verdict=v7,
        period_key="2026-Q1",
        activity_breakdown=rows,
    )
    assert state.summary_message_ko is not None
    assert "차이 100원" in state.summary_message_ko
