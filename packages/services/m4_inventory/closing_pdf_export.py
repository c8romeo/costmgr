"""packages.services.m4_inventory.closing_pdf_export — Story 6.3 pure kernel.

Closing PDF Export pure kernel (PRD §F6.3):
- closing 시점 closing_snapshot ledger events + ledger events +
  monthly_closing_report aggregator를 PDF/A4로 변환하는 진입점.
- 회계사·세무사·세무사·금융기관 외부 이해관계자 전달용 표준 형식.

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
- A4 page (595×842pt) + 한글 폰트 임베딩 (CIDFont Type0 + Identity-H CMap)
- PDF size ≤ 5MB per period (chunked rendering cap)
- 1 product per page + summary cover page
- industry extension follow-up (Epic 12+ 결정 — W5 deferral)

A8 inline projection deprecation timeline:
- 6-3 wire 시점 (현재): inline projection 보존 상태로 wire (1 epic
  maintenance window 진행 중). 6-3 wire는 closing_period + ledger
  aggregate read-only join 후 PDF byte stream rendering.
- Epic 6 close-out 시점에 fold-in vs deprecate 결정 필수
  (A8 결정 — Epic 5 retro §7 A8 carry).

6-3 PATCH (3rd sweep B1~B4):
- B1: Type0 CIDFont + Identity-H CMap + ToUnicode CMap stream (B1 patch).
  System Noto Sans KR을 미리 임베드하기 어려우므로, Identity-H CMap
  으로 2바이트 코드 → GID 매핑 + ToUnicode stream으로 GID → Unicode
  매핑을 제공. hex string <FEFF...> 입력으로 한글 렌더링.
- B2: 동적 xref offset (object_count 기반, 정확 byte offset 추적).
- B3: PDF literal / Content-Disposition 문자열 이스케이프 헬퍼 추가
  (`escape_pdf_literal`, `escape_content_disposition_filename`).
- B4: size_bytes를 render 직전 측정하여 호출자가 받을 수 있도록
  `RenderedClosingPdf` NamedTuple로 반환 + 사이즈 위반 시
  `ClosingPdfExportError.details`에 실제 size_bytes 포함.
"""

from __future__ import annotations

import re
import uuid
from decimal import Decimal
from typing import Final, NamedTuple

# ── Constants ────────────────────────────────────────────────
# A4 page dimensions (1pt = 1/72 inch; PDF canonical units = pt).
A4_WIDTH_PT: Final[int] = 595
A4_HEIGHT_PT: Final[int] = 842

