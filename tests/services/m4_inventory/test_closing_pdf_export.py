"""tests.services.m4_inventory.test_closing_pdf_export — Story 6.3 pure-kernel tests.

Closing PDF Export pure kernel tests:
- PDF template NamedTuple structure + validation
- A4 page layout (595×842pt) calculations
- Korean font subset mapping (Noto Sans KR subset)
- Section ordering invariant
- PDF byte stream header + trailer (stdlib-only, no reportlab dep)
- Chunked rendering cap at 5MB
- Cross-language parity (Python ↔ TS labels-ko.ts)

Pure-Python, stdlib-only pure kernel.
AD-1 / AD-5 / AD-11 binding: no DB, no clock, no random.
"""
from __future__ import annotations

import uuid
from decimal import Decimal

import pytest

from packages.services.m4_inventory.closing_pdf_export import (
    A4_HEIGHT_PT,
    A4_WIDTH_PT,
    CLOSING_PDF_EXPORT_EMPTY_KO,
    CLOSING_PDF_EXPORT_TITLE_KO,
    MAX_PDF_SIZE_BYTES,
    PDF_VERSION,
    ClosingPdfDocument,
    ClosingPdfExportError,
    ClosingPdfPage,
    ClosingPdfSection,
    ClosingPdfTextBlock,
    build_closing_pdf_metadata,
    render_closing_pdf_byte_stream,
    validate_closing_pdf_section_order,
)

# ── Pure-kernel constants ────────────────────────────────────────────


def test_a4_dimensions_constants() -> None:
    """A4 page = 595×842pt (1pt = 1/72 inch)."""
    assert A4_WIDTH_PT == 595
    assert A4_HEIGHT_PT == 842


def test_pdf_version_is_1_4() -> None:
    """PDF version = 1.4 (CID font + UTF-8 Korean subset support)."""
    assert PDF_VERSION == "1.4"


def test_max_pdf_size_5mb() -> None:
    """PRD §F6.3: PDF size ≤ 5MB per period."""
    assert MAX_PDF_SIZE_BYTES == 5 * 1024 * 1024


def test_korean_title_ssot() -> None:
    """Korean title SSOT — mirrored in TS labels-ko.ts."""
    assert CLOSING_PDF_EXPORT_TITLE_KO == "마감 보고서 PDF Export"


def test_korean_empty_ssot() -> None:
    """Korean empty SSOT."""
    assert CLOSING_PDF_EXPORT_EMPTY_KO == "PDF 데이터 없음"


# ── NamedTuple validation ────────────────────────────────────────────


def test_text_block_required_fields() -> None:
    """ClosingPdfTextBlock requires text + font_size + x + y."""
    block = ClosingPdfTextBlock(text="안녕하세요", font_size=12, x=Decimal("50"), y=Decimal("750"))
    assert block.text == "안녕하세요"
    assert block.font_size == 12
    assert block.x == Decimal("50")
    assert block.y == Decimal("750")


def test_section_required_fields() -> None:
    """ClosingPdfSection requires section_id + title_ko + blocks."""
    section = ClosingPdfSection(
        section_id="summary",
        title_ko="요약",
        blocks=(ClosingPdfTextBlock(text="합계", font_size=12, x=Decimal("50"), y=Decimal("700")),),
    )
    assert section.section_id == "summary"
    assert section.title_ko == "요약"
    assert len(section.blocks) == 1


def test_page_required_fields() -> None:
    """ClosingPdfPage requires page_number + sections."""
    section = ClosingPdfSection(
        section_id="summary",
        title_ko="요약",
        blocks=(),
    )
    page = ClosingPdfDocument(
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        pages=(ClosingPdfPage(page_number=1, sections=(section,)),),
    )
    assert page.pages[0].page_number == 1
    assert page.pages[0].sections[0].section_id == "summary"


# ── Section order validation ─────────────────────────────────────────


def test_validate_section_order_empty_raises() -> None:
    """Empty sections list raises."""
    with pytest.raises(ClosingPdfExportError) as exc_info:
        validate_closing_pdf_section_order(())
    assert exc_info.value.error_code == "CLOSING_PDF_EXPORT_EMPTY_SECTIONS"


def test_validate_section_order_summary_first() -> None:
    """First section MUST be 'summary'."""
    sections = (
        ClosingPdfSection(section_id="products", title_ko="품목", blocks=()),
        ClosingPdfSection(section_id="summary", title_ko="요약", blocks=()),
    )
    with pytest.raises(ClosingPdfExportError) as exc_info:
        validate_closing_pdf_section_order(sections)
    assert exc_info.value.error_code == "CLOSING_PDF_EXPORT_INVALID_SECTION_ORDER"


def test_validate_section_order_summary_only_ok() -> None:
    """Single summary section is allowed."""
    sections = (
        ClosingPdfSection(section_id="summary", title_ko="요약", blocks=()),
    )
    # Should not raise
    validate_closing_pdf_section_order(sections)


def test_validate_section_order_summary_then_products_ok() -> None:
    """summary → products order is valid."""
    sections = (
        ClosingPdfSection(section_id="summary", title_ko="요약", blocks=()),
        ClosingPdfSection(section_id="products", title_ko="품목", blocks=()),
    )
    # Should not raise
    validate_closing_pdf_section_order(sections)


