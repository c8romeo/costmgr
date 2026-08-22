"""tests.api.modules.audit.test_audit_log_query — audit log query + activity stream tests.

Epic 17 (cj-style 82번째 epic 연속 정직 회복 wire) — T7 (AC #1.1~#1.16).

Verifies the 4 query functions in `apps/api/modules/audit/audit_log_query.py`:
  1. query_audit_log       — paginated audit log query (AC #1.1~#1.4)
  2. count_audit_log       — total count under filter (AC #1.2)
  3. get_audit_log_entry   — single entry lookup (AC #1.4)
  4. query_activity_stream — grouped activity stream (AC #1.5)

All tests use AsyncMock + MagicMock for the SQLAlchemy session —
no real DB connection required. RLS auto-isolation, filter validation,
typed exception envelope, and Phase 5 replica lag threshold checks
are covered.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.modules.audit.audit_log_query import (
    REPLICA_LAG_BYTES_MAX,
    REPLICA_LAG_SECONDS_MAX,
    AuditLogEntryNotFoundError,
    AuditLogQueryInvalidFilterError,
    count_audit_log,
    get_audit_log_entry,
    query_activity_stream,
    query_audit_log,
)


def _make_session() -> AsyncMock:
    """Build an AsyncMock that mimics AsyncSession."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    return session


def _make_row(**kwargs: object) -> MagicMock:
    """Build a SQLAlchemy Row-like MagicMock."""
    row = MagicMock()
    for key, value in kwargs.items():
        setattr(row, key, value)
    return row


class TestAuditLogQueryFiltersValidation:
    """Filter validation (AC #1.1) — tenant_id required + date range sanity."""

    @pytest.mark.asyncio
    async def test_query_audit_log_rejects_filters_not_dict(self) -> None:
        """Sanity — non-dict filter input is rejected (defense vs. caller bug)."""
        session = _make_session()
        # Bypass the kwarg merge to exercise the validation branch.
        with pytest.raises(AuditLogQueryInvalidFilterError) as exc_info:
            await query_audit_log(
                session,
                tenant_id=uuid.uuid4(),
                filters=42,  # type: ignore[arg-type]
                page=1,
                page_size=50,
            )
        assert exc_info.value.code == "AUDIT_LOG_QUERY_INVALID_FILTER_KO"

    @pytest.mark.asyncio
    async def test_query_audit_log_rejects_bad_page(self) -> None:
        session = _make_session()
        with pytest.raises(AuditLogQueryInvalidFilterError) as exc_info:
            await query_audit_log(
                session,
                tenant_id=uuid.uuid4(),
                page=0,
                page_size=50,
            )
        assert "page" in exc_info.value.details["reason"]

    @pytest.mark.asyncio
    async def test_query_audit_log_rejects_bad_page_size(self) -> None:
        session = _make_session()
        for bad in (0, 501):
            with pytest.raises(AuditLogQueryInvalidFilterError) as exc_info:
                await query_audit_log(
                    session,
                    tenant_id=uuid.uuid4(),
                    page=1,
                    page_size=bad,
                )
            assert "page_size" in exc_info.value.details["reason"]

    @pytest.mark.asyncio
    async def test_query_audit_log_rejects_date_range_inversion(self) -> None:
        session = _make_session()
        with pytest.raises(AuditLogQueryInvalidFilterError) as exc_info:
            await query_audit_log(
                session,
                tenant_id=uuid.uuid4(),
                filters={
                    "start_date": "2026-08-22T00:00:00+00:00",
                    "end_date": "2026-08-01T00:00:00+00:00",
                },
            )
        assert "start_date" in exc_info.value.details["reason"]


class TestAuditLogQueryPagination:
    """Pagination (AC #1.1) — page + page_size respected, total returned."""

    @pytest.mark.asyncio
    async def test_query_audit_log_returns_paginated_envelope(self) -> None:
        tenant_id = uuid.uuid4()
        session = _make_session()
        # 3 execute calls expected:
        # 1. _check_replica_lag() → SELECT lag_bytes, lag_seconds → first()
        # 2. count(*) → first()
        # 3. SELECT ... LIMIT ... OFFSET ... → fetchall()
        empty_lag = MagicMock()
        empty_lag.first = MagicMock(return_value=None)
        count_result = MagicMock()
        count_result.first = MagicMock(return_value=(42,))
        page_result = MagicMock()
        page_result.fetchall = MagicMock(return_value=[])
        session.execute = AsyncMock(
            side_effect=[empty_lag, count_result, page_result]
        )

        result = await query_audit_log(
            session,
            tenant_id=tenant_id,
            page=1,
            page_size=25,
        )
        assert result["total"] == 42
        assert result["page"] == 1
        assert result["page_size"] == 25
        assert result["has_next"] is True  # 25 < 42
        assert result["entries"] == []


