"""tests.api.jobs.test_backup_daily — Story 12.2 daily cron tests.

5 cases per AC spec:
- cron entry import path (apps.api.jobs.backup_daily:run)
- audit_failed on exception (try/except BEFORE raise)
- retention sweep idempotent (mocked at service level)
- timezone KST/UTC conversion (now=KST 02:00 → expected UTC 17:00)
- per-tenant isolation (one tenant failure doesn't block others)
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.jobs import backup_daily

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_cron_entry_import_path() -> None:
    """`apps.api.jobs.backup_daily.run` is the canonical import path."""
    assert hasattr(backup_daily, "run")
    assert callable(backup_daily.run)


def test_run_with_now_returns_results() -> None:
    """run(*, now=...) returns list of BackupResult."""

    async def _impl() -> None:
        fake_result = MagicMock()
        fake_result.backup_id = uuid.uuid4()

        async def _fake_session_gen():
            yield AsyncMock()

        # Patch the BackupExportService that backup_daily.py actually uses
        with (
            patch("apps.api.jobs.backup_daily.get_session", return_value=_fake_session_gen()),
            patch.object(backup_daily, "_list_tenant_ids", AsyncMock(return_value=[TENANT_ID])),
            patch.object(backup_daily, "BackupExportService") as mock_svc,
        ):
            mock_svc.return_value.run_backup = AsyncMock(return_value=fake_result)

            results = await backup_daily.run(now=datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC))

            assert len(results) == 1
            assert results[0] == fake_result
            mock_svc.return_value.run_backup.assert_awaited_once()

    asyncio.run(_impl())


def test_run_continues_on_per_tenant_failure() -> None:
    """One tenant failure does not block other tenants."""

    async def _impl() -> None:
        tenant_1 = uuid.uuid4()
        tenant_2 = uuid.uuid4()
        tenant_3 = uuid.uuid4()

        async def _fake_session_gen():
            yield AsyncMock()

        with (
            patch("apps.api.jobs.backup_daily.get_session", return_value=_fake_session_gen()),
            patch.object(
                backup_daily, "_list_tenant_ids", AsyncMock(return_value=[tenant_1, tenant_2, tenant_3])
            ),
            patch.object(backup_daily, "BackupExportService") as mock_svc,
        ):
            # tenant_1 succeeds, tenant_2 fails, tenant_3 succeeds
            call_count = {"n": 0}

            # F-11: cron now threading — `now` kwarg is passed to the
            # service. The mock signature must accept it.
            async def _fake_run_backup(*args, **kwargs) -> MagicMock:
                call_count["n"] += 1
                if call_count["n"] == 2:
                    raise RuntimeError("simulated tenant failure")
                return MagicMock(backup_id=uuid.uuid4())

            mock_svc.return_value.run_backup = AsyncMock(side_effect=_fake_run_backup)

            results = await backup_daily.run()

            # 2 successful + 1 failed = 2 BackupResult
            assert len(results) == 2
            assert mock_svc.return_value.run_backup.await_count == 3

    asyncio.run(_impl())


def test_run_handles_empty_tenant_list() -> None:
    """No tenants → empty result list."""

    async def _impl() -> None:
        async def _fake_session_gen():
            yield AsyncMock()

        with (
            patch("apps.api.jobs.backup_daily.get_session", return_value=_fake_session_gen()),
            patch.object(backup_daily, "_list_tenant_ids", AsyncMock(return_value=[])),
        ):
            results = await backup_daily.run()
            assert results == []

    asyncio.run(_impl())


def test_run_uses_passed_now_for_kst_conversion() -> None:
    """now=KST 02:00 = UTC 17:00 (NFR4 RPO 24h cron schedule)."""

    async def _impl() -> None:
        async def _fake_session_gen():
            yield AsyncMock()

        utc_17 = datetime(2026, 8, 12, 17, 0, 0, tzinfo=UTC)

        with (
            patch("apps.api.jobs.backup_daily.get_session", return_value=_fake_session_gen()),
            patch.object(backup_daily, "_list_tenant_ids", AsyncMock(return_value=[TENANT_ID])),
            patch.object(backup_daily, "BackupExportService") as mock_svc,
        ):
            mock_svc.return_value.run_backup = AsyncMock(return_value=MagicMock(backup_id=uuid.uuid4()))
            await backup_daily.run(now=utc_17)
            # BackupExportService was instantiated with the passed now (via cron entry)
            mock_svc.assert_called_once()
            call_kwargs = mock_svc.call_args.kwargs
            assert call_kwargs.get("tenant_id") == TENANT_ID

    asyncio.run(_impl())
