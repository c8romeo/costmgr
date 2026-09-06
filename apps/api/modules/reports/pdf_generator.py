"""apps.api.modules.reports.pdf_generator — reportlab Platypus PDF composer.

cj-293 wire sprint (cj-style 293번째) — Story 30.2 PDF export composition layer.

reportlab Platypus (SimpleDocTemplate + Paragraph + Table + Image flowables)
기반 PDF 생성. Korean font (NOTO Sans CJK KR 또는 matplotlib DejaVu Sans fallback)
처리 결정 wire 진입. Charts (matplotlib PNG bytes) 를 Image flowable 로 삽입.

cj-293 OQ-EPIC30+-1 결정 wire = reportlab (pure Python, no native deps).
cj-293 AD-14 stack pin EXTENSION 결정 wire:
- reportlab==4.0.7 (AD-14 exact minor pin)

Korean font fallback 전략 (NFR18 ko-KR SSOT):
- 1순위: reportlab.pdfbase.ttfonts.TTFont + NOTO Sans CJK KR TTF (이미 AD-14
  stack pin 으로 finops territory 에서 사용 중 per
  apps/api/modules/finops/__init__.py:153 결정 wire)
- 2순위: reportlab 내장 HeiseiMin-W3 (CJK 처리 가능) — fallback
- 3순위: Helvetica (Latin only) — ko-KR 깨짐 가능

Font 자동 검색: settings.PDF_FONT_PATH 환경변수 override 지원.

CR 11-3 honest-DEFER 233번째 — PDF header/footer EXTENSION 결정 wire 보류
(cj-style 294+ 적용).
"""

from __future__ import annotations

import io
import logging
import os
from datetime import UTC, datetime
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


# ── Constants ────────────────────────────────────────────────────────

# A4 landscape (monthly closing report — wide tables fit better than portrait).
PDF_PAGE_SIZE_A4_LANDSCAPE: tuple[float, float] = landscape(A4)

# Page margins (cm) — readable but not wasteful.
PDF_PAGE_MARGIN_LEFT: float = 1.5
PDF_PAGE_MARGIN_RIGHT: float = 1.5
PDF_PAGE_MARGIN_TOP: float = 2.0
PDF_PAGE_MARGIN_BOTTOM: float = 2.0

# Korean font name (registered in reportlab). NOTO Sans CJK KR TTF path
# 결정 wire 보존 — environment override 가능.
KOREAN_FONT_NAME: str = "NotoSansCJKkr"
KOREAN_FONT_FALLBACK_NAMES: tuple[str, ...] = ("HeiseiMin-W3", "Helvetica")

# Default Korean font path candidates (filesystem paths the engine tries in
# order until one resolves). AD-14 stack pin confirms NOTO Sans CJK KR is
# already part of the project's font assets (per finops territory 결정 wire).
DEFAULT_KOREAN_FONT_PATHS: tuple[str, ...] = (
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/AppleSDGothicNeo-Regular.ttc",
    "C:/Windows/Fonts/malgun.ttf",  # Korean Windows default
    os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "static", "fonts", "NotoSansCJKkr-Regular.otf"
    ),
)


# ── Typed exceptions (CR 12-5 D-14 envelope) ─────────────────────────