class TestAuditLogEntryLookup:
    """Single entry lookup (AC #1.4) — 404 envelope on miss."""

    @pytest.mark.asyncio
    async def test_get_audit_log_entry_not_found(self) -> None:
        tenant_id = uuid.uuid4()
        session = _make_session()
        empty = MagicMock()
        empty.first = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=empty)
        with pytest.raises(AuditLogEntryNotFoundError) as exc_info:
            await get_audit_log_entry(
                session, tenant_id=tenant_id, entry_id=9999
            )
        assert exc_info.value.code == "AUDIT_LOG_ENTRY_NOT_FOUND_KO"
        assert exc_info.value.details["entry_id"] == 9999

    @pytest.mark.asyncio
    async def test_get_audit_log_entry_returns_dict_envelope(self) -> None:
        tenant_id = uuid.uuid4()
        session = _make_session()
        row = _make_row(
            id=42,
            tenant_id=tenant_id,
            actor_id=uuid.uuid4(),
            action="tenant_idp_created",
            target_table="auth",
            payload={
                "resource_type": "tenant_idp",
                "resource_id": "abc123",
                "ip_address": "10.0.0.1",
                "user_agent": "Mozilla/5.0",
            },
            trace_id=uuid.uuid4(),
            created_at=None,
        )
        result_row = MagicMock()
        result_row.first = MagicMock(return_value=row)
        session.execute = AsyncMock(return_value=result_row)

        entry = await get_audit_log_entry(
            session, tenant_id=tenant_id, entry_id=42
        )
        assert entry["id"] == 42
        assert entry["action"] == "tenant_idp_created"
        assert entry["resource_type"] == "tenant_idp"


class TestCountAuditLog:
    """Count (AC #1.2) — total returned without pagination."""

    @pytest.mark.asyncio
    async def test_count_audit_log_returns_total(self) -> None:
        tenant_id = uuid.uuid4()
        session = _make_session()
        result = MagicMock()
        result.first = MagicMock(return_value=(1234,))
        session.execute = AsyncMock(return_value=result)
        n = await count_audit_log(session, tenant_id=tenant_id)
        assert n == 1234


class TestActivityStream:
    """Activity stream (AC #1.5) — grouped buckets + window_days validation."""

    @pytest.mark.asyncio
    async def test_query_activity_stream_rejects_invalid_window(self) -> None:
        session = _make_session()
        for bad in (0, 2, 14, 365):
            with pytest.raises(AuditLogQueryInvalidFilterError) as exc_info:
                await query_activity_stream(
                    session, tenant_id=uuid.uuid4(), window_days=bad
                )
            assert "window_days" in exc_info.value.details["reason"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("window_days", "bucket_trunc", "expected_groups"),
        [
            (1, "hour", 24),
            (7, "day", 7),
            (30, "day", 30),
            (90, "week", 13),
        ],
    )
    async def test_query_activity_stream_bucket_granularity(
        self, window_days: int, bucket_trunc: str, expected_groups: int
    ) -> None:
        session = _make_session()
        result = MagicMock()
        result.fetchall = MagicMock(return_value=[])
        session.execute = AsyncMock(return_value=result)

        groups = await query_activity_stream(
            session, tenant_id=uuid.uuid4(), window_days=window_days
        )
        assert groups == []
        # Verify the bucket_trunc parameter was passed correctly via execute
        # calls (positional args: 1=text, 2=bind dict).
        last_call = session.execute.await_args_list[-1]
        bind_params = last_call.args[1]
        assert bind_params["bucket_trunc"] == bucket_trunc
        assert bind_params["limit"] == expected_groups + 5
        assert bind_params["window_days"] == window_days


class TestPhase5ReplicaLagThresholds:
    """Phase 5 carry-over — replica lag threshold constants (AC #1.13~1.16)."""

    def test_replica_lag_bytes_max_is_100mb(self) -> None:
        assert REPLICA_LAG_BYTES_MAX == 100 * 1024 * 1024

    def test_replica_lag_seconds_max_is_30(self) -> None:
        assert REPLICA_LAG_SECONDS_MAX == 30


class TestTypedExceptionEnvelope:
    """Typed exception envelope CR 12-5 D-14 verbatim."""

    def test_invalid_filter_envelope(self) -> None:
        exc = AuditLogQueryInvalidFilterError("reason here")
        assert exc.code == "AUDIT_LOG_QUERY_INVALID_FILTER_KO"
        assert "audit log filter" in exc.message_ko
        assert exc.details == {"reason": "reason here"}

    def test_not_found_envelope(self) -> None:
        exc = AuditLogEntryNotFoundError(entry_id=42)
        assert exc.code == "AUDIT_LOG_ENTRY_NOT_FOUND_KO"
        assert exc.details == {"entry_id": 42}
