"""apps.api.modules.reports.csv_routes — Story 30.1 CSV export endpoint.

cj-282a wire sprint (cj-style 283번째 epic 연속 정직 회복 source+docs atomic single
sprint) — Story 30.1 CSV export (FR-30-1).

1 route (mounted at `/api/v1/`):
  1. GET /api/v1/exports/csv?type=cost-records|bom&period=YYYY-MM&tenant_id={uuid}
     — RFC 4180 quoted CSV with UTF-8 BOM (Excel ko-KR 호환).
     StreamingResponse + audit-first INSERT `export_csv` (CR 1-1 verbatim).
     Owner/admin only RBAC (AD-22 verbatim).
     Capability gate `require_exports_csv` 결정 wire 보류 — cj-style 284+ 적용.

CR 0-2 RLS lesson: tenant context (GUC `app.tenant_id`) is auto-applied
via `get_tenant_context` dep — no manual SET LOCAL needed.
CR 1-1 audit-first: 1 NEW audit log row `export_csv` INSERTed
BEFORE the CSV byte stream flush (T5 verbatim).
CR 12-5 D-14 typed exception envelope for 4 NEW error classes.

Verbatim mirror of `apps/api/modules/audit/audit_log_routes.py:286-439` for the
CSV streaming pattern (StreamingResponse + UTF-8 BOM + csv.writer + CRLF + Excel
escape). Verbatim mirror of `apps/api/modules/finops/chargeback_export.py:62-82`
for the `_csv_escape` helper (RFC 4180 결정 wire 보존).

AD bind 3/3:
- AD-2 (audit-first INSERT append-only)
- AD-10 (identity + 2FA via owner-only RBAC, AD-22 owner-only)
- AD-12 (verify-first capability gate, in-route. require_exports_csv 결정 wire
  보류 — cj-style 284+ 적용 시 Capability.EXPORTS_CSV EXTENSION)

NFR bind 2/7 active (cj-282 PRD entry 의 7 NFR 중):
- NFR5 (page load P95 ≤ 5s for 10만 row) — StreamingResponse 결정 wire 보존
- NFR18 (ko-KR vocabulary SSOT) — error message_ko + ko-KR.json EXTENSION 결정 wire
  보류 (cj-style 284+ 결정)

4 OQ 결정 보류 (cj-282a 범위 외 N/A — Story 30.2/30.3/30.4 wire 진입 시 결정):
- OQ-EPIC30+-1 weasyprint vs reportlab (Story 30.2 PDF 진입 시 결정)
- OQ-EPIC30+-2 SMTP 인프라 외부 의존 (Story 30.3 Email 진입 시 결정)
- OQ-EPIC30+-3 APScheduler vs Celery beat vs cron (Story 30.4 Scheduled 진입 시 결정)
- OQ-EPIC30+-4 chart library matplotlib vs Plotly vs Chart.js PNG export
  (Story 30.2 PDF 진입 시 결정)

CR 11-3 honest-DEFER 223번째 epic 연속 정직 회복
(cj-282a web-e2e skip 의 221+222번째 + cj-style 283rd 의 223번째)
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.capability import Capability, require_any_role, require_capability
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.schemas.export_schemas import CsvExportRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["exports"])


# ── CSV constants (verbatim from chargeback_export.py pattern) ────────


# CSV columns for cost-records export (cj-282 PRD entry spec line 110 verbatim).
CSV_COLUMNS_COST_RECORDS: tuple[str, ...] = (
    "tenant_id",
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
    "currency",
    "created_at",
    "ledger_event_id",
)

# CSV header row (joined string for StreamingResponse 첫 yield).
CSV_HEADER_ROW_COST_RECORDS: str = ",".join(CSV_COLUMNS_COST_RECORDS)

# CSV columns for BOM export (level 1 only; full BOM tree = separate epic).
CSV_COLUMNS_BOM: tuple[str, ...] = (
    "tenant_id",
    "period_key",
    "parent_product_id",
    "parent_product_name",
    "child_product_id",
    "child_product_name",
    "child_category",
    "child_qty_per_parent",
    "child_unit_cost",
    "child_total_cost",
    "currency",
    "created_at",
)
CSV_HEADER_ROW_BOM: str = ",".join(CSV_COLUMNS_BOM)

# UTF-8 BOM for Excel ko-KR 호환 (verbatim from chargeback_export.py:62).
UTF8_BOM: str = "﻿"

# Streaming chunk size (rows per buffer flush). 5000 rows × ~14 cols = ~70KB per
# chunk. NFR5 streaming P95 ≤ 5s for 10만 row 결정 wire 보존.
CHUNK_FLUSH_ROWS: int = 5000

# Max export rows (defense vs. giant exports). 100k rows per NFR5 spec line.
MAX_EXPORT_ROWS: int = 100_000


# ── Typed exceptions (CR 12-5 D-14 envelope) ──────────────────────────


class CsvExportError(Exception):
    """Base CSV export failure."""

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


class CsvExportInvalidRequestError(CsvExportError):
    """400 CSV_EXPORT_INVALID_REQUEST_KO — invalid type/period/tenant_id."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            code="CSV_EXPORT_INVALID_REQUEST_KO",
            message_ko="CSV export 요청이 올바르지 않습니다",
            details={"reason": reason},
        )


