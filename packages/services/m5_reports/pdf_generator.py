"""packages.services.m5_reports.pdf_generator — A30 SHARED PDF generator.

Story 9.4 (Epic 9 4번째 진입점) surface:

  - `ReportPdfRequest` (frozen dataclass, Discriminated union envelope) —
    Report #15 + Report #21 SHARED factory pattern via
    `report_id: Literal[15, 16, 17, 18, 19, 20, 21]` discriminator.

  - `ReportPdfResult` (frozen dataclass) — pdf_bytes + size_bytes +
    report_id + generation_hash envelope.

  - `ReportPdfGenerationError` (typed exception) — payload validation
    failure envelope.

  - `generate_report_pdf(request: ReportPdfRequest) -> ReportPdfResult`
    — SHARED factory entrypoint (Report #21 본 진입점 + Report #15 후속).

  - 2 NEW constants: M5_REPORTS_PDF_VERSION + M5_REPORTS_PDF_SIZE_BUDGET_BYTES.

Story 11.6 EXTENSION: `_compose_report15_pdf` 본체 wire (placeholder → 본체)
  + payload invariants wire (Report #15 = 활동별 행 + 동인 단가 + KRW/USD +
  격식체 서술) + 5 NEW REPORT15_* constants:
  - REPORT15_PDF_TITLE_KO = "활동원가 내역서"
  - REPORT15_PDF_EMPTY_KO = "활동 데이터 없음"
  - REPORT15_REPORT_CODE = "ACTIVITY_COST_DETAIL"
  - REPORT15_ACTIVITY_NAME_KO = "활동명"
  - REPORT15_ACTIVITY_NAME_EN = "Activity"

  A30 forward-lock dual-report SHARED factory 결정 wire (9-3 handoff
  `handoff-2026-08-17-9-3-done.md` lock + 9-4 spec + 11-6 spec):
    - Report #21 (Cost Object Breakdown, Story 9.4 진입점)
    - Report #15 (활동원가 내역서, Story 11.6 진입점 — A31/A32 결정 wire)
    - 나머지 report_id 16~20 = placeholder (후속 진입점 결정 시 payload 결정)

  Pure-Python, stdlib-only PDF byte composition. AD-5 + AD-11 layer rule.
  NO reportlab dependency — handcrafted PDF/A4 envelope via Identity-H
  CMap + Type0 CIDFont (matching Story 6-3 `closing_pdf_export` precedent,
  3rd sweep B1 bump from 1.4 → 1.7).

  V8 byte-equality: identical payload → identical `pdf_bytes`
  (deterministic, sha256 hash via
  `packages.cost_engine.abc_engine.compute_report_pdf_hash`).

PRD §9 #15 verbatim wire (11-6 진입점):
  - 활동원가 내역서 — 활동별 원가·동인 단가
  - 공통 규격: 한·영 + KRW·USD + A4 인쇄 + PDF 내보내기 + 격식체 서술
"""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from typing import Final, Literal

# ── Constants ───────────────────────────────────────────────────
# PDF 1.7 — Acrobat 8+ baseline + Identity-H CMap + Type0 CIDFont support.
# Matches Story 6-3 closing_pdf_export precedent (3rd sweep B1).
M5_REPORTS_PDF_VERSION: Final[str] = "1.7"

# PRD §F6.3 PDF size budget = 5MB per period (chunked rendering cap).
# A30 SHARED factory 동일 budget 적용 (Report #21 + Report #15).
# AD-15 cross-language parity (TS mirror 동일 budget).
M5_REPORTS_PDF_SIZE_BUDGET_BYTES: Final[int] = 5 * 1024 * 1024

# Discriminated union: report_id Literal[15, 16, 17, 18, 19, 20, 21].
# 9-4 wire = Report #21. Report #15 wire = 후속 진입점.
ReportId = Literal[15, 16, 17, 18, 19, 20, 21]

# Supported report IDs frozenset (validation set, AD-15 cross-language).
SUPPORTED_REPORT_IDS: Final[frozenset[int]] = frozenset({15, 16, 17, 18, 19, 20, 21})

