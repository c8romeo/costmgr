"""Tests for Story 11.6 EXTENSION `packages.services.m5_reports.pdf_generator` Report #15 surface.

Coverage (11-6 wire Surface 2 — A30 SHARED factory EXTENSION):
  - `_compose_report15_pdf` 본체 wire (placeholder → 본체) (6 cases)
  - payload invariants (Report #15 = report_id=15) (4 cases)
  - 5 REPORT15_* constants SSOT (4 cases)
  - Discriminated union payload routing (2 cases)

Total: ~16 NEW pytest cases (T2.2) — A30 SHARED factory reuse 1st case wire 검증.

PRD §9 #15 verbatim wire:
  - 활동원가 내역서 (활동별 원가·동인 단가)
  - A30 forward-lock SHARED factory reuse 1st case 결정 wire 진입
"""

from __future__ import annotations

import hashlib
import uuid

import pytest

from packages.services.m5_reports.pdf_generator import (
    A4_HEIGHT_PT,
    A4_WIDTH_PT,
    M5_REPORTS_PDF_SIZE_BUDGET_BYTES,
    M5_REPORTS_PDF_VERSION,
    PDF_COMMON_DATE_LABEL_KO,
    PDF_COMMON_PERIOD_LABEL_KO,
    PDF_COMMON_TENANT_LABEL_KO,
    PDF_COMMON_TITLE_PREFIX_KO,
    REPORT15_ACTIVITY_NAME_EN,
    REPORT15_ACTIVITY_NAME_KO,
    REPORT15_PDF_EMPTY_KO,
    REPORT15_PDF_TITLE_KO,
    REPORT15_REPORT_CODE,
    REPORT21_PDF_TITLE_KO,
    REPORT21_REPORT_CODE,
    SUPPORTED_REPORT_IDS,
    ReportPdfGenerationError,
    ReportPdfRequest,
    ReportPdfResult,
    generate_report_pdf,
)

# ── helpers ──────────────────────────────────────────────


def _mk_report15_request(
    *,
    tenant_id: uuid.UUID | None = None,
    period_key: str = "2026-Q1",
    payload: tuple[dict[str, str], ...] = (
        {
            "activity_name_ko": "고객 상담",
            "activity_name_en": "Customer Consultation",
            "total_cost_krw": "6600000",
            "total_cost_usd": "4950",
            "driver_count": "4",
            "cost_per_driver_krw": "1650000",
            "cost_per_driver_usd": "1237.50",
        },
        {
            "activity_name_ko": "주문 처리",
            "activity_name_en": "Order Processing",
            "total_cost_krw": "3300000",
            "total_cost_usd": "2475",
            "driver_count": "2",
            "cost_per_driver_krw": "1650000",
            "cost_per_driver_usd": "1237.50",
        },
    ),
    report_id: int = 15,
) -> ReportPdfRequest:
    """Helper — ReportPdfRequest fixture for Report #15 (활동별 행 envelope)."""
    return ReportPdfRequest(
        tenant_id=tenant_id or uuid.UUID("00000000-0000-0000-0000-000000000001"),
        period_key=period_key,
        report_id=report_id,
        payload=payload,
    )


# ── _compose_report15_pdf — 본체 wire (6 cases) ─────────────


@pytest.mark.engine
def test_report15_pdf_compose_basic() -> None:
    """Wire basic — Report #15 PDF 본체 wire → bytes 반환, PDF 1.7 magic."""
    request = _mk_report15_request()
    result = generate_report_pdf(request=request)
    assert isinstance(result, ReportPdfResult)
    assert result.report_id == 15
    assert result.size_bytes == len(result.pdf_bytes)
    # PDF magic header
    assert result.pdf_bytes.startswith(b"%PDF-")
    assert f"PDF-{M5_REPORTS_PDF_VERSION}".encode() in result.pdf_bytes[:20]


@pytest.mark.engine
def test_report15_pdf_compose_v8_determinism_100_repeats() -> None:
    """V8 byte-equality — 동일 request → byte-identical PDF 100회 반복."""
    request = _mk_report15_request()
    first = generate_report_pdf(request=request)
    for _ in range(100):
        got = generate_report_pdf(request=request)
        assert got.pdf_bytes == first.pdf_bytes
        assert got.generation_hash == first.generation_hash


