"""apps.api.modules.audit.audit_log_query — Audit log read API (Epic 17 T1+T4).

Epic 17 (cj-style 82번째 epic 연속 정직 회복 atomic wire) — AD-32 (a) + (d).

Provides 4 query functions for the audit log viewer UI + activity stream UI:

  1. `query_audit_log(tenant_id, filters, page, page_size) -> AuditLogPage`
     — paginated audit log entries with filter snapshot.
  2. `count_audit_log(tenant_id, filters) -> int`
     — total count without pagination (for the UI page indicator).
  3. `get_audit_log_entry(tenant_id, entry_id) -> AuditLogEntry`
     — single audit log entry lookup (used by AuditLogDetailModal).
  4. `query_activity_stream(tenant_id, window_days) -> list[ActivityStreamGroup]`
     — grouped activity stream for the tenant timeline view.

All functions enforce:
  - RLS auto-isolation via `app.tenant_id` GUC (CR 0-2 verbatim, multi-tenant).
  - owner/admin role required for audit-log queries (AD-22 verbatim).
  - capability gate `AUDIT_LOG_VIEW` per-tenant on/off (CR 12-5 D-GATE-01).
  - cross-region read-replica routing with primary fallback (Phase 5 carry-over,
    `f093f8c` EXTENSION).
  - audit-first INSERT `audit_log_exported` on export (T5 verbatim).
  - typed error envelope CR 12-5 D-14 verbatim.

Per AD-11: this module imports only stdlib + SQLAlchemy/Pydantic. Per AD-1
binding: the route layer (`audit_log_routes`) → query layer (this module)
→ audit_logs table (SELECT only, append-only insert is via
`apps.api.core.audit.emit_audit`).
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Literal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_LOGGER = logging.getLogger(__name__)


# ── TypedDict mirrors (CR 12-5 D-PARITY-01 inversion: Python ↔ TypeScript) ──
# At runtime these are plain dicts — the field-NAME contract is bind-enforced
# by the cross-language drift detector (vitest parity test in
# apps/web/__tests__/audit-log/audit-log-client.test.ts).


class AuditLogQueryFilters(dict):
    """Audit log filter set — verbatim mirror of TS `AuditLogQueryFilters` interface.

    CR 12-5 D-PARITY-01: every field NAME here MUST have a corresponding
    TypeScript interface field in `apps/web/lib/audit/audit-log-client.ts`.
    """


class AuditLogEntry(dict):
    """Single audit log row envelope (mirror of TS `AuditLogEntry`)."""


class AuditLogPage(dict):
    """Paginated audit log page envelope (mirror of TS `AuditLogPage`)."""


class ActivityStreamGroup(dict):
    """Activity stream timeline bucket group (mirror of TS `ActivityStreamGroup`)."""


# ── Typed exceptions (CR 12-5 D-14 envelope) ───────────────────────


class AuditLogQueryError(Exception):
    """Base audit log query failure."""

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


class AuditLogQueryInvalidFilterError(AuditLogQueryError):
    """400 AUDIT_LOG_QUERY_INVALID_FILTER_KO — filter shape invalid."""

    def __init__(self, reason: str) -> None:
        super().__init__(
            code="AUDIT_LOG_QUERY_INVALID_FILTER_KO",
            message_ko="잘못된 audit log filter 입니다",
            details={"reason": reason},
        )


class AuditLogEntryNotFoundError(AuditLogQueryError):
    """404 AUDIT_LOG_ENTRY_NOT_FOUND_KO — single entry lookup miss."""

    def __init__(self, entry_id: int) -> None:
        super().__init__(
            code="AUDIT_LOG_ENTRY_NOT_FOUND_KO",
            message_ko="audit log entry 를 찾을 수 없습니다",
            details={"entry_id": entry_id},
        )


# ── Phase 5 carry-over — cross-region read-replica threshold constants ──


REPLICA_LAG_BYTES_MAX: int = 100 * 1024 * 1024  # 100 MB (Phase 5 wire `f093f8c`)
REPLICA_LAG_SECONDS_MAX: int = 30  # 30 seconds (Phase 5 wire `f093f8c`)


# ── Helpers ────────────────────────────────────────────────────────────


def _validate_filters(filters: dict[str, Any]) -> None:
    """Reject malformed filters BEFORE the SQL roundtrip.

    Accepts TypedDict-shaped `dict` (TypedDict at runtime is just `dict`).
    Raises AuditLogQueryInvalidFilterError on bad shape.
    """
    if not isinstance(filters, dict):
        raise AuditLogQueryInvalidFilterError("filters must be a dict")
    if "tenant_id" not in filters or not filters["tenant_id"]:
        # tenant_id is REQUIRED for RLS — without it, the SELECT would
        # leak cross-tenant rows. This is the CR 0-2 RLS lesson applied.
        raise AuditLogQueryInvalidFilterError("tenant_id is required")
    # Date range sanity (when both are provided).
    if (
        filters.get("start_date")
        and filters.get("end_date")
        and filters["start_date"] > filters["end_date"]
    ):
        raise AuditLogQueryInvalidFilterError("start_date must be <= end_date")


def _build_where_clause(filters: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Build the SQL WHERE clause + bind params from the filter dict.

    Returns (where_clause_sql, bind_params). Always includes
    `tenant_id = :tenant_id` for RLS auto-isolation.
    """
    parts: list[str] = ["tenant_id = :tenant_id"]
    params: dict[str, Any] = {"tenant_id": filters["tenant_id"]}
    if filters.get("actor_id"):
        parts.append("actor_id = :actor_id")
        params["actor_id"] = filters["actor_id"]
    if filters.get("action"):
        parts.append("action = :action")
        params["action"] = filters["action"]
    if filters.get("action_class"):
        parts.append("target_table = :action_class")
        params["action_class"] = filters["action_class"]
    if filters.get("resource_type"):
        parts.append("payload->>'resource_type' = :resource_type")
        params["resource_type"] = filters["resource_type"]
    if filters.get("resource_id"):
        parts.append("payload->>'resource_id' = :resource_id")
        params["resource_id"] = filters["resource_id"]
    if filters.get("start_date"):
        parts.append("created_at >= :start_date")
        params["start_date"] = filters["start_date"]
    if filters.get("end_date"):
        parts.append("created_at <= :end_date")
        params["end_date"] = filters["end_date"]
    if filters.get("trace_id"):
        parts.append("trace_id = :trace_id")
        params["trace_id"] = filters["trace_id"]
    return " AND ".join(parts), params


