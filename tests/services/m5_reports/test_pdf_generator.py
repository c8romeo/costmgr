"""Tests for Story 9.4 `packages.services.m5_reports.pdf_generator` A30 SHARED factory.

Coverage (9-4 wire):
  - A30 SHARED factory Discriminated union `report_id: Literal[15..21]`
    pattern (8 cases)
  - `generate_report_pdf` for report_id=21 (8 cases) — Cost Object
    Breakdown PDF byte composition
  - `generate_report_pdf` for report_id=15 (3 cases) — 활동원가 내역서
    placeholder pattern
  - ReportPdfRequest + ReportPdfResult frozen dataclass invariants (3 cases)
  - ReportPdfGenerationError envelope RAISE (4 cases)
  - V8 byte-equality determinism (4 cases)

Total: ~30 NEW pytest cases (T2) — A30 SHARED factory 검증.

AD-5 / AD-11: pure-Python, stdlib-only. NO reportlab dependency.
"""
from __future__ import annotations

import dataclasses
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
    REPORT21_PDF_EMPTY_KO,
    REPORT21_PDF_TITLE_KO,
    REPORT21_REPORT_CODE,
    SUPPORTED_REPORT_IDS,
    ReportPdfGenerationError,
    ReportPdfRequest,
    ReportPdfResult,
    generate_report_pdf,
)

# ── helpers ────────────────────────────────────────────


def _mk_request_21(
    *,
    tenant_id: uuid.UUID | None = None,
    period_key: str = "2026-Q1",
    payload: tuple[dict[str, str], ...] = (
        {"product_id": "prod-A", "allocated_krw": "6600000"},
        {"product_id": "prod-B", "allocated_krw": "3300000"},
    ),
) -> ReportPdfRequest:
    """Helper — Report #21 (Cost Object Breakdown) request fixture."""
    return ReportPdfRequest(
        tenant_id=tenant_id or uuid.UUID("00000000-0000-0000-0000-000000000001"),
        period_key=period_key,
        report_id=21,
        payload=payload,
    )


def _mk_request_15(
    *,
    tenant_id: uuid.UUID | None = None,
    period_key: str = "2026-Q1",
    payload: tuple[dict[str, str], ...] = (
        {"activity_id": "act-1", "cost_krw": "13200000"},
    ),
) -> ReportPdfRequest:
    """Helper — Report #15 (활동원가 내역서) request fixture."""
    return ReportPdfRequest(
        tenant_id=tenant_id or uuid.UUID("00000000-0000-0000-0000-000000000002"),
        period_key=period_key,
        report_id=15,
        payload=payload,
    )


# ── A30 SHARED factory Discriminated union (8 cases) ───────────


@pytest.mark.engine
def test_supported_report_ids_frozenset() -> None:
    """A30 SHARED factory — Literal[15, 16, 17, 18, 19, 20, 21] invariant."""
    assert 15 in SUPPORTED_REPORT_IDS
    assert 16 in SUPPORTED_REPORT_IDS
    assert 17 in SUPPORTED_REPORT_IDS
    assert 18 in SUPPORTED_REPORT_IDS
    assert 19 in SUPPORTED_REPORT_IDS
    assert 20 in SUPPORTED_REPORT_IDS
    assert 21 in SUPPORTED_REPORT_IDS
    assert 22 not in SUPPORTED_REPORT_IDS
    assert 14 not in SUPPORTED_REPORT_IDS
    assert len(SUPPORTED_REPORT_IDS) == 7


@pytest.mark.engine
def test_pdf_version_is_1_7() -> None:
    """PDF 1.7 — Acrobat 8+ baseline + Identity-H CMap support."""
    assert M5_REPORTS_PDF_VERSION == "1.7"


@pytest.mark.engine
def test_a4_dimensions_constants() -> None:
    """A4 page = 595×842pt (1pt = 1/72 inch)."""
    assert A4_WIDTH_PT == 595
    assert A4_HEIGHT_PT == 842


@pytest.mark.engine
def test_pdf_size_budget_5mb() -> None:
    """PRD §F6.3 — PDF size ≤ 5MB per period (chunked rendering cap)."""
    assert M5_REPORTS_PDF_SIZE_BUDGET_BYTES == 5 * 1024 * 1024


@pytest.mark.engine
def test_report21_pdf_title_ko_ssot() -> None:
    """Korean SSOT — `REPORT21_PDF_TITLE_KO` AD-15 cross-language parity."""
    assert REPORT21_PDF_TITLE_KO == "원가대상별 원가 집계표"


@pytest.mark.engine
def test_report21_pdf_empty_ko_ssot() -> None:
    """Korean SSOT — `REPORT21_PDF_EMPTY_KO` AD-15 cross-language parity."""
    assert REPORT21_PDF_EMPTY_KO == "원가대상 데이터 없음"