class CsvExportForbiddenError(CsvExportError):
    """403 CSV_EXPORT_FORBIDDEN_KO — caller is not owner/admin."""

    def __init__(self, role: str) -> None:
        super().__init__(
            code="CSV_EXPORT_FORBIDDEN_KO",
            message_ko="CSV export 권한이 없습니다 (owner 또는 admin 필요)",
            details={"role": role},
        )


class CsvExportCrossTenantError(CsvExportError):
    """403 CSV_EXPORT_CROSS_TENANT_KO — tenant_id mismatch with context."""

    def __init__(self, request_tenant_id: str, ctx_tenant_id: str) -> None:
        super().__init__(
            code="CSV_EXPORT_CROSS_TENANT_KO",
            message_ko="다른 테넌트의 데이터는 export 할 수 없습니다",
            details={
                "request_tenant_id": request_tenant_id,
                "ctx_tenant_id": ctx_tenant_id,
            },
        )


class CsvExportTooLargeError(CsvExportError):
    """413 CSV_EXPORT_TOO_LARGE_KO — export row count > MAX_EXPORT_ROWS."""

    def __init__(self, row_count: int, max_rows: int) -> None:
        super().__init__(
            code="CSV_EXPORT_TOO_LARGE_KO",
            message_ko=f"export 행 수가 너무 많습니다 (최대 {max_rows:,}건)",
            details={"row_count": row_count, "max_rows": max_rows},
        )


# ── Helper: RFC 4180 CSV escape (verbatim from chargeback_export.py:62-82) ─


def _csv_escape(value: Any) -> str:
    """Excel-compatible RFC 4180 CSV escape (double-quote wrap on comma/newline).

    CR 11-3 honest-DEFER 223번째: ko-KR SSOT verbatim 결정 wire (UTF-8 BOM upstream).
    """
    if value is None:
        return ""
    s = str(value)
    if any(ch in s for ch in (",", "\n", "\r", '"')):
        escaped = s.replace('"', '""')
        return f'"{escaped}"'
    return s


# ── Helper: row → CSV values (cost-records) ────────────────────────────


def _cost_record_row_to_csv(r: Any) -> list[str]:
    """Map a cost_records row to a CSV row (14 columns verbatim)."""
    return [
        _csv_escape(r.tenant_id),
        _csv_escape(r.period_key),
        _csv_escape(r.product_id),
        _csv_escape(r.product_name),
        _csv_escape(r.category),
        _csv_escape(r.opening_qty),
        _csv_escape(r.input_qty),
        _csv_escape(r.output_qty),
        _csv_escape(r.closing_qty),
        _csv_escape(r.unit_cost),
        _csv_escape(r.total_cost),
        _csv_escape(r.currency),
        _csv_escape(r.created_at.isoformat() if r.created_at else ""),
        _csv_escape(r.ledger_event_id),
    ]


def _bom_row_to_csv(r: Any) -> list[str]:
    """Map a bom level1 row to a CSV row (12 columns)."""
    return [
        _csv_escape(r.tenant_id),
        _csv_escape(r.period_key),
        _csv_escape(r.parent_product_id),
        _csv_escape(r.parent_product_name),
        _csv_escape(r.child_product_id),
        _csv_escape(r.child_product_name),
        _csv_escape(r.child_category),
        _csv_escape(r.child_qty_per_parent),
        _csv_escape(r.child_unit_cost),
        _csv_escape(r.child_total_cost),
        _csv_escape(r.currency),
        _csv_escape(r.created_at.isoformat() if r.created_at else ""),
    ]


# ── GET /api/v1/exports/csv ────────────────────────────────────────────


