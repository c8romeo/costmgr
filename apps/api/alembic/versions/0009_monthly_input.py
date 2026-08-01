"""Monthly Input Capture — Story 3.1 (Tasks 2.1-2.3).

Adds two tables that back the six-stream monthly input domain:

- ``monthly_input_periods`` — one row per (tenant, period_key, baseline_revision).
  Carries the mode toggle (``month_total`` | ``daily``) and a
  ``baseline_revision`` counter that bumps when the first calculation runs
  (Epic 4 — see AD-13 ``MonthInputAdapter`` and Story 3.4 baseline lock).

- ``monthly_input_rows`` — one row per user-entered cell
  ``(stream, product, day_no)``. The natural key is
  ``(tenant_id, period_id, stream, COALESCE(product_id, 0), COALESCE(day_no, 0))``
  via a **partial unique index** that treats NULL ``product_id`` (for
  ``labor`` / ``expenses`` rows) and NULL ``day_no`` (for month-total mode)
  as the same value so identical rows dedupe.

Per AD-15:
- business IDs (``period_id``, ``row_id``) — UUID **v7**
- ``tenant_id`` — UUID **v4** (from JWT, never request body)

Per AD-8 (monetary parity):
- KRW amounts — ``BIGINT`` (no fractional won)
- ``qty`` — ``NUMERIC(18,4)`` (qty is small decimal; Story 4 cost engine
  multiplies it with KRW unit prices, so 4dp precision is enough; the
  engine's intermediate step rounds to BIGINT KRW at the boundary)

Per AD-23 (4-namespace): the unique constraint
``(tenant_id, period_key, baseline_revision)`` on ``monthly_input_periods``
keeps tenant data isolated; cross-tenant writes are rejected at the
constraint level. RLS in ``supabase/policies/0009_monthly_input_rls.sql``
adds a defense-in-depth tenant predicate.

Stream values (Story 3.1 — Task 1.2):
    ('orders','production','sales','purchases','expenses','labor')

Mode values:
    ('month_total', 'daily')

Revision ID: 0009_monthly_input
Revises:    0008_ai_documents_idempotency
Create Date: 2026-08-01
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0009_monthly_input"
down_revision: str | Sequence[str] | None = "0008_ai_documents_idempotency"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Stream enum values — Story 3.1 §Task 1.2 (mirrored in
# `packages.services.m2_input.stream_completion` and the TS mirror).
_STREAM_VALUES = ("orders", "production", "sales", "purchases", "expenses", "labor")

# Mode enum values — PRD §8.M2(b) + F2.1.
_MODE_VALUES = ("month_total", "daily")


def upgrade() -> None:
    # ── monthly_input_periods ────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_input_periods (
            period_id           UUID PRIMARY KEY,                 -- UUID v7 (time-ordered)
            tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            period_key          TEXT NOT NULL,                    -- AD-24 YYYY-MM
            mode                TEXT NOT NULL DEFAULT 'month_total' CHECK (mode IN (
                'month_total', 'daily'
            )),
            baseline_revision   INTEGER NOT NULL DEFAULT 1 CHECK (baseline_revision >= 1),
            locked_by_calculation BOOLEAN NOT NULL DEFAULT false,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    # AD-23 4-namespace: tenant-scoped uniqueness on
    # (tenant_id, period_key, baseline_revision). Different revisions
    # of the same period coexist as separate rows so Epic 4 can keep
    # history (V8 regression, AD-16 fiscal snapshot contract).
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_monthly_input_periods_tenant_period_revision
        ON monthly_input_periods(tenant_id, period_key, baseline_revision)
        """
    )
    # List-by-period query (newest first) — used by m2_input page mount.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_monthly_input_periods_tenant_period
        ON monthly_input_periods(tenant_id, period_key)
        """
    )

    # ── monthly_input_rows ────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS monthly_input_rows (
            row_id              UUID PRIMARY KEY,                 -- UUID v7
            tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            period_id           UUID NOT NULL REFERENCES monthly_input_periods(period_id) ON DELETE CASCADE,
            stream              TEXT NOT NULL,
            product_id          UUID NULL REFERENCES products(id) ON DELETE RESTRICT,
            day_no              INTEGER NULL CHECK (day_no IS NULL OR (day_no BETWEEN 1 AND 31)),
            qty                 NUMERIC(18,4) NULL CHECK (qty IS NULL OR qty >= 0),
            unit_price_krw      BIGINT NULL CHECK (unit_price_krw IS NULL OR unit_price_krw >= 0),
            amount_krw          BIGINT NULL CHECK (amount_krw IS NULL OR amount_krw >= 0),
            workers             INTEGER NULL CHECK (workers IS NULL OR workers >= 0),
            days_per_worker     INTEGER NULL CHECK (days_per_worker IS NULL OR days_per_worker >= 0),
            daily_wage_krw      BIGINT NULL CHECK (daily_wage_krw IS NULL OR daily_wage_krw >= 0),
            memo                TEXT NULL CHECK (memo IS NULL OR length(memo) <= 500),
            created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    # Stream CHECK — explicit so the database rejects typos like
    # 'order' (vs 'orders') early. Mirrored in Pydantic schema layer.
    op.execute(
        f"""
        ALTER TABLE monthly_input_rows
        DROP CONSTRAINT IF EXISTS monthly_input_rows_stream_check
        """
    )
    stream_list = ", ".join(f"'{s}'" for s in _STREAM_VALUES)
    op.execute(
        f"""
        ALTER TABLE monthly_input_rows
        ADD CONSTRAINT monthly_input_rows_stream_check
        CHECK (stream IN ({stream_list}))
        """
    )

    # Cross-stream natural key — partial unique index treats NULL
    # ``product_id`` (labor/expenses without FK) and NULL ``day_no``
    # (month-total mode) as the same value so identical rows collapse.
    # The COALESCE trick keeps the index valid (Postgres treats NULL
    # comparison as NULL, which defeats unique constraints).
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_monthly_input_rows_natural
        ON monthly_input_rows(
            tenant_id,
            period_id,
            stream,
            COALESCE(product_id, '00000000-0000-0000-0000-000000000000'::uuid),
            COALESCE(day_no, 0)
        )
        """
    )
    # Per-stream aggregation query (yellow dot decision).
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_monthly_input_rows_tenant_period_stream
        ON monthly_input_rows(tenant_id, period_id, stream)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS monthly_input_rows")
    op.execute("DROP TABLE IF EXISTS monthly_input_periods")