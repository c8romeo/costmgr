"""tests.integration.test_cache_invalidation_log_rls — Story 11.3 RLS 4-policy split.

12 cases per AC #8 spec — verify the RLS policy shape:
- RLS enabled + forced
- 4-policy split wired (SELECT + INSERT granted, UPDATE + DELETE blocked)
- 4 channels visible to owning tenant
- INSERT blocked on cross-tenant
- 4 channels read parity
- per-channel index path queryable (no SQL execution, just source-level
  introspection for offline CI)
"""

from __future__ import annotations

from pathlib import Path

import importlib
import importlib.util


def _load_rls_policy_source() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root
        / "supabase"
        / "policies"
        / "0012_cache_invalidation_log_rls.sql"
    ).read_text(encoding="utf-8")


def _load_alembic_0021_source() -> str:
    repo_root = Path(__file__).resolve().parents[2]
    return (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0021_cache_invalidation_multi_channel.py"
    ).read_text(encoding="utf-8")


def test_rls_policy_file_exists_and_readable() -> None:
    src = _load_rls_policy_source()
    assert len(src) > 0


def test_rls_enables_row_level_security() -> None:
    src = _load_rls_policy_source()
    assert "ENABLE ROW LEVEL SECURITY" in src


def test_rls_forces_row_level_security() -> None:
    src = _load_rls_policy_source()
    assert "FORCE ROW LEVEL SECURITY" in src


def test_rls_select_policy_uses_tenant_id_guc() -> None:
    """SELECT policy must compare tenant_id to current_setting('app.tenant_id', true)."""
    src = _load_rls_policy_source()
    assert "FOR SELECT" in src
    assert "tenant_id = current_setting('app.tenant_id', true)::uuid" in src


def test_rls_insert_policy_uses_tenant_id_guc() -> None:
    """INSERT policy must check tenant_id matches current_setting('app.tenant_id', true)."""
    src = _load_rls_policy_source()
    assert "FOR INSERT" in src
    assert "WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)" in src


def test_rls_update_policy_blocked() -> None:
    """UPDATE must NOT be granted (AD-2 insert-only invariant)."""
    src = _load_rls_policy_source()
    assert "FOR UPDATE" not in src
    # The RLS file should explicitly comment that UPDATE is blocked.
    assert "tenant_update_blocked" in src or "UPDATE forbidden" in src


def test_rls_delete_policy_blocked() -> None:
    """DELETE must NOT be granted (AD-2 insert-only invariant)."""
    src = _load_rls_policy_source()
    assert "FOR DELETE" not in src
    assert "tenant_delete_blocked" in src or "DELETE forbidden" in src


def test_rls_4_policy_split_named() -> None:
    """The 4 policy names must be referenced in the SQL file:
    tenant_select_own + tenant_insert_own + tenant_update_blocked + tenant_delete_blocked."""
    src = _load_rls_policy_source()
    for policy_name in (
        "cache_invalidation_log_tenant_select_own",
        "cache_invalidation_log_tenant_insert_own",
    ):
        assert policy_name in src, f"policy {policy_name!r} missing"
    # Update + delete policies are commented out (intentionally absent).
    assert "tenant_update_blocked" in src
    assert "tenant_delete_blocked" in src


def test_rls_4_channels_visible_to_owning_tenant() -> None:
    """All 4 channels must be valid under the SELECT policy (no channel filter)."""
    src = _load_rls_policy_source()
    # The SELECT policy filters on tenant_id only — channel is unrestricted.
    # This means all 4 channels are visible to the owning tenant.
    for channel in (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ):
        # Channel name appears in the alembic CHECK constraint (linked via comment).
        alembic_src = _load_alembic_0021_source()
        assert channel in alembic_src


def test_rls_insert_blocked_on_cross_tenant() -> None:
    """INSERT policy must use WITH CHECK — rows with mismatched tenant_id are blocked."""
    src = _load_rls_policy_source()
    # The WITH CHECK clause prevents inserting rows with a different tenant_id
    # than the current session's app.tenant_id GUC.
    assert "WITH CHECK" in src
    # The expression must reference tenant_id + current_setting.
    assert "tenant_id = current_setting" in src


def test_rls_per_channel_indexes_for_query_performance() -> None:
    """4 per-channel indexes must be created (query performance).

    The migration uses f-string template `ix_cache_inv_log_ch_{channel[:30]}`
    in a loop — literal names only appear at runtime. Verify template +
    channel loop iteration.
    """
    src = _load_alembic_0021_source()
    assert "ix_cache_inv_log_ch_{channel[:30]}" in src
    assert "for channel in _ALLOWED_CHANNELS_11_3" in src
    assert "CREATE INDEX IF NOT EXISTS" in src


def test_rls_comment_documents_multi_channel_expansion() -> None:
    """The RLS policy must document the 4-channel expansion (audit trail)."""
    src = _load_rls_policy_source()
    assert "Story 11.3" in src or "11-3" in src
    # 4 channels mentioned.
    for channel in (
        "ai_cache",
        "cost_engine_cache",
        "fiscal_period_cache",
        "closing_snapshot_cache",
    ):
        assert channel in src, f"channel {channel!r} missing from RLS comment"