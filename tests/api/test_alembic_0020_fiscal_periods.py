"""tests.api.test_alembic_0020_fiscal_periods — Story 11.2 migration tests.

8 cases per AC #9 spec — verify the Alembic 0020 migration shape:
- revision / down_revision attributes
- upgrade() emits CREATE TABLE fiscal_periods + CHECK constraints
- down_revision = '0019_m11_reversal_ledger' (11-1 wire tip)
- 5 expected CHECK constraints are referenced
- UNIQUE (tenant_id, period_key) constraint
- 2 INDEX entries (tenant_period + close_sequence_state)
- downgrade() drops both INDEX entries and the table
"""

from __future__ import annotations

import importlib
from pathlib import Path

# Lazy-load migration module to avoid alembic env side effects.
_MIGRATION_PATH = (
    "apps.api.alembic.versions.0020_fiscal_periods_close_sequence"
)


def _load_migration_module() -> object:
    """Import the 0020 migration module by file path.

    Alembic migration files don't follow the apps.api. package layout
    (they live in `apps/api/alembic/versions/`), so we load by file
    location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0020_fiscal_periods_close_sequence.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0020",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_migration_revision_attribute() -> None:
    m = _load_migration_module()
    assert m.revision == "0020_fiscal_periods_close_sequence"


def test_migration_down_revision_is_11_1_tip() -> None:
    """down_revision must be '0019_m11_reversal_ledger' (11-1 wire tip)."""
    m = _load_migration_module()
    assert m.down_revision == "0019_m11_reversal_ledger"


def test_migration_upgrade_function_exists() -> None:
    m = _load_migration_module()
    assert callable(m.upgrade)
    assert callable(m.downgrade)


def test_migration_creates_fiscal_periods_table() -> None:
    """upgrade() emits CREATE TABLE IF NOT EXISTS fiscal_periods.

    We can't actually run upgrade() (no live DB), but we can introspect
    the source via importlib and confirm the file references the table.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0020_fiscal_periods_close_sequence.py"
    ).read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS fiscal_periods" in src
    assert "ALTER TABLE fiscal_periods" not in src.split("def downgrade")[0]


def test_migration_includes_required_check_constraints() -> None:
    """upgrade() SQL must reference 5 required CHECK constraints."""
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0020_fiscal_periods_close_sequence.py"
    ).read_text(encoding="utf-8")
    expected = (
        "fiscal_periods_status_check",
        "fiscal_periods_close_sequence_state_check",
        "fiscal_periods_divisions_ordering_check",
        "fiscal_periods_manufacturing_ordering_check",
        "fiscal_periods_abc_ordering_check",
        "fiscal_periods_confirmed_requires_closed_check",
        "fiscal_periods_closed_requires_closed_at_check",
    )
    for c in expected:
        assert c in src, f"CHECK constraint {c} missing in migration source"


def test_migration_creates_unique_tenant_period() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0020_fiscal_periods_close_sequence.py"
    ).read_text(encoding="utf-8")
    assert "UNIQUE (tenant_id, period_key)" in src
    assert "fiscal_periods_tenant_period_unique" in src


def test_migration_creates_two_indexes() -> None:
    """idx_fiscal_periods_tenant_period + idx_fiscal_periods_close_sequence_state."""
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0020_fiscal_periods_close_sequence.py"
    ).read_text(encoding="utf-8")
    assert "idx_fiscal_periods_tenant_period" in src
    assert "idx_fiscal_periods_close_sequence_state" in src
    assert src.count("CREATE INDEX IF NOT EXISTS") == 2


def test_migration_downgrade_drops_indexes_and_table() -> None:
    """downgrade() drops both indexes + the table."""
    repo_root = Path(__file__).resolve().parents[2]
    src = (
        repo_root
        / "apps"
        / "api"
        / "alembic"
        / "versions"
        / "0020_fiscal_periods_close_sequence.py"
    ).read_text(encoding="utf-8")
    down_section = src.split("def downgrade")[1]
    assert "DROP INDEX IF EXISTS idx_fiscal_periods_close_sequence_state" in down_section
    assert "DROP INDEX IF EXISTS idx_fiscal_periods_tenant_period" in down_section
    assert "DROP TABLE IF EXISTS fiscal_periods" in down_section
