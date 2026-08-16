"""Story 8.3 — fiscal_period_snapshots.engine_type CHECK EXTENSION.

PRD §F8.3 + AD-22 + AD-24 + AD-3:
This migration extends the `fiscal_period_snapshots.engine_type` free-text
column to a 4-value enum CHECK constraint (`'trad' | 'abc' | 'tdabc' | 'budget'`).

Schema changes:
  - DROP existing no-op CHECK on `engine_type` (4-2 wire kept it as free text).
  - ADD CHECK constraint `engine_type IN ('trad','abc','tdabc','budget')`
  - CREATE INDEX `idx_fiscal_period_snapshots_engine_type` for engine_type
    lookup hot path (pre-standard cost preview query optimization).
  - UPDATE existing rows: `engine_type = 'trad'` (idempotency guard — all
    existing rows are already 'trad' per 4-2 wire).

Down revision: 0026_budget_scenarios (8-1 wire).
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0027_budget_pre_standard"
down_revision = "0026_budget_scenarios"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. Idempotent UPDATE (existing rows already 'trad' per 4-2 wire) ──
    # Guard against any future rows that might have a non-standard engine_type
    # (e.g., legacy data from pre-CHECK constraint). Snap them to 'trad'.
    op.execute(
        "UPDATE fiscal_period_snapshots "
        "SET engine_type = 'trad' "
        "WHERE engine_type NOT IN ('trad', 'abc', 'tdabc', 'budget')"
    )

    # ── 2. ADD CHECK constraint (4-value enum) ──────────────────────
    op.execute(
        "ALTER TABLE fiscal_period_snapshots "
        "ADD CONSTRAINT ck_fiscal_period_snapshots_engine_type "
        "CHECK (engine_type IN ('trad', 'abc', 'tdabc', 'budget'))"
    )

    # ── 3. Index for engine_type-based queries (pre-standard preview) ──
    op.execute(
        "CREATE INDEX idx_fiscal_period_snapshots_engine_type "
        "ON fiscal_period_snapshots (engine_type)"
    )

    # ── 4. Documentation ───────────────────────────────────────────
    op.execute(
        "COMMENT ON CONSTRAINT ck_fiscal_period_snapshots_engine_type "
        "ON fiscal_period_snapshots IS "
        "'Story 8.3 — fiscal_period_snapshots.engine_type 4-value enum "
        "(`trad` | `abc` | `tdabc` | `budget`). Pre-standard cost preview "
        "uses `budget` (8-3 wire). ABC engine planned for Epic 9 (placeholder). "
        "3D-ABC `tdabc` placeholder reserved for Epic 9+ follow-up.'"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_fiscal_period_snapshots_engine_type")
    op.execute(
        "ALTER TABLE fiscal_period_snapshots "
        "DROP CONSTRAINT IF EXISTS ck_fiscal_period_snapshots_engine_type"
    )