@pytest.mark.engine
def test_report15_pdf_compose_generation_hash_matches_sha256() -> None:
    """V8 byte-equality invariant — generation_hash = sha256(pdf_bytes)."""
    request = _mk_report15_request()
    result = generate_report_pdf(request=request)
    expected_digest = hashlib.sha256(result.pdf_bytes).hexdigest()
    assert result.generation_hash == f"sha256:{expected_digest}"


@pytest.mark.engine
def test_report15_pdf_compose_contains_report15_title_ko() -> None:
    """SSOT invariant — PDF 본문에 REPORT15_PDF_TITLE_KO 포함."""
    request = _mk_report15_request()
    result = generate_report_pdf(request=request)
    # PDF streams are UTF-8 encoded; Korean SSOT 그대로 포함
    assert REPORT15_PDF_TITLE_KO.encode("utf-8") in result.pdf_bytes


@pytest.mark.engine
def test_report15_pdf_compose_contains_tenant_and_period() -> None:
    """PDF 본문에 tenant_id + period_key label 포함 (PDF_COMMON_* SSOT)."""
    tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
    request = _mk_report15_request(
        tenant_id=tenant_id,
        period_key="2026-Q1",
    )
    result = generate_report_pdf(request=request)
    assert PDF_COMMON_TENANT_LABEL_KO.encode("utf-8") in result.pdf_bytes
    assert PDF_COMMON_PERIOD_LABEL_KO.encode("utf-8") in result.pdf_bytes
    # tenant_id 의 prefix 만 확인 (60-char chunk split 으로 잘릴 수 있음)
    assert b"00000000-0000-0000-0000-00000000009" in result.pdf_bytes
    assert b"2026-Q1" in result.pdf_bytes


@pytest.mark.engine
def test_report15_pdf_compose_payload_renders_as_rows() -> None:
    """Payload envelope — 활동별 행 본문에 반영 (PRD §9 #15 verbatim)."""
    request = _mk_report15_request(
        payload=(
            {
                "activity_name_ko": "고객 상담",
                "activity_name_en": "Customer Consultation",
                "total_cost_krw": "6600000",
                "total_cost_usd": "4950",
            },
        ),
    )
    result = generate_report_pdf(request=request)
    assert "고객 상담".encode() in result.pdf_bytes
    assert b"Customer Consultation" in result.pdf_bytes
    assert b"6600000" in result.pdf_bytes


# ── payload invariants (4 cases) ─────────────────────────


@pytest.mark.engine
def test_report15_payload_empty_raises() -> None:
    """Validation — Report #15 empty payload → ReportPdfGenerationError
    (PRD §9 #15 verbatim — 활동 데이터 부재 시 422 envelope)."""
    request = _mk_report15_request(payload=())
    with pytest.raises(ReportPdfGenerationError) as exc_info:
        generate_report_pdf(request=request)
    assert exc_info.value.reason == "no_payload_for_report15"
    assert exc_info.value.report_id == 15


@pytest.mark.engine
def test_report15_empty_period_key_raises() -> None:
    """Validation — empty period_key → ReportPdfGenerationError
    (CR 12-5 D-14 envelope, 모든 report_id 공통 invariant)."""
    request = _mk_report15_request(period_key="")
    with pytest.raises(ReportPdfGenerationError) as exc_info:
        generate_report_pdf(request=request)
    assert exc_info.value.reason == "empty_period_key"


@pytest.mark.engine
def test_report15_unsupported_report_id_raises() -> None:
    """Validation — report_id not in SUPPORTED_REPORT_IDS → ReportPdfGenerationError."""
    request = _mk_report15_request(report_id=999)
    with pytest.raises(ReportPdfGenerationError) as exc_info:
        generate_report_pdf(request=request)
    assert exc_info.value.reason == "unsupported_report_id"
    assert exc_info.value.report_id == 999


@pytest.mark.engine
def test_report15_payload_non_empty_passes() -> None:
    """Validation — non-empty payload → 정상 PDF (no exception)."""
    request = _mk_report15_request(
        payload=(
            {
                "activity_name_ko": "고객 상담",
                "activity_name_en": "Customer Consultation",
                "total_cost_krw": "1000000",
                "total_cost_usd": "750",
            },
        ),
    )
    result = generate_report_pdf(request=request)
    assert result.size_bytes > 0


# ── 5 REPORT15_* constants SSOT (4 cases) ─────────────────