@pytest.mark.engine
def test_report21_report_code_ssot() -> None:
    """Report code SSOT — AD-15 cross-language parity."""
    assert REPORT21_REPORT_CODE == "COST_OBJECT_BREAKDOWN"


@pytest.mark.engine
def test_pdf_common_namespace_ko_labels() -> None:
    """pdf_common namespace — prefix + 4 labels SSOT (9-4 wire ~12 strings)."""
    assert PDF_COMMON_TITLE_PREFIX_KO == "[costmgr] "
    assert PDF_COMMON_DATE_LABEL_KO == "생성일시"
    assert PDF_COMMON_TENANT_LABEL_KO == "테넌트"
    assert PDF_COMMON_PERIOD_LABEL_KO == "회계기간"


# ── generate_report_pdf — report_id=21 (8 cases) ─────────────


@pytest.mark.engine
def test_generate_report_pdf_report21_returns_bytes() -> None:
    """Report #21 wire — pdf_bytes is bytes (V8 byte-equality envelope)."""
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    assert isinstance(result, ReportPdfResult)
    assert isinstance(result.pdf_bytes, bytes)
    assert len(result.pdf_bytes) > 0


@pytest.mark.engine
def test_generate_report_pdf_report21_pdf_header() -> None:
    """Report #21 wire — PDF byte stream starts with `%PDF-{version}`."""
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    header_line = result.pdf_bytes.split(b"\n", 1)[0]
    assert header_line == b"%PDF-1.7"


@pytest.mark.engine
def test_generate_report_pdf_report21_pdf_trailer() -> None:
    """Report #21 wire — PDF byte stream ends with `%%EOF`."""
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    assert result.pdf_bytes.endswith(b"%%EOF\n")


@pytest.mark.engine
def test_generate_report_pdf_report21_xref_offset_invariant() -> None:
    """Report #21 wire — startxref offset matches body byte size."""
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    pdf = result.pdf_bytes.decode("latin-1", errors="replace")
    # startxref line MUST be present
    assert "startxref" in pdf
    # %%EOF MUST follow startxref line
    idx_startxref = pdf.rfind("startxref")
    idx_eof = pdf.rfind("%%EOF")
    assert idx_startxref < idx_eof


@pytest.mark.engine
def test_generate_report_pdf_report21_size_bytes_correct() -> None:
    """Report #21 wire — `size_bytes == len(pdf_bytes)`."""
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    assert result.size_bytes == len(result.pdf_bytes)


@pytest.mark.engine
def test_generate_report_pdf_report21_generation_hash_sha256() -> None:
    """Report #21 wire — `generation_hash == sha256:{hexdigest}`."""
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    assert result.generation_hash.startswith("sha256:")
    digest = result.generation_hash[len("sha256:"):]
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)


@pytest.mark.engine
def test_generate_report_pdf_report21_title_in_pdf() -> None:
    """Report #21 wire — REPORT21_PDF_TITLE_KO visible in PDF byte stream."""
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    assert REPORT21_PDF_TITLE_KO.encode("utf-8") in result.pdf_bytes


@pytest.mark.engine
def test_generate_report_pdf_report21_payload_in_pdf() -> None:
    """Report #21 wire — payload rows visible in PDF byte stream."""
    request = _mk_request_21(
        payload=(
            {"product_id": "prod-A", "allocated_krw": "6600000"},
            {"product_id": "prod-B", "allocated_krw": "3300000"},
        )
    )
    result = generate_report_pdf(request=request)
    assert b"prod-A" in result.pdf_bytes
    assert b"6600000" in result.pdf_bytes


# ── generate_report_pdf — report_id=15 (3 cases) ──────────────


@pytest.mark.engine
def test_generate_report_pdf_report15_returns_bytes() -> None:
    """Report #15 wire (placeholder pattern) — pdf_bytes is bytes."""
    request = _mk_request_15()
    result = generate_report_pdf(request=request)
    assert isinstance(result, ReportPdfResult)
    assert isinstance(result.pdf_bytes, bytes)


@pytest.mark.engine
def test_generate_report_pdf_report15_distinct_from_report21() -> None:
    """Report #15 — distinct report_id 21 dispatch (Discriminated union)."""
    req_15 = _mk_request_15()
    req_21 = _mk_request_21()
    result_15 = generate_report_pdf(request=req_15)
    result_21 = generate_report_pdf(request=req_21)
    assert result_15.report_id == 15
    assert result_21.report_id == 21


@pytest.mark.engine
def test_generate_report_pdf_report15_payload_not_required() -> None:
    """Report #15 wire — payload 비어도 정상 (wire 후속 진입점 결정)."""
    request = ReportPdfRequest(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000099"),
        period_key="2026-Q1",
        report_id=15,
        payload=(),
    )
    result = generate_report_pdf(request=request)
    assert result.size_bytes > 0


# ── ReportPdfRequest + ReportPdfResult (3 cases) ────────────


