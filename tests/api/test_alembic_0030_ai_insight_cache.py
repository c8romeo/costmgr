"""tests.api.test_alembic_0030_ai_insight_cache — Story 10.2 migration tests.

Story 10.2 (cj-style Epic 10 cj-style 29번째 epic 연속) —
T2.2 tests for `apps.api.alembic.versions.0030_ai_insight_cache.py`.

Test breakdown (~10 cases, source-text parsing, no DB):
- revision / down_revision attributes × 3
- upgrade() creates ai_insight_cache table × 1
- upgrade() adds UNIQUE constraint (AD-25 3-tuple + per-kind row) × 1
- upgrade() adds 2 CHECK constraints (insight_kind + source_kind) × 1
- upgrade() creates 3 indexes × 1
- upgrade() AD-2 INSERT-only trigger EXTENSION × 1
- downgrade() drops everything in reverse × 2
- COMMENT ON TABLE for AD-25 verbatim 3-tuple × 1
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration_module() -> object:
    """Import the 0030 migration module by file path.

    Alembic migration files live in `apps/api/alembic/versions/` (not the
    apps.api. package layout), so we load by file location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions"
        / "0030_ai_insight_cache.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0030",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ── Revision attributes ────────────────────────────────────────────


def test_revision_id_correct() -> None:
    """revision = '0030_ai_insight_cache' (Story 10.2 wire)."""
    module = _load_migration_module()
    assert module.revision == "0030_ai_insight_cache"


def test_down_revision_0029_input_drafts_monthly_extension() -> None:
    """down_revision = '0029_input_drafts_monthly_extension' (10-1 wire tip)."""
    module = _load_migration_module()
    assert module.down_revision == "0029_input_drafts_monthly_extension"


def test_no_branch_labels_depends_on() -> None:
    """branch_labels / depends_on = None (no branching)."""
    module = _load_migration_module()
    assert module.branch_labels is None
    assert module.depends_on is None


# ── Upgrade shape ──────────────────────────────────────────────────


def test_upgrade_creates_ai_insight_cache_table() -> None:
    """upgrade() creates ai_insight_cache table with 10 columns."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "CREATE TABLE ai_insight_cache" in source
    assert "insight_cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid()" in source
    assert "tenant_id UUID NOT NULL" in source
    assert "REFERENCES tenants(id) ON DELETE RESTRICT" in source
    assert "period_key VARCHAR(32) NOT NULL" in source
    assert "calculation_result_hash VARCHAR(64) NOT NULL" in source
    assert "insight_kind VARCHAR(32) NOT NULL" in source
    assert "source_kind VARCHAR(32) NOT NULL" in source
    assert "question TEXT NOT NULL" in source
    assert "answer TEXT NOT NULL" in source
    assert "evidence_ref TEXT NULL" in source
    assert "generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()" in source


def test_upgrade_unique_constraint_3_tuple() -> None:
    """upgrade() adds UNIQUE constraint uq_ai_insight_cache_tenant_period_kind_hash
    on AD-25 verbatim 3-tuple (tenant_id, period_key, insight_kind, calculation_result_hash).
    """
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "uq_ai_insight_cache_tenant_period_kind_hash" in source
    assert "UNIQUE (tenant_id, period_key, insight_kind, calculation_result_hash)" in source


def test_upgrade_2_check_constraints() -> None:
    """upgrade() adds 2 CHECK constraints: insight_kind discriminator + source_kind discriminator.

    AD-15 cross-language parity SSOT:
      - insight_kind: ('cost_reduction_candidate', 'anomaly_pattern', 'forecast')
      - source_kind:  ('auto_analysis', 'ai_reference')
    """
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "ck_ai_insight_cache_insight_kind" in source
    assert "ck_ai_insight_cache_source_kind" in source
    # insight_kind ADMIT list (master PRD §12 AI 3종)
    assert "'cost_reduction_candidate'" in source
    assert "'anomaly_pattern'" in source
    assert "'forecast'" in source
    # source_kind ADMIT list (AD-7 + 10-3 forward-bind)
    assert "'auto_analysis'" in source
    assert "'ai_reference'" in source


def test_upgrade_creates_3_indexes() -> None:
    """upgrade() creates 3 indexes: tenant_period + calculation_hash + published_at_desc."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "CREATE INDEX idx_ai_insight_cache_tenant_period" in source
    assert "(tenant_id, period_key)" in source
    assert "CREATE INDEX idx_ai_insight_cache_calculation_hash" in source
    assert "(calculation_result_hash)" in source
    assert "CREATE INDEX idx_ai_insight_cache_published_at_desc" in source
    assert "(tenant_id, generated_at DESC)" in source


def test_upgrade_insert_only_trigger() -> None:
    """upgrade() wires AD-2 INSERT-only trigger: UPDATE/DELETE blocked + audit log append."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "trg_ai_insight_cache_no_update_delete" in source
    assert "BEFORE UPDATE" in source
    assert "BEFORE DELETE" in source
    assert "AI_INSIGHT_CACHE_MUTATION_BLOCKED" in source
    assert "RAISE EXCEPTION" in source
    assert "audit-first" in source.lower() or "audit_logs" in source


def test_upgrade_comment_on_table_ad25_verbatim() -> None:
    """upgrade() adds COMMENT ON TABLE mentioning AD-25 verbatim 3-tuple."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "COMMENT ON TABLE ai_insight_cache" in source
    assert "AD-25" in source
    assert "(tenant_id, period_key, calculation_result_hash)" in source


def test_upgrade_period_key_format_check() -> None:
    """upgrade() adds AD-24 typed period_key format check (YYYY-MM)."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "ck_ai_insight_cache_period_key_format" in source
    assert "^\\\\d{4}-(0[1-9]|1[0-2])$" in source or "^\\d{4}-(0[1-9]|1[0-2])$" in source


# ── Downgrade shape ────────────────────────────────────────────────


def test_downgrade_drops_triggers_first() -> None:
    """downgrade() drops triggers + function before table (reverse order)."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    trigger_update_idx = source.find("DROP TRIGGER IF EXISTS trg_ai_insight_cache_update_block")
    trigger_delete_idx = source.find("DROP TRIGGER IF EXISTS trg_ai_insight_cache_delete_block")
    function_idx = source.find("DROP FUNCTION IF EXISTS trg_ai_insight_cache_no_update_delete")
    table_idx = source.find("DROP TABLE IF EXISTS ai_insight_cache")
    assert trigger_update_idx > 0
    assert trigger_delete_idx > 0
    assert function_idx > 0
    assert table_idx > 0
    # Triggers dropped before function, function before table (reverse DDL)
    assert trigger_update_idx < function_idx
    assert function_idx < table_idx