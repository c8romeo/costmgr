"""Story 9.3 — fiscal_period_snapshots cost object breakdown JSONB subdocument.

PRD §F9.3 + A29 forward-lock decision wire:
M3 dispatch EXTENSION + M9 NO public endpoint. The AbcAllocationService
compute_and_persist method persists per-department / per-product ABC
allocation rows into `fiscal_period_snapshots` as JSONB subdocuments.

Schema changes:
  - ADD COLUMN `cost_object_breakdown JSONB` to `fiscal_period_snapshots`
    — per-product ABC allocation rows (department_id × cost_object_id ×
    allocated_krw × sha256: hash).
  - ADD COLUMN `unused_capacity_breakdown JSONB` to `fiscal_period_snapshots`
    — per-department unused capacity rows (department_id × unused_hours ×
    unused_cost_krw × sha256: hash).
  - CREATE GIN indexes (`jsonb_path_ops`) for hot path queries (PRD §V8
    determinism requires deterministic serialization keyed by product_id
    and department_id).
  - COMMENT ON COLUMN documentation (NFR18 lock — column semantics
    captured in DB schema).

Down revision: 0027_budget_pre_standard (8-3 wire).

NOTE: `engine_type='abc'` value was already wired by Alembic 0027 (4-value
enum CHECK constraint `trad | abc | tdabc | budget`); 9-3 wire does NOT
need a new CHECK migration.
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0028_abc_fiscal_period_breakdown"
down_revision = "0027_budget_pre_standard"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── 1. cost_object_breakdown JSONB subdocument ────────────────────
    # Per-product ABC allocation rows keyed by product_id (deterministic
    # for V8 hash stability). Each row: {department_id, cost_object_id,
    # allocated_krw, activity_id, driver_id, sha256_hash}.
    op.execute(
        "ALTER TABLE fiscal_period_snapshots "
        "ADD COLUMN cost_object_breakdown JSONB"
    )
    op.execute(
        "COMMENT ON COLUMN fiscal_period_snapshots.cost_object_breakdown "
        "IS 'Per-product ABC allocation rows (department_id x cost_object_id x allocated_krw x sha256 hash). NFR18 lock.'"
    )
    op.execute(
        "CREATE INDEX idx_fiscal_period_snapshots_cost_object_breakdown_gin "
        "ON fiscal_period_snapshots USING GIN (cost_object_breakdown jsonb_path_ops)"
    )

    # ── 2. unused_capacity_breakdown JSONB subdocument ────────────────
    # Per-department unused capacity rows (department_id x unused_hours x
    # unused_cost_krw x sha256_hash). Used for V7 balance verification
    # (sum of allocated_krw + sum of unused_cost_krw == sum of
    # department_cost_krw at 1-won precision).
    op.execute(
        "ALTER TABLE fiscal_period_snapshots "
        "ADD COLUMN unused_capacity_breakdown JSONB"
    )
    op.execute(
        "COMMENT ON COLUMN fiscal_period_snapshots.unused_capacity_breakdown "
        "IS 'Per-department unused capacity rows (department_id x unused_hours x unused_cost_krw x sha256 hash). NFR18 lock.'"
    )
    op.execute(
        "CREATE INDEX idx_fiscal_period_snapshots_unused_capacity_breakdown_gin "
        "ON fiscal_period_snapshots USING GIN (unused_capacity_breakdown jsonb_path_ops)"
    )


def downgrade() -> None:
    # Reverse order: indexes first, then columns
    op.execute(
        "DROP INDEX IF EXISTS idx_fiscal_period_snapshots_unused_capacity_breakdown_gin"
    )
    op.execute(
        "DROP INDEX IF EXISTS idx_fiscal_period_snapshots_cost_object_breakdown_gin"
    )
    op.execute(
        "ALTER TABLE fiscal_period_snapshots DROP COLUMN IF EXISTS unused_capacity_breakdown"
    )
    op.execute(
        "ALTER TABLE fiscal_period_snapshots DROP COLUMN IF EXISTS cost_object_breakdown"
    )