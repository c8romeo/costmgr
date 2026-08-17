"""tests.api.test_alembic_0028_abc_fiscal_period_breakdown — Story 9.3 migration tests.

7 cases — verify the Alembic 0028 migration shape (Story 9.3 wire,
PRD §F9.3 + A29 forward-lock dual-route + AD-22 + NFR18 lock):

- revision / down_revision attributes
- down_revision = '0027_budget_pre_standard' (8-3 wire tip)
- upgrade() ADD COLUMN cost_object_breakdown JSONB
- upgrade() ADD COLUMN unused_capacity_breakdown JSONB
- upgrade() creates 2 GIN indexes (jsonb_path_ops) for both JSONB columns
- upgrade() COMMENT ON COLUMN documentation (NFR18 lock)
- downgrade() drops indexes then columns in reverse order
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration_module() -> object:
    """Import the 0028 migration module by file path.

    Alembic migration files live in `apps/api/alembic/versions/` (not the
    apps.api. package layout), so we load by file location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions"
        / "0028_abc_fiscal_period_breakdown.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0028",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ── Revision attributes ────────────────────────────────────────────


def test_revision_id_correct() -> None:
    """revision = '0028_abc_fiscal_period_breakdown' (9-3 wire)."""
    module = _load_migration_module()
    assert module.revision == "0028_abc_fiscal_period_breakdown"


def test_down_revision_0027_budget_pre_standard() -> None:
    """down_revision = '0027_budget_pre_standard' (8-3 wire tip).

    9-3 wire precedes 9-4 forward-lock (PRD §F9.3 + A29 forward-lock 결정).
    """
    module = _load_migration_module()
    assert module.down_revision == "0027_budget_pre_standard"


def test_no_branch_labels_depends_on() -> None:
    """branch_labels / depends_on = None (no branching)."""
    module = _load_migration_module()
    assert module.branch_labels is None
    assert module.depends_on is None


# ── upgrade() SQL contract ──────────────────────────────────────────


def test_upgrade_adds_cost_object_breakdown_jsonb_column() -> None:
    """upgrade() ADD COLUMN cost_object_breakdown JSONB (PRD §F9.3 + §A6)."""
    module = _load_migration_module()
    src = Path(module.__file__).read_text(encoding="utf-8")
    assert "ADD COLUMN cost_object_breakdown JSONB" in src, (
        "Migration MUST add cost_object_breakdown JSONB column to "
        "fiscal_period_snapshots (PRD §F9.3 + §A6)."
    )


def test_upgrade_adds_unused_capacity_breakdown_jsonb_column() -> None:
    """upgrade() ADD COLUMN unused_capacity_breakdown JSONB (PRD §A9 + §V7)."""
    module = _load_migration_module()
    src = Path(module.__file__).read_text(encoding="utf-8")
    assert "ADD COLUMN unused_capacity_breakdown JSONB" in src, (
        "Migration MUST add unused_capacity_breakdown JSONB column to "
        "fiscal_period_snapshots (PRD §A9 + §V7)."
    )


def test_upgrade_creates_gin_indexes_jsonb_path_ops() -> None:
    """upgrade() creates 2 GIN indexes using jsonb_path_ops (hot path query support).

    PRD §V8 determinism requires deterministic serialization keyed by
    product_id and department_id; jsonb_path_ops GIN index supports
    efficient containment queries (@>) without bloat from default opclass.
    """
    module = _load_migration_module()
    src = Path(module.__file__).read_text(encoding="utf-8")
    upgrade_section = src.split("def upgrade()")[1].split("def downgrade()")[0]

    assert "CREATE INDEX idx_fiscal_period_snapshots_cost_object_breakdown_gin" in upgrade_section
    assert "CREATE INDEX idx_fiscal_period_snapshots_unused_capacity_breakdown_gin" in upgrade_section
    # jsonb_path_ops opclass (PRD §V8 deterministic serialization).
    assert "jsonb_path_ops" in upgrade_section, (
        "Migration MUST use jsonb_path_ops opclass for GIN indexes "
        "(PRD §V8 deterministic serialization)"
    )
    # Both indexes use jsonb_path_ops (2 occurrences expected in upgrade()).
    assert upgrade_section.count("jsonb_path_ops") == 2, (
        f"Expected 2 jsonb_path_ops GIN indexes in upgrade(), got "
        f"{upgrade_section.count('jsonb_path_ops')}"
    )


def test_upgrade_creates_comment_on_column_documentation() -> None:
    """upgrade() adds COMMENT ON COLUMN documentation (NFR18 lock).

    Column semantics captured in DB schema (PRD §F9.3 + NFR18 lock).
    """
    module = _load_migration_module()
    src = Path(module.__file__).read_text(encoding="utf-8")
    assert "COMMENT ON COLUMN fiscal_period_snapshots.cost_object_breakdown" in src, (
        "Migration MUST add COMMENT ON COLUMN for cost_object_breakdown (NFR18)"
    )
    assert "COMMENT ON COLUMN fiscal_period_snapshots.unused_capacity_breakdown" in src, (
        "Migration MUST add COMMENT ON COLUMN for unused_capacity_breakdown (NFR18)"
    )
    # NFR18 lock assertion — comment text includes the lock marker.
    assert "NFR18 lock" in src, (
        "Migration MUST mark column documentation as NFR18 lock"
    )


# ── downgrade() rollback contract ─────────────────────────────────


def test_downgrade_drops_indexes_then_columns_reverse_order() -> None:
    """downgrade() drops indexes THEN columns (reverse order of upgrade()).

    Reverse order prevents index-on-missing-column errors during rollback.
    """
    module = _load_migration_module()
    src = Path(module.__file__).read_text(encoding="utf-8")
    downgrade_section = src.split("def downgrade()")[1]

    # Order check: DROP INDEX must appear BEFORE DROP COLUMN.
    drop_index_pos = downgrade_section.find("DROP INDEX")
    drop_column_pos = downgrade_section.find("DROP COLUMN")
    assert drop_index_pos != -1, "downgrade() MUST drop GIN indexes"
    assert drop_column_pos != -1, "downgrade() MUST drop JSONB columns"
    assert drop_index_pos < drop_column_pos, (
        f"downgrade() order violation: DROP INDEX ({drop_index_pos}) MUST "
        f"come before DROP COLUMN ({drop_column_pos})"
    )

    # Both indexes + both columns present in downgrade().
    assert "idx_fiscal_period_snapshots_cost_object_breakdown_gin" in downgrade_section
    assert "idx_fiscal_period_snapshots_unused_capacity_breakdown_gin" in downgrade_section
    assert "DROP COLUMN IF EXISTS unused_capacity_breakdown" in downgrade_section
    assert "DROP COLUMN IF EXISTS cost_object_breakdown" in downgrade_section