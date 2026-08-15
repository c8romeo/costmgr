"""Monthly Input Periods — Opening Inventory JSONB Column

Story 3.3 (Task 2.1) — 음수재고·조업도 실시간 경고 (Negative Inventory
& Overcapacity Real-Time Warning).

Adds the ``opening_inventory`` JSONB column to
``monthly_input_periods`` for the per-period per-product opening balance
that the inventory projection kernel consumes:

- ``monthly_input_periods.opening_inventory``  JSONB NOT NULL DEFAULT '{}'

Schema (MVP, empty when no operator has set anything):
```jsonc
{
  "products": [
    {"product_id": "...uuid...", "product_code": "PRD-0001", "qty": 100.0},
    ...
  ]
}
```

AD-23 (4-namespace) binding: the column is a payload-only JSONB
sub-object (no separate table). Service layer reads via
``monthly_input_periods.opening_inventory`` and converts to a
``dict[product_id, Decimal]`` for the pure projection kernel.

No new indexes — the pure kernel reads the row once per state call
(get_state / save_row). MVP scale (1 period × N products) is small
(~50 products worst case); the GIN index documented in the spec is
NOT created in this migration (Epic 5 Story 5-1 will re-evaluate
when the ledger-backed read lands).

MVP default is empty ``{}``. Operators set the opening balance via
the M0/M1 settings UI (deferred to Story 0.5 plumbing). Epic 5
Story 5-1 auto-carries closing balances from the previous period
(``TODO(epic-5)`` marker closed in Story 5-2; A19 carry-over sprint
removed the legacy ``inventory_projection.py`` module — math surface
lives at ``packages/services/m2_input/inventory_math.py``).

Revision ID: 0011_monthly_input_periods_opening_inventory
Revises:    0010_monthly_input_labor_breakdown
Create Date: 2026-08-01
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0011_monthly_input_periods_opening_inventory"
down_revision: str | Sequence[str] | None = "0010_monthly_input_labor_breakdown"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # opening_inventory JSONB — per-period per-product opening balance
    # consumed by Story 3.3 inventory projection kernel.
    # NOT NULL with default '{}' so existing rows (Story 3.1 onwards)
    # backfill cleanly. Empty dict means "no data" — service layer
    # falls back to 0 for all products (MVP).
    op.execute(
        """
        ALTER TABLE monthly_input_periods
        ADD COLUMN IF NOT EXISTS opening_inventory JSONB NOT NULL
        DEFAULT '{}'::jsonb
        """
    )
    # COMMENT attached via DDL (Postgres-specific). Documents the
    # epic-5 hand-off for the next database reader.
    op.execute(
        """
        COMMENT ON COLUMN monthly_input_periods.opening_inventory IS
        'Story 3.3 placeholder for Epic 5 Story 5-1 (opening inventory '
        'auto-carry chain). MVP default: {}. Service layer reads + '
        'fetches from previous period closing balance (cj-style default 0).'
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE monthly_input_periods DROP COLUMN IF EXISTS opening_inventory")
