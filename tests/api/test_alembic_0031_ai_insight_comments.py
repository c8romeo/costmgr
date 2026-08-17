"""tests.api.test_alembic_0031_ai_insight_comments — Story 10.3 migration tests.

Story 10.3 (cj-style Epic 10 4번째 진입점, cj-style 30번째 epic 연속) —
T2.2 tests for `apps/api/alembic/versions/0031_ai_insight_comments.py`.

Test breakdown (10 cases, source-text parsing, no DB):
- revision / down_revision attributes × 3
- upgrade() creates ai_insight_comments table (9 columns) × 1
- upgrade() adds UNIQUE constraint (AD-25 3-tuple + per-kind row) × 1
- upgrade() adds 2 CHECK constraints (comment_kind 5 + source_kind 2) × 1
- upgrade() creates 3 indexes × 1
- upgrade() AD-2 INSERT-only trigger EXTENSION (F10.2-(c)) × 1
- COMMENT ON TABLE for AD-25 + AD-7 verbatim × 1
- downgrade() drops everything in reverse × 1
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration_module() -> object:
    """Import the 0031 migration module by file path."""
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions"
        / "0031_ai_insight_comments.py"
    )
    spec = importlib.util.spec_from_file_location("migration_0031", migration_file)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _migration_source() -> str:
    module = _load_migration_module()
    return Path(module.__file__).read_text(encoding="utf-8")


# ── Revision attributes (3 cases) ─────────────────────────────────


def test_revision_id_correct() -> None:
    """revision = '0031_ai_insight_comments' (Story 10.3 wire)."""
    assert _load_migration_module().revision == "0031_ai_insight_comments"


def test_down_revision_0030_ai_insight_cache() -> None:
    """down_revision = '0030_ai_insight_cache' (10-2 wire tip)."""
    assert _load_migration_module().down_revision == "0030_ai_insight_cache"


def test_no_branch_labels_depends_on() -> None:
    """branch_labels / depends_on = None (no branching)."""
    module = _load_migration_module()
    assert module.branch_labels is None
    assert module.depends_on is None


# ── Upgrade shape (5 cases) ───────────────────────────────────────


def test_upgrade_creates_ai_insight_comments_table() -> None:
    """upgrade() creates ai_insight_comments table with 9 columns."""
    source = _migration_source()
    assert "CREATE TABLE ai_insight_comments" in source
    assert "comment_id UUID PRIMARY KEY DEFAULT gen_random_uuid()" in source
    assert "tenant_id UUID NOT NULL" in source
    assert "REFERENCES tenants(id) ON DELETE RESTRICT" in source
    assert "period_key VARCHAR(32) NOT NULL" in source
    assert "calculation_result_hash VARCHAR(64) NOT NULL" in source
    assert "comment_kind VARCHAR(32) NOT NULL" in source
    assert "source_kind VARCHAR(32) NOT NULL" in source
    assert "body_text TEXT NOT NULL" in source
    assert "evidence_ref TEXT NULL" in source
    assert "generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()" in source


def test_upgrade_unique_constraint_3_tuple_per_kind() -> None:
    """UNIQUE (tenant_id, period_key, comment_kind, calculation_result_hash)."""
    source = _migration_source()
    assert "uq_ai_insight_comments_tenant_period_kind_hash" in source
    assert (
        "UNIQUE (tenant_id, period_key, comment_kind, calculation_result_hash)"
        in source
    )


def test_upgrade_2_check_constraints() -> None:
    """2 CHECK constraints: comment_kind (5 values) + source_kind (2 values)."""
    source = _migration_source()
    assert "ck_ai_insight_comments_comment_kind" in source
    assert "ck_ai_insight_comments_source_kind" in source
    # comment_kind ADMIT list (master PRD §12 + 10-3 forward-fill 2 kinds)
    for kind in (
        "'cost_reduction_candidate'",
        "'anomaly_pattern'",
        "'forecast'",
        "'risk_warning'",
        "'industry_benchmark'",
    ):
        assert kind in source
    # source_kind ADMIT list (AD-7 verbatim)
    assert "'auto_analysis'" in source
    assert "'ai_reference'" in source


def test_upgrade_creates_3_indexes() -> None:
    """3 indexes: tenant_period + calculation_hash + source_kind (F10.2-(a))."""
    source = _migration_source()
    assert "CREATE INDEX idx_ai_insight_comments_tenant_period" in source
    assert "CREATE INDEX idx_ai_insight_comments_calculation_hash" in source
    assert "CREATE INDEX idx_ai_insight_comments_source_kind" in source
    assert "(tenant_id, source_kind)" in source


def test_upgrade_insert_only_trigger_f10_2_c() -> None:
    """AD-2 INSERT-only trigger: UPDATE/DELETE audited then blocked (F10.2-(c))."""
    source = _migration_source()
    assert "trg_ai_insight_comments_no_update_delete" in source
    assert "BEFORE UPDATE" in source
    assert "BEFORE DELETE" in source
    assert "ai_insight_cache_accessed" in source  # ActionClass.AI_INSIGHT_CACHE_ACCESSED (10-3 fix)
    assert "RAISE EXCEPTION" in source
    assert "audit_logs" in source
    # audit INSERT must precede the RAISE (CR 1.1 audit-first verbatim)
    assert source.find("INSERT INTO audit_logs") < source.find("RAISE EXCEPTION")


# ── COMMENT ON TABLE + downgrade (2 cases) ────────────────────────


def test_upgrade_comment_on_table_ad25_ad7_verbatim() -> None:
    """COMMENT ON TABLE mentions AD-25 3-tuple + AD-7 source_kind discriminator."""
    source = _migration_source()
    assert "COMMENT ON TABLE ai_insight_comments" in source
    assert "AD-25" in source
    assert "AD-7" in source
    assert "(tenant_id, period_key, calculation_result_hash)" in source


def test_downgrade_drops_triggers_before_table() -> None:
    """downgrade() drops triggers + function before table (reverse DDL order)."""
    source = _migration_source()
    trigger_idx = source.find(
        "DROP TRIGGER IF EXISTS trg_ai_insight_comments_update_block"
    )
    delete_trigger_idx = source.find(
        "DROP TRIGGER IF EXISTS trg_ai_insight_comments_delete_block"
    )
    function_idx = source.find(
        "DROP FUNCTION IF EXISTS trg_ai_insight_comments_no_update_delete"
    )
    table_idx = source.find("DROP TABLE IF EXISTS ai_insight_comments")
    assert trigger_idx > 0
    assert delete_trigger_idx > 0
    assert function_idx > 0
    assert table_idx > 0
    assert trigger_idx < function_idx < table_idx
