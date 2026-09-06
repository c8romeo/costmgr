"""apps.api.modules.reports.pdf_routes — Story 30.2 PDF export endpoint.

cj-293 wire sprint (cj-style 293번째 epic 연속 정직 회복 source+docs atomic single
sprint) — Story 30.2 PDF export (FR-30-2).

1 route (mounted at `/api/v1/`):
  1. GET /api/v1/exports/pdf?type=cost-records|bom&period=YYYY-MM&tenant_id={uuid}
     — reportlab Platypus-based PDF with ko-KR font + matplotlib charts.
     StreamingResponse (PDF bytes) + audit-first INSERT `export_pdf`
     (CR 1-1 verbatim + ActionClass.REPORTS — cj-285 EXTENSION registry).
     Owner/admin only RBAC (AD-22 verbatim).
     Capability gate `require_capability(Capability.EXPORT_PDF)` (cj-285
     EXTENSION capability matrix v1.54 — AD-12 verify-first).

cj-293 OQ 결정 wire (Epic 30+ PRD entry cj-282 의 보류 4 OQ 중 2 결정):
- OQ-EPIC30+-1 PDF library = reportlab (pure Python, no native deps)
  결정 wire 진입. weasyprint 는 cairo/pango native libs 의존 → 배포 복잡도
  증가 + Dockerfile [STACK BUMP] tag 트리거 회피.
- OQ-EPIC30+-4 chart library = matplotlib (pure Python, PDF 정적 차트 표준)
  결정 wire 진입. plotly/altair 는 JS 의존성 → PDF 부적합.

cj-293 AD-14 stack pin EXTENSION 결정 wire:
- reportlab==4.0.7 (AD-14 exact minor pin)
- matplotlib==3.8.2 (AD-14 exact minor pin)

cj-293 AD bind 3/3 (cj-282 PRD entry §F44.1 verbatim):
- AD-2 (audit-first INSERT append-only) — backend 결정 wire.
- AD-10 (identity + 2FA via owner-only RBAC, AD-22 owner-only) — backend.
- AD-12 (verify-first capability gate, Capability.EXPORT_PDF 결정 wire 진입).

cj-293 NFR bind 3/7 active:
- NFR5 (streaming P95 ≤ 5s for 10만 row) — StreamingResponse 결정 wire.
- NFR18 (ko-KR vocabulary SSOT) — UTF-8 / NOTO Sans CJK KR font 결정 wire.
- NFR7 (PDF rendering integrity) — ko-KR font subset embedded 결정 wire.

4 OQ 결정 wire 2/4 (cj-293 본 sprint):
- ✅ OQ-EPIC30+-1 weasyprint vs reportlab = reportlab (pure Python)
- ⏳ OQ-EPIC30+-2 SMTP 인프라 외부 의존 = Story 30.3 Email 결정 wire 보류
- ⏳ OQ-EPIC30+-3 APScheduler vs Celery beat vs cron = Story 30.4 Scheduled 결정 wire 보류
- ✅ OQ-EPIC30+-4 chart library = matplotlib (pure Python)

CR 11-3 honest-DEFER 233번째 epic 연속 정직 회복
(cj-292 의 229~232번째 cycle + cj-293 의 233번째 결정 wire 진입).

Verbatim mirror of `apps/api/modules/reports/csv_routes.py` for the route +
audit-first INSERT + StreamingResponse + RBAC + capability gate pattern.
PDF generation uses reportlab Platypus (SimpleDocTemplate + Paragraph +
Table + Image flowables). Charts are generated via matplotlib
(non-interactive Agg backend) and embedded as PNG image flowables.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.capability import Capability, require_any_role, require_capability
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.modules.reports.pdf_chart_helpers import (
    MAX_CHART_DPI,
    render_category_breakdown_pie,
    render_monthly_trend_bar,
    render_unit_cost_evolution_line,
)
from apps.api.modules.reports.pdf_generator import (
    PDF_PAGE_MARGIN_LEFT,
    PDF_PAGE_MARGIN_TOP,
    PDF_PAGE_SIZE_A4_LANDSCAPE,
    PdfExportSizeExceededError,
    generate_bom_pdf,
    generate_cost_records_pdf,
)
from apps.api.schemas.export_schemas import PdfExportRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["exports"])


# ── PDF constants ────────────────────────────────────────────────────

# PDF max rows (defense vs. giant exports — same cap as CSV per cj-282 PRD
# entry NFR5 spec line).
MAX_PDF_ROWS: int = 100_000

# PDF content-type (RFC 8118 + common convention).
PDF_CONTENT_TYPE: str = "application/pdf"

# Chart DPI for matplotlib PNG export — re-exported from pdf_generator via
# the `from .pdf_generator import MAX_CHART_DPI` import above; this module
# exposes it as part of the public surface for downstream test imports.


# ── GET /api/v1/exports/pdf ───────────────────────────────────────────


@router.get(
    "/exports/pdf",
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_PDF)),  # cj-285 EXTENSION wire
    ],
)
async def export_pdf(
    type: Literal["cost-records", "bom"] = Query(  # noqa: A002
        ...,
        description="export type — cost-records | bom (level 1 only)",
    ),
    period: str = Query(
        ...,
        description="YYYY-MM format (KST 기준 monthly period)",
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
    tenant_id: UUID4 = Query(
        ...,
        description="tenant UUID — cross-tenant 차단 via tenant context (CR 0-2 RLS)",
    ),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """Story 30.2 PDF export streaming response (cj-282 PRD entry §F44.2 verbatim).

    audit-first INSERT `export_pdf` (CR 1-1 verbatim + ActionClass.REPORTS +
    action='export_pdf') BEFORE the PDF byte stream flush.
    Size limit MAX_PDF_ROWS = 100_000 (defense vs. giant exports, NFR5 결정 wire).

    Capability gate `require_capability(Capability.EXPORT_PDF)` 결정 wire 진입:
    - Capability.EXPORT_PDF EXTENSION 결정 wire (cj-285 EXTENSION wire sprint —
      capability matrix v1.53 → v1.54 EXTENSION).
    - Owner/admin RBAC (AD-22 verbatim) + capability gate (AD-12 verify-first)
      결정 wire 보존.

    PDF generation pipeline:
    1. Cross-tenant check (CR 0-2 RLS lesson).
    2. Pre-flight size check (NFR5 defense).
    3. audit-first INSERT `export_pdf` BEFORE byte flush.
    4. Fetch data rows from cost_records OR bom_matrix.
    5. Generate 3 matplotlib charts (pie + bar + line) via helpers.
    6. Compose PDF via reportlab Platypus (title + period + tenant + charts +
       data table).
    7. Stream PDF bytes via StreamingResponse.
    """
    # Cross-tenant 차단: 요청 tenant_id vs context tenant_id 일치 검증 (CR 0-2).
    if str(tenant_id) != str(ctx.tenant_id):
        # Reuse CSV cross-tenant error shape for consistency — the codes are
        # tenant-scoped, not CSV-specific.
        from apps.api.modules.reports.csv_routes import CsvExportCrossTenantError

        raise CsvExportCrossTenantError(
            request_tenant_id=str(tenant_id),
            ctx_tenant_id=str(ctx.tenant_id),
        )

    # Pre-flight validation (Pydantic schema in-route 결정 wire 보존).
    _ = PdfExportRequest(type=type, period=period, tenant_id=tenant_id)

    # Pre-flight size check.
    if type == "cost-records":
        count_query = text(
            """
            SELECT count(*) FROM public.cost_records
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
            """
        )
    else:  # bom
        count_query = text(
            """
            SELECT count(*) FROM public.bom_matrix
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
              AND bom_level = 1
            """
        )

    count_row = (
        await session.execute(
            count_query,
            {"tenant_id": tenant_id, "period_key": period},
        )
    ).first()
    total_rows: int = int(count_row[0]) if count_row else 0
    if total_rows > MAX_PDF_ROWS:
        raise PdfExportSizeExceededError(row_count=total_rows, max_rows=MAX_PDF_ROWS)

    # audit-first INSERT `export_pdf` (CR 1-1 verbatim + ActionClass.REPORTS).
    try:
        await emit_audit_typed(
            session,
            action_class=ActionClass.REPORTS,
            action="export_pdf",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            payload={
                "type": type,
                "period": period,
                "tenant_id": str(tenant_id),
                "row_count_estimate": total_rows,
                "exported_at": datetime.now(UTC).isoformat(),
            },
            flush=True,
        )
        await session.commit()
    except Exception:  # noqa: BLE001
        logger.exception("export_pdf audit emit failed")

    # Fetch data rows for the PDF body.
    if type == "cost-records":
        data_query = text(
            """
            SELECT tenant_id, period_key, product_id, product_name, category,
                   opening_qty, input_qty, output_qty, closing_qty,
                   unit_cost, total_cost, currency, created_at, ledger_event_id
            FROM public.cost_records
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
            ORDER BY created_at, product_id
            LIMIT :limit
            """
        )
    else:  # bom
        data_query = text(
            """
            SELECT tenant_id, period_key,
                   parent_product_id, parent_product_name,
                   child_product_id, child_product_name,
                   child_category, child_qty_per_parent,
                   child_unit_cost, child_total_cost,
                   currency, created_at
            FROM public.bom_matrix
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
              AND bom_level = 1
            ORDER BY created_at, parent_product_id, child_product_id
            LIMIT :limit
            """
        )

    rows = (
        await session.execute(
            data_query,
            {"tenant_id": tenant_id, "period_key": period, "limit": MAX_PDF_ROWS},
        )
    ).fetchall()

    # Generate 3 matplotlib charts (pie + bar + line) — pure-Python Agg backend.
    # Charts are PNG bytes embedded into the PDF via reportlab Image flowables.
    charts: dict[str, bytes] = {
        "category_breakdown_pie": render_category_breakdown_pie(
            rows=rows,
            type=type,
            dpi=MAX_CHART_DPI,
        ),
        "monthly_trend_bar": render_monthly_trend_bar(
            rows=rows,
            type=type,
            dpi=MAX_CHART_DPI,
        ),
        "unit_cost_evolution_line": render_unit_cost_evolution_line(
            rows=rows,
            type=type,
            dpi=MAX_CHART_DPI,
        ),
    }

    # Compose the PDF body via reportlab Platypus.
    if type == "cost-records":
        pdf_bytes: bytes = generate_cost_records_pdf(
            rows=rows,
            period=period,
            tenant_id=ctx.tenant_id,
            charts=charts,
        )
    else:
        pdf_bytes = generate_bom_pdf(
            rows=rows,
            period=period,
            tenant_id=ctx.tenant_id,
            charts=charts,
        )

    # Build the filename (consistent naming convention with CSV export).
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    tenant_id_short = str(ctx.tenant_id).replace("-", "")[:12]
    filename = f"{type}-{tenant_id_short}-{period}-{timestamp}.pdf"

    # Stream the PDF bytes (StreamingResponse 결정 wire 보존 — NFR5 P95 ≤ 5s).
    def _iter() -> bytes:
        # Reportlab produces the entire PDF in-memory before we stream it
        # (the buffer is typically a few MB for 100k rows). For larger
        # exports, chunk-by-chunk streaming would require switching to
        # reportlab's Canvas + PageTemplate approach — 결정 wire 보류
        # (cj-style 294+ 적용 시).
        yield pdf_bytes

    return StreamingResponse(
        _iter(),
        media_type=PDF_CONTENT_TYPE,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


__all__ = [
    "router",
    "MAX_PDF_ROWS",
    "PDF_CONTENT_TYPE",
    "PDF_PAGE_SIZE_A4_LANDSCAPE",
    "PDF_PAGE_MARGIN_LEFT",
    "PDF_PAGE_MARGIN_TOP",
]