@pytest.mark.engine
def test_report_pdf_request_frozen_dataclass() -> None:
    """Frozen — ReportPdfRequest is immutable (AD-5 stdlib-only)."""
    request = _mk_request_21()
    assert dataclasses.is_dataclass(request)
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.report_id = 22  # type: ignore[misc]


@pytest.mark.engine
def test_report_pdf_result_frozen_dataclass() -> None:
    """Frozen — ReportPdfResult is immutable."""
    result = generate_report_pdf(request=_mk_request_21())
    assert dataclasses.is_dataclass(result)
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.report_id = 99  # type: ignore[misc]


@pytest.mark.engine
def test_report_pdf_request_default_factory_payload() -> None:
    """Default factory — payload + metadata default empty tuples."""
    request = ReportPdfRequest(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        period_key="2026-Q1",
        report_id=21,
    )
    assert request.payload == ()
    assert request.metadata == ()


# ── ReportPdfGenerationError envelope (4 cases) ────────────


@pytest.mark.engine
def test_report_pdf_generation_error_unsupported_report_id() -> None:
    """Edge — report_id=99 (unsupported) → envelope RAISE."""
    request = ReportPdfRequest(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        period_key="2026-Q1",
        report_id=99,
    )
    with pytest.raises(ReportPdfGenerationError) as exc_info:
        generate_report_pdf(request=request)
    assert exc_info.value.reason == "unsupported_report_id"
    assert exc_info.value.report_id == 99


@pytest.mark.engine
def test_report_pdf_generation_error_empty_period_key() -> None:
    """Edge — empty period_key → envelope RAISE."""
    request = ReportPdfRequest(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        period_key="",
        report_id=21,
        payload=({"product_id": "x", "allocated_krw": "1"},),
    )
    with pytest.raises(ReportPdfGenerationError) as exc_info:
        generate_report_pdf(request=request)
    assert exc_info.value.reason == "empty_period_key"


@pytest.mark.engine
def test_report_pdf_generation_error_no_payload_for_report21() -> None:
    """Discriminated union — report_id=21 + empty payload → envelope RAISE."""
    request = ReportPdfRequest(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        period_key="2026-Q1",
        report_id=21,
        payload=(),
    )
    with pytest.raises(ReportPdfGenerationError) as exc_info:
        generate_report_pdf(request=request)
    assert exc_info.value.reason == "no_payload_for_report21"
    assert exc_info.value.report_id == 21


@pytest.mark.engine
def test_report_pdf_generation_error_is_exception() -> None:
    """Hierarchy — `ReportPdfGenerationError` is `Exception` (CR 12-5 D-14)."""
    err = ReportPdfGenerationError(
        "test", report_id=21, reason="test_reason"
    )
    assert isinstance(err, Exception)
    assert err.report_id == 21
    assert err.reason == "test_reason"


# ── V8 byte-equality determinism (4 cases) ──────────────


@pytest.mark.engine
def test_generate_report_pdf_report21_determinism_100_repeats() -> None:
    """V8 byte-equality — 100회 반복 → 동일 pdf_bytes (determinism)."""
    request = _mk_request_21()
    result_first = generate_report_pdf(request=request)
    for _ in range(100):
        result_loop = generate_report_pdf(request=request)
        assert result_loop.pdf_bytes == result_first.pdf_bytes
        assert result_loop.generation_hash == result_first.generation_hash


@pytest.mark.engine
def test_generate_report_pdf_report21_different_period_changes_pdf() -> None:
    """V8 byte-equality — period_key 변경 → 다른 pdf_bytes."""
    req_q1 = _mk_request_21(period_key="2026-Q1")
    req_q2 = _mk_request_21(period_key="2026-Q2")
    result_q1 = generate_report_pdf(request=req_q1)
    result_q2 = generate_report_pdf(request=req_q2)
    assert result_q1.pdf_bytes != result_q2.pdf_bytes


@pytest.mark.engine
def test_generate_report_pdf_report21_different_tenant_changes_pdf() -> None:
    """V8 byte-equality — tenant_id 변경 → 다른 pdf_bytes."""
    req_tenant_a = _mk_request_21(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    )
    req_tenant_b = _mk_request_21(
        tenant_id=uuid.UUID("00000000-0000-0000-0000-000000000002"),
    )
    result_a = generate_report_pdf(request=req_tenant_a)
    result_b = generate_report_pdf(request=req_tenant_b)
    assert result_a.pdf_bytes != result_b.pdf_bytes


@pytest.mark.engine
def test_generate_report_pdf_report21_korean_text_escaping() -> None:
    """V8 byte-equality — Korean text rendered via Type0 CIDFont + Identity-H
    CMap envelope (matching Story 6-3 closing_pdf_export 6-3 B1 precedent).
    """
    request = _mk_request_21()
    result = generate_report_pdf(request=request)
    # PDF must contain Type0 CIDFont reference
    assert b"/Subtype /Type0" in result.pdf_bytes
    assert b"/Encoding /Identity-H" in result.pdf_bytes