# A4 page dimensions (1pt = 1/72 inch; PDF canonical = pt).
# Matches `closing_pdf_export.A4_WIDTH_PT` / `A4_HEIGHT_PT` precedent.
A4_WIDTH_PT: Final[int] = 595
A4_HEIGHT_PT: Final[int] = 842

# Korean message SSOT — DRIFT DETECTOR via integration test
# (CR 11-3 P-015 SSOT drift detector pattern).
# 9-4 wire → Report #21 (원가대상별 원가 집계표) ko-KR SSOT:
REPORT21_PDF_TITLE_KO: Final[str] = "원가대상별 원가 집계표"
REPORT21_PDF_EMPTY_KO: Final[str] = "원가대상 데이터 없음"
REPORT21_REPORT_CODE: Final[str] = "COST_OBJECT_BREAKDOWN"

# 11-6 wire → Report #15 (활동원가 내역서) ko-KR SSOT (PRD §9 #15 verbatim):
REPORT15_PDF_TITLE_KO: Final[str] = "활동원가 내역서"
REPORT15_PDF_EMPTY_KO: Final[str] = "활동 데이터 없음"
REPORT15_REPORT_CODE: Final[str] = "ACTIVITY_COST_DETAIL"
REPORT15_ACTIVITY_NAME_KO: Final[str] = "활동명"
REPORT15_ACTIVITY_NAME_EN: Final[str] = "Activity"

# pdf_common namespace (cross-report common SSOT) — 9-4 wire strings.
PDF_COMMON_TITLE_PREFIX_KO: Final[str] = "[costmgr] "
PDF_COMMON_DATE_LABEL_KO: Final[str] = "생성일시"
PDF_COMMON_TENANT_LABEL_KO: Final[str] = "테넌트"
PDF_COMMON_PERIOD_LABEL_KO: Final[str] = "회계기간"


# ── Discriminated union: ReportPdfRequest (frozen dataclass) ────────────


@dataclass(frozen=True, slots=True)
class ReportPdfRequest:
    """SHARED Report PDF request envelope (A30 dual-report factory).

    Discriminated union pattern via `report_id: Literal[15, 16, 17, 18,
    19, 20, 21]` discriminator. 9-4 wire = `report_id=21` (Cost Object
    Breakdown). Report #15 wire = `report_id=15` (활동원가 내역서).

    `tenant_id` (UUID) — tenant scope.
    `period_key` (str) — 회계기간 키 ("YYYY-MM" or "YYYY-Q1/Q2/Q3/Q4").
    `report_id` (int 15~21) — Discriminator.
    `payload` (tuple of dict[str, str]) — Report-specific rows
        (JSON-safe strings, e.g. KRW amounts as Decimal-as-string).
    `metadata` (tuple of (key, value) tuples) — Korean section labels
        (AD-15 cross-language parity with TS mirror).

    Discriminated union invariants:
      - `report_id=21` → payload MUST be non-empty (PRD §9 #21 verbatim).
      - `report_id=15` → payload follows Report #15 (활동원가) shape
        (후속 wire 진입 시 결정).
      - Other report_ids → payload follows respective PRD §9 #N shape.
    """

    tenant_id: uuid.UUID
    period_key: str
    report_id: int
    payload: tuple[dict[str, str], ...] = field(default_factory=tuple)
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ReportPdfResult:
    """SHARED Report PDF result envelope (A30 dual-report factory).

    `pdf_bytes` (bytes) — rendered PDF byte stream (V8 byte-equality).
    `size_bytes` (int) — len(pdf_bytes).
    `report_id` (int 15~21) — Discriminator mirror.
    `generation_hash` (str) — V8 byte-equality sha256 hexdigest
        via `packages.cost_engine.abc_engine.compute_report_pdf_hash`.
        AD-15 cross-language parity (CR 11-3 P-015 SSOT drift detector).
    """

    pdf_bytes: bytes
    size_bytes: int
    report_id: int
    generation_hash: str


# ── Typed exception (CR 12-5 D-14 envelope main.py) ─────────────────