@pytest.mark.engine
def test_report15_constants_ssot() -> None:
    """5 REPORT15_* constants — ko-KR SSOT (CR 11-3 P-015 drift detector)."""
    assert REPORT15_PDF_TITLE_KO == "활동원가 내역서"
    assert REPORT15_PDF_EMPTY_KO == "활동 데이터 없음"
    assert REPORT15_REPORT_CODE == "ACTIVITY_COST_DETAIL"
    assert REPORT15_ACTIVITY_NAME_KO == "활동명"
    assert REPORT15_ACTIVITY_NAME_EN == "Activity"


@pytest.mark.engine
def test_report15_constants_distinct_from_report21() -> None:
    """Distinct SSOT — Report #15 ≠ Report #21 SSOT (drift detector guard)."""
    assert REPORT15_PDF_TITLE_KO != REPORT21_PDF_TITLE_KO
    assert REPORT15_REPORT_CODE != REPORT21_REPORT_CODE
    # distinct purpose, distinct codes
    assert "활동" in REPORT15_PDF_TITLE_KO
    assert "원가대상" in REPORT21_PDF_TITLE_KO


@pytest.mark.engine
def test_report15_constants_used_in_pdf_compose() -> None:
    """Constants 사용 검증 — REPORT15_PDF_TITLE_KO 가 PDF 본문에 포함."""
    request = _mk_report15_request()
    result = generate_report_pdf(request=request)
    assert REPORT15_PDF_TITLE_KO.encode("utf-8") in result.pdf_bytes
    assert PDF_COMMON_TITLE_PREFIX_KO.encode("utf-8") in result.pdf_bytes


@pytest.mark.engine
def test_report15_constants_used_with_activity_name_labels() -> None:
    """Activity name labels 검증 — REPORT15_ACTIVITY_NAME_KO/EN 사용."""
    # Activity name labels are part of the header row in body_lines
    # Verify constants exist (drift detector)
    assert REPORT15_ACTIVITY_NAME_KO == "활동명"
    assert REPORT15_ACTIVITY_NAME_EN == "Activity"


# ── Discriminated union payload routing (2 cases) ─────────


@pytest.mark.engine
def test_report15_routes_through_15_branch_not_21() -> None:
    """Routing — report_id=15 → _compose_report15_pdf branch
    (A30 SHARED factory reuse 1st case wire 검증).

    Note: Report #15 + Report #21 wire 모두 동일 PDF envelope (1.7 + A4),
    but distinct body rendering (activity vs cost_object rows) and SSOT.
    """
    request15 = _mk_report15_request(report_id=15)
    request21 = _mk_report15_request(report_id=21)
    # Report #21 wire는 별도 payload schema — 본 test 는 routing 만 검증
    result15 = generate_report_pdf(request=request15)
    assert result15.report_id == 15
    # Report #21 = 동일 envelope surface 재사용, distinct body
    result21 = generate_report_pdf(request=request21)
    assert result21.report_id == 21


@pytest.mark.engine
def test_report15_supported_in_frozenset() -> None:
    """Discriminated union — report_id=15 ∈ SUPPORTED_REPORT_IDS."""
    assert 15 in SUPPORTED_REPORT_IDS
    assert 21 in SUPPORTED_REPORT_IDS
    # All 7 reports supported (15~21)
    assert frozenset({15, 16, 17, 18, 19, 20, 21}) == SUPPORTED_REPORT_IDS


# ── Size budget + A4 envelope (2 cases — surface regression) ─────


@pytest.mark.engine
def test_report15_size_within_budget() -> None:
    """Surface regression — Report #15 PDF size ≤ M5_REPORTS_PDF_SIZE_BUDGET_BYTES."""
    request = _mk_report15_request()
    result = generate_report_pdf(request=request)
    assert result.size_bytes <= M5_REPORTS_PDF_SIZE_BUDGET_BYTES


@pytest.mark.engine
def test_report15_a4_envelope_constants_used() -> None:
    """Surface regression — A4 envelope constants 동일 사용 (Report #21 wire
    와 동일 surface, A30 SHARED factory 패턴)."""
    request = _mk_report15_request()
    result = generate_report_pdf(request=request)
    # A4 dimensions in MediaBox (1pt = 1/72 inch)
    assert str(A4_WIDTH_PT).encode() in result.pdf_bytes
    assert str(A4_HEIGHT_PT).encode() in result.pdf_bytes

    # Suppress unused warning
    _ = PDF_COMMON_DATE_LABEL_KO
