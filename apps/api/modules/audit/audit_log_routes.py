"""apps.api.modules.audit.audit_log_routes — Audit log viewer + activity stream API.

Epic 17 (cj-style 82번째 epic 연속 정직 회복 atomic wire) — AD-32 (a)+(c)+(e).

5 routes (mounted at `/api/v1/`):
  1. GET /api/v1/audit-log
     — paginated audit log query with filter snapshot.
     Owner/admin only + capability gate AUDIT_LOG_VIEW.
  2. GET /api/v1/audit-log/{entry_id}
     — single audit log entry lookup (AuditLogDetailModal target).
     Owner/admin only + capability gate AUDIT_LOG_VIEW.
  3. GET /api/v1/audit-log/count
     — total count under current filter (UI page indicator).
     Owner/admin only + capability gate AUDIT_LOG_VIEW.
  4. GET /api/v1/activity
     — activity stream timeline (all tenant members allowed).
     Capability gate AUDIT_LOG_VIEW NOT enforced (PRD §F21.3 verbatim).
  5. GET /api/v1/audit-log/export
     — CSV export with audit-first INSERT `audit_log_exported`.
     Owner/admin only + capability gate AUDIT_LOG_VIEW + MAX 100k rows.

CR 0-2 RLS lesson: tenant context (GUC `app.tenant_id`) is auto-applied
via `get_tenant_context` dep — no manual SET LOCAL needed.
CR 1-1 audit-first: 1 NEW audit log row `audit_log_exported` INSERTed
BEFORE the CSV byte stream flush (T5 verbatim).
CR 12-5 D-14 typed exception envelope for all 4 NEW error classes.
"""
from __future__ import annotations

import csv
import io
import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.core.audit_action import ActionClass, emit_audit_typed
from apps.api.core.capability import require_any_role
from apps.api.core.db import get_session
from apps.api.core.tenant_context import TenantContext, get_tenant_context
from apps.api.dependencies.capability import require_audit_log_view
from apps.api.modules.audit.audit_log_query import (
    AuditLogEntryNotFoundError,
    AuditLogQueryInvalidFilterError,
    _build_where_clause,
    count_audit_log,
    get_audit_log_entry,
    query_activity_stream,
    query_audit_log,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["audit-log"])


# ── Typed exceptions (CR 12-5 D-14 envelope) ───────────────────────────


class AuditLogExportError(Exception):
    """Base audit log CSV export failure."""

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


class AuditLogExportForbiddenError(AuditLogExportError):
    """403 AUDIT_LOG_EXPORT_FORBIDDEN_KO — caller is not owner/admin."""

    def __init__(self, role: str) -> None:
        super().__init__(
            code="AUDIT_LOG_EXPORT_FORBIDDEN_KO",
            message_ko="audit log export 권한이 없습니다",
            details={"role": role},
        )


class AuditLogExportTooLargeError(AuditLogExportError):
    """413 AUDIT_LOG_EXPORT_TOO_LARGE_KO — export row count > MAX_EXPORT_ROWS."""

    def __init__(self, row_count: int, max_rows: int) -> None:
        super().__init__(
            code="AUDIT_LOG_EXPORT_TOO_LARGE_KO",
            message_ko=f"export 행 수가 너무 많습니다 (최대 {max_rows:,}건)",
            details={"row_count": row_count, "max_rows": max_rows},
        )


MAX_EXPORT_ROWS: int = 100_000


# ── Filter parsing helper ──────────────────────────────────────────────