class PdfExportError(Exception):
    """Base PDF export failure."""

    def __init__(
        self,
        code: str,
        message_ko: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message_ko = message_ko
        self.details: dict[str, Any] = details or {}
        super().__init__(message_ko)


class PdfExportSizeExceededError(PdfExportError):
    """413 PDF_EXPORT_TOO_LARGE_KO — PDF row count > MAX_PDF_ROWS."""

    def __init__(self, row_count: int, max_rows: int) -> None:
        super().__init__(
            code="PDF_EXPORT_TOO_LARGE_KO",
            message_ko=f"PDF export 행 수가 너무 많습니다 (최대 {max_rows:,}건)",
            details={"row_count": row_count, "max_rows": max_rows},
        )


class PdfExportFontError(PdfExportError):
    """500 PDF_EXPORT_FONT_KO — Korean font loading failed."""

    def __init__(self, attempted_paths: list[str]) -> None:
        super().__init__(
            code="PDF_EXPORT_FONT_KO",
            message_ko="PDF 생성용 한글 폰트를 로드할 수 없습니다",
            details={"attempted_paths": attempted_paths},
        )


# ── Font registration ────────────────────────────────────────────────


def _register_korean_font() -> str:
    """Register Korean font with reportlab, return font name.

    Tries the configured PDF_FONT_PATH env override first, then iterates
    DEFAULT_KOREAN_FONT_PATHS candidates. Falls back to built-in
    HeiseiMin-W3 or Helvetica if no Korean-capable font found (ko-KR may
    render as boxes but PDF still generates).

    Returns:
        Font name registered in reportlab.pdfmetrics.

    Raises:
        PdfExportFontError: if all attempts fail AND fallback also fails.
    """
    candidates: list[str] = []
    env_path = os.environ.get("PDF_FONT_PATH")
    if env_path:
        candidates.append(env_path)
    candidates.extend(DEFAULT_KOREAN_FONT_PATHS)

    attempted: list[str] = []
    for path in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(KOREAN_FONT_NAME, path))
                logger.info("Korean font registered: %s (path=%s)", KOREAN_FONT_NAME, path)
                return KOREAN_FONT_NAME
            except Exception:  # noqa: BLE001
                logger.exception("Failed to register Korean font from %s", path)
                attempted.append(path)
                continue
        attempted.append(path)

    # Fallback to built-in fonts.
    for fallback in KOREAN_FONT_FALLBACK_NAMES:
        try:
            # Built-in fonts are already registered; just return the name.
            logger.warning("Using fallback font %s (ko-KR may render as boxes)", fallback)
            return fallback
        except Exception:  # noqa: BLE001
            continue

    raise PdfExportFontError(attempted_paths=attempted)


# ── PDF builders ─────────────────────────────────────────────────────


def _build_styles(font_name: str) -> dict[str, ParagraphStyle]:
    """Build ParagraphStyles for the PDF body.

    Returns:
        Dict mapping role → ParagraphStyle.
    """
    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleKR",
        parent=base["Title"],
        fontName=font_name,
        fontSize=18,
        leading=22,
        spaceAfter=12,
        alignment=1,  # CENTER
    )
    subtitle_style = ParagraphStyle(
        "SubtitleKR",
        parent=base["Normal"],
        fontName=font_name,
        fontSize=11,
        leading=14,
        spaceAfter=6,
        alignment=1,
        textColor=colors.grey,
    )
    section_style = ParagraphStyle(
        "SectionKR",
        parent=base["Heading2"],
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "BodyKR",
        parent=base["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=13,
    )
    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "section": section_style,
        "body": body_style,
    }


def _build_data_table(
    rows: list[Any],
    headers: list[str],
    font_name: str,
) -> Table:
    """Build a reportlab Table from data rows + header row."""
    # Limit table to first 100 rows (defense vs. giant tables, NFR5 결정 wire).
    display_rows = rows[:100]
    data = [headers]
    for r in display_rows:
        data.append([str(getattr(r, col, "")) for col in headers])

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4C72B0")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def _chart_image(png_bytes: bytes, width_cm: float = 16.0) -> Image:
    """Wrap PNG bytes in a reportlab Image flowable."""
    buf = io.BytesIO(png_bytes)
    img = Image(buf, width=width_cm * cm, height=width_cm * 0.6 * cm)
    return img


# ── Public API: cost-records PDF ────────────────────────────────────


