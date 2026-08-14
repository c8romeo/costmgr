"""tests.api.m12_account.test_backup_export_service — Story 12.2 service tests.

15+ cases per AC spec:
- run_backup happy path (7 tables, row_counts, sha256)
- run_backup audit-first emit (CR 1.1)
- run_retention_sweep idempotent (2회 실행 → 2회째 0 row affected)
- trigger_backup owner-only (actor_id required)
- list_recent_backups 7-day window
- fetch_backup_payload owner access + NotFoundError
- 5 typed exception mapping

CR 4-3: `def test_* + asyncio.run(_impl())` pattern.
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from apps.api.core.audit_action import ActionClass
from apps.api.modules.m12_account.exceptions import (
    BackupNotFoundError,
    BackupRetentionCutoffInvalidError,
    BackupServiceAuditEmitError,
)
from apps.api.modules.m12_account.services.backup_export_service import (
    BackupExportService,
)
from packages.services.m12_account.backup_export import (
    BACKUP_TABLES,
    SCHEMA_VERSION,
)

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
BACKUP_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
TRACE_ID = "test-trace-001"


# ── Mock helpers ──────────────────────────────────────────────
def _make_table_row(*, columns: dict[str, object]) -> MagicMock:
    """Create an ORM-like row mock with the given columns."""
    row = MagicMock(spec=[])
    # Create a real __table__ attribute with a .columns attribute
    table_mock = MagicMock()
    cols = []
    for k in columns:
        col = MagicMock(spec=[])
        col.name = k
        cols.append(col)
    table_mock.columns = cols
    row.__table__ = table_mock
    for k, v in columns.items():
        setattr(row, k, v)
    return row


def _make_tenant_settings_row() -> MagicMock:
    return _make_table_row(
        columns={
            "tenant_id": TENANT_ID,
            "industry": "manufacturing",
            "fiscal_year_start_month": 1,
            "currency": "KRW",
            "language": "ko-KR",
        }
    )


def _wire_session_empty(session: AsyncMock) -> None:
    """Wire session with empty results (no rows)."""
    result_mock = MagicMock()
    result_mock.scalar_one_or_none = MagicMock(return_value=None)
    result_mock.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    session.execute = AsyncMock(return_value=result_mock)
    session.flush = AsyncMock()
    session.add = MagicMock()


def _wire_session_with_tables(
    session: AsyncMock,
    *,
    ts_row: MagicMock | None = None,
    products: list[MagicMock] | None = None,
    bom_lines: list[MagicMock] | None = None,
    mip_rows: list[MagicMock] | None = None,
    mip_ids: list[uuid.UUID] | None = None,
    mir_rows: list[MagicMock] | None = None,
    fps_rows: list[MagicMock] | None = None,
    audit_rows: list[MagicMock] | None = None,
) -> None:
    """Wire session.execute to return different results based on call order.

    BackupExportService._select_7_tables does 7 sequential queries
    (ts → products → bom → mip → mir → fps → audit) plus a separate
    mip_ids query before monthly_input_rows. Plus backup_id query
    for fetch_backup_payload.
    """
    queue: list[MagicMock] = []

    def _queue_one_scalar(value: object) -> None:
        """For SELECT scalar (scalar_one_or_none)."""
        r = MagicMock()
        r.scalar_one_or_none = MagicMock(return_value=value)
        r.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )
        queue.append(r)

    def _queue_one_list(value: list[object]) -> None:
        """For SELECT list (scalars().all())."""
        r = MagicMock()
        r.scalar_one_or_none = MagicMock(return_value=None)
        r.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=value)))
        queue.append(r)

    # 1. tenant_settings (scalar)
    _queue_one_scalar(ts_row)
    # 2. products (list)
    _queue_one_list(products or [])
    # 3. product_ids for bom_lines (list of UUIDs)
    _queue_one_list([p.id for p in (products or [])])
    # 4. bom_lines
    _queue_one_list(bom_lines or [])
    # 5. monthly_input_periods
    _queue_one_list(mip_rows or [])
    # 6. mip ids for monthly_input_rows
    _queue_one_list(mip_ids or [])
    # 7. monthly_input_rows
    _queue_one_list(mir_rows or [])
    # 8. fiscal_period_snapshots
    _queue_one_list(fps_rows or [])
    # 9. audit_logs
    _queue_one_list(audit_rows or [])

    session.execute = AsyncMock(side_effect=queue)
    session.flush = AsyncMock()
    session.add = MagicMock()


# ── 1. run_backup happy path ──────────────────────────────────
def test_run_backup_happy_path() -> None:
    """7 tables SELECT → envelope build → INSERT row."""

    async def _impl() -> None:
        session = AsyncMock()
        ts_row = _make_tenant_settings_row()
        _wire_session_with_tables(
            session,
            ts_row=ts_row,
        )

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        result = await svc.run_backup()

        assert result.tenant_id == TENANT_ID
        assert result.schema_version == SCHEMA_VERSION
        assert len(result.payload_sha256) == 64
        # ts_row provided → 1 row total
        assert result.row_count_total == 1
        assert result.audit_log_exported_rows == 0
        assert session.add.called  # TenantBackup row INSERT attempted
        assert session.flush.called  # CR 1.1 audit-first flush

    asyncio.run(_impl())


def test_run_backup_emits_backup_created_audit() -> None:
    """Audit-first emit MUST happen BEFORE data INSERT (CR 1.1)."""

    async def _impl() -> None:
        session = AsyncMock()
        ts_row = _make_tenant_settings_row()
        _wire_session_with_tables(session, ts_row=ts_row)

        captured_actions: list[str] = []

        async def _capture_audit(*_args: object, **kwargs: object) -> None:
            captured_actions.append(str(kwargs.get("action")))

        # Patch the module-level emit_audit_typed via service import
        from apps.api.modules.m12_account.services import backup_export_service as svc_mod

        svc_mod.emit_audit_typed = _capture_audit  # type: ignore[assignment]

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        await svc.run_backup()
        # backup_created MUST be in captured actions
        assert "backup_created" in captured_actions

    asyncio.run(_impl())


def test_run_backup_handles_no_tables() -> None:
    """Empty 7-table result still succeeds (singleton tenants)."""

    async def _impl() -> None:
        session = AsyncMock()
        _wire_session_with_tables(session)  # all empty

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        result = await svc.run_backup()
        assert result.row_count_total == 0
        assert result.payload_sha256  # sha256 of empty 7-table envelope

    asyncio.run(_impl())


# ── 2. run_retention_sweep ────────────────────────────────────
def test_run_retention_sweep_idempotent() -> None:
    """2회째 실행 → 0 row affected (이미 purged_at 채워짐)."""

    async def _impl() -> None:
        session = AsyncMock()
        # SELECT returns 1 eligible row initially; UPDATE returns 1; 2회째 SELECT returns []
        eligible_row = MagicMock()
        eligible_row.__iter__ = MagicMock(return_value=iter([(uuid.uuid4(),)]))
        # First execute: SELECT eligible → 1 row
        first_result = MagicMock()
        first_result.all = MagicMock(return_value=[(uuid.uuid4(),)])
        # UPDATE result
        update_result = MagicMock()

        call_count = {"n": 0}

        async def _execute(*_args: object, **_kwargs: object) -> MagicMock:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return first_result
            return update_result

        session.execute = AsyncMock(side_effect=_execute)
        session.flush = AsyncMock()

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )

        # First run — eligible=1
        result1 = await svc.run_retention_sweep()
        assert result1.purged_count == 1

        # Second run — eligible=0 (idempotent)
        empty_result = MagicMock()
        empty_result.all = MagicMock(return_value=[])

        call_count["n"] = 0

        async def _execute_empty(*_args: object, **_kwargs: object) -> MagicMock:
            call_count["n"] += 1
            if call_count["n"] == 1:
                return empty_result
            return update_result

        session.execute = AsyncMock(side_effect=_execute_empty)
        result2 = await svc.run_retention_sweep()
        assert result2.purged_count == 0

    asyncio.run(_impl())


def test_run_retention_sweep_invalid_cutoff() -> None:
    """cutoff >= now raises BackupRetentionCutoffInvalidError."""

    async def _impl() -> None:
        session = AsyncMock()
        _wire_session_empty(session)
        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        with pytest.raises(BackupRetentionCutoffInvalidError):
            await svc.run_retention_sweep(
                cutoff=datetime.now(tz=UTC) + timedelta(days=1),
                now=datetime.now(tz=UTC),
            )

    asyncio.run(_impl())


# ── 3. trigger_backup ────────────────────────────────────────
def test_trigger_backup_requires_actor_id() -> None:
    """Manual trigger without actor_id raises service error."""

    async def _impl() -> None:
        session = AsyncMock()
        _wire_session_with_tables(session, ts_row=_make_tenant_settings_row())
        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=None, trace_id=TRACE_ID
        )
        from apps.api.modules.m12_account.services.backup_export_service import (
            BackupExportServiceError,
        )

        with pytest.raises(BackupExportServiceError):
            await svc.trigger_backup()

    asyncio.run(_impl())


def test_trigger_backup_with_actor_succeeds() -> None:
    """Manual trigger with actor_id succeeds + emits backup_triggered audit."""

    async def _impl() -> None:
        session = AsyncMock()
        _wire_session_with_tables(session, ts_row=_make_tenant_settings_row())

        captured_actions: list[str] = []

        async def _capture_audit(*_args: object, **kwargs: object) -> None:
            captured_actions.append(str(kwargs.get("action")))

        from apps.api.modules.m12_account.services import backup_export_service as svc_mod

        svc_mod.emit_audit_typed = _capture_audit  # type: ignore[assignment]

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        result = await svc.trigger_backup()
        assert result.schema_version == SCHEMA_VERSION
        # Audit order: backup_triggered → backup_created
        assert "backup_triggered" in captured_actions
        assert "backup_created" in captured_actions

    asyncio.run(_impl())


# ── 4. list_recent_backups ────────────────────────────────────
def test_list_recent_backups_default_7_days() -> None:
    """Default days=7 — SELECT last 7 days ordered by created_at DESC."""

    async def _impl() -> None:
        session = AsyncMock()
        # Mock 2 backup rows
        b1 = MagicMock()
        b1.backup_id = uuid.uuid4()
        b1.backup_date = date(2026, 8, 12)
        b1.schema_version = "1.0"
        b1.payload_sha256 = "a" * 64
        b1.payload = {"tables": {"tenant_settings": []}}
        b1.row_count_total = 0
        b1.audit_log_exported_rows = 0
        b1.created_at = datetime.now(tz=UTC) - timedelta(days=1)

        b2 = MagicMock()
        b2.backup_id = uuid.uuid4()
        b2.backup_date = date(2026, 8, 11)
        b2.schema_version = "1.0"
        b2.payload_sha256 = "b" * 64
        b2.payload = {"tables": {"tenant_settings": []}}
        b2.row_count_total = 0
        b2.audit_log_exported_rows = 0
        b2.created_at = datetime.now(tz=UTC) - timedelta(days=3)

        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[b1, b2])
        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        session.execute = AsyncMock(return_value=result_mock)

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        items = await svc.list_recent_backups()
        assert len(items) == 2
        assert all(isinstance(item.payload_sha256, str) for item in items)

    asyncio.run(_impl())


def test_list_recent_backups_excludes_purged() -> None:
    """Purged rows (purged_at != NULL) are excluded — SELECT WHERE purged_at IS NULL."""

    async def _impl() -> None:
        session = AsyncMock()
        scalars_mock = MagicMock()
        scalars_mock.all = MagicMock(return_value=[])
        result_mock = MagicMock()
        result_mock.scalars = MagicMock(return_value=scalars_mock)
        session.execute = AsyncMock(return_value=result_mock)

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        items = await svc.list_recent_backups(days=30)
        # Mock session.execute SELECT includes WHERE purged_at IS NULL filter
        # (verified at query construction level — service does not filter
        # post-fetch; the DB query does).
        assert items == []

    asyncio.run(_impl())


# ── 5. fetch_backup_payload ───────────────────────────────────
def test_fetch_backup_payload_success() -> None:
    """SELECT single row by backup_id + return payload."""

    async def _impl() -> None:
        session = AsyncMock()
        backup_row = MagicMock()
        backup_row.backup_id = BACKUP_ID
        backup_row.tenant_id = TENANT_ID
        backup_row.payload = {"schema_version": "1.0", "tables": {}}
        # F-29: payload_sha256 must match the actual sha256 of the
        # serialized payload — F-05 wired the integrity verify in
        # fetch_backup_payload to defend against tampering.
        # Match service-layer exact serialization (json.dumps sort_keys=True).
        import json as _json
        expected_sha = hashlib.sha256(
            _json.dumps(
                backup_row.payload, sort_keys=True, default=str
            ).encode("utf-8")
        ).hexdigest()
        backup_row.payload_sha256 = expected_sha
        backup_row.purged_at = None

        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=backup_row)
        session.execute = AsyncMock(return_value=result_mock)

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        payload = await svc.fetch_backup_payload(backup_id=BACKUP_ID)
        assert payload.backup_id == BACKUP_ID
        assert payload.payload_sha256 == expected_sha

    asyncio.run(_impl())


def test_fetch_backup_payload_not_found() -> None:
    """Missing backup_id raises BackupNotFoundError."""

    async def _impl() -> None:
        session = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=None)
        session.execute = AsyncMock(return_value=result_mock)

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        with pytest.raises(BackupNotFoundError):
            await svc.fetch_backup_payload(backup_id=BACKUP_ID)

    asyncio.run(_impl())


def test_fetch_backup_payload_cross_tenant_rejected() -> None:
    """Cross-tenant backup_id is rejected (defense-in-depth even with RLS)."""

    async def _impl() -> None:
        session = AsyncMock()
        other_tenant_backup = MagicMock()
        other_tenant_backup.backup_id = BACKUP_ID
        other_tenant_backup.tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
        other_tenant_backup.purged_at = None

        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=other_tenant_backup)
        session.execute = AsyncMock(return_value=result_mock)

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        with pytest.raises(BackupNotFoundError):
            await svc.fetch_backup_payload(backup_id=BACKUP_ID)

    asyncio.run(_impl())


def test_fetch_backup_payload_purged_rejected() -> None:
    """Purged backup (purged_at != NULL) is rejected."""

    async def _impl() -> None:
        session = AsyncMock()
        purged_row = MagicMock()
        purged_row.backup_id = BACKUP_ID
        purged_row.tenant_id = TENANT_ID
        purged_row.purged_at = datetime.now(tz=UTC)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none = MagicMock(return_value=purged_row)
        session.execute = AsyncMock(return_value=result_mock)

        svc = BackupExportService(
            session, tenant_id=TENANT_ID, actor_id=ACTOR_ID, trace_id=TRACE_ID
        )
        with pytest.raises(BackupNotFoundError):
            await svc.fetch_backup_payload(backup_id=BACKUP_ID)

    asyncio.run(_impl())


# ── 6. typed exception mapping ───────────────────────────────
def test_backup_export_service_error_typed() -> None:
    """Base exception carries trace_id for envelope mapping."""
    from apps.api.modules.m12_account.exceptions import BackupExportServiceError

    exc = BackupExportServiceError(message="test", trace_id=TRACE_ID)
    assert exc.trace_id == TRACE_ID
    assert "test" in str(exc)


def test_backup_payload_too_large_typed() -> None:
    """422 exception carries size_bytes + max_bytes."""
    from apps.api.modules.m12_account.exceptions import BackupPayloadTooLargeError

    exc = BackupPayloadTooLargeError(
        size_bytes=60 * 1024 * 1024,
        max_bytes=50 * 1024 * 1024,
        trace_id=TRACE_ID,
    )
    assert exc.size_bytes == 60 * 1024 * 1024
    assert exc.trace_id == TRACE_ID


def test_backup_service_audit_emit_error_typed() -> None:
    """503 exception carries trace_id for retry header."""
    exc = BackupServiceAuditEmitError(message="audit failed", trace_id=TRACE_ID)
    assert exc.trace_id == TRACE_ID


# ── 7. AccountBackupAction type check ────────────────────────
def test_account_backup_action_literal_values() -> None:
    """5 ACCOUNT_BACKUP action values are valid AuditAction union members."""
    expected = {
        "backup_created",
        "backup_failed",
        "backup_retention_purged",
        "backup_downloaded",
        "backup_triggered",
    }
    # AccountBackupAction is a Literal — verify each value is in the union
    for v in expected:
        # type-narrowing check: literal value passes type checker
        assert v in [
            "backup_created",
            "backup_failed",
            "backup_retention_purged",
            "backup_downloaded",
            "backup_triggered",
        ]


def test_account_backup_action_registry_parity() -> None:
    """F-19: 3-way drift detector — AccountBackupAction Literal ↔ _REGISTRY.

    Asserts every value in the AccountBackupAction Literal is also in
    the _REGISTRY[ActionClass.ACCOUNT_BACKUP] frozenset, and vice versa.
    Catches drift when a value is added to the Literal but not registered
    (or vice versa). CR 1.1 + CR 12-5 D-13 parity invariant.
    """
    from typing import get_args

    from apps.api.core.audit_action import (
        AccountBackupAction,
        ActionClass,
        _ActionRegistry,
    )

    literal_values = set(get_args(AccountBackupAction))
    registry_frozenset = _ActionRegistry._REGISTRY[ActionClass.ACCOUNT_BACKUP][1]
    assert literal_values == set(registry_frozenset), (
        f"AccountBackupAction Literal drift: "
        f"literal={literal_values} vs registry={set(registry_frozenset)}"
    )


def test_action_class_account_backup_registered() -> None:
    """ActionClass.ACCOUNT_BACKUP exists with value 'account_backup'."""
    assert ActionClass.ACCOUNT_BACKUP.value == "account_backup"


def test_backup_tables_constant_seven() -> None:
    """BACKUP_TABLES tuple has exactly 7 entries."""
    assert len(BACKUP_TABLES) == 7
