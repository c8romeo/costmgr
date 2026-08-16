"""tests.api.test_alembic_0027_budget_pre_standard — Story 8.3 migration tests.

8 cases — verify the Alembic 0027 migration shape (Story 8.3 follow-up,
PRD §F8.3 + AD-22 + AD-24 + AD-3):

- revision / down_revision attributes
- down_revision = '0026_budget_scenarios' (8-1 wire tip)
- upgrade() extends CHECK constraint to 4 values ('trad' | 'abc' | 'tdabc' | 'budget')
- upgrade() creates idx_fiscal_period_snapshots_engine_type index
- upgrade() idempotent UPDATE for existing rows
- upgrade() COMMENT ON CONSTRAINT for documentation
- downgrade() drops index + CHECK constraint
- 8-3 spec: down_revision wire precedes 0026 (8-1 sprint-up)
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration_module() -> object:
    """Import the 0027 migration module by file path.

    Alembic migration files live in `apps/api/alembic/versions/` (not the
    apps.api. package layout), so we load by file location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions"
        / "0027_budget_pre_standard.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0027",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ── Revision attributes ────────────────────────────────────────────
def test_revision_id_correct() -> None:
    """revision = '0027_budget_pre_standard' (8-3 wire)."""
    module = _load_migration_module()
    assert module.revision == "0027_budget_pre_standard"


def test_down_revision_0026_budget_scenarios() -> None:
    """down_revision = '0026_budget_scenarios' (8-1 wire tip)."""
    module = _load_migration_module()
    assert module.down_revision == "0026_budget_scenarios"


def test_no_branch_labels_depends_on() -> None:
    """branch_labels / depends_on = None (no branching)."""
    module = _load_migration_module()
    assert module.branch_labels is None
    assert module.depends_on is None


# ── Upgrade shape ──────────────────────────────────────────────────
def test_upgrade_adds_4_value_check_constraint() -> None:
    """upgrade() adds CHECK constraint with 4 values: trad | abc | tdabc | budget."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "CHECK" in source
    assert "'trad'" in source
    assert "'abc'" in source
    assert "'tdabc'" in source
    assert "'budget'" in source
    assert "ck_fiscal_period_snapshots_engine_type" in source


def test_upgrade_creates_engine_type_index() -> None:
    """upgrade() creates idx_fiscal_period_snapshots_engine_type for hot path."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "CREATE INDEX" in source
    assert "idx_fiscal_period_snapshots_engine_type" in source


def test_upgrade_idempotent_update_for_existing_rows() -> None:
    """upgrade() updates existing rows to 'trad' (idempotency guard)."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "UPDATE fiscal_period_snapshots" in source
    assert "engine_type = 'trad'" in source
    assert "NOT IN ('trad', 'abc', 'tdabc', 'budget')" in source


def test_upgrade_includes_comment_on_constraint() -> None:
    """upgrade() documents the constraint with COMMENT ON (NFR18 lock)."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "COMMENT ON CONSTRAINT" in source


# ── Downgrade shape ────────────────────────────────────────────────
def test_downgrade_drops_index_and_check() -> None:
    """downgrade() drops index + CHECK constraint."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "DROP INDEX" in source
    assert "DROP CONSTRAINT" in source
    assert "idx_fiscal_period_snapshots_engine_type" in source
    assert "ck_fiscal_period_snapshots_engine_type" in source
