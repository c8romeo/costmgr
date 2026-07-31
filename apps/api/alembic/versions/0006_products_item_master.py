"""Product & Item Master — Story 2.1 (Task 3.1).

Adds the ``products`` table that backs the M1 baseline catalog (PRD §8.M1).

Per AD-15 (docs/conventions.md §3 + AD-15-tenant-id-variance.md):
- ``id`` — UUID **v7** (time-ordered business identity; AD-18 single product
  identity)
- ``tenant_id`` — UUID **v4** (JWT-derived; never from request body)

Per AD-18 — ``products.id`` is the sole product identity across traditional
costing, ABC, inventory ledger, and reports. The Story 2.3 integrity guard
will lock type-change paths after this revision.

Code uniqueness:
- ``(tenant_id, code)`` is the unique key. Different tenants may share
  ``MAT-0001`` (per-tenant per-type sequence per AC #3).
- Race-condition protection (AC #3): a concurrent auto-generated sequence
  may collide; the unique index surfaces 409 PRODUCT_CODE_DUPLICATE
  deterministically. The auto-generation in ``ProductService`` is a
  fast path; the index is the ground truth.

Money columns (AD-8):
- ``unit_cost_krw`` BIGINT NOT NULL CHECK (>= 0). KRW has no fractional
  part — TS uses ``bigint``; Python uses ``KRW`` NewType.
- ``unit_cost_usd`` NUMERIC(18,2) NOT NULL CHECK (>= 0). Decimal-typed
  in both languages; rounded to 2 decimal places per AD-8 (ROUND_HALF_EVEN).

Indexes (T3.1):
- ``uq_products_tenant_code`` (UNIQUE, AC #3).
- ``idx_products_tenant_created_at`` (newest-first list query, AC #2).
- ``idx_products_tenant_type_active`` (M2 input filter — Epic 3+).

Soft-delete state machine:
- ``is_active BOOLEAN NOT NULL DEFAULT TRUE`` (AC #5). Hard delete
  forbidden (AD-2 append-only-leaning + BOM/ledger referential safety).

Revision ID: 0006_products_item_master
Revises:    0005_ai_documents_input_drafts
Create Date: 2026-07-31
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006_products_item_master"
down_revision: str | Sequence[str] | None = "0005_ai_documents_input_drafts"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Product type values — must match `packages.services.m1_baseline.schemas.ProductType`.
_PRODUCT_TYPES = ("product", "semi_product", "material", "goods", "service")


def upgrade() -> None:
    # ── products ─────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id              UUID PRIMARY KEY,                 -- UUID v7 (business)
            tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            product_type    TEXT NOT NULL,
            code            TEXT NOT NULL,
            name            TEXT NOT NULL,
            unit            TEXT NULL,
            unit_cost_krw   BIGINT NULL,
            unit_cost_usd   NUMERIC(18,2) NULL,
            description     TEXT NULL,
            is_active       BOOLEAN NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # ── CHECK constraints ───────────────────────────────────
    op.execute(
        f"""
        ALTER TABLE products
        ADD CONSTRAINT products_product_type_check
        CHECK (product_type IN ({', '.join(repr(t) for t in _PRODUCT_TYPES)}))
        """
    )
    op.execute(
        "ALTER TABLE products "
        "ADD CONSTRAINT products_name_length_check "
        "CHECK (length(name) BETWEEN 1 AND 200)"
    )
    op.execute(
        "ALTER TABLE products "
        "ADD CONSTRAINT products_unit_length_check "
        "CHECK (unit IS NULL OR length(unit) <= 20)"
    )
    op.execute(
        "ALTER TABLE products "
        "ADD CONSTRAINT products_unit_cost_krw_nonneg "
        "CHECK (unit_cost_krw IS NULL OR unit_cost_krw >= 0)"
    )
    op.execute(
        "ALTER TABLE products "
        "ADD CONSTRAINT products_unit_cost_usd_nonneg "
        "CHECK (unit_cost_usd IS NULL OR unit_cost_usd >= 0)"
    )
    op.execute(
        "ALTER TABLE products "
        "ADD CONSTRAINT products_description_length_check "
        "CHECK (description IS NULL OR length(description) <= 2000)"
    )

    # ── Indexes ─────────────────────────────────────────────
    # AC #3 — same-tenant code uniqueness (RLS-scoped, not global).
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_products_tenant_code
        ON products(tenant_id, code)
        """
    )
    # AC #2 — newest-first list query.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_products_tenant_created_at
        ON products(tenant_id, created_at DESC)
        """
    )
    # Epic 3 M2 input filter — type + active state.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_products_tenant_type_active
        ON products(tenant_id, product_type, is_active)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_products_tenant_type_active")
    op.execute("DROP INDEX IF EXISTS idx_products_tenant_created_at")
    op.execute("DROP INDEX IF EXISTS uq_products_tenant_code")
    op.execute("DROP TABLE IF EXISTS products")
