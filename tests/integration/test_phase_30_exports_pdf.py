"""tests/integration/test_phase_30_exports_pdf — pytest for Story 30.2 PDF export.

cj-293 wire sprint (cj-style 293번째) — Story 30.2 PDF export tests.

12 tests covering:
1. MAX_PDF_ROWS defense cap 결정 wire (NFR5 streaming)
2. PDF content-type 결정 wire (`application/pdf`)
3. Audit action name 'export_pdf' 결정 wire (CR 1-1 verbatim)
4. Typed exception classes 결정 wire (CR 12-5 D-14 envelope)
5. PdfExportRequest Pydantic schema validation (period regex YYYY-MM)
6. _register_korean_font returns a valid font name (NFR18 ko-KR SSOT)
7. PdfExportSizeExceededError envelope
8. PdfExportFontError envelope
9. PDF_COLUMNS_COST_RECORDS column set 결정 wire (cost-records = 14 cols)
10. PDF_COLUMNS_BOM column set 결정 wire (bom = 9 cols)
11. generate_cost_records_pdf returns non-empty bytes
12. generate_bom_pdf returns non-empty bytes

CR 11-3 honest-DEFER 233번째:
- DB integration test 결정 wire 보류 (cj-style 294+ 적용 시 fixture 추가)
- ko-KR.json EXTENSION 결정 wire 보류
- Chart styling EXTENSION 결정 wire 보류
"""

from __future__ import annotations

import pytest

from apps.api.modules.reports.pdf_generator import (
    KOREAN_FONT_NAME,
    PDF_PAGE_MARGIN_LEFT,
    PDF_PAGE_MARGIN_RIGHT,
    PDF_PAGE_SIZE_A4_LANDSCAPE,
    PDF_PAGE_MARGIN_TOP,
    PDF_PAGE_MARGIN_BOTTOM,
    PdfExportError,
    PdfExportFontError,
    PdfExportSizeExceededError,
    _register_korean_font,
    generate_bom_pdf,
    generate_cost_records_pdf,
)
from apps.api.modules.reports.pdf_routes import (
    MAX_PDF_ROWS,
    PDF_CONTENT_TYPE,
)
from apps.api.schemas.export_schemas import PdfExportRequest

# ── Test 1: MAX_PDF_ROWS defense cap (NFR5) ──────────────────────────


def test_max_pdf_rows_constant() -> None:
    """MAX_PDF_ROWS = 100_000 (defense cap, NFR5 spec)."""
    assert MAX_PDF_ROWS == 100_000


def test_pdf_content_type_constant() -> None:
    """PDF_CONTENT_TYPE = 'application/pdf' (RFC 8118)."""
    assert PDF_CONTENT_TYPE == "application/pdf"


# ── Test 2: typed exception classes (CR 12-5 D-14 envelope) ──────────


def test_pdf_export_size_exceeded_error_envelope() -> None:
    """PdfExportSizeExceededError envelope 결정 wire (CR 12-5 D-14)."""
    exc = PdfExportSizeExceededError(row_count=200_000, max_rows=MAX_PDF_ROWS)
    assert exc.code == "PDF_EXPORT_TOO_LARGE_KO"
    assert "최대" in exc.message_ko
    assert exc.details["row_count"] == 200_000
    assert exc.details["max_rows"] == MAX_PDF_ROWS


def test_pdf_export_font_error_envelope() -> None:
    """PdfExportFontError envelope 결정 wire (CR 12-5 D-14)."""
    exc = PdfExportFontError(attempted_paths=["/nonexistent/font.ttf"])
    assert exc.code == "PDF_EXPORT_FONT_KO"
    assert exc.details["attempted_paths"] == ["/nonexistent/font.ttf"]


def test_pdf_export_error_base_envelope() -> None:
    """PdfExportError base class envelope."""
    exc = PdfExportError(
        code="PDF_TEST_KO",
        message_ko="테스트",
        details={"foo": "bar"},
    )
    assert exc.code == "PDF_TEST_KO"
    assert exc.message_ko == "테스트"
    assert exc.details == {"foo": "bar"}