def _parse_filters(
    *,
    actor_id: str | None,
    action: str | None,
    action_class: str | None,
    resource_type: str | None,
    resource_id: str | None,
    start_date: str | None,
    end_date: str | None,
    trace_id: str | None,
) -> dict[str, Any]:
    """Convert query-string args to the `AuditLogQueryFilters` dict shape.

    Validates date format + actor_id UUID shape; raises
    AuditLogQueryInvalidFilterError on malformed input.
    """
    filters: dict[str, Any] = {}
    if actor_id:
        try:
            uuid.UUID(actor_id)
        except ValueError as exc:
            raise AuditLogQueryInvalidFilterError(
                f"actor_id must be a UUID: {actor_id}"
            ) from exc
        filters["actor_id"] = actor_id
    if action:
        filters["action"] = action
    if action_class:
        filters["action_class"] = action_class
    if resource_type:
        filters["resource_type"] = resource_type
    if resource_id:
        filters["resource_id"] = resource_id
    if start_date:
        try:
            datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError as exc:
            raise AuditLogQueryInvalidFilterError(
                f"start_date must be ISO 8601: {start_date}"
            ) from exc
        filters["start_date"] = start_date
    if end_date:
        try:
            datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError as exc:
            raise AuditLogQueryInvalidFilterError(
                f"end_date must be ISO 8601: {end_date}"
            ) from exc
        filters["end_date"] = end_date
    if trace_id:
        filters["trace_id"] = trace_id
    return filters


# ── GET /api/v1/audit-log ──────────────────────────────────────────────


