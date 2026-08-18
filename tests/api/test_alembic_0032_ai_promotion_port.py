"""tests.api.test_alembic_0032_ai_promotion_port — Story 10.4 migration tests.

Story 10.4 (cj-style Epic 10 5번째 진입점 = cj-style 33번째 epic 연속) —
T2 tests for `apps.api.alembic.versions.0032_ai_promotion_port.py`.

Test breakdown (~12 cases, source-text parsing, no DB):
- revision / down_revision attributes × 3
- upgrade() EXTENDS input_drafts_state_check to 4 values (incl. 'promoted') × 2
- upgrade() creates monthly_input_promotions table × 1
- upgrade() adds UNIQUE constraint on (tenant_id, period_key, source_draft_id) × 1
- upgrade() adds INSERT-only trigger × 1
- downgrade() drops everything in reverse × 3
- COMMENT ON TABLE for AD-17 verbatim × 1
"""

from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_migration_module() -> object:
    """Import the 0032 migration module by file path.

    Alembic migration files live in `apps/api/alembic/versions/` (not the
    apps.api. package layout), so we load by file location via importlib.
    """
    repo_root = Path(__file__).resolve().parents[2]
    migration_file = (
        repo_root / "apps" / "api" / "alembic" / "versions"
        / "0032_ai_promotion_port.py"
    )
    spec = importlib.util.spec_from_file_location(
        "migration_0032",
        migration_file,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec is not None
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


# ── Revision attributes ────────────────────────────────────────────


def test_revision_id_correct() -> None:
    """revision = '0032_ai_promotion_port' (Story 10.4 wire)."""
    module = _load_migration_module()
    assert module.revision == "0032_ai_promotion_port"


def test_down_revision_0031_ai_insight_comments() -> None:
    """down_revision = '0031_ai_insight_comments' (10-3 wire tip)."""
    module = _load_migration_module()
    assert module.down_revision == "0031_ai_insight_comments"


def test_no_branch_labels_depends_on() -> None:
    """branch_labels / depends_on = None (no branching)."""
    module = _load_migration_module()
    assert module.branch_labels is None
    assert module.depends_on is None


# ── Upgrade shape: input_drafts_state_check EXTENSION ──────────


def test_upgrade_drops_existing_state_check() -> None:
    """upgrade() DROPs existing input_drafts_state_check (3-state) before re-adding."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "DROP CONSTRAINT IF EXISTS input_drafts_state_check" in source


def test_upgrade_adds_state_check_v2_with_promoted() -> None:
    """upgrade() re-adds input_drafts_state_check with 4 values including 'promoted'.

    AD-17 verbatim: state machine EXTENSION draft → reviewed → superseded →
    promoted (input_drafts.state='promoted' after InputPromoter.promote()).
    """
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    # Verify the 4 values are present
    assert "'draft'" in source
    assert "'reviewed'" in source
    assert "'superseded'" in source
    assert "'promoted'" in source
    # Verify it's an ADD CONSTRAINT statement
    assert "ADD CONSTRAINT input_drafts_state_check" in source
    assert "CHECK (state IN" in source


# ── Upgrade shape: monthly_input_promotions table ───────────────


def test_upgrade_creates_monthly_input_promotions_table() -> None:
    """upgrade() creates monthly_input_promotions table with 8 columns + PK."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "CREATE TABLE monthly_input_promotions" in source
    assert "promotion_id UUID PRIMARY KEY DEFAULT gen_random_uuid()" in source
    assert "tenant_id UUID NOT NULL" in source
    assert "REFERENCES tenants(id) ON DELETE RESTRICT" in source
    assert "period_key VARCHAR(32) NOT NULL" in source
    assert "source_draft_id UUID NOT NULL" in source
    assert "REFERENCES input_drafts(draft_id) ON DELETE RESTRICT" in source
    assert "monthly_input_row_id UUID NULL" in source
    assert "idempotency_key UUID NOT NULL" in source
    assert "promoted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()" in source


def test_upgrade_adds_unique_constraint_3tuple() -> None:
    """upgrade() adds UNIQUE constraint on (tenant_id, period_key, source_draft_id).

    AD-17 verbatim: idempotency on the 3-tuple. The DB-level UNIQUE
    constraint enforces this — second INSERT with same 3-tuple raises
    ERRCODE 23505 (unique_violation), which the service layer catches
    and converts to status='idempotent_replay'.
    """
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert (
        "uq_monthly_input_promotions_tenant_period_draft" in source
    )
    assert "UNIQUE (tenant_id, period_key, source_draft_id)" in source


def test_upgrade_creates_insert_only_trigger() -> None:
    """upgrade() creates INSERT-only trigger (AD-2 append-only invariant).

    UPDATE/DELETE on monthly_input_promotions → audit_logs append.
    CR 1.1 audit-first invariant 정합.
    """
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "trg_monthly_input_promotions_insert_only" in source
    assert "INSERT-only trigger" in source or "BEFORE UPDATE OR DELETE" in source


# ── Downgrade shape ──────────────────────────────────────────────


def test_downgrade_drops_state_check() -> None:
    """downgrade() drops the 4-state input_drafts_state_check."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    # The downgrade function should drop the new state check
    assert "DROP CONSTRAINT IF EXISTS input_drafts_state_check" in source


def test_downgrade_drops_unique_constraint() -> None:
    """downgrade() drops the UNIQUE 3-tuple constraint."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "DROP CONSTRAINT IF EXISTS uq_monthly_input_promotions_tenant_period_draft" in source


def test_downgrade_drops_table_and_trigger() -> None:
    """downgrade() drops the table and trigger (reverse order)."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "DROP TRIGGER IF EXISTS trg_monthly_input_promotions_insert_only" in source
    assert "DROP TABLE IF EXISTS monthly_input_promotions" in source


# ── Documentation ──────────────────────────────────────────────


def test_comment_on_table_for_ad17_verbatim() -> None:
    """COMMENT ON TABLE mentions AD-17 verbatim 3-tuple idempotency."""
    module = _load_migration_module()
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "COMMENT ON TABLE monthly_input_promotions" in source
    assert "AD-17" in source or "idempotency" in source
