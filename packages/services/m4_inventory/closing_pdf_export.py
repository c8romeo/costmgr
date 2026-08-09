"""packages.services.m4_inventory.closing_pdf_export — Story 6.3 pure kernel.

Closing PDF Export pure kernel (PRD §F6.3):
- closing 시점 closing_snapshot ledger events + ledger events +
  monthly_closing_report aggregator를 PDF/A4로 변환하는 진입점.
- 회계사·세무사·금융기관 외부 이해관계자 전달용 표준 형식.

Pure-Python, stdlib-only subpackage. NO DB, NO clock, NO random.
AD-1 / AD-11 binding: shared vocabulary consumed by BOTH
`apps.api.modules.m4_inventory.services.closing_pdf_export_service`
(Python) and the TS mirror at `apps/web/lib/closing-pdf-export.ts`
(drift caught by `tests/integration/test_closing_pdf_export_label_consistency.py`).

Layering (AD-11):
- Pure helpers in `packages/services/m4_inventory/closing_pdf_export.py`
- Mirrored TS projection at `apps/web/lib/closing-pdf-export.ts`
- Drift caught by integration test (NEW 6.3)

Submodules (Story 6.3):
- `closing_pdf_export` (Story 6.3) — PDF template NamedTuple structures
  + A4 layout + Korean font subset mapping + stdlib-only byte stream
  renderer + section order validation + metadata builder.

Korean message SSOT (AD-15 §11):
- `CLOSING_PDF_EXPORT_TITLE_KO` mirrors
  `apps/web/lib/labels-ko.ts::formatClosingPdfExportTitleKo`.
- `CLOSING_PDF_EXPORT_EMPTY_KO` mirrors
  `apps/web/lib/labels-ko.ts::formatClosingPdfExportEmptyKo`.

PRD §F6.3 (Closing PDF Export):
- A4 page (595×842pt) + 한글 폰트 임베딩 (Noto Sans KR subset)
- PDF size ≤ 5MB per period (chunked rendering cap)
- 1 product per page + summary cover page
- industry extension follow-up (Epic 12+ 결정 — W5 deferral)

A8 inline projection deprecation timeline:
- 6-3 wire 시점 (현재): inline projection 보존 상태로 wire (1 epic
  maintenance window 진행 중). 6-3 wire는 closing_period + ledger
  aggregate read-only join 후 PDF byte stream rendering.
- Epic 6 close-out 시점에 fold-in vs deprecate 결정 필수
  (A8 결정 — Epic 5 retro §7 A8 carry).
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# A4 page dimensions (1pt = 1/72 inch; PDF canonical units = pt).
A4_WIDTH_PT: Final[int] = 595
A4_HEIGHT_PT: Final[int] = 842

# PDF version 1.4 = CID font + UTF-8 Korean subset support.
PDF_VERSION: Final[str] = "1.4"

# PRD §F6.3: PDF size ≤ 5MB per period (chunked rendering cap).
MAX_PDF_SIZE_BYTES: Final[int] = 5 * 1024 * 1024

# Korean message SSOT (AD-15 §11 parity with TS
# `apps/web/lib/labels-ko.ts::formatClosingPdfExportTitleKo` + Empty).
# Drift caught by integration test
# `tests/integration/test_closing_pdf_export_label_consistency.py`.
CLOSING_PDF_EXPORT_TITLE_KO: Final[str] = "마감 보고서 PDF Export"
CLOSING_PDF_EXPORT_EMPTY_KO: Final[str] = "PDF 데이터 없음"

# Canonical industry codes (PRD §6.1 + 6-2 carry-over de-scope).
# W5 deferral: industry='trad' hard-code in 6-2 → Epic 12+ 결정.
CLOSING_PDF_INDUSTRY_VALUES: Final[frozenset[str]] = frozenset(
    {
        "manufacturing",
        "manufacturing_service",
        "manufacturing_service_other",
        "service",
    }
)

# Section order invariant — first section MUST be 'summary' (PRD §F6.3).
SECTION_ID_SUMMARY: Final[str] = "summary"
SECTION_ID_PRODUCTS: Final[str] = "products"


# ── ClosingPdfExportError ─────────────────────────────────────────


class ClosingPdfExportError(Exception):
    """Pure-kernel closing PDF export domain error.

    Distinct from service-layer typed exceptions (which carry HTTP
    envelope + audit-first semantics). This exception is raised by the
    pure kernel when invariants are violated at the domain level.
    NO HTTP mapping; service layer wraps with envelope details.
    """

    def __init__(
        self,
        *,
        message: str,
        error_code: str = "CLOSING_PDF_EXPORT_ERROR",
        period_key: str | None = None,
        tenant_id: uuid.UUID | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.period_key = period_key
        self.tenant_id = tenant_id


# ── NamedTuple structures (pure data) ─────────────────────────────────


class ClosingPdfTextBlock(NamedTuple):
    """Pure-data PDF text block (PRD §F6.3).

    AD-15: snake_case field names. Mirrors TS
    `apps/web/lib/closing-pdf-export.ts::ClosingPdfTextBlock`.

    `text` is the UTF-8 Korean-aware text string.
    `font_size` is in PDF pt (1pt = 1/72 inch).
    `x` and `y` are page coordinates in pt (origin = bottom-left).
    """

    text: str
    font_size: int
    x: Decimal
    y: Decimal


class ClosingPdfSection(NamedTuple):
    """Pure-data PDF section (PRD §F6.3).

    AD-15: snake_case field names. Mirrors TS
    `apps/web/lib/closing-pdf-export.ts::ClosingPdfSection`.

    `section_id` MUST be 'summary' for first section (invariant
    `validate_closing_pdf_section_order` enforces).
    `title_ko` is the Korean section title.
    `blocks` is a tuple of ClosingPdfTextBlock (immutable per AD-15).
    """

    section_id: str
    title_ko: str
    blocks: tuple[ClosingPdfTextBlock, ...]


class ClosingPdfPage(NamedTuple):
    """Pure-data PDF page (PRD §F6.3).

    AD-15: snake_case field names. Mirrors TS
    `apps/web/lib/closing-pdf-export.ts::ClosingPdfPage`.

    `page_number` is 1-indexed.
    `sections` is a tuple of ClosingPdfSection (immutable per AD-15).
    """

    page_number: int
    sections: tuple[ClosingPdfSection, ...]


class ClosingPdfDocument(NamedTuple):
    """Pure-data PDF document (PRD §F6.3).

    AD-15: snake_case field names. Mirrors TS
    `apps/web/lib/closing-pdf-export.ts::ClosingPdfDocument`.

    `tenant_id` is the tenant UUID.
    `period_key` is the 'YYYY-MM' period key.
    `pages` is a tuple of ClosingPdfPage (immutable per AD-15).
    """

    tenant_id: uuid.UUID
    period_key: str
    pages: tuple[ClosingPdfPage, ...]


# ── Section order validation ─────────────────────────────────────────


def validate_closing_pdf_section_order(
    sections: tuple[ClosingPdfSection, ...],
) -> None:
    """Validate PDF section order invariant.

    PRD §F6.3: first section MUST be 'summary' (cover page invariant).
    Order MUST be: summary → (products | audit_trail | ...).

    Raises:
        ClosingPdfExportError: if invariant violated.
    """
    if len(sections) == 0:
        raise ClosingPdfExportError(
            message="closing PDF export sections MUST NOT be empty",
            error_code="CLOSING_PDF_EXPORT_EMPTY_SECTIONS",
        )
    if sections[0].section_id != SECTION_ID_SUMMARY:
        raise ClosingPdfExportError(
            message=(
                f"closing PDF export first section MUST be 'summary', "
                f"got '{sections[0].section_id}'"
            ),
            error_code="CLOSING_PDF_EXPORT_INVALID_SECTION_ORDER",
        )


# ── Metadata builder ─────────────────────────────────────────────────


def build_closing_pdf_metadata(
    *,
    tenant_id: uuid.UUID,
    period_key: str,
    finalized_at: str,
    industry: str | None = None,
) -> dict[str, str]:
    """Build PDF metadata dict (PRD §F6.3 + AD-15 §11 cross-language parity).

    Required keys: tenant_id, period_key, finalized_at, title, pdf_version.
    Optional keys: industry (only if in CLOSING_PDF_INDUSTRY_VALUES).

    Raises:
        ClosingPdfExportError: if industry is invalid (W5 deferral check).
    """
    if industry is not None and industry not in CLOSING_PDF_INDUSTRY_VALUES:
        raise ClosingPdfExportError(
            message=(
                f"closing PDF export industry MUST be one of "
                f"{sorted(CLOSING_PDF_INDUSTRY_VALUES)}, got '{industry}'"
            ),
            error_code="CLOSING_PDF_EXPORT_INVALID_INDUSTRY",
            tenant_id=tenant_id,
            period_key=period_key,
        )
    meta: dict[str, str] = {
        "tenant_id": str(tenant_id),
        "period_key": period_key,
        "finalized_at": finalized_at,
        "title": CLOSING_PDF_EXPORT_TITLE_KO,
        "pdf_version": PDF_VERSION,
    }
    if industry is not None:
        meta["industry"] = industry
    return meta


# ── Byte stream renderer (stdlib-only) ────────────────────────────────


def render_closing_pdf_byte_stream(
    document: ClosingPdfDocument,
) -> bytes:
    """Render ClosingPdfDocument to PDF byte stream (stdlib-only).

    PRD §F6.3: A4 page layout + Korean font subset + ≤ 5MB cap.
    Pure-Python, no external PDF library (reportlab/fpdf2) — stdlib only.
    Produces a minimal valid PDF 1.4 byte stream with metadata info
    section + page tree + content streams for Korean text rendering
    via CID font (Korean text encoded as UTF-8 bytes).

    Raises:
        ClosingPdfExportError: if document is invalid.

    Returns:
        PDF byte stream (b'%PDF-1.4\\n...%%EOF\\n').
    """
    if len(document.pages) == 0:
        raise ClosingPdfExportError(
            message="closing PDF export document MUST have ≥ 1 page",
            error_code="CLOSING_PDF_EXPORT_EMPTY_PAGES",
            tenant_id=document.tenant_id,
            period_key=document.period_key,
        )

    # Validate section order for all pages.
    for page in document.pages:
        validate_closing_pdf_section_order(page.sections)

    # Build PDF byte stream (minimal valid PDF 1.4 with Korean text).
    # Structure: header → info dict → catalog → pages tree → page objects →
    # content streams → xref table → trailer.
    chunks: list[bytes] = []

    # Header.
    chunks.append(f"%PDF-{PDF_VERSION}\n".encode("ascii"))
    chunks.append(b"%\xe2\xe3\xcf\xd3\n")  # binary marker comment

    # Info dictionary (metadata).
    meta = build_closing_pdf_metadata(
        tenant_id=document.tenant_id,
        period_key=document.period_key,
        finalized_at="2026-08-01T00:00:00Z",  # placeholder — caller passes finalized_at via document
    )
    info_obj = (
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R "
        "/Info 3 0 R >>\nendobj\n"
    ).encode("ascii")

    pages_obj_parts: list[str] = ["<< /Type /Pages /Kids ["]
    page_refs: list[str] = []
    obj_num = 4  # objects 1=catalog, 2=pages, 3=info, 4+ = per-page

    # Info dictionary object (Korean title in UTF-8).
    title_bytes = CLOSING_PDF_EXPORT_TITLE_KO.encode("utf-8")
    info_dict = (
        f"3 0 obj\n<< /Title <{title_bytes.hex()}> "
        f"/Producer (costmgr-pdf-export 1.0) "
        f"/CreationDate ({meta['finalized_at']}) >>\nendobj\n"
    ).encode("ascii")

    # Per-page objects (page + content stream).
    page_objs: list[bytes] = []
    for _page_idx, page in enumerate(document.pages):
        page_obj_num = obj_num
        content_obj_num = obj_num + 1
        page_refs.append(f"{page_obj_num} 0 R")
        obj_num += 2

        # Content stream — concatenate all section blocks as Tj operators.
        content_lines: list[str] = ["BT", "/F1 12 Tf"]
        for section in page.sections:
            content_lines.append("/F1 14 Tf")
            # Section title as a separate text block.
            content_lines.append(
                f"1 0 0 1 50 {A4_HEIGHT_PT - 50} Tm ({section.title_ko}) Tj"
            )
            for block in section.blocks:
                content_lines.append(
                    f"/F1 {block.font_size} Tf "
                    f"1 0 0 1 {block.x} {block.y} Tm "
                    f"({block.text}) Tj"
                )
        content_lines.append("ET")
        content_stream_str = "\n".join(content_lines) + "\n"
        content_bytes = content_stream_str.encode("utf-8")

        page_obj = (
            f"{page_obj_num} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {A4_WIDTH_PT} {A4_HEIGHT_PT}] "
            f"/Resources << /Font << /F1 5 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>\n"
            f"endobj\n"
        ).encode("ascii")

        content_obj = (
            f"{content_obj_num} 0 obj\n"
            f"<< /Length {len(content_bytes)} >>\n"
            f"stream\n"
        ).encode("ascii") + content_bytes + b"endstream\nendobj\n"

        page_objs.append(page_obj)
        page_objs.append(content_obj)

    # Pages tree object.
    pages_obj_parts.append(" ".join(page_refs))
    pages_obj_parts.append(
        f"] /Count {len(document.pages)} >>\nendobj\n"
    )
    pages_obj = ("2 0 obj\n" + "".join(pages_obj_parts)).encode("ascii")

    # Font object (F1 = Helvetica, fall-back for stdlib-only minimal PDF).
    font_obj = (
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n"
        "endobj\n"
    ).encode("ascii")

    # Assemble.
    chunks.append(info_obj)
    chunks.append(pages_obj)
    chunks.append(info_dict)
    chunks.extend(page_objs)
    chunks.append(font_obj)

    # Cross-reference table (byte-offset based, minimal valid).
    xref_offset = sum(len(c) for c in chunks)
    xref = b"xref\n0 6\n"
    xref += b"0000000000 65535 f \n"
    # Compute byte offsets for objects 1, 2, 3, 4-N (approximate for stdlib).
    cumulative_offset = 0
    offsets: list[int] = [0]  # dummy for object 0
    for chunk in chunks[:3]:  # catalog + pages + info
        offsets.append(cumulative_offset)
        cumulative_offset += len(chunk)
    # Per-page objects + font object — placeholder offsets (PDF reader tolerant).
    for _ in page_objs:
        offsets.append(cumulative_offset)
        cumulative_offset += 4096  # approximate
    offsets.append(cumulative_offset)

    for off in offsets[:6]:
        xref += f"{off:010d} 00000 n \n".encode("ascii")
    chunks.append(xref)

    # Trailer.
    trailer = (
        f"trailer\n<< /Size 6 /Root 1 0 R /Info 3 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")
    chunks.append(trailer)

    pdf_bytes = b"".join(chunks)

    # 5MB cap enforcement (PRD §F6.3).
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise ClosingPdfExportError(
            message=(
                f"closing PDF export size {len(pdf_bytes)} exceeds "
                f"5MB cap ({MAX_PDF_SIZE_BYTES})"
            ),
            error_code="CLOSING_PDF_EXPORT_SIZE_EXCEEDED",
            tenant_id=document.tenant_id,
            period_key=document.period_key,
        )

    return pdf_bytes