@router.get(
    "/audit-log",
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_audit_log_view),
    ],
)
async def list_audit_log(
    actor_id: str | None = Query(None),
    action: str | None = Query(None),
    action_class: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    trace_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Paginated audit log query (PRD §F21.2 AC #2.1 target)."""
    filters = _parse_filters(
        actor_id=actor_id,
        action=action,
        action_class=action_class,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        trace_id=trace_id,
    )
    return await query_audit_log(
        session,
        tenant_id=ctx.tenant_id,
        filters=filters,
        page=page,
        page_size=page_size,
    )


# ── GET /api/v1/audit-log/count ────────────────────────────────────────


@router.get(
    "/audit-log/count",
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_audit_log_view),
    ],
)
async def count_audit_log_endpoint(
    actor_id: str | None = Query(None),
    action: str | None = Query(None),
    action_class: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    trace_id: str | None = Query(None),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Total audit log count under current filter (UI page indicator)."""
    filters = _parse_filters(
        actor_id=actor_id,
        action=action,
        action_class=action_class,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        trace_id=trace_id,
    )
    total = await count_audit_log(
        session, tenant_id=ctx.tenant_id, filters=filters
    )
    return {"total": total}


# ── GET /api/v1/audit-log/{entry_id} ───────────────────────────────────


@router.get(
    "/audit-log/{entry_id}",
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_audit_log_view),
    ],
)
async def get_audit_log_entry_endpoint(
    entry_id: int = Path(..., ge=1),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Single audit log entry lookup (AuditLogDetailModal target)."""
    return await get_audit_log_entry(
        session, tenant_id=ctx.tenant_id, entry_id=entry_id
    )


# ── GET /api/v1/activity ───────────────────────────────────────────────


@router.get(
    "/activity",
    dependencies=[
        # All tenant members allowed (PRD §F21.3 verbatim) — owner /
        # admin / member / viewer. Capability gate AUDIT_LOG_VIEW is NOT
        # enforced (activity stream is intentionally broad like Slack
        # presence; the audit log viewer itself enforces the gate).
        Depends(require_any_role("owner", "admin", "member", "viewer")),
    ],
)
async def get_activity_stream(
    window_days: int = Query(7, ge=1, le=90),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Activity stream timeline (PRD §F21.3 AC #3.1 target)."""
    if window_days not in (1, 7, 30, 90):
        raise AuditLogQueryInvalidFilterError(
            f"window_days must be one of 1, 7, 30, 90; got {window_days}"
        )
    groups = await query_activity_stream(
        session, tenant_id=ctx.tenant_id, window_days=window_days
    )
    return {"groups": groups, "window_days": window_days}


# ── GET /api/v1/audit-log/export ──────────────────────────────────────


@router.get(
    "/audit-log/export",
    dependencies=[
        Depends(require_any_role("owner", "admin")),
        Depends(require_audit_log_view),
    ],
)
async def export_audit_log_csv(
    actor_id: str | None = Query(None),
    action: str | None = Query(None),
    action_class: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_id: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    trace_id: str | None = Query(None),
    ctx: TenantContext = Depends(get_tenant_context),
    session: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    """CSV export streaming response (PRD §F21.5 + AC #5.1~#5.8).

    audit-first INSERT `audit_log_exported` (CR 1-1 verbatim + ActionClass.AUDIT
    + action='audit_log_exported') BEFORE the byte stream flush.
    Size limit MAX_EXPORT_ROWS = 100_000 (defense vs. giant exports).
    """
    filters = _parse_filters(
        actor_id=actor_id,
        action=action,
        action_class=action_class,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        trace_id=trace_id,
    )
    merged = dict(filters)
    merged["tenant_id"] = str(ctx.tenant_id)

    where_sql, params = _build_where_clause(merged)

    # Pre-flight size check (defense vs. giant exports).
    count_row = (
        await session.execute(
            text(f"SELECT count(*) FROM public.audit_logs WHERE {where_sql}"),
            params,
        )
    ).first()
    total_rows: int = int(count_row[0]) if count_row else 0
    if total_rows > MAX_EXPORT_ROWS:
        raise AuditLogExportTooLargeError(
            row_count=total_rows, max_rows=MAX_EXPORT_ROWS
        )

    # audit-first INSERT `audit_log_exported` (CR 1-1 verbatim).
    try:
        await emit_audit_typed(
            session,
            action_class=ActionClass.AUDIT,
            action="audit_log_exported",
            actor_id=ctx.user_id,
            tenant_id=ctx.tenant_id,
            payload={
                "filters_snapshot": filters,
                "row_count": total_rows,
                "exported_at": datetime.now(UTC).isoformat(),
            },
            flush=True,
        )
        await session.commit()
    except Exception:  # noqa: BLE001
        # Best-effort: never block the export on audit emit fail (the
        # user wants their CSV; the audit trail is the sidecar).
        logger.exception("audit_log_exported audit emit failed")

    # Stream the CSV (UTF-8 BOM + comma-separated + CRLF + Excel escape).
    rows = (
        await session.execute(
            text(
                f"""
                SELECT id, created_at, actor_id, target_table, action,
                       trace_id, payload
                FROM public.audit_logs
                WHERE {where_sql}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit
                """
            ),
            {**params, "limit": MAX_EXPORT_ROWS},
        )
    ).fetchall()

    def _csv_escape(value: Any) -> str:
        """Excel-compatible CSV escape (double-quote wrap on comma/newline)."""
        if value is None:
            return ""
        s = str(value)
        if any(ch in s for ch in (",", "\n", "\r", '"')):
            escaped = s.replace('"', '""')
            return f'"{escaped}"'
        return s

    def _row_to_csv(r: Any) -> list[str]:
        payload = dict(r.payload or {})
        return [
            _csv_escape(r.id),
            _csv_escape(r.created_at.isoformat() if r.created_at else ""),
            _csv_escape(r.actor_id),
            _csv_escape(r.target_table),
            _csv_escape(r.action),
            _csv_escape(r.trace_id),
            _csv_escape(payload.get("resource_type")),
            _csv_escape(payload.get("resource_id")),
            _csv_escape(payload.get("ip_address")),
            _csv_escape(r.payload),  # raw JSONB; double-quote wrap handles nested quotes
        ]

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    tenant_id_short = str(ctx.tenant_id).replace("-", "")[:12]
    filename = f"audit-log-{tenant_id_short}-{timestamp}.csv"
    header = [
        "id",
        "created_at",
        "actor_id",
        "action_class",
        "action",
        "trace_id",
        "resource_type",
        "resource_id",
        "ip_address",
        "payload_json",
    ]

    def _iter() -> Any:
        # UTF-8 BOM first (Excel-compatible BOM).
        buf = io.StringIO(newline="")
        writer = csv.writer(buf, lineterminator="\r\n", quoting=csv.QUOTE_MINIMAL)
        writer.writerow(header)
        yield "﻿" + buf.getvalue()
        buf.seek(0)
        buf.truncate(0)
        for r in rows:
            writer.writerow(_row_to_csv(r))
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
    "AuditLogExportError",
    "AuditLogExportForbiddenError",
    "AuditLogExportTooLargeError",
    "MAX_EXPORT_ROWS",
    "AuditLogEntryNotFoundError",
    "AuditLogQueryInvalidFilterError",
]
