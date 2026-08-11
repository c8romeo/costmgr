"""tests.api.test_alembic_0023_used_challenge_tokens — Story 12.4 review P-05 test.

4 cases — verify the Alembic 0023 migration shape (Epic 12 carry-over sprint,
review P-05 replay guard):

- revision / down_revision attributes
- down_revision = '0022_users_totp_columns' (12-4 wire tip)
- upgrade() creates `used_challenge_tokens` table with jti PK
- upgrade() adds used_at + tenant_id indexes for GC sweep
- downgrade() drops the table
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_MIGRATION_FILENAME = "0023_used_challenge_tokens.py"


def _load_migration_module() -> object:
    """Import the 0023 migration module by file path."""
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions" / _MIGRATION_FILENAME
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0023",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_migration_0023_revision_and_down_revision() -> None:
    """Migration 0023 has the correct revision/down_revision chain."""
    module = _load_migration_module()
    assert module.revision == "0023_used_challenge_tokens"
    assert module.down_revision == "0022_users_totp_columns"


def test_migration_0023_creates_used_challenge_tokens_table() -> None:
    """upgrade() calls CREATE TABLE for used_challenge_tokens."""
    import inspect

    module = _load_migration_module()
    src = inspect.getsource(module.upgrade)
    assert "CREATE TABLE used_challenge_tokens" in src
    assert "jti TEXT PRIMARY KEY" in src
    assert "user_id UUID NOT NULL" in src
    assert "tenant_id UUID NOT NULL" in src
    assert "used_at TIMESTAMPTZ NOT NULL DEFAULT now()" in src


def test_migration_0023_creates_indexes() -> None:
    """upgrade() creates indexes for GC sweep + per-tenant tenant_id lookup."""
    import inspect

    module = _load_migration_module()
    src = inspect.getsource(module.upgrade)
    assert "used_challenge_tokens_used_at_idx" in src
    assert "used_challenge_tokens_tenant_id_idx" in src


def test_migration_0023_downgrade_drops_table() -> None:
    """downgrade() drops the used_challenge_tokens table."""
    import inspect

    module = _load_migration_module()
    src = inspect.getsource(module.downgrade)
    assert "DROP TABLE IF EXISTS used_challenge_tokens" in src
