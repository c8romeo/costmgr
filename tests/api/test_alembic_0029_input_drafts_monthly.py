"""tests.api.test_alembic_0029_input_drafts_monthly — Story 10.1 migration tests.

Story 10.1 (cj-style Epic 10 cj-style 28번째 epic 연속) —
T3.2 tests for `apps.api.alembic.versions.0029_input_drafts_monthly_extension.py`.

D-10-1-DEFER-2 해소: AD-7 strict invariant enforcement + confidence precision
upgrade + period_key attribution + INSERT-only trigger EXTENSION.

Test breakdown (~10 cases, source-text parsing, no DB):
- revision / down_revision attributes × 3
- upgrade() adds 5 NEW columns × 1 (target_table + extraction_confidence + extracted_at + period_key + DEFAULT)
- upgrade() adds 2 CHECK constraints × 1 (target_table discriminator + period_key consistency)
- upgrade() creates composite index × 1
- upgrade() INSERT-only trigger EXTENSION × 1
- downgrade() drops everything in reverse × 3
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration_module() -> object:
    """Import the 0029 migration module by file path.

    Alembic migration files live in `apps/api/alembic/versions/` (not the
    apps.api. package layout), so we load by file location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions"
        / "0029_input_drafts_monthly_extension.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0029",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ── Revision attributes ────────────────────────────────────────────


def test_revision_id_correct() -> None:
    """revision = '0029_input_drafts_monthly_extension' (Story 10.1 wire)."""
    module = _load_migration_module()
    assert module.revision == "0029_input_drafts_monthly_extension"


def test_down_revision_0028_abc_fiscal_period_breakdown() -> None:
    """down_revision = '0028_abc_fiscal_period_breakdown' (9-3 wire tip)."""
    module = _load_migration_module()
    assert module.down_revision == "0028_abc_fiscal_period_breakdown"


def test_no_branch_labels_depends_on() -> None:
    """branch_labels / depends_on = None (no branching)."""
    module = _load_migration_module()
    assert module.branch_labels is None
    assert module.depends_on is None


# ── Upgrade shape ──────────────────────────────────────────────────


def test_upgrade_adds_4_new_columns_with_defaults() -> None:
    """upgrade() adds 4 NEW columns: target_table + extraction_confidence + extracted_at + period_key.

    The `target_table` column carries a NOT NULL DEFAULT 'onboarding_inputs'
    for atomic fill (PG 11+ safe, no backfill required).
    """
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "ADD COLUMN target_table" in source
    assert "DEFAULT 'onboarding_inputs'" in source
    assert "ADD COLUMN extraction_confidence" in source
    assert "NUMERIC(4,3)" in source
    assert "ADD COLUMN extracted_at" in source
    assert "TIMESTAMPTZ" in source
    assert "DEFAULT NOW()" in source
    assert "ADD COLUMN period_key" in source


def test_upgrade_adds_2_check_constraints() -> None:
    """upgrade() adds 2 CHECK constraints: target_table discriminator + period_key consistency.

    AD-7 verbatim: 'confirmed_inputs' is EXPLICITLY EXCLUDED from target_table CHECK ADMIT list.
    """
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "ck_input_drafts_target_table" in source
    assert "ck_input_drafts_period_key_consistency" in source
    # AD-7 ADMIT list: 'onboarding_inputs' | 'monthly_inputs'
    assert "'onboarding_inputs'" in source
    assert "'monthly_inputs'" in source
    # AD-7 verbatim: 'confirmed_inputs' is NEVER in the CHECK ADMIT list
    # (the literal string may appear in docstring as an EXCLUSION reference,
    # but it MUST NOT appear in the actual SQL ADMIT list clause)
    # We verify the SQL-specific check by inspecting only the upgrade() body.
    import inspect

    upgrade_source = inspect.getsource(module.upgrade)
    # The CHECK constraint ADMIT list is the tuple inside
    # `CHECK (target_table IN (...))` — 'confirmed_inputs' must not be there.
    assert "target_table IN ('onboarding_inputs', 'monthly_inputs')" in upgrade_source


def test_upgrade_creates_composite_index() -> None:
    """upgrade() creates idx_input_drafts_tenant_target_period composite BTREE index."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "CREATE INDEX" in source
    assert "idx_input_drafts_tenant_target_period" in source
    assert "(tenant_id, target_table, period_key)" in source


def test_upgrade_insert_trigger_extension() -> None:
    """upgrade() creates fn_input_drafts_monthly_ext_trigger + trg_input_drafts_monthly_ext BEFORE INSERT."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "fn_input_drafts_monthly_ext_trigger" in source
    assert "trg_input_drafts_monthly_ext" in source
    assert "BEFORE INSERT" in source
    assert "target_table = 'monthly_inputs'" in source
    # Defense-in-depth: trigger raises ERRCODE 23514 (check_violation)
    assert "23514" in source


# ── Downgrade shape ────────────────────────────────────────────────


def test_downgrade_drops_trigger_and_function() -> None:
    """downgrade() drops trigger + function before anything else (reverse order)."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    # Trigger + function drop come first
    trigger_idx = source.find("DROP TRIGGER IF EXISTS trg_input_drafts_monthly_ext")
    function_idx = source.find("DROP FUNCTION IF EXISTS fn_input_drafts_monthly_ext_trigger")
    index_idx = source.find("DROP INDEX IF EXISTS idx_input_drafts_tenant_target_period")
    constraint_idx = source.find("DROP CONSTRAINT IF EXISTS ck_input_drafts_period_key_consistency")
    column_idx = source.find("DROP COLUMN IF EXISTS period_key")
    assert trigger_idx > 0
    assert function_idx > 0
    assert trigger_idx < function_idx  # trigger first, function second
    assert function_idx < index_idx
    assert index_idx < constraint_idx
    assert constraint_idx < column_idx


def test_downgrade_drops_check_constraints() -> None:
    """downgrade() drops both CHECK constraints."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "DROP CONSTRAINT IF EXISTS ck_input_drafts_period_key_consistency" in source
    assert "DROP CONSTRAINT IF EXISTS ck_input_drafts_target_table" in source


def test_downgrade_drops_4_columns() -> None:
    """downgrade() drops 4 NEW columns in reverse insertion order."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "DROP COLUMN IF EXISTS period_key" in source
    assert "DROP COLUMN IF EXISTS extracted_at" in source
    assert "DROP COLUMN IF EXISTS extraction_confidence" in source
    assert "DROP COLUMN IF EXISTS target_table" in source


# ── NFR18 lock + AD bind ───────────────────────────────────────────


def test_migration_docstring_includes_ad7_and_story_10_1() -> None:
    """Migration docstring references Story 10.1 + AD-7 verbatim for ops traceability."""
    module = _load_migration_module()
    docstring = module.__doc__ or ""
    assert "Story 10.1" in docstring
    assert "AD-7" in docstring or "AD7" in docstring
    assert "D-10-1-DEFER-2" in docstring or "DEFER-2" in docstring
    # NFR18 lock referenced
    assert "NFR18" in docstring


def test_migration_includes_comment_on_column() -> None:
    """Migration uses COMMENT ON COLUMN for NFR18 lock documentation."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "COMMENT ON COLUMN" in source
    # Each NEW column documented
    assert "input_drafts.target_table" in source
    assert "input_drafts.extraction_confidence" in source
    assert "input_drafts.extracted_at" in source
    assert "input_drafts.period_key" in source