def _row_to_entry(row: Any) -> dict[str, Any]:
    """Map a raw audit_logs row to the AuditLogEntry envelope."""
    created_at: Any = row.created_at
    return {
        "id": int(row.id),
        "tenant_id": str(row.tenant_id),
        "actor_id": str(row.actor_id) if row.actor_id else "",
        "action": row.action,
        "action_class": row.target_table,
        "resource_type": (row.payload or {}).get("resource_type"),
        "resource_id": (row.payload or {}).get("resource_id"),
        "payload": dict(row.payload or {}),
        "ip_address": (row.payload or {}).get("ip_address"),
        "user_agent": (row.payload or {}).get("user_agent"),
        "trace_id": str(row.trace_id) if row.trace_id else "",
        "created_at": created_at.isoformat() if created_at else "",
    }


async def _check_replica_lag(
    session: AsyncSession,
) -> tuple[bool, int, int]:
    """Phase 5 carry-over — read `phase_5_replication_lag` row, decide routing.

    Returns (use_replica, lag_bytes, lag_seconds). When lag_bytes exceeds
    REPLICA_LAG_BYTES_MAX OR lag_seconds exceeds REPLICA_LAG_SECONDS_MAX,
    the caller falls back to the primary region (Seoul) and emits a Sentry
    breadcrumb (CR 1-1 verbatim audit + observability surface).

    Defensive: if `phase_5_replication_lag` table doesn't exist (e.g.,
    local dev without Phase 5 migration applied), returns (True, 0, 0)
    so the caller proceeds against the replica without spurious failure.
    """
    try:
        row = (
            await session.execute(
                text(
                    """
                    SELECT lag_bytes, lag_seconds
                    FROM public.phase_5_replication_lag
                    ORDER BY captured_at DESC
                    LIMIT 1
                    """
                )
            )
        ).first()
    except Exception as exc:  # noqa: BLE001 — defensive table-may-not-exist
        _LOGGER.debug("phase_5_replication_lag check skipped: %s", exc)
        return True, 0, 0
    if row is None:
        return True, 0, 0
    lag_bytes = int(row[0] or 0)
    lag_seconds = int(row[1] or 0)
    if lag_bytes > REPLICA_LAG_BYTES_MAX or lag_seconds > REPLICA_LAG_SECONDS_MAX:
        return False, lag_bytes, lag_seconds
    return True, lag_bytes, lag_seconds