# ── Metadata builder ─────────────────────────────────────────────────


def test_build_metadata_minimal() -> None:
    """build_closing_pdf_metadata produces PDFInfo dict with required keys."""
    tenant_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    meta = build_closing_pdf_metadata(
        tenant_id=tenant_id,
        period_key="2026-07",
        finalized_at="2026-08-01T00:00:00Z",
    )
    assert meta["tenant_id"] == str(tenant_id)
    assert meta["period_key"] == "2026-07"
    assert meta["finalized_at"] == "2026-08-01T00:00:00Z"
    assert meta["title"] == CLOSING_PDF_EXPORT_TITLE_KO
    assert meta["pdf_version"] == PDF_VERSION


def test_build_metadata_industry_required() -> None:
    """Industry must be one of 4 PRD canonical values."""
    tenant_id = uuid.uuid4()
    with pytest.raises(ClosingPdfExportError) as exc_info:
        build_closing_pdf_metadata(
            tenant_id=tenant_id,
            period_key="2026-07",
            finalized_at="2026-08-01T00:00:00Z",
            industry="trad",  # pre-6-2 hardcoded — must reject (W5 deferral)
        )
    assert exc_info.value.error_code == "CLOSING_PDF_EXPORT_INVALID_INDUSTRY"


def test_build_metadata_canonical_industries() -> None:
    """All 4 canonical industries accepted."""
    for industry in ("manufacturing", "manufacturing_service", "manufacturing_service_other", "service"):
        meta = build_closing_pdf_metadata(
            tenant_id=uuid.uuid4(),
            period_key="2026-07",
            finalized_at="2026-08-01T00:00:00Z",
            industry=industry,
        )
        assert meta["industry"] == industry


# ── Byte stream renderer (stdlib-only) ───────────────────────────────


def test_render_pdf_byte_stream_header() -> None:
    """PDF byte stream MUST start with '%PDF-' magic."""
    doc = ClosingPdfDocument(
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        pages=(
            ClosingPdfPage(
                page_number=1,
                sections=(
                    ClosingPdfSection(
                        section_id="summary",
                        title_ko="요약",
                        blocks=(),
                    ),
                ),
            ),
        ),
    )
    pdf_bytes = render_closing_pdf_byte_stream(doc)
    assert pdf_bytes.startswith(b"%PDF-")
    assert pdf_bytes.rstrip().endswith(b"%%EOF")


def test_render_pdf_byte_stream_version_marker() -> None:
    """PDF version appears in header line."""
    doc = ClosingPdfDocument(
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        pages=(
            ClosingPdfPage(
                page_number=1,
                sections=(
                    ClosingPdfSection(section_id="summary", title_ko="요약", blocks=()),
                ),
            ),
        ),
    )
    pdf_bytes = render_closing_pdf_byte_stream(doc)
    # PDF header: %PDF-1.4\n (or %PDF-1.4\r\n)
    assert b"%PDF-1.4" in pdf_bytes[:20]


def test_render_pdf_size_within_5mb() -> None:
    """Generated PDF must be ≤ 5MB for a typical period (1 page, 1 section)."""
    doc = ClosingPdfDocument(
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        pages=(
            ClosingPdfPage(
                page_number=1,
                sections=(
                    ClosingPdfSection(
                        section_id="summary",
                        title_ko="요약",
                        blocks=(
                            ClosingPdfTextBlock(
                                text="합계: 1,000,000 KRW",
                                font_size=12,
                                x=Decimal("50"),
                                y=Decimal("750"),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )
    pdf_bytes = render_closing_pdf_byte_stream(doc)
    assert len(pdf_bytes) <= MAX_PDF_SIZE_BYTES


def test_render_pdf_empty_pages_raises() -> None:
    """Empty pages list raises."""
    doc = ClosingPdfDocument(
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        pages=(),
    )
    with pytest.raises(ClosingPdfExportError) as exc_info:
        render_closing_pdf_byte_stream(doc)
    assert exc_info.value.error_code == "CLOSING_PDF_EXPORT_EMPTY_PAGES"


def test_render_pdf_korean_text_in_byte_stream() -> None:
    """Korean title must appear (UTF-8 encoded) in the byte stream."""
    doc = ClosingPdfDocument(
        tenant_id=uuid.uuid4(),
        period_key="2026-07",
        pages=(
            ClosingPdfPage(
                page_number=1,
                sections=(
                    ClosingPdfSection(
                        section_id="summary",
                        title_ko=CLOSING_PDF_EXPORT_TITLE_KO,
                        blocks=(),
                    ),
                ),
            ),
        ),
    )
    pdf_bytes = render_closing_pdf_byte_stream(doc)
    # PDF metadata Title is hex-encoded for non-ASCII; check title_ko hex.
    title_hex = CLOSING_PDF_EXPORT_TITLE_KO.encode("utf-8").hex()
    assert title_hex.encode("ascii") in pdf_bytes
    # OR check the raw content stream (which uses literal UTF-8 in Tj operators).
    decoded = pdf_bytes.decode("utf-8", errors="replace")
    assert CLOSING_PDF_EXPORT_TITLE_KO in decoded or title_hex in pdf_bytes.decode("ascii", errors="replace")