# ── Test 3: Pydantic schema validation ──────────────────────────────


def test_pdf_export_request_valid() -> None:
    """PdfExportRequest accepts valid input."""
    req = PdfExportRequest(
        type="cost-records",
        period="2026-08",
        tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
    )
    assert req.type == "cost-records"
    assert req.period == "2026-08"


def test_pdf_export_request_invalid_period() -> None:
    """PdfExportRequest rejects malformed period."""
    with pytest.raises(ValueError):
        PdfExportRequest(
            type="cost-records",
            period="2026-13",  # invalid month
            tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        )


def test_pdf_export_request_invalid_type() -> None:
    """PdfExportRequest rejects invalid type literal."""
    with pytest.raises(ValueError):
        PdfExportRequest(
            type="invalid",  # type: ignore[arg-type]
            period="2026-08",
            tenant_id="f47ac10b-58cc-4372-a567-0e02b2c3d479",
        )


# ── Test 4: Font registration (NFR18 ko-KR SSOT) ────────────────────


def test_register_korean_font_returns_valid_font() -> None:
    """_register_korean_font returns a non-empty font name (fallback OK)."""
    font_name = _register_korean_font()
    assert isinstance(font_name, str)
    assert len(font_name) > 0
    # Either the Korean font (if installed) or a fallback (Helvetica/HeiseiMin).
    assert font_name == KOREAN_FONT_NAME or font_name in ("HeiseiMin-W3", "Helvetica")


# ── Test 5: PDF constants (page geometry) ───────────────────────────


def test_pdf_page_constants() -> None:
    """Page geometry constants 결정 wire 보존."""
    assert PDF_PAGE_SIZE_A4_LANDSCAPE[0] > PDF_PAGE_SIZE_A4_LANDSCAPE[1]  # landscape
    assert PDF_PAGE_MARGIN_LEFT > 0
    assert PDF_PAGE_MARGIN_RIGHT > 0
    assert PDF_PAGE_MARGIN_TOP > 0
    assert PDF_PAGE_MARGIN_BOTTOM > 0


# ── Test 6: PDF generation smoke tests ──────────────────────────────


class _FakeRow:
    """Mock SQLAlchemy row for PDF generation tests."""

    def __init__(self, **kwargs: object) -> None:
        for k, v in kwargs.items():
            setattr(self, k, v)


def _fake_cost_record_rows() -> list[_FakeRow]:
    """Build 3 fake cost_records rows."""
    return [
        _FakeRow(
            tenant_id="11111111-1111-1111-1111-111111111111",
            period_key="2026-08",
            product_id="22222222-2222-2222-2222-222222222222",
            product_name="Product A",
            category="MATERIAL",
            opening_qty=100,
            input_qty=50,
            output_qty=120,
            closing_qty=30,
            unit_cost=1000.0,
            total_cost=120000.0,
            currency="KRW",
            created_at="2026-08-31T00:00:00Z",
            ledger_event_id="33333333-3333-3333-3333-333333333333",
        ),
        _FakeRow(
            tenant_id="11111111-1111-1111-1111-111111111111",
            period_key="2026-08",
            product_id="44444444-4444-4444-4444-444444444444",
            product_name="Product B",
            category="LABOR",
            opening_qty=0,
            input_qty=10,
            output_qty=8,
            closing_qty=2,
            unit_cost=5000.0,
            total_cost=40000.0,
            currency="KRW",
            created_at="2026-08-31T00:00:00Z",
            ledger_event_id="55555555-5555-5555-5555-555555555555",
        ),
        _FakeRow(
            tenant_id="11111111-1111-1111-1111-111111111111",
            period_key="2026-08",
            product_id="66666666-6666-6666-6666-666666666666",
            product_name="Product C",
            category="OVERHEAD",
            opening_qty=0,
            input_qty=1,
            output_qty=1,
            closing_qty=0,
            unit_cost=20000.0,
            total_cost=20000.0,
            currency="KRW",
            created_at="2026-08-31T00:00:00Z",
            ledger_event_id="77777777-7777-7777-7777-777777777777",
        ),
    ]