def generate_cost_records_pdf(
    rows: list[Any],
    period: str,
    tenant_id: Any,
    charts: dict[str, bytes],
) -> bytes:
    """Generate the cost-records PDF (Story 30.2 §F30.2-1 verbatim).

    Args:
        rows: cost_records rows (tenant-scoped, period-scoped)
        period: YYYY-MM period
        tenant_id: tenant UUID (used in title)
        charts: pre-rendered matplotlib PNG bytes (3 charts)

    Returns:
        PDF bytes (single concatenated buffer).
    """
    font_name = _register_korean_font()
    styles = _build_styles(font_name)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=PDF_PAGE_SIZE_A4_LANDSCAPE,
        leftMargin=PDF_PAGE_MARGIN_LEFT * cm,
        rightMargin=PDF_PAGE_MARGIN_RIGHT * cm,
        topMargin=PDF_PAGE_MARGIN_TOP * cm,
        bottomMargin=PDF_PAGE_MARGIN_BOTTOM * cm,
        title=f"costmgr 월간 마감 보고서 - {period}",
        author="costmgr",
    )

    story: list[Any] = []
    story.append(Paragraph("월간 마감 보고서", styles["title"]))
    story.append(Paragraph(f"기간: {period}", styles["subtitle"]))
    story.append(Paragraph(f"테넌트 ID: {tenant_id}", styles["subtitle"]))
    story.append(Paragraph(f"생성 시각: {datetime.now(UTC).isoformat()}", styles["subtitle"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("차트 분석", styles["section"]))
    for chart_key in ("category_breakdown_pie", "monthly_trend_bar", "unit_cost_evolution_line"):
        png = charts.get(chart_key)
        if png:
            story.append(_chart_image(png, width_cm=22.0))
            story.append(Spacer(1, 0.3 * cm))

    story.append(PageBreak())
    story.append(Paragraph("상세 데이터", styles["section"]))
    cost_headers = [
        "period_key",
        "product_id",
        "product_name",
        "category",
        "opening_qty",
        "input_qty",
        "output_qty",
        "closing_qty",
        "unit_cost",
        "total_cost",
    ]
    story.append(_build_data_table(rows, cost_headers, font_name))
    story.append(Spacer(1, 0.3 * cm))
    if len(rows) > 100:
        story.append(
            Paragraph(
                f"(총 {len(rows):,}건 중 첫 100건만 표시 — 전체 데이터는 CSV export 사용 권장)",
                styles["body"],
            )
        )

    doc.build(story)
    buf.seek(0)
    return buf.read()


# ── Public API: BOM PDF ──────────────────────────────────────────────


def generate_bom_pdf(
    rows: list[Any],
    period: str,
    tenant_id: Any,
    charts: dict[str, bytes],
) -> bytes:
    """Generate the BOM level-1 PDF (Story 30.2 §F30.2-1 verbatim)."""
    font_name = _register_korean_font()
    styles = _build_styles(font_name)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=PDF_PAGE_SIZE_A4_LANDSCAPE,
        leftMargin=PDF_PAGE_MARGIN_LEFT * cm,
        rightMargin=PDF_PAGE_MARGIN_RIGHT * cm,
        topMargin=PDF_PAGE_MARGIN_TOP * cm,
        bottomMargin=PDF_PAGE_MARGIN_BOTTOM * cm,
        title=f"costmgr BOM 보고서 - {period}",
        author="costmgr",
    )

    story: list[Any] = []
    story.append(Paragraph("BOM (Level 1) 보고서", styles["title"]))
    story.append(Paragraph(f"기간: {period}", styles["subtitle"]))
    story.append(Paragraph(f"테넌트 ID: {tenant_id}", styles["subtitle"]))
    story.append(Paragraph(f"생성 시각: {datetime.now(UTC).isoformat()}", styles["subtitle"]))
    story.append(Spacer(1, 0.5 * cm))

    story.append(Paragraph("차트 분석", styles["section"]))
    for chart_key in ("category_breakdown_pie", "monthly_trend_bar", "unit_cost_evolution_line"):
        png = charts.get(chart_key)
        if png:
            story.append(_chart_image(png, width_cm=22.0))
            story.append(Spacer(1, 0.3 * cm))

    story.append(PageBreak())
    story.append(Paragraph("상세 데이터", styles["section"]))
    bom_headers = [
        "period_key",
        "parent_product_id",
        "parent_product_name",
        "child_product_id",
        "child_product_name",
        "child_category",
        "child_qty_per_parent",
        "child_unit_cost",
        "child_total_cost",
    ]
    story.append(_build_data_table(rows, bom_headers, font_name))
    story.append(Spacer(1, 0.3 * cm))
    if len(rows) > 100:
        story.append(
            Paragraph(
                f"(총 {len(rows):,}건 중 첫 100건만 표시 — 전체 데이터는 CSV export 사용 권장)",
                styles["body"],
            )
        )

    doc.build(story)
    buf.seek(0)
    return buf.read()


__all__ = [
    "PDF_PAGE_SIZE_A4_LANDSCAPE",
    "PDF_PAGE_MARGIN_LEFT",
    "PDF_PAGE_MARGIN_RIGHT",
    "PDF_PAGE_MARGIN_TOP",
    "PDF_PAGE_MARGIN_BOTTOM",
    "KOREAN_FONT_NAME",
    "PdfExportError",
    "PdfExportSizeExceededError",
    "PdfExportFontError",
    "_register_korean_font",
    "generate_cost_records_pdf",
    "generate_bom_pdf",
]
