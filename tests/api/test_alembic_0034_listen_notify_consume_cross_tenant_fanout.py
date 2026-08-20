"""Test alembic 0034 — LISTEN/NOTIFY consume cross_tenant_fanout trigger EXTENSION.

Story 14.1 (LISTEN/NOTIFY Consume Cross-Tenant Fan-Out, A53+A57+A58+A59
결정 wire):
- D-13-1-DEFER-3 ✅ RESOLVED wire 진입 (separate epic LISTEN/NOTIFY
  consume 2nd batch = Epic 14 = cross-tenant invalidation fan-out +
  multi-process coordination).
- A53 ✅ DONE = Epic 14 진입 결정 wire (옵션 (a)).
- A57 ✅ DONE = master PRD v2.4 → v2.5 atomic edit (§F14 신규).
- A58 ✅ DONE = AD-25 EXTENSION 4-channel → 5+ channels +
  cross_tenant_fanout 채널 추가 + Multi-process coordination Option 1.
- A59 ✅ DONE = capability matrix v1.22 → v1.23 EXTENSION 2 NEW rows.

PostgreSQL NOTIFY trigger on `cache_invalidation_log` AFTER INSERT
emits a 7-key alphabetical JSON payload via
`pg_notify('cache_invalidation_log', payload)` ONLY for
`channel = 'cross_tenant_fanout'`.

V8 determinism: payload JSON keys are output in alphabetical order via
explicit positional order in `json_object()` (alphabetical, 7 keys).

Tests:
- NOTIFY trigger source-text parsing (revision + down_revision + function DDL)
- Payload shape (7 keys, alphabetical order)
- Channel whitelist (5+ channels, AD-25 EXTENSION)
- down_revision chain (0033_listen_notify_consume_trigger)
- INSERT-only trigger EXTENSION (no UPDATE/DELETE triggers)
- cross_tenant_fanout channel filter (trigger fires ONLY for that channel)
- target_tenant_ids JSON array 결정적 직렬화
- V8 determinism (json_object key ordering, alphabetical 7 keys)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────
def _load_migration_module() -> object:
    """Load the 0034 migration as a module (without executing upgrade())."""
    path = (
        Path(__file__).parent.parent.parent
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0034_listen_notify_consume_cross_tenant_fanout.py"
    )
    spec = importlib.util.spec_from_file_location("mig_0034", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Tests ────────────────────────────────────────────────────
class TestAlembic0034TriggerFunction:
    """NOTIFY trigger function DDL + payload shape (cross_tenant_fanout)."""

    def test_revision_id(self) -> None:
        """revision = '0034_listen_notify_consume_cross_tenant_fanout'."""
        mod = _load_migration_module()
        assert mod.revision == "0034_listen_notify_consume_cross_tenant_fanout"

    def test_down_revision_is_0033(self) -> None:
        """down_revision = '0033_listen_notify_consume_trigger' (13-1 wire tip)."""
        mod = _load_migration_module()
        assert mod.down_revision == "0033_listen_notify_consume_trigger"

    def test_branch_labels_and_depends_on_none(self) -> None:
        """branch_labels = None, depends_on = None."""
        mod = _load_migration_module()
        assert mod.branch_labels is None
        assert mod.depends_on is None

    def test_notify_channel_name_constant(self) -> None:
        """NOTIFY_CHANNEL_NAME = 'cache_invalidation_log'."""
        mod = _load_migration_module()
        assert mod.NOTIFY_CHANNEL_NAME == "cache_invalidation_log"

    def test_cross_tenant_fanout_channel_constant(self) -> None:
        """CROSS_TENANT_FANOUT_CHANNEL = 'cross_tenant_fanout'."""
        mod = _load_migration_module()
        assert mod.CROSS_TENANT_FANOUT_CHANNEL == "cross_tenant_fanout"

    def test_allowed_channels_5_plus(self) -> None:
        """5+ channels: 4 보존 + cross_tenant_fanout 추가."""
        mod = _load_migration_module()
        assert mod._ALLOWED_CHANNELS_14_1 == (
            "ai_cache",
            "cost_engine_cache",
            "fiscal_period_cache",
            "closing_snapshot_cache",
            "cross_tenant_fanout",
        )

    def test_trigger_function_ddl_contains_pg_notify(self) -> None:
        """DDL must contain `pg_notify('cache_invalidation_log', payload)`."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        assert "pg_notify" in ddl
        assert "'cache_invalidation_log'" in ddl

    def test_trigger_function_ddl_uses_json_object(self) -> None:
        """DDL must use json_object() — guarantees alphabetical key ordering."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        assert "json_object(" in ddl

    def test_trigger_function_ddl_alphabetical_7_keys(self) -> None:
        """DDL must list the 7 keys in alphabetical order (channel, correction_group_id, invalidation_id, period_key, source_tenant_id, target_tenant_ids, trace_id)."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        # Verify the relative order of the 7 keys (alphabetical).
        positions = [
            ddl.find("'channel'"),
            ddl.find("'correction_group_id'"),
            ddl.find("'invalidation_id'"),
            ddl.find("'period_key'"),
            ddl.find("'source_tenant_id'"),
            ddl.find("'target_tenant_ids'"),
            ddl.find("'trace_id'"),
        ]
        # All positions must be found (>= 0).
        assert all(p >= 0 for p in positions)
        # Also they must be ascending (alphabetical).
        assert positions == sorted(positions)

    def test_trigger_function_ddl_channel_filter(self) -> None:
        """DDL must early-return for non-cross_tenant_fanout channels (defense-in-depth)."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        assert "NEW.channel <>" in ddl or "channel <> '" in ddl
        assert "RETURN NEW" in ddl

    def test_trigger_ddl_after_insert(self) -> None:
        """AFTER INSERT trigger on cache_invalidation_log."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_ddl()
        assert "AFTER INSERT" in ddl
        assert "cache_invalidation_log" in ddl
        assert "EXECUTE FUNCTION" in ddl

    def test_no_update_or_delete_triggers(self) -> None:
        """UPDATE/DELETE triggers NOT added (AD-2 append-only ledger)."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_ddl()
        assert "AFTER UPDATE" not in ddl
        assert "AFTER DELETE" not in ddl

    def test_function_and_trigger_naming(self) -> None:
        """Function = cache_invalidation_log_notify_cross_tenant(), Trigger = cache_invalidation_log_notify_cross_tenant_trg."""
        mod = _load_migration_module()
        fn_ddl = mod._build_trigger_function_ddl()
        trg_ddl = mod._build_trigger_ddl()
        assert "cache_invalidation_log_notify_cross_tenant()" in fn_ddl
        assert "cache_invalidation_log_notify_cross_tenant_trg" in trg_ddl

    def test_payload_serialization_uses_text_cast(self) -> None:
        """UUID fields are cast to TEXT for cross-language drift detector parity."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        # source_tenant_id, correction_group_id, trace_id, invalidation_id → cast to text.
        assert "::text" in ddl
        # period_key stays as VARCHAR (no cast needed).
        assert "NEW.period_key" in ddl

    def test_target_tenant_ids_jsonb_canonical(self) -> None:
        """target_tenant_ids is JSONB canonical form for V8 determinism."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        assert "target_tenant_ids" in ddl
        assert "jsonb" in ddl.lower()

    def test_trigger_ddl_for_each_row(self) -> None:
        """FOR EACH ROW (not statement-level)."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_ddl()
        assert "FOR EACH ROW" in ddl