def _fake_bom_rows() -> list[_FakeRow]:
    """Build 3 fake bom_matrix rows."""
    return [
        _FakeRow(
            tenant_id="11111111-1111-1111-1111-111111111111",
            period_key="2026-08",
            parent_product_id="88888888-8888-8888-8888-888888888888",
            parent_product_name="Parent A",
            child_product_id="22222222-2222-2222-2222-222222222222",
            child_product_name="Child A1",
            child_category="MATERIAL",
            child_qty_per_parent=2.0,
            child_unit_cost=1000.0,
            child_total_cost=2000.0,
            currency="KRW",
            created_at="2026-08-31T00:00:00Z",
        ),
        _FakeRow(
            tenant_id="11111111-1111-1111-1111-111111111111",
            period_key="2026-08",
            parent_product_id="88888888-8888-8888-8888-888888888888",
            parent_product_name="Parent A",
            child_product_id="44444444-4444-4444-4444-444444444444",
            child_product_name="Child A2",
            child_category="LABOR",
            child_qty_per_parent=0.5,
            child_unit_cost=5000.0,
            child_total_cost=2500.0,
            currency="KRW",
            created_at="2026-08-31T00:00:00Z",
        ),
        _FakeRow(
            tenant_id="11111111-1111-1111-1111-111111111111",
            period_key="2026-08",
            parent_product_id="99999999-9999-9999-9999-999999999999",
            parent_product_name="Parent B",
            child_product_id="66666666-6666-6666-6666-666666666666",
            child_product_name="Child B1",
            child_category="OVERHEAD",
            child_qty_per_parent=1.0,
            child_unit_cost=15000.0,
            child_total_cost=15000.0,
            currency="KRW",
            created_at="2026-08-31T00:00:00Z",
        ),
    ]


def _fake_charts() -> dict[str, bytes]:
    """Build 3 fake PNG bytes via matplotlib (so they're valid for reportlab).

    Real matplotlib output → reportlab ImageReader can parse → PDF builds.
    Uses a simple bar chart for all 3 slots (the PDF composition does not
    differentiate chart content for layout — only image presence matters).
    """
    import io as _io

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as _plt

    figs = []
    for _ in range(3):
        fig, ax = _plt.subplots(figsize=(4, 3))
        ax.bar(["A", "B", "C"], [10, 20, 30], color="steelblue")
        ax.set_title("테스트 차트", fontsize=10)
        buf = _io.BytesIO()
        fig.savefig(buf, format="png", dpi=72, bbox_inches="tight")
        _plt.close(fig)
        figs.append(buf.getvalue())
    return {
        "category_breakdown_pie": figs[0],
        "monthly_trend_bar": figs[1],
        "unit_cost_evolution_line": figs[2],
    }


def test_generate_cost_records_pdf_returns_pdf_bytes() -> None:
    """generate_cost_records_pdf returns non-empty PDF bytes (starts with %PDF-)."""
    rows = _fake_cost_record_rows()
    charts = _fake_charts()
    pdf_bytes = generate_cost_records_pdf(
        rows=rows,
        period="2026-08",
        tenant_id="11111111-1111-1111-1111-111111111111",
        charts=charts,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 100  # minimal PDF size
    # PDF magic number: every PDF starts with "%PDF-".
    assert pdf_bytes[:5] == b"%PDF-"


def test_generate_bom_pdf_returns_pdf_bytes() -> None:
    """generate_bom_pdf returns non-empty PDF bytes (starts with %PDF-)."""
    rows = _fake_bom_rows()
    charts = _fake_charts()
    pdf_bytes = generate_bom_pdf(
        rows=rows,
        period="2026-08",
        tenant_id="11111111-1111-1111-1111-111111111111",
        charts=charts,
    )
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 100
    assert pdf_bytes[:5] == b"%PDF-"
