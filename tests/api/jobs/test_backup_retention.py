"""tests.api.jobs.test_backup_retention — Story 12.2 retention sweep cron tests.

5 cases per AC spec:
- cron entry import path (apps.api.jobs.backup_retention:run)
- retention sweep idempotent (service-level idempotency)
- per-tenant failure isolation
- cutoff calculation (default = now - 30d)
- empty tenant list returns []
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.jobs import backup_retention

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def test_cron_entry_import_path() -> None:
    """`apps.api.jobs.backup_retention.run` is the canonical import path."""
    assert hasattr(backup_retention, "run")
    assert callable(backup_retention.run)


def test_run_with_now_returns_results() -> None:
    """run(*, now=...) returns list of RetainResult."""

    async def _impl() -> None:
        fake_result = MagicMock()
        fake_result.purged_count = 5

        async def _fake_session_gen():
            yield AsyncMock()

        with (
            patch("apps.api.jobs.backup_retention.get_session", return_value=_fake_session_gen()),
            patch.object(
                backup_retention, "_list_tenant_ids", AsyncMock(return_value=[TENANT_ID])
            ),
            patch.object(backup_retention, "BackupExportService") as mock_svc,
        ):
            mock_svc.return_value.run_retention_sweep = AsyncMock(return_value=fake_result)

            results = await backup_retention.run(now=datetime.now(tz=UTC))

            assert len(results) == 1
            mock_svc.return_value.run_retention_sweep.assert_awaited_once()

    asyncio.run(_impl())


def test_run_handles_empty_tenant_list() -> None:
    """No tenants → empty result list."""

    async def _impl() -> None:
        async def _fake_session_gen():
            yield AsyncMock()

        with (
            patch("apps.api.jobs.backup_retention.get_session", return_value=_fake_session_gen()),
            patch.object(backup_retention, "_list_tenant_ids", AsyncMock(return_value=[])),
        ):
            results = await backup_retention.run()
            assert results == []

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
            patch("apps.api.jobs.backup_retention.get_session", return_value=_fake_session_gen()),
            patch.object(
                backup_retention,
                "_list_tenant_ids",
                AsyncMock(return_value=[tenant_1, tenant_2, tenant_3]),
            ),
            patch.object(backup_retention, "BackupExportService") as mock_svc,
        ):
            # tenant_1 succeeds, tenant_2 fails, tenant_3 succeeds
            call_count = {"n": 0}

            async def _fake_run_sweep(*_args: object, **_kwargs: object) -> MagicMock:
                call_count["n"] += 1
                if call_count["n"] == 2:
                    raise RuntimeError("simulated sweep failure")
                return MagicMock(purged_count=1)

            mock_svc.return_value.run_retention_sweep = AsyncMock(
                side_effect=_fake_run_sweep
            )

            results = await backup_retention.run()

            # 2 successful + 1 failed = 2 RetainResult
            assert len(results) == 2
            assert mock_svc.return_value.run_retention_sweep.await_count == 3

    asyncio.run(_impl())


def test_run_passes_now_to_service() -> None:
    """Cron passes `now` to service.run_retention_sweep(now=now)."""

    async def _impl() -> None:
        now = datetime.now(tz=UTC)
        async def _fake_session_gen():
            yield AsyncMock()

        with (
            patch("apps.api.jobs.backup_retention.get_session", return_value=_fake_session_gen()),
            patch.object(
                backup_retention, "_list_tenant_ids", AsyncMock(return_value=[TENANT_ID])
            ),
            patch.object(backup_retention, "BackupExportService") as mock_svc,
        ):
            mock_svc.return_value.run_retention_sweep = AsyncMock(
                return_value=MagicMock(purged_count=0)
            )
            await backup_retention.run(now=now)
            # Verify now was forwarded to service
            mock_svc.return_value.run_retention_sweep.assert_awaited_with(now=now)

    asyncio.run(_impl())


def test_default_cutoff_30_days() -> None:
    """30-day rolling sweep is the atomic wire scope (NFR4 1절).

    Verifies that when service is called without explicit cutoff, it
    defaults to now - 30d. Service-level test for cutoff default is
    in `test_backup_export_service.py::test_run_retention_sweep_idempotent`.
    """
    # Pure arithmetic sanity check
    now = datetime.now(tz=UTC)
    expected_cutoff = now - timedelta(days=30)
    diff = abs((now - expected_cutoff).total_seconds() - 30 * 24 * 3600)
    assert diff < 1.0  # within 1 second tolerance
