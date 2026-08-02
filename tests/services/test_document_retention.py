"""tests.services.test_document_retention — 90-day soft-delete cron logic.

Story 1.3 — Task 5 (cron boundary).

Tests the pure orchestration:
- Documents older than `DOCUMENT_RETENTION_DAYS` → soft-deleted
- Documents newer than the window → left alone
- Already soft-deleted documents → not re-touched (idempotency)
- Empty result → no audit row, no error

These tests stub the AsyncSession + emit_audit_typed, so they run without a
DB. Real DB integration is covered by RLS tests (test_ai_documents_input_drafts).

Note: pytest-asyncio is NOT in this repo's dependency set (pyproject.toml
comment line 143: "driven via asyncio.run — no pytest-asyncio plugin
needed"). So we wrap each coroutine in `asyncio.run()` synchronously.

A5 migration (Story 4.3 T4): emit_audit → emit_audit_typed. The patched
attribute reflects the A5 single-source-of-truth migration.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.modules.m10_ai import config as m10_config
from apps.api.modules.m10_ai.service import run_document_retention


def _make_doc(*, uploaded_at: datetime, deleted_at: datetime | None = None) -> MagicMock:
    doc = MagicMock()
    doc.uploaded_at = uploaded_at
    doc.deleted_at = deleted_at
    doc.document_id = uuid.uuid4()
    doc.tenant_id = uuid.uuid4()
    return doc


def _make_session_mock(rows: list[MagicMock]) -> AsyncMock:
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = rows
    execute_result = MagicMock()
    execute_result.scalars.return_value = scalars_mock
    session = AsyncMock()
    session.execute.return_value = execute_result
    return session


def test_retention_soft_deletes_old_documents() -> None:
    """Documents older than 90 days → deleted_at set to `now`."""
    now = datetime.now(tz=UTC)
    old_doc = _make_doc(uploaded_at=now - timedelta(days=91))
    new_doc = _make_doc(uploaded_at=now - timedelta(days=89))
    session = _make_session_mock([old_doc])

    with patch(
        "apps.api.modules.m10_ai.service.emit_audit_typed", new=AsyncMock()
    ) as mock_audit:
        result = asyncio.run(run_document_retention(session, now=now))

    assert result.soft_deleted_documents == 1
    assert old_doc.deleted_at == now
    assert new_doc.deleted_at is None  # not touched
    assert mock_audit.await_count == 1


def test_retention_is_idempotent() -> None:
    """Re-running with the same `now` is a no-op (WHERE clause excludes soft-deleted)."""
    now = datetime.now(tz=UTC)
    already_deleted = _make_doc(
        uploaded_at=now - timedelta(days=100),
        deleted_at=now - timedelta(days=10),  # already deleted
    )
    session = _make_session_mock([])  # WHERE clause filters out deleted

    with patch(
        "apps.api.modules.m10_ai.service.emit_audit_typed", new=AsyncMock()
    ) as mock_audit:
        result = asyncio.run(run_document_retention(session, now=now))

    assert result.soft_deleted_documents == 0
    assert already_deleted.deleted_at == now - timedelta(days=10)  # unchanged
    # No audit row when nothing changed
    assert mock_audit.await_count == 0


def test_retention_window_matches_config() -> None:
    """`DOCUMENT_RETENTION_DAYS` is the cutoff; test config is 90."""
    assert m10_config.DOCUMENT_RETENTION_DAYS == 90


def test_retention_cutoff_is_now_minus_window() -> None:
    """`cutoff` returned in result = now - 90 days (UTC)."""
    now = datetime.now(tz=UTC)
    session = _make_session_mock([])

    with patch("apps.api.modules.m10_ai.service.emit_audit_typed", new=AsyncMock()):
        result = asyncio.run(run_document_retention(session, now=now))

    expected_cutoff = now - timedelta(days=m10_config.DOCUMENT_RETENTION_DAYS)
    # Allow a 2-second slop for the isoformat/fromtimestamp round-trip.
    assert abs((result.cutoff - expected_cutoff).total_seconds()) < 2