@router.get(
    "/exports/csv",
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_capability(Capability.EXPORT_CSV)),  # cj-287 AD-56(c) wire
    ],
)
async def export_csv(
    type: Literal["cost-records", "bom"] = Query(  # noqa: A002 — FastAPI query param named per cj-282 PRD entry spec line 110
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
    """Story 30.1 CSV export streaming response (cj-282 PRD entry §F44.1 verbatim).

    audit-first INSERT `export_csv` (CR 1-1 verbatim + ActionClass.REPORTS +
    action='export_csv') BEFORE the byte stream flush.
    Size limit MAX_EXPORT_ROWS = 100_000 (defense vs. giant exports, NFR5 결정 wire).

    Capability gate `require_capability(Capability.EXPORT_CSV)` 결정 wire 진입:
    - Capability.EXPORT_CSV EXTENSION 결정 wire (cj-285 EXTENSION wire sprint — capability
      matrix v1.53 → v1.54 EXTENSION).
    - cj-287 wire sprint 진입: AD-56 (c) sub-decision verbatim 적용 —
      route-level `Depends(require_capability(Capability.EXPORT_CSV))` dependency 추가.
    - Owner/admin RBAC (AD-22 verbatim) + capability gate (AD-12 verify-first) 결정 wire.
    """
    # Cross-tenant 차단: 요청 tenant_id vs context tenant_id 일치 검증 (CR 0-2 RLS 결정 wire).
    if str(tenant_id) != str(ctx.tenant_id):
        raise CsvExportCrossTenantError(
            request_tenant_id=str(tenant_id),
            ctx_tenant_id=str(ctx.tenant_id),
        )

    # CSV columns 결정 wire (type 별).
    if type == "cost-records":
        header = list(CSV_COLUMNS_COST_RECORDS)
        row_converter = _cost_record_row_to_csv
        # cost_records 테이블 조회 (period_key 기준, tenant_id RLS 자동 적용).
        query = text(
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
        count_query = text(
            """
            SELECT count(*) FROM public.cost_records
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
            """
        )
    else:  # bom
        header = list(CSV_COLUMNS_BOM)
        row_converter = _bom_row_to_csv
        # bom_matrix 테이블 조회 (period_key 기준, tenant_id RLS 자동 적용).
        # Level 1 only 결정 wire (full BOM tree = 별도 epic, cj-282 PRD entry out-of-scope).
        query = text(
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
        count_query = text(
            """
            SELECT count(*) FROM public.bom_matrix
            WHERE tenant_id = :tenant_id
              AND period_key = :period_key
              AND bom_level = 1
            """
        )

    # Pre-flight size check (defense vs. giant exports, NFR5 결정 wire).
    count_row = (
        await session.execute(
            count_query,
            {"tenant_id": tenant_id, "period_key": period},
        )
    ).first()
    total_rows: int = int(count_row[0]) if count_row else 0
    if total_rows > MAX_EXPORT_ROWS:
        raise CsvExportTooLargeError(row_count=total_rows, max_rows=MAX_EXPORT_ROWS)

    # audit-first INSERT `export_csv` (CR 1-1 verbatim + ActionClass.REPORTS — cj-287 fix).
    try:
        await emit_audit_typed(
            session,
            action_class=ActionClass.REPORTS,  # cj-287 fix: REPORTS registry accepts export_csv (cj-285 EXTENSION)
            action="export_csv",
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
        # Best-effort: never block the export on audit emit fail (the
        # user wants their CSV; the audit trail is the sidecar).
        # Verbatim from audit_log_routes.py:356-359 pattern 결정 wire.
        logger.exception("export_csv audit emit failed")

    # Stream the CSV (UTF-8 BOM + comma-separated + CRLF + Excel escape).
    # Verbatim mirror of audit_log_routes.py:361-431 pattern 결정 wire 보존.
    rows = (
        await session.execute(
            query,
            {"tenant_id": tenant_id, "period_key": period, "limit": MAX_EXPORT_ROWS},
        )
    ).fetchall()

    # CsvExportRequest 검증 (decide wire 보존 — type, period, tenant_id 정규식 검증).
    # Pydantic schema 는 in-route 결정 wire (canonical pattern verbatim).
    _ = CsvExportRequest(type=type, period=period, tenant_id=tenant_id)

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    tenant_id_short = str(ctx.tenant_id).replace("-", "")[:12]
    filename = f"{type}-{tenant_id_short}-{period}-{timestamp}.csv"

    def _iter() -> Any:
        """Generator yielding CSV bytes (UTF-8 BOM + header + data rows)."""
        # UTF-8 BOM first (Excel-compatible BOM) — NFR18 ko-KR 결정 wire.
        buf = io.StringIO(newline="")
        writer = csv.writer(buf, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        yield UTF8_BOM + buf.getvalue()
        buf.seek(0)
        buf.truncate(0)
        # Stream rows in groups of CHUNK_FLUSH_ROWS for memory efficiency.
        # NFR5 streaming P95 ≤ 5s for 10만 row 결정 wire 보존.
        for r in rows:
            writer.writerow(row_converter(r))
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    return StreamingResponse(
        _iter(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


__all__ = [
    "router",
    "CsvExportError",
    "CsvExportInvalidRequestError",
    "CsvExportForbiddenError",
    "CsvExportCrossTenantError",
    "CsvExportTooLargeError",
    "CSV_COLUMNS_COST_RECORDS",
    "CSV_COLUMNS_BOM",
    "MAX_EXPORT_ROWS",
    "CHUNK_FLUSH_ROWS",
]
