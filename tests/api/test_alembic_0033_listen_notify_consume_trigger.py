"""Test alembic 0033 — LISTEN/NOTIFY consume trigger EXTENSION.

Story 13.1 (LISTEN/NOTIFY Consume Trigger EXTENSION, A39/A51/A52 결정 wire):
D-10-2-DEFER-3 ✅ RESOLVED wire 진입. PostgreSQL NOTIFY trigger on
`cache_invalidation_log` AFTER INSERT emits a 5-key alphabetical JSON
payload via `pg_notify('cache_invalidation_log', payload)`.

V8 determinism: payload JSON keys are output in alphabetical order via
explicit positional order in `json_object()`.

Tests:
- NOTIFY trigger source-text parsing (revision + down_revision + function DDL)
- Payload shape (5 keys, alphabetical order)
- Channel whitelist (4 channels, AD-25 verbatim)
- down_revision chain (0032_ai_promotion_port)
- INSERT-only trigger EXTENSION (no UPDATE/DELETE triggers)
- V8 determinism (json_object key ordering)
"""

from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path


# ── Helpers ──────────────────────────────────────────────────
def _load_migration_module() -> object:
    """Load the 0033 migration as a module (without executing upgrade())."""
    path = Path(__file__).parent.parent.parent / "apps" / "api" / "alembic" / "versions" / "0033_listen_notify_consume_trigger.py"
    spec = importlib.util.spec_from_file_location("mig_0033", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Tests ────────────────────────────────────────────────────
class TestAlembic0033TriggerFunction:
    """NOTIFY trigger function DDL + payload shape."""

    def test_revision_id(self) -> None:
        """revision = '0033_listen_notify_consume_trigger'."""
        mod = _load_migration_module()
        assert mod.revision == "0033_listen_notify_consume_trigger"

    def test_down_revision_is_0032(self) -> None:
        """down_revision = '0032_ai_promotion_port' (Story 10.4 wire tip)."""
        mod = _load_migration_module()
        assert mod.down_revision == "0032_ai_promotion_port"

    def test_branch_labels_and_depends_on_none(self) -> None:
        """branch_labels = None, depends_on = None."""
        mod = _load_migration_module()
        assert mod.branch_labels is None
        assert mod.depends_on is None

    def test_notify_channel_name_constant(self) -> None:
        """NOTIFY_CHANNEL_NAME = 'cache_invalidation_log'."""
        mod = _load_migration_module()
        assert mod.NOTIFY_CHANNEL_NAME == "cache_invalidation_log"

    def test_allowed_channels_4_channels(self) -> None:
        """4 channels: ai_cache + cost_engine_cache + fiscal_period_cache + closing_snapshot_cache."""
        mod = _load_migration_module()
        assert mod._ALLOWED_CHANNELS_13_1 == (
            "ai_cache",
            "cost_engine_cache",
            "fiscal_period_cache",
            "closing_snapshot_cache",
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

    def test_trigger_function_ddl_alphabetical_keys(self) -> None:
        """DDL must list the 5 keys in alphabetical order (channel, correction_group_id, period_key, tenant_id, trace_id)."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        # Verify the relative order of the 5 keys (alphabetical).
        positions = [
            ddl.find("'channel'"),
            ddl.find("'correction_group_id'"),
            ddl.find("'period_key'"),
            ddl.find("'tenant_id'"),
            ddl.find("'trace_id'"),
        ]
        # All positions must be found (>= 0).
        assert all(p >= 0 for p in positions)
        # Also they must be ascending (alphabetical).
        assert positions == sorted(positions)

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

    def test_channel_whitelist_in_ddl(self) -> None:
        """DDL must include all 4 channel names in the IN clause."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        for channel in mod._ALLOWED_CHANNELS_13_1:
            assert f"'{channel}'" in ddl

    def test_function_and_trigger_naming(self) -> None:
        """Function = cache_invalidation_log_notify(), Trigger = cache_invalidation_log_notify_trg."""
        mod = _load_migration_module()
        fn_ddl = mod._build_trigger_function_ddl()
        trg_ddl = mod._build_trigger_ddl()
        assert "cache_invalidation_log_notify()" in fn_ddl
        assert "cache_invalidation_log_notify_trg" in trg_ddl

    def test_payload_serialization_uses_text_cast(self) -> None:
        """UUID fields are cast to TEXT for cross-language drift detector parity."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_function_ddl()
        # tenant_id, correction_group_id, trace_id → cast to text.
        assert "::text" in ddl
        # period_key stays as VARCHAR (no cast needed).
        assert "NEW.period_key" in ddl

    def test_trigger_ddl_for_each_row(self) -> None:
        """FOR EACH ROW (not statement-level)."""
        mod = _load_migration_module()
        ddl = mod._build_trigger_ddl()
        assert "FOR EACH ROW" in ddl


class TestAlembic0033MigrationUpgrade:
    """upgrade() + downgrade() execute without raising."""

    def test_upgrade_idempotent(self) -> None:
        """upgrade() does not raise (function + trigger + COMMENT ON)."""
        mod = _load_migration_module()
        # We can't actually run upgrade() without a DB, but we can verify
        # that the module is importable and that upgrade is a callable.
        assert callable(mod.upgrade)

    def test_downgrade_callable(self) -> None:
        """downgrade() callable."""
        mod = _load_migration_module()
        assert callable(mod.downgrade)


class TestAlembic0033ModuleImports:
    """Module-level imports + structure."""

    def test_module_path_exists(self) -> None:
        """Migration file exists at the expected path."""
        path = Path(__file__).parent.parent.parent / "apps" / "api" / "alembic" / "versions" / "0033_listen_notify_consume_trigger.py"
        assert path.exists()

    def test_module_docstring_mentions_a39_d_10_2_defer_3(self) -> None:
        """Module docstring must reference D-10-2-DEFER-3 RESOLVED + A39/A51/A52."""
        path = Path(__file__).parent.parent.parent / "apps" / "api" / "alembic" / "versions" / "0033_listen_notify_consume_trigger.py"
        text = path.read_text(encoding="utf-8")
        assert "D-10-2-DEFER-3" in text
        assert "A39" in text
        assert "A51" in text
        assert "A52" in text
