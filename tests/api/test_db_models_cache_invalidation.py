"""tests.api.test_db_models_cache_invalidation — Story 11.3 ORM/table introspection.

6 cases per AC #8 spec — verify the cache_invalidation_log table shape:
- Table exists in db_models / Alembic mirror
- 4 channels: ai_cache + cost_engine_cache + fiscal_period_cache +
  closing_snapshot_cache (CHECK constraint)
- target_event_id NOT NULL
- correction_group_id NOT NULL (per AD-22: every receipt is part of a
  reversal pair chain; even single-channel broadcasts carry a
  correction_group_id for traceability)
- trace_id UUID NOT NULL (AD-24 + 11-1 wire convention)
- RLS policy 4-policy split (supabase/policies/0012)
"""

from __future__ import annotations

import importlib
from pathlib import Path


def _load_alembic_0019_source() -> str:
    """Read the 11.1 Alembic 0019 source (defines cache_invalidation_log)."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0019_m11_reversal_ledger.py"
    ).read_text(encoding="utf-8")


def _load_alembic_0021_source() -> str:
    """Read the 11.3 Alembic 0021 source (extends channel CHECK)."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    ).read_text(encoding="utf-8")


def _load_rls_policy_source() -> str:
    """Read the 11.3 RLS policy file."""
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root
        / "supabase"
        / "policies"
        / "0012_cache_invalidation_log_rls.sql"
    ).read_text(encoding="utf-8")


def test_cache_invalidation_log_table_columns_present() -> None:
    """cache_invalidation_log must define receipt_id, tenant_id, channel,
    target_event_id, correction_group_id, trace_id, published_at."""
    src = _load_alembic_0019_source()
    for col in (
        "receipt_id",
        "tenant_id",
        "channel",
        "target_event_id",
        "correction_group_id",
        "trace_id",
        "published_at",
    ):
        assert col in src, f"column {col!r} missing from cache_invalidation_log"


def test_cache_invalidation_log_channel_constraint_4_values_11_3() -> None:
    """Alembic 0021 must reference the 4-channel CHECK constraint."""
    src = _load_alembic_0021_source()
    for channel in (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ):
        assert channel in src, (
            f"channel {channel!r} missing from 0021 migration CHECK"
        )


def test_target_event_id_not_null_in_cache_invalidation_log() -> None:
    """target_event_id is NOT NULL — every receipt points to a target event."""
    src = _load_alembic_0019_source()
    # Find the column definition for target_event_id.
    # Expect: target_event_id      UUID NOT NULL
    assert "target_event_id" in src
    # Find the line with target_event_id NOT NULL marker.
    for line in src.splitlines():
        if "target_event_id" in line and "UUID" in line:
            assert "NOT NULL" in line, (
                f"target_event_id must be NOT NULL, got: {line!r}"
            )
            return
    raise AssertionError("target_event_id column line not found")


def test_correction_group_id_not_null_in_cache_invalidation_log() -> None:
    """correction_group_id is NOT NULL — per AD-22 reversal pair chain.

    Every cache invalidation receipt in 11-1 wire is part of either a
    single AD-4 commit broadcast or an AD-22 reversal pair (sign-negating
    row + corrected row). All pairs share a non-null correction_group_id
    so consumers can correlate receipts across channels.
    """
    src = _load_alembic_0019_source()
    for line in src.splitlines():
        if "correction_group_id" in line and "UUID" in line:
            assert "NOT NULL" in line, (
                f"correction_group_id must be NOT NULL per AD-22, got: {line!r}"
            )
            return
    raise AssertionError("correction_group_id column line not found")


def test_trace_id_not_null_in_cache_invalidation_log() -> None:
    """trace_id is UUID NOT NULL — every receipt must carry a correlation ID."""
    src = _load_alembic_0019_source()
    for line in src.splitlines():
        if "trace_id" in line and "UUID" in line:
            assert "NOT NULL" in line, (
                f"trace_id must be NOT NULL, got: {line!r}"
            )
            return
    raise AssertionError("trace_id column line not found")


def test_rls_policy_4_policy_split_wired() -> None:
    """supabase/policies/0012 must define 4-policy split
    (SELECT + INSERT granted, UPDATE + DELETE blocked)."""
    src = _load_rls_policy_source()
    # 1. SELECT policy
    assert "FOR SELECT" in src, "RLS policy must include SELECT"
    # 2. INSERT policy
    assert "FOR INSERT" in src, "RLS policy must include INSERT"
    # 3. FORCE ROW LEVEL SECURITY
    assert "FORCE ROW LEVEL SECURITY" in src, "RLS must FORCE"
    # 4. UPDATE/DELETE intentionally absent (insert-only)
    assert "FOR UPDATE" not in src, "RLS policy must NOT include UPDATE"
    assert "FOR DELETE" not in src, "RLS policy must NOT include DELETE"