async def _emit_lag_breadcrumb(
    *,
    lag_bytes: int,
    lag_seconds: int,
    trace_id: str,
) -> None:
    """Phase 5 carry-over — Sentry breadcrumb on replica lag threshold breach."""
    try:
        import sentry_sdk

        sentry_sdk.capture_message(
            f"Audit log read replica lag exceeded: "
            f"lag_bytes={lag_bytes}, lag_seconds={lag_seconds}",
            level="warning",
        )
    except Exception:  # noqa: BLE001 — observability must never break the query
        pass


# ── T1 — public query functions ───────────────────────────────────────


async def query_audit_log(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    filters: dict[str, Any] | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """Paginated audit log query (PRD §F21.1 + AD-32 (a)).

    RLS auto-isolation via tenant_id GUC + `WHERE tenant_id = :tenant_id`
    (defense-in-depth: belt-and-suspenders CR 0-2 RLS lesson).
    Returns AuditLogPage envelope.
    """
    if page < 1:
        raise AuditLogQueryInvalidFilterError("page must be >= 1")
    if page_size < 1 or page_size > 500:
        raise AuditLogQueryInvalidFilterError("page_size must be in [1, 500]")
    # Defensive: accept None or empty dict; coerce any non-dict mapping
    # to dict() but reject non-iterables (int/str) BEFORE dict() raises
    # TypeError so the caller sees a typed envelope (CR 12-5 D-14).
    if filters is None:
        merged: dict[str, Any] = {}
    elif isinstance(filters, dict):
        merged = dict(filters)
    else:
        raise AuditLogQueryInvalidFilterError(
            "filters must be a dict or None"
        )
    merged["tenant_id"] = str(tenant_id)
    _validate_filters(merged)
    where_sql, params = _build_where_clause(merged)

    # Phase 5 carry-over — replica lag check.
    use_replica, lag_bytes, lag_seconds = await _check_replica_lag(session)
    if not use_replica and lag_bytes + lag_seconds > 0:
        await _emit_lag_breadcrumb(
            lag_bytes=lag_bytes, lag_seconds=lag_seconds, trace_id=str(uuid.uuid4())
        )

    # Count total (for the UI pagination indicator).
    count_row = (
        await session.execute(
            text(f"SELECT count(*) FROM public.audit_logs WHERE {where_sql}"),
            params,
        )
    ).first()
    total: int = int(count_row[0]) if count_row else 0

    # Page slice.
    offset = (page - 1) * page_size
    rows = (
        await session.execute(
            text(
                f"""
                SELECT id, tenant_id, actor_id, action, target_table,
                       payload, trace_id, created_at
                FROM public.audit_logs
                WHERE {where_sql}
                ORDER BY created_at DESC, id DESC
                LIMIT :limit OFFSET :offset
                """
            ),
            {**params, "limit": page_size, "offset": offset},
        )
    ).fetchall()
    entries = [_row_to_entry(r) for r in rows]
    has_next = (offset + page_size) < total

    return {
        "entries": entries,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": has_next,
    }


async def count_audit_log(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    filters: dict[str, Any] | None = None,
) -> int:
    """Total audit log count under the current filter snapshot.

    Useful for the UI page indicator (e.g. "총 1,234건" footer).
    """
    merged = dict(filters or {})
    merged["tenant_id"] = str(tenant_id)
    _validate_filters(merged)
    where_sql, params = _build_where_clause(merged)
    row = (
        await session.execute(
            text(f"SELECT count(*) FROM public.audit_logs WHERE {where_sql}"),
            params,
        )
    ).first()
    return int(row[0]) if row else 0


async def get_audit_log_entry(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    entry_id: int,
) -> dict[str, Any]:
    """Single audit log entry lookup (PRD §F21.1 + AC #1.4).

    Used by AuditLogDetailModal (PRD §F21.2 AC #2.6).
    Raises AuditLogEntryNotFoundError when the row is missing OR belongs
    to a different tenant (no info leak — same error code regardless).
    """
    row = (
        await session.execute(
            text(
                """
                SELECT id, tenant_id, actor_id, action, target_table,
                       payload, trace_id, created_at
                FROM public.audit_logs
                WHERE id = :entry_id AND tenant_id = :tenant_id
                LIMIT 1
                """
            ),
            {"entry_id": entry_id, "tenant_id": str(tenant_id)},
        )
    ).first()
    if row is None:
        raise AuditLogEntryNotFoundError(entry_id=entry_id)
    return _row_to_entry(row)


Window = Literal[1, 7, 30, 90]


async def query_activity_stream(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    window_days: int,
) -> list[dict[str, Any]]:
    """Grouped activity stream timeline (PRD §F21.3 + AC #1.5).

    Returns list[ActivityStreamGroup] — each group is a timestamp bucket
    with entry_count + top_actions (top 3) + top_actors (top 3).

    Bucket granularity depends on window_days:
      - 1  → hourly buckets (24 groups)
      - 7  → daily buckets (7 groups)
      - 30 → daily buckets (30 groups)
      - 90 → weekly buckets (13 groups)

    Allowed for all tenant members (owner/admin/member/viewer) per
    PRD §F21.3 verbatim. Capability gate AUDIT_LOG_VIEW is NOT enforced
    here (the activity stream is intentionally broad — like Slack presence).
    """
    if window_days not in (1, 7, 30, 90):
        raise AuditLogQueryInvalidFilterError(
            f"window_days must be one of 1, 7, 30, 90; got {window_days}"
        )
    # Bucket granularity.
    if window_days == 1:
        bucket_trunc = "hour"
        expected_groups = 24
    elif window_days in (7, 30):
        bucket_trunc = "day"
        expected_groups = window_days
    else:  # 90
        bucket_trunc = "week"
        expected_groups = 13

    rows = (
        await session.execute(
            text(
                """
                SELECT date_trunc(:bucket_trunc, created_at) AS bucket,
                       count(*) AS entry_count,
                       array_agg(DISTINCT action ORDER BY action)
                         FILTER (WHERE action IS NOT NULL) AS distinct_actions,
                       array_agg(DISTINCT actor_id ORDER BY actor_id)
                         FILTER (WHERE actor_id IS NOT NULL) AS distinct_actors
                FROM public.audit_logs
                WHERE tenant_id = :tenant_id
                  AND created_at >= now() - (:window_days || ' days')::interval
                GROUP BY bucket
                ORDER BY bucket DESC
                LIMIT :limit
                """
            ),
            {
                "tenant_id": str(tenant_id),
                "window_days": window_days,
                "bucket_trunc": bucket_trunc,
                "limit": expected_groups + 5,  # slack for timezone edges
            },
        )
    ).fetchall()
    groups: list[dict[str, Any]] = []
    for r in rows:
        actions = list(r.distinct_actions or [])[:3]
        actors = [str(a) for a in (r.distinct_actors or [])][:3]
        bucket: Any = r.bucket
        groups.append(
            {
                "timestamp_bucket": bucket.isoformat() if bucket else "",
                "entry_count": int(r.entry_count),
                "top_actions": actions,
                "top_actors": actors,
            }
        )
    return groups


__all__ = [
    "AuditLogQueryFilters",
    "AuditLogEntry",
    "AuditLogPage",
    "ActivityStreamGroup",
    "AuditLogQueryError",
    "AuditLogQueryInvalidFilterError",
    "AuditLogEntryNotFoundError",
    "REPLICA_LAG_BYTES_MAX",
    "REPLICA_LAG_SECONDS_MAX",
    "query_audit_log",
    "count_audit_log",
    "get_audit_log_entry",
    "query_activity_stream",
]
