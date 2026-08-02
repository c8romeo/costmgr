"""BOM Matrix — Story 2.2 (Task 2.1).

Adds the ``bom_lines`` table that backs the M1 baseline BOM editor
(PRD §8.M1(b), §6.1(1), §F1.1). Per (AD-15 + AD-18 + AD-23):
- ``id`` — UUID **v7** (business, time-ordered for the matrix list query)
- ``tenant_id`` — UUID **v4** (JWT-derived, never from request body)
- ``parent_product_id`` / ``child_product_id`` — UUID v7 FK to ``products.id``

Per AD-2 / append-only-leaning: NO DELETE policy in RLS (bulk-replace
PUT is the only mutation path). The UNIQUE INDEX surfaces duplicate
children at the DB layer as a 23505 defense-in-depth (the service
pre-validates duplicates for typed 422 responses — see
``BOMDuplicateChildError``).

Per AD-8 / ratio: ``ratio`` is ``NUMERIC(7,4)`` (4 decimal places,
max 100.0000). Python ``Decimal``. CHECK ``0 < ratio <= 100``. Quantize
via ``ROUND_HALF_EVEN`` per ``packages.services.m1_baseline.bom_validation``.

Per PRD §6.1(1): only ``material`` (and ``semi_product`` for multi-level
BOM) participate as children. The DB does NOT enforce this — it would
require a trigger JOINing to ``products``. The service layer is the
source of truth (``BOMChildType`` set in ``packages.services.m1_baseline.schemas``).

Revision ID: 0007_bom_matrix
Revises:    0006_products_item_master
Create Date: 2026-08-01

Indexes (T2.1):
- ``uq_bom_lines_tenant_parent_child`` UNIQUE — AC #7 (no duplicate children).
- ``idx_bom_lines_tenant_parent`` — AC #1 list query (the matrix view).
- ``idx_bom_lines_tenant_child`` — reverse lookup ("in which BOMs is
  material X used?" — needed for inventory rollup in Epic 5+).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007_bom_matrix"
down_revision: str | Sequence[str] | None = "0006_products_item_master"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── bom_lines ─────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS bom_lines (
            id                  UUID PRIMARY KEY,         -- UUID v7 (business)
            tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            parent_product_id   UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            child_product_id    UUID NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
            ratio               NUMERIC(7,4) NOT NULL CHECK (ratio > 0 AND ratio <= 100),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # ── Indexes ─────────────────────────────────────────────
    # AC #7 — UNIQUE (tenant_id, parent_product_id, child_product_id):
    # no two BOM rows for the same parent may reference the same child.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_bom_lines_tenant_parent_child
        ON bom_lines(tenant_id, parent_product_id, child_product_id)
        """
    )
    # AC #1 — list query (the matrix view, ordered by created_at).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bom_lines_tenant_parent
        ON bom_lines(tenant_id, parent_product_id, created_at)
        """
    )
    # Reverse lookup — "in which BOMs is material X used?". Epic 5+
    # inventory rollup needs this for the BOM-to-ledger join.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_bom_lines_tenant_child
        ON bom_lines(tenant_id, child_product_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_bom_lines_tenant_child")
    op.execute("DROP INDEX IF EXISTS idx_bom_lines_tenant_parent")
    op.execute("DROP INDEX IF EXISTS uq_bom_lines_tenant_parent_child")
    op.execute("DROP TABLE IF EXISTS bom_lines")