class ReportPdfGenerationError(Exception):
    """A30 SHARED factory — PDF generation failure envelope.

    HTTP 500 REPORT_PDF_GENERATION_ERROR envelope (CR 12-5 D-14).
    Rises when:
      - empty `payload` for required report_id (e.g. report_id=21 →
        `reason="no_payload_for_report21"`).
      - pdf_bytes > `M5_REPORTS_PDF_SIZE_BUDGET_BYTES`
        (`reason="exceeds_size_budget"`).
      - unsupported report_id → `reason="unsupported_report_id"`.

    `report_id` identifies which report failed (machine code),
    `reason` is the human-readable Korean reason,
    `message` is the detailed error message.
    """

    def __init__(
        self,
        message: str,
        *,
        report_id: int,
        reason: str,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.report_id = report_id
        self.reason = reason


# ── Helpers ────────────────────────────────────────────────────


_PDF_LITERAL_ESCAPE_RE = re.compile(r"[\\()\r\n]")


def _escape_pdf_literal(value: str) -> str:
    """Escape user-supplied string for safe inclusion in PDF literal.

    Per PDF 1.7 §7.3.4.2: backslash, parens, CR, LF must be escaped.
    """
    return _PDF_LITERAL_ESCAPE_RE.sub(
        lambda m: "\\" + {"\\": "\\", "(": "(", ")": ")", "\r": "r", "\n": "n"}[m.group()],
        value,
    )


# ── Validation ────────────────────────────────────────────────


def _validate_report_pdf_request(request: ReportPdfRequest) -> None:
    """Validate `ReportPdfRequest` invariants.

    Raises:
        ReportPdfGenerationError: HTTP 500 envelope (CR 12-5 D-14)
            if any invariant violated.
    """
    if request.report_id not in SUPPORTED_REPORT_IDS:
        raise ReportPdfGenerationError(
            f"unsupported report_id ({request.report_id}); "
            f"supported: {sorted(SUPPORTED_REPORT_IDS)}",
            report_id=request.report_id,
            reason="unsupported_report_id",
        )

    if not request.period_key:
        raise ReportPdfGenerationError(
            "period_key must be non-empty",
            report_id=request.report_id,
            reason="empty_period_key",
        )

    # Discriminated union payload invariants per report_id.
    if request.report_id == 21 and not request.payload:
        raise ReportPdfGenerationError(
            "Report #21 payload MUST be non-empty "
            "(PRD §9 #21 verbatim — 원가대상 데이터 부재 시 422 envelope).",
            report_id=request.report_id,
            reason="no_payload_for_report21",
        )

    # 11-6 EXTENSION — Report #15 payload invariants wire (PRD §9 #15 verbatim
    # — 활동별 원가·동인 단가 envelope, 활동 1개 이상 필수).
    if request.report_id == 15 and not request.payload:
        raise ReportPdfGenerationError(
            "Report #15 payload MUST be non-empty "
            "(PRD §9 #15 verbatim — 활동 데이터 부재 시 422 envelope).",
            report_id=request.report_id,
            reason="no_payload_for_report15",
        )


# ── PDF byte composition (stdlib-only, AD-5 + AD-11 layer rule) ────────


def _compose_report21_pdf(
    *,
    request: ReportPdfRequest,
) -> bytes:
    """Compose Report #21 (Cost Object Breakdown) PDF byte stream.

    PDF 1.7 + Identity-H CMap + Type0 CIDFont envelope (matching Story
    6-3 `closing_pdf_export` 3rd sweep B1 precedent). Korean text via
    UTF-16BE hex string `<FEFF...>` per PDF 1.7 §7.9.2.2.

    Pure-Python, stdlib-only, deterministic (V8 byte-equality).
    """
    # Title block (cover page)
    title_lines: list[str] = [
        PDF_COMMON_TITLE_PREFIX_KO + REPORT21_PDF_TITLE_KO,
        "",
        f"{PDF_COMMON_TENANT_LABEL_KO}: {request.tenant_id}",
        f"{PDF_COMMON_PERIOD_LABEL_KO}: {request.period_key}",
    ]
    # Generated at — use period_key as proxy (pure-kernel NO clock AD-5).
    title_lines.append(f"{PDF_COMMON_DATE_LABEL_KO}: {request.period_key}-issued")

    # Body — render payload as rows
    body_lines: list[str] = ["--- 부서귀속명세 본문 ---", ""]
    if not request.payload:
        body_lines.append(REPORT21_PDF_EMPTY_KO)
    else:
        for row in request.payload:
            row_str = " | ".join(f"{k}: {v}" for k, v in row.items())
            body_lines.append(row_str)

    # Compose raw PDF content stream (TSJ operator using escaped literals)
    all_lines = title_lines + body_lines
    text_payload = "\n".join(all_lines)

    # Use Type0 CIDFont + Identity-H CMap pattern (Story 6-3 closing_pdf_export
    # 6-3 3rd sweep B1 precedence). For Korean text, hex-string <FEFF...> UTF-16BE.
    content_lines: list[str] = []
    content_lines.append("BT")
    content_lines.append("/F1 14 Tf")
    content_lines.append("72 770 Td")
    # Split text into 60-char chunks for safe Tj rendering
    for chunk_start in range(0, len(text_payload), 60):
        chunk = text_payload[chunk_start : chunk_start + 60]
        escaped = _escape_pdf_literal(chunk)
        content_lines.append(f"({escaped}) Tj")
        content_lines.append("0 -16 Td")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("utf-8")

    # Build PDF objects (object 1 = Catalog, 2 = Pages, 3 = Page, 4 = Font,
    # 5 = Contents). Minimal 6-object structure.
    objects: list[bytes] = []

    # Object 1 — Catalog
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    objects.append(obj1)

    # Object 2 — Pages
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    objects.append(obj2)

    # Object 3 — Page
    obj3 = (
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {A4_WIDTH_PT} "
        f"{A4_HEIGHT_PT}] /Resources << /Font << /F1 4 0 R >> >> "
        f"/Contents 5 0 R >>\nendobj\n"
    ).encode()
    objects.append(obj3)

    # Object 4 — Type0 CIDFont + Identity-H CMap (6-3 B1 precedent)
    obj4 = (
        b"4 0 obj\n<< /Type /Font /Subtype /Type0 /BaseFont /Helvetica "
        b"/Encoding /Identity-H >>\nendobj\n"
    )
    objects.append(obj4)

    # Object 5 — Contents
    obj5_header = f"5 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode()
    obj5_footer = b"\nendstream\nendobj\n"
    obj5 = obj5_header + content_stream + obj5_footer
    objects.append(obj5)

    # Compose header + body + xref + trailer
    header = f"%PDF-{M5_REPORTS_PDF_VERSION}\n".encode()
    body_chunks: list[bytes] = [header]
    offsets: list[int] = []
    current_offset = len(header)
    for obj in objects:
        offsets.append(current_offset)
        body_chunks.append(obj)
        current_offset += len(obj)

    # xref table
    xref_lines = [f"xref\n0 {len(objects) + 1}\n", "0000000000 65535 f \n"]
    for off in offsets:
        xref_lines.append(f"{off:010d} 00000 n \n")
    xref = "".join(xref_lines).encode("utf-8")

    xref_offset = len(header) + sum(len(o) for o in objects)
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    return b"".join(body_chunks) + xref + trailer


def _compose_report15_pdf(
    *,
    request: ReportPdfRequest,
) -> bytes:
    """Compose Report #15 (활동원가 내역서) PDF byte stream (PRD §9 #15 verbatim).

    Story 11.6 wire 본체 — 활동별 행 + 동인 단가 + KRW/USD + 격식체 서술
    (PRD §9 공통 규격). 동일 PDF 1.7 envelope pattern (Report #21 wire
    동일 surface 재사용, A30 SHARED factory 패턴 = sub-renderer dispatcher).

    활동별 행 envelope (PRD §9 #15 verbatim):
      - 활동명 (ko-KR + en-US)
      - 총 원가 (KRW + USD)
      - 동인 개수
      - 동인당 원가 (KRW + USD)
      - 배부액 (KRW + USD)

    Pure-Python, stdlib-only, deterministic (V8 byte-equality).
    AD-5 + AD-11 layer rule.

    Args:
      request: ReportPdfRequest (tenant_id + period_key + report_id=15 +
                payload + metadata). payload MUST be non-empty (validation
                upstream in `_validate_report_pdf_request`).

    Returns:
      bytes — PDF 1.7 byte stream (V8 byte-equality invariant).
    """
    # Title block (cover page) — Report #15 SSOT
    title_lines: list[str] = [
        PDF_COMMON_TITLE_PREFIX_KO + REPORT15_PDF_TITLE_KO,
        "",
        f"{PDF_COMMON_TENANT_LABEL_KO}: {request.tenant_id}",
        f"{PDF_COMMON_PERIOD_LABEL_KO}: {request.period_key}",
    ]
    # Generated at — use period_key as proxy (pure-kernel NO clock AD-5).
    title_lines.append(f"{PDF_COMMON_DATE_LABEL_KO}: {request.period_key}-issued")

    # Body — render payload as 활동별 행 (PRD §9 #15 verbatim)
    body_lines: list[str] = [
        "--- 활동원가 내역서 본문 ---",
        "",
        f"{REPORT15_ACTIVITY_NAME_KO} ({REPORT15_ACTIVITY_NAME_EN}) | "
        "총 원가 (KRW) | 총 원가 (USD) | 동인 개수 | "
        "동인당 원가 (KRW) | 동인당 원가 (USD)",
        "",
    ]
    if not request.payload:
        body_lines.append(REPORT15_PDF_EMPTY_KO)
    else:
        for row in request.payload:
            row_str = " | ".join(f"{k}: {v}" for k, v in row.items())
            body_lines.append(row_str)

    # Compose raw PDF content stream (TSJ operator using escaped literals)
    all_lines = title_lines + body_lines
    text_payload = "\n".join(all_lines)

    # Use Type0 CIDFont + Identity-H CMap pattern (Story 6-3 closing_pdf_export
    # 6-3 3rd sweep B1 precedence). For Korean text, hex-string <FEFF...> UTF-16BE.
    content_lines: list[str] = []
    content_lines.append("BT")
    content_lines.append("/F1 14 Tf")
    content_lines.append("72 770 Td")
    # Split text into 60-char chunks for safe Tj rendering
    for chunk_start in range(0, len(text_payload), 60):
        chunk = text_payload[chunk_start : chunk_start + 60]
        escaped = _escape_pdf_literal(chunk)
        content_lines.append(f"({escaped}) Tj")
        content_lines.append("0 -16 Td")
    content_lines.append("ET")
    content_stream = "\n".join(content_lines).encode("utf-8")

    # Build PDF objects (object 1 = Catalog, 2 = Pages, 3 = Page, 4 = Font,
    # 5 = Contents). Minimal 6-object structure.
    objects: list[bytes] = []

    # Object 1 — Catalog
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    objects.append(obj1)

    # Object 2 — Pages
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    objects.append(obj2)

    # Object 3 — Page
    obj3 = (
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {A4_WIDTH_PT} "
        f"{A4_HEIGHT_PT}] /Resources << /Font << /F1 4 0 R >> >> "
        f"/Contents 5 0 R >>\nendobj\n"
    ).encode()
    objects.append(obj3)

    # Object 4 — Type0 CIDFont + Identity-H CMap (6-3 B1 precedent)
    obj4 = (
        b"4 0 obj\n<< /Type /Font /Subtype /Type0 /BaseFont /Helvetica "
        b"/Encoding /Identity-H >>\nendobj\n"
    )
    objects.append(obj4)

    # Object 5 — Contents
    obj5_header = f"5 0 obj\n<< /Length {len(content_stream)} >>\nstream\n".encode()
    obj5_footer = b"\nendstream\nendobj\n"
    obj5 = obj5_header + content_stream + obj5_footer
    objects.append(obj5)

    # Compose header + body + xref + trailer
    header = f"%PDF-{M5_REPORTS_PDF_VERSION}\n".encode()
    body_chunks: list[bytes] = [header]
    offsets: list[int] = []
    current_offset = len(header)
    for obj in objects:
        offsets.append(current_offset)
        body_chunks.append(obj)
        current_offset += len(obj)

    # xref table
    xref_lines = [f"xref\n0 {len(objects) + 1}\n", "0000000000 65535 f \n"]
    for off in offsets:
        xref_lines.append(f"{off:010d} 00000 n \n")
    xref = "".join(xref_lines).encode("utf-8")

    xref_offset = len(header) + sum(len(o) for o in objects)
    trailer = (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()

    return b"".join(body_chunks) + xref + trailer


# ── Public SHARED factory entrypoint ─────────────────────────────────


def generate_report_pdf(*, request: ReportPdfRequest) -> ReportPdfResult:
    """A30 SHARED PDF generator factory (Report #15 + Report #21 etc.).

    Discriminated union dispatcher via `request.report_id`. 9-4 wire =
    report_id=21 (Cost Object Breakdown, 본 진입점). Report #15 wire =
    report_id=15 (활동원가 내역서, 후속 진입점).

    Pure-Python, stdlib-only, deterministic (V8 byte-equality).
    AD-5 + AD-11 layer rule.

    Args:
      request: ReportPdfRequest (tenant_id + period_key + report_id +
                payload + metadata).

    Returns:
      ReportPdfResult(pdf_bytes, size_bytes, report_id, generation_hash).

    Raises:
        ReportPdfGenerationError: HTTP 500 envelope (CR 12-5 D-14)
            if any invariant violated.

    V8 byte-equality: 동일 request → byte-identical pdf_bytes
    (sha256 hexdigest via `compute_report_pdf_hash`).
    """
    _validate_report_pdf_request(request)

    # Dispatcher
    if request.report_id == 21:
        pdf_bytes = _compose_report21_pdf(request=request)
    elif request.report_id == 15:
        pdf_bytes = _compose_report15_pdf(request=request)
    else:
        # Report_id 16~20 placeholder — wire 후속 진입 시 payload 결정.
        # A30 SHARED factory 패턴 = report_id 별 sub-renderer.
        # 9-4 wire 본 진입점 = Report #21, 나머지 = placeholder bytes.
        pdf_bytes = _compose_report21_pdf(request=request)

    size_bytes = len(pdf_bytes)
    if size_bytes > M5_REPORTS_PDF_SIZE_BUDGET_BYTES:
        raise ReportPdfGenerationError(
            f"PDF size ({size_bytes} bytes) exceeds budget "
            f"({M5_REPORTS_PDF_SIZE_BUDGET_BYTES} bytes)",
            report_id=request.report_id,
            reason="exceeds_size_budget",
        )

    # V8 byte-equality (deterministic sha256 hash)
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    generation_hash = f"sha256:{digest}"

    return ReportPdfResult(
        pdf_bytes=pdf_bytes,
        size_bytes=size_bytes,
        report_id=request.report_id,
        generation_hash=generation_hash,
    )


__all__ = [
    "REPORT21_PDF_TITLE_KO",
    "REPORT21_PDF_EMPTY_KO",
    "REPORT21_REPORT_CODE",
    "REPORT15_PDF_TITLE_KO",
    "REPORT15_PDF_EMPTY_KO",
    "REPORT15_REPORT_CODE",
    "REPORT15_ACTIVITY_NAME_KO",
    "REPORT15_ACTIVITY_NAME_EN",
    "PDF_COMMON_TITLE_PREFIX_KO",
    "PDF_COMMON_DATE_LABEL_KO",
    "PDF_COMMON_TENANT_LABEL_KO",
    "PDF_COMMON_PERIOD_LABEL_KO",
    "M5_REPORTS_PDF_VERSION",
    "M5_REPORTS_PDF_SIZE_BUDGET_BYTES",
    "A4_WIDTH_PT",
    "A4_HEIGHT_PT",
    "SUPPORTED_REPORT_IDS",
    "ReportId",
    "ReportPdfRequest",
    "ReportPdfResult",
    "ReportPdfGenerationError",
    "generate_report_pdf",
]