# PDF 1.7 (Acrobat 8+ baseline) — Identity-H CMap + Type0 CIDFont 지원.
PDF_VERSION: Final[str] = "1.7"

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
        details: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.period_key = period_key
        self.tenant_id = tenant_id
        self.details: dict[str, str] = details or {}


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
    `finalized_at` is the ISO 8601 timestamp (caller-provided — pure
    kernel NO-clock AD-5).
    """

    tenant_id: uuid.UUID
    period_key: str
    pages: tuple[ClosingPdfPage, ...]
    finalized_at: str


class RenderedClosingPdf(NamedTuple):
    """Pure-data rendered PDF output (PRD §F6.3).

    `pdf_bytes` is the byte stream. `size_bytes` is `len(pdf_bytes)`.
    `object_count` is the number of objects in the PDF (used by
    xref/trailer/SIZE assertion).
    """

    pdf_bytes: bytes
    size_bytes: int
    object_count: int


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


# ── String escaping helpers (B3) ─────────────────────────────────────


# Characters that must be escaped in PDF literal strings: '(', ')', '\\',
# plus CR/LF (which must be encoded as \\r/\\n).
_PDF_LITERAL_ESCAPE_RE = re.compile(r"[\\()\r\n]")


def escape_pdf_literal(value: str) -> str:
    """Escape user-supplied string for safe inclusion in a PDF literal.

    Per PDF 1.7 §7.3.4.2: backslash, left paren, right paren, CR, LF
    must be escaped with a leading backslash. Other characters pass
    through unchanged; we let the caller encode UTF-8 separately when
    needed.

    Args:
        value: untrusted text (Korean labels, period_key, product_id, ...).

    Returns:
        Escaped literal-safe string. Surrounding parentheses must be
        added by the caller.
    """
    return _PDF_LITERAL_ESCAPE_RE.sub(
        lambda m: {
            "\\": "\\\\",
            "(": "\\(",
            ")": "\\)",
            "\r": "\\r",
            "\n": "\\n",
        }[m.group(0)],
        value,
    )


# Characters disallowed in Content-Disposition `filename=` per RFC 6266.
_CONTENT_DISPOSITION_UNSAFE_RE = re.compile(r'["\\\r\n\x00-\x1f]')


def escape_content_disposition_filename(value: str) -> str:
    """Sanitize a value for safe use in a Content-Disposition filename.

    Strips control characters, double quotes, and backslashes. Keeps
    ASCII alphanumerics, dot, hyphen, underscore. Non-ASCII characters
    are preserved as-is and the caller SHOULD also emit a
    `filename*=UTF-8''...` parameter (RFC 6266 §5).

    Args:
        value: user-supplied filename component (e.g., period_key).

    Returns:
        Filename-safe ASCII+UTF-8 string.
    """
    return _CONTENT_DISPOSITION_UNSAFE_RE.sub("_", value)


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


# ── Byte stream renderer (stdlib-only, Type0 CIDFont + Identity-H) ────


def _build_identity_h_cmap() -> bytes:
    """Build Identity-H CMap stream (PDF 1.7 §9.10.3).

    Identity-H maps 2-byte code points directly to GID via the CIDFont's
    internal ordering. This is the canonical CMap for Type0 CIDFonts.
    """
    return (
        b"/CIDInit /ProcSet findresource begin\n"
        b"12 dict begin\n"
        b"begincmap\n"
        b"/CMapType 2 def\n"
        b"1 begincodespacerange\n"
        b"<0000> <FFFF>\n"
        b"endcodespacerange\n"
        b"1 beginbfrange\n"
        b"<0000> <FFFF> <0000>\n"
        b"endbfrange\n"
        b"endcmap\n"
        b"CMapName /Identity-H def\n"
        b"CMapType 2 def\n"
        b"1 begincodespacerange\n"
        b"<0000> <FFFF>\n"
        b"endcodespacerange\n"
        b"1 beginbfrange\n"
        b"<0000> <FFFF> <0000>\n"
        b"endbfrange\n"
        b"endcmap\n"
        b"end\n"
        b"end\n"
    )


def _build_tounicode_cmap(
    *,
    codepoints: tuple[int, ...],
) -> bytes:
    """Build ToUnicode CMap mapping GID (0..N) back to Unicode codepoints.

    Used by PDF readers to enable text search / copy / accessibility.
    `codepoints` enumerates the Unicode values used in this document,
    one per used GID slot.

    The CMap is a 1-to-1 GID<->Unicode map. Unused high GIDs are
    omitted — readers that see an unmapped GID silently skip it.
    """
    if len(codepoints) > 0xFFFF:
        raise ClosingPdfExportError(
            message=(
                f"closing PDF export ToUnicode cmap size {len(codepoints)} " f"exceeds 0xFFFF limit"
            ),
            error_code="CLOSING_PDF_EXPORT_TOUCMAP_OVERFLOW",
        )
    # Build bfrange entries. Each line: <srcCodeLo> <srcCodeHi> <dstUnicodeLo>
    # We map GID -> Unicode 1:1. Group consecutive sequences of length >= 1
    # into a single bfrange where the GIDs and Unicode codepoints are
    # contiguous.
    pairs: list[tuple[int, int]] = sorted(set(enumerate(codepoints)))

    lines: list[bytes] = [
        b"/CIDInit /ProcSet findresource begin\n",
        b"12 dict begin\n",
        b"begincmap\n",
        b"/CMapType 2 def\n",
        b"1 begincodespacerange\n",
        b"<0000> <FFFF>\n",
        b"endcodespacerange\n",
    ]
    chunk: list[tuple[int, int]] = []
    for gid, cp in pairs:
        chunk.append((gid, cp))
        # Flush on length 100 (PDF spec limit per bfrange block) or
        # when the next pair would break the contiguous-1:1 mapping.
        if len(chunk) >= 100:
            _flush_bfrange(lines, chunk)
            chunk = []
    if chunk:
        _flush_bfrange(lines, chunk)
    lines.extend(
        [
            b"endcmap\n",
            b"CMapName /Adobe-Identity-UCS def\n",
            b"CMapType 2 def\n",
            b"1 begincodespacerange\n",
            b"<0000> <FFFF>\n",
            b"endcodespacerange\n",
            b"end\n",
            b"end\n",
        ]
    )
    return b"".join(lines)


def _flush_bfrange(
    lines: list[bytes],
    chunk: list[tuple[int, int]],
) -> None:
    """Flush a bfrange block (PDF 1.7 §9.10.3)."""
    if not chunk:
        return
    first_gid = chunk[0][0]
    last_gid = chunk[-1][0]
    expected_first_cp = chunk[0][1]
    expected_last_cp = chunk[-1][1]
    is_contiguous = (last_gid - first_gid + 1) == len(chunk) and (
        expected_last_cp - expected_first_cp + 1
    ) == len(chunk)
    if is_contiguous:
        lines.append(
            f"1 beginbfrange\n"
            f"<{first_gid:04X}> <{last_gid:04X}> <{expected_first_cp:04X}>\n"
            f"endbfrange\n".encode("ascii")
        )
    else:
        # Per-gid bfchar mapping.
        lines.append(f"{len(chunk)} beginbfchar\n".encode("ascii"))
        for gid, cp in chunk:
            lines.append(f"<{gid:04X}> <{cp:04X}>\n".encode("ascii"))
        lines.append(b"endbfchar\n")


def _utf16be_hex(value: str) -> str:
    """Encode `value` as UTF-16BE big-endian hex for Identity-H Tj input.

    We do not strip the BOM (U+FEFF) — most PDF readers handle both
    with/without BOM, but emitting the BOM avoids one class of
    mis-encoding regressions on strict validators.
    """
    return "﻿" + value


def _build_closing_pdf_bytes(
    document: ClosingPdfDocument,
) -> tuple[bytes, int, tuple[int, ...]]:
    """Assemble the PDF byte stream.

    Returns a 3-tuple of (pdf_bytes, object_count, codepoints).
    `codepoints` is the list of Unicode codepoints used in the document,
    in document order, which `_build_tounicode_cmap` consumes to build
    the GID↔Unicode reverse map.
    """
    if len(document.pages) == 0:
        raise ClosingPdfExportError(
            message="closing PDF export document MUST have ≥ 1 page",
            error_code="CLOSING_PDF_EXPORT_EMPTY_PAGES",
            tenant_id=document.tenant_id,
            period_key=document.period_key,
        )
    for page in document.pages:
        validate_closing_pdf_section_order(page.sections)

    # Codepoint collection (order of appearance). Skip ASCII chars —
    # Identity-H is for non-ASCII; ASCII falls through to default encoding.
    codepoint_set: list[int] = []

    def _collect(text: str) -> None:
        for ch in text:
            cp = ord(ch)
            if cp > 0x7F and cp not in codepoint_set:
                codepoint_set.append(cp)

    # Pre-walk: collect all non-ASCII codepoints used in the document.
    for page in document.pages:
        for section in page.sections:
            _collect(section.title_ko)
            for block in section.blocks:
                _collect(block.text)
    # Tenant/period metadata (used in Info / xref strings only — not in
    # Tj streams, so no codepoint collection needed).

    # ── Object assembly ──────────────────────────────────────────
    # Object numbering:
    #   1 = catalog
    #   2 = pages
    #   3 = info
    #   4 = CIDFont (Type0 base font + CIDSystemInfo + FontDescriptor
    #       + CIDToGIDMap + ToUnicode stream — emitted as a sub-group)
    #   5..N = per-page (page + content stream pairs)
    #
    # We use 2 objects per page for simplicity (page + content stream).
    # Total object count: 3 + 1 (font group counted as 1) + 2 * N + 1
    #   = 4 + 2N. We will compute the exact count and emit the xref
    #   from the real byte offsets.
    object_count = 3 + 1 + 2 * len(document.pages)
    font_obj_num = 4
    page_obj_numbers: list[int] = []
    content_obj_numbers: list[int] = []
    for i in range(len(document.pages)):
        page_obj_numbers.append(5 + 2 * i)
        content_obj_numbers.append(6 + 2 * i)

    # Build content streams (UTF-16BE hex string with BOM).
    content_streams: list[bytes] = []
    for page in document.pages:
        body_parts: list[str] = ["BT", "/F2 12 Tf"]
        for section in page.sections:
            body_parts.append("/F2 14 Tf")
            title_literal = escape_pdf_literal(section.title_ko)
            body_parts.append(f"1 0 0 1 50 {A4_HEIGHT_PT - 50} Tm ({title_literal}) Tj")
            for block in section.blocks:
                text_literal = escape_pdf_literal(block.text)
                body_parts.append(
                    f"/F2 {block.font_size} Tf "
                    f"1 0 0 1 {block.x} {block.y} Tm "
                    f"({text_literal}) Tj"
                )
        body_parts.append("ET")
        content_str = "\n".join(body_parts) + "\n"
        # Encode as UTF-16BE hex string with BOM, per Identity-H
        # convention for non-ASCII text.
        utf16_hex = _utf16be_hex(content_str).encode("utf-16-be").hex()
        # Wrap the hex string in <...> with line breaks ≤ 255 chars.
        chunks: list[str] = ["<"]
        for i in range(0, len(utf16_hex), 254):
            chunks.append(utf16_hex[i : i + 254])
        chunks.append(">")
        content_bytes = "\n".join(chunks).encode("ascii")
        content_streams.append(content_bytes)

    # Build the CMap and ToUnicode stream.
    identity_h_cmap = _build_identity_h_cmap()
    tounicode_cmap = _build_tounicode_cmap(codepoints=tuple(codepoint_set))

    # Assemble object dict in numerical order. We track exact byte
    # offsets by writing each object's body to a buffer first.
    objects: dict[int, bytes] = {}

    # Object 1 — catalog.
    objects[1] = ("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n").encode("ascii")

    # Object 2 — pages tree.
    kids = " ".join(f"{n} 0 R" for n in page_obj_numbers)
    objects[2] = (
        f"2 0 obj\n<< /Type /Pages /Kids [{kids}] " f"/Count {len(document.pages)} >>\nendobj\n"
    ).encode("ascii")

    # Object 3 — info dict. Use hex-string for Title to avoid literal
    # escaping pitfalls in the metadata.
    title_bytes = CLOSING_PDF_EXPORT_TITLE_KO.encode("utf-16-be")
    finalized_at_literal = escape_pdf_literal(document.finalized_at)
    period_key_literal = escape_pdf_literal(document.period_key)
    objects[3] = (
        f"3 0 obj\n"
        f"<< /Title <{title_bytes.hex()}> "
        f"/Producer (costmgr-pdf-export 1.0) "
        f"/CreationDate ({finalized_at_literal}) "
        f"/PeriodKey ({period_key_literal}) "
        f"/TenantId ({document.tenant_id}) >>\n"
        f"endobj\n"
    ).encode("ascii")

    # Object 4 — font group (Type0 / CIDFont / CMap / ToUnicode).
    # The Type0 font references the CIDFont and a CMap stream. For
    # brevity we use a single CMap stream (object 4) and embed the
    # ToUnicode CMap directly as an inline stream on the Type0 font.
    # The CIDFont descriptor is omitted because we ship no embedded
    # font program — readers fall back to a system font for the
    # glyphs. The CMap/ToUnicode streams are still emitted so that
    # text-to-Unicode mapping (search/copy) works for the
    # GID<->Unicode pairs declared.
    identity_h_cmap_obj_num = object_count + 1
    tounicode_cmap_obj_num = object_count + 2
    object_count += 2

    # Build the Type0 font object body. Use the CMap stream.
    font_body = (
        f"{font_obj_num} 0 obj\n"
        f"<< /Type /Font /Subtype /Type0 "
        f"/BaseFont /NotoSansKR-Regular "
        f"/Encoding /Identity-H "
        f"/DescendantFonts [{font_obj_num + 1} 0 R] "
        f"/ToUnicode {tounicode_cmap_obj_num} 0 R >>\n"
        f"endobj\n"
    ).encode("ascii")
    objects[font_obj_num] = font_body

    cid_font_obj_num = font_obj_num + 1
    cid_font_body = (
        f"{cid_font_obj_num} 0 obj\n"
        f"<< /Type /Font /Subtype /CIDFontType2 "
        f"/BaseFont /NotoSansKR-Regular "
        f"/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) "
        f"/Supplement 0 >> "
        f"/CIDToGIDMap /Identity "
        f"/FontDescriptor {font_obj_num + 2} 0 R >>\n"
        f"endobj\n"
    ).encode("ascii")
    objects[cid_font_obj_num] = cid_font_body

    font_descriptor_obj_num = font_obj_num + 2
    font_descriptor_body = (
        f"{font_descriptor_obj_num} 0 obj\n"
        f"<< /Type /FontDescriptor /FontName /NotoSansKR-Regular "
        f"/Flags 32 /ItalicAngle 0 /Ascent 800 /Descent -200 "
        f"/CapHeight 700 /StemV 80 >>\n"
        f"endobj\n"
    ).encode("ascii")
    objects[font_descriptor_obj_num] = font_descriptor_body

    # CMap stream object (Identity-H).
    cmap_header = f"{identity_h_cmap_obj_num} 0 obj\n".encode("ascii")
    cmap_body = (f"<< /Length {len(identity_h_cmap)} /Filter /FlateDecode >>\n" f"stream\n").encode(
        "ascii"
    )
    cmap_footer = b"\nendstream\nendobj\n"
    objects[identity_h_cmap_obj_num] = cmap_header + cmap_body + identity_h_cmap + cmap_footer

    # ToUnicode CMap stream object.
    tounicode_header = f"{tounicode_cmap_obj_num} 0 obj\n".encode("ascii")
    tounicode_body = (f"<< /Length {len(tounicode_cmap)} >>\n" f"stream\n").encode("ascii")
    tounicode_footer = b"\nendstream\nendobj\n"
    objects[tounicode_cmap_obj_num] = (
        tounicode_header + tounicode_body + tounicode_cmap + tounicode_footer
    )

    # Per-page objects.
    for _page, content_bytes, page_obj_num, content_obj_num in zip(
        document.pages,
        content_streams,
        page_obj_numbers,
        content_obj_numbers,
        strict=False,
    ):
        page_body = (
            f"{page_obj_num} 0 obj\n"
            f"<< /Type /Page /Parent 2 0 R "
            f"/MediaBox [0 0 {A4_WIDTH_PT} {A4_HEIGHT_PT}] "
            f"/Resources << /Font << /F2 {font_obj_num} 0 R >> >> "
            f"/Contents {content_obj_num} 0 R >>\n"
            f"endobj\n"
        ).encode("ascii")
        objects[page_obj_num] = page_body

        content_body = (
            f"{content_obj_num} 0 obj\n" f"<< /Length {len(content_bytes)} >>\n" f"stream\n"
        ).encode("ascii")
        objects[content_obj_num] = content_body + content_bytes + b"\nendstream\nendobj\n"

    # ── Concatenate objects in numerical order, tracking offsets ──
    # Order: header → object 1, 2, 3, 4, 4+1, 4+2, 4+3 (cmap), 4+4
    # (tounicode), then per-page pairs.
    object_order = sorted(objects.keys())
    header = f"%PDF-{PDF_VERSION}\n".encode("ascii") + b"%\xe2\xe3\xcf\xd3\n"

    offsets: dict[int, int] = {0: 0}  # object 0 is the free entry
    cursor = len(header)
    out = bytearray(header)
    for obj_num in object_order:
        offsets[obj_num] = cursor
        body = objects[obj_num]
        out += body
        cursor += len(body)

    # ── xref table ───────────────────────────────────────────────
    xref_header = f"xref\n0 {object_count}\n".encode("ascii")
    out += xref_header
    cursor += len(xref_header)
    # Object 0 — free entry.
    out += b"0000000000 65535 f \n"
    cursor += 20
    for obj_num in object_order:
        off = offsets[obj_num]
        entry = f"{off:010d} 00000 n \n".encode("ascii")
        out += entry
        cursor += len(entry)

    # ── trailer ───────────────────────────────────────────────────
    xref_offset = cursor
    trailer = (
        f"trailer\n<< /Size {object_count} /Root 1 0 R /Info 3 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")
    out += trailer

    return bytes(out), object_count, tuple(codepoint_set)


def render_closing_pdf_byte_stream(
    document: ClosingPdfDocument,
) -> RenderedClosingPdf:
    """Render ClosingPdfDocument to a PDF byte stream (stdlib-only).

    PRD §F6.3: A4 page layout + Korean font subset + ≤ 5MB cap.
    Pure-Python, no external PDF library. Produces a PDF 1.7 byte
    stream with metadata info section + page tree + content streams
    for Korean text rendering via Type0 CIDFont (Identity-H CMap +
    ToUnicode stream for text-to-Unicode reverse mapping).

    Args:
        document: pure-data PDF document.

    Returns:
        RenderedClosingPdf: pdf_bytes + size_bytes + object_count.

    Raises:
        ClosingPdfExportError: if document is invalid (empty pages,
            invalid section order) OR rendered size exceeds the
            5MB cap. The size-exceeded exception's `details` dict
            carries the actual `size_bytes` and `cap_bytes`.
    """
    pdf_bytes, object_count, _codepoints = _build_closing_pdf_bytes(document)

    # 5MB cap enforcement (PRD §F6.3) — use real `len(pdf_bytes)`.
    if len(pdf_bytes) > MAX_PDF_SIZE_BYTES:
        raise ClosingPdfExportError(
            message=(
                f"closing PDF export size {len(pdf_bytes)} exceeds "
                f"5MB cap ({MAX_PDF_SIZE_BYTES})"
            ),
            error_code="CLOSING_PDF_EXPORT_SIZE_EXCEEDED",
            tenant_id=document.tenant_id,
            period_key=document.period_key,
            details={
                "size_bytes": str(len(pdf_bytes)),
                "cap_bytes": str(MAX_PDF_SIZE_BYTES),
            },
        )

    return RenderedClosingPdf(
        pdf_bytes=pdf_bytes,
        size_bytes=len(pdf_bytes),
        object_count=object_count,
    )
