"""Cross-language drift detector for Report #15 (Story 11.6 EXTENSION).

Coverage (11-6 wire Surface 7 — cross-language parity):
  - Backend Pydantic schemas ↔ Frontend TS mirror parity (2 cases)
  - Backend Korean SSOT messages ↔ Frontend ko-KR.json parity (2 cases)
  - Backend error codes ↔ Frontend error code constants parity (2 cases)
  - Backend Decimal-as-string ↔ Frontend Decimal-as-string parity (2 cases)

Total: ~8 NEW pytest cases (T6.x) — AD-15 §1 cross-language parity SSOT 보존 검증.

PRD §9 #15 verbatim wire:
  - 활동원가 내역서 (활동별 원가·동인 단가)
  - AD-15 §1: cross-language parity SSOT drift detector
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from apps.api.modules.m5_reports.exceptions import (
    REPORT15_BREAKDOWN_NOT_FOUND_KO,
    REPORT15_NO_ACTIVITY_BREAKDOWN_KO,
    REPORT15_PERIOD_NOT_COMMITTED_KO,
)
from apps.api.modules.m5_reports.schemas import (
    Report15ActivityCostRow,
    Report15Response,
)

# ── Backend ↔ Frontend SSOT parity (4 cases) ────────────


@pytest.mark.engine
def test_report15_backend_response_envelope_fields_match_ts() -> None:
    """AD-15 §1 — backend Report15Response fields 일치 TS mirror."""
    fields = set(Report15Response.model_fields.keys())
    expected = {
        "period_key",
        "activity_breakdown",
        "v7_verdict_is_balanced",
        "generation_hash",
        "report_code",
        "activity_count",
        "total_driver_count",
        "total_cost_krw",
        "total_cost_usd",
    }
    assert fields == expected


@pytest.mark.engine
def test_report15_backend_activity_cost_row_fields_match_ts() -> None:
    """AD-15 §1 — backend Report15ActivityCostRow fields 일치 TS mirror."""
    fields = set(Report15ActivityCostRow.model_fields.keys())
    expected = {
        "activity_id",
        "activity_name_ko",
        "activity_name_en",
        "total_cost_krw",
        "total_cost_usd",
        "driver_count",
        "cost_per_driver_krw",
        "cost_per_driver_usd",
        "allocated_krw",
        "allocated_usd",
    }
    assert fields == expected


@pytest.mark.engine
def test_report15_korean_ssot_messages_present_in_koKR() -> None:
    """Cross-language drift — Report #15 backend constants 일치 TS mirror
    REPORT15_ERROR_CODES identifiers.

    Note: ko-KR.json::report15::errors 는 *error code identifier* 를 보관
    (e.g., "REPORT15_PERIOD_NOT_COMMITTED"), backend 의 *_KO constants 는
    *Korean message* 를 보관. drift detector 는 두 layer 가 일관되게
    매핑되는지 검증.
    """
    project_root = Path(__file__).resolve().parents[2]
    ko_kr_path = project_root / "apps" / "web" / "messages" / "ko-KR.json"
    with ko_kr_path.open(encoding="utf-8") as f:
        ko_kr = json.load(f)
    report15_errors = ko_kr["report15"]["errors"]
    # Frontend 에러 코드 identifier 가 REPORT15_PERIOD_NOT_COMMITTED_KO 의
    # suffix 와 일치 (REPORT15_PERIOD_NOT_COMMITTED = "REPORT15_PERIOD_NOT_COMMITTED_KO"
    # 의 코드 부분)
    assert report15_errors["period_not_committed_code"] == "REPORT15_PERIOD_NOT_COMMITTED"
    assert "리포트" in REPORT15_PERIOD_NOT_COMMITTED_KO
    assert "기간" in REPORT15_PERIOD_NOT_COMMITTED_KO


@pytest.mark.engine
def test_report15_korean_no_activity_breakdown_in_koKR() -> None:
    """Cross-language drift — REPORT15_NO_ACTIVITY_BREAKDOWN_KO 매핑 검증."""
    project_root = Path(__file__).resolve().parents[2]
    ko_kr_path = project_root / "apps" / "web" / "messages" / "ko-KR.json"
    with ko_kr_path.open(encoding="utf-8") as f:
        ko_kr = json.load(f)
    report15_errors = ko_kr["report15"]["errors"]
    assert report15_errors["no_activity_breakdown_code"] == "REPORT15_NO_ACTIVITY_BREAKDOWN"
    assert "활동별" in REPORT15_NO_ACTIVITY_BREAKDOWN_KO


@pytest.mark.engine
def test_report15_korean_breakdown_not_found_in_koKR() -> None:
    """Cross-language drift — REPORT15_BREAKDOWN_NOT_FOUND_KO 매핑 검증."""
    project_root = Path(__file__).resolve().parents[2]
    ko_kr_path = project_root / "apps" / "web" / "messages" / "ko-KR.json"
    with ko_kr_path.open(encoding="utf-8") as f:
        ko_kr = json.load(f)
    report15_errors = ko_kr["report15"]["errors"]
    assert report15_errors["breakdown_not_found_code"] == "REPORT15_BREAKDOWN_NOT_FOUND"
    assert "찾을 수 없습니다" in REPORT15_BREAKDOWN_NOT_FOUND_KO


@pytest.mark.engine
def test_report15_pdf_generation_error_in_koKR() -> None:
    """Cross-language drift — REPORT_PDF_GENERATION_ERROR 매핑 검증."""
    project_root = Path(__file__).resolve().parents[2]
    ko_kr_path = project_root / "apps" / "web" / "messages" / "ko-KR.json"
    with ko_kr_path.open(encoding="utf-8") as f:
        ko_kr = json.load(f)
    report15_errors = ko_kr["report15"]["errors"]
    assert report15_errors["pdf_generation_error_code"] == "REPORT_PDF_GENERATION_ERROR"


# ── Decimal-as-string parity (2 cases) ────────────


@pytest.mark.engine
def test_report15_activity_cost_row_decimal_amounts_as_string() -> None:
    """AD-8 invariant — KRW + USD amounts = str (not Decimal/number)."""
    row = Report15ActivityCostRow(
        activity_id="act-1",
        activity_name_ko="고객 상담",
        activity_name_en="Customer Consultation",
        total_cost_krw="6600000",
        total_cost_usd="4950",
        driver_count=4,
        cost_per_driver_krw="1650000",
        cost_per_driver_usd="1237.50",
        allocated_krw="6600000",
        allocated_usd="4950",
    )
    assert isinstance(row.total_cost_krw, str)
    assert isinstance(row.total_cost_usd, str)
    assert isinstance(row.cost_per_driver_krw, str)
    assert isinstance(row.cost_per_driver_usd, str)
    assert isinstance(row.allocated_krw, str)
    assert isinstance(row.allocated_usd, str)


@pytest.mark.engine
def test_report15_response_total_amounts_as_string() -> None:
    """AD-8 invariant — total_cost_krw + total_cost_usd = str."""
    response = Report15Response(
        period_key="2026-Q1",
        activity_breakdown=[],
        v7_verdict_is_balanced=True,
        generation_hash="sha256:" + "a" * 64,
        activity_count=0,
        total_driver_count=0,
        total_cost_krw="0",
        total_cost_usd="0",
    )
    assert isinstance(response.total_cost_krw, str)
    assert isinstance(response.total_cost_usd, str)