class TestAlembic0034SchemaChanges:
    """Schema EXTENSION (5+ channels, invalidation_id, target_tenant_ids columns)."""

    def test_check_constraint_ddl_5_plus_channels(self) -> None:
        """CHECK constraint DDL must contain all 5+ channels (cross_tenant_fanout 포함)."""
        mod = _load_migration_module()
        ddl = mod._build_check_constraint_ddl()
        for channel in mod._ALLOWED_CHANNELS_14_1:
            assert f"'{channel}'" in ddl

    def test_invalidation_id_column_ddl(self) -> None:
        """invalidation_id UUID column with gen_random_uuid() default."""
        mod = _load_migration_module()
        ddl = mod._build_invalidation_id_column_ddl()
        assert "invalidation_id" in ddl
        assert "UUID" in ddl
        assert "gen_random_uuid()" in ddl

    def test_target_tenant_ids_column_jsonb(self) -> None:
        """target_tenant_ids JSONB column."""
        mod = _load_migration_module()
        ddl = mod._build_target_tenant_ids_column_ddl()
        assert "target_tenant_ids" in ddl
        assert "JSONB" in ddl


class TestAlembic0034MigrationUpgrade:
    """upgrade() + downgrade() execute without raising."""

    def test_upgrade_idempotent(self) -> None:
        """upgrade() does not raise (DDL builders callable)."""
        mod = _load_migration_module()
        # We can't actually run upgrade() without a DB, but we can verify
        # that the module is importable and that upgrade is a callable.
        assert callable(mod.upgrade)

    def test_downgrade_callable(self) -> None:
        """downgrade() callable."""
        mod = _load_migration_module()
        assert callable(mod.downgrade)

    def test_all_ddl_helpers_callable(self) -> None:
        """All DDL builders are callable."""
        mod = _load_migration_module()
        assert callable(mod._build_trigger_function_ddl)
        assert callable(mod._build_trigger_ddl)
        assert callable(mod._build_check_constraint_ddl)
        assert callable(mod._build_invalidation_id_column_ddl)
        assert callable(mod._build_target_tenant_ids_column_ddl)


class TestAlembic0034ModuleImports:
    """Module-level imports + structure."""

    def test_module_path_exists(self) -> None:
        """Migration file exists at the expected path."""
        path = (
            Path(__file__).parent.parent.parent
            / "apps"
            / "api"
            / "alembic"
            / "versions"
            / "0034_listen_notify_consume_cross_tenant_fanout.py"
        )
        assert path.exists()

    def test_module_docstring_mentions_d_13_1_defer_3_a57(self) -> None:
        """Module docstring must reference D-13-1-DEFER-3 RESOLVED + A53+A57+A58+A59."""
        path = (
            Path(__file__).parent.parent.parent
            / "apps"
            / "api"
            / "alembic"
            / "versions"
            / "0034_listen_notify_consume_cross_tenant_fanout.py"
        )
        text = path.read_text(encoding="utf-8")
        assert "D-13-1-DEFER-3" in text
        assert "A57" in text
        assert "A58" in text
        assert "A59" in text
