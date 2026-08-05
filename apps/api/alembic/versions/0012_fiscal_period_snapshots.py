"""Fiscal Period Snapshots + Calc Log — Epic 4 Story 4.2

Story 4.2 (Task 1.3) — `POST /api/v1/calc` first_calc endpoint.

Adds two tables to back the single calculation endpoint (AD-19):

1. ``fiscal_period_snapshots`` — append-only-leaning (AD-22) ledger of
   per-tenant per-period calculation results. M3 module is the only
   writer. State field is `verified` at INSERT time; `committed` /
   `reversed` are M11 territory (Epic 11).

   AD-8: KRW fields are `BIGINT` (1원 precision). AD-16: `result_hash`
   is the deterministic SHA-256 64-hex (engine's `result_hash`).
   Uniqueness on `(tenant_id, period_key, baseline_revision, engine_type)`
   provides idempotency at the DB layer (AC #4).

2. ``calc_log`` — audit-first (CR 1.1) ledger. Written before
   `fiscal_period_snapshots` INSERT in the same transaction. `action`
   is `compute` (first write) or `idempotent_skip` (same-hash re-call).

Both tables are RLS-scoped (CR 0.2 lesson — defense-in-depth in
addition to the SQLAlchemy `tenant_id` filter on every read). RLS
policies use the `app.tenant_id` GUC (set by `attach_tenant_listener`
on every session).

No data backfill — the tables start empty. Operators do not migrate
existing calc data (none exists pre-Story 4.2).

Revision ID: 0012_fiscal_period_snapshots
Revises:    0011_monthly_input_periods_opening_inventory
Create Date: 2026-08-02
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0012_fiscal_period_snapshots"
down_revision: str | Sequence[str] | None = "0011_monthly_input_periods_opening_inventory"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── fiscal_period_snapshots (Story 4.2 — Task 1.3) ──────────
    # Append-only-leaning (AD-22). Engine's draft state is transient
    # (service layer owns state transition). M3 module is the only
    # writer. `engine_type='trad'` is the default — Epic 9 Story 9-2
    # will INSERT 'abc' rows.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS fiscal_period_snapshots (
            snapshot_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            period_key TEXT NOT NULL,
            baseline_revision INTEGER NOT NULL DEFAULT 1,
            engine_type TEXT NOT NULL DEFAULT 'trad',
            material_cost BIGINT NOT NULL,
            labor_cost BIGINT NOT NULL,
            overhead_cost BIGINT NOT NULL,
            manufacturing_cost BIGINT NOT NULL,
            inventory_adjustment BIGINT NOT NULL DEFAULT 0,
            result_hash TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ('verified', 'committed', 'reversed')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_fiscal_period_snapshots_tenant_period_revision_engine
                UNIQUE (tenant_id, period_key, baseline_revision, engine_type)
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_fiscal_period_snapshots_tenant_period
            ON fiscal_period_snapshots(tenant_id, period_key)
        """
    )
    op.execute(
        """
        COMMENT ON TABLE fiscal_period_snapshots IS
        'Story 4.2 append-only-leaning ledger of per-tenant per-period '
        'calculation results. M3 module is the only writer (AD-22). '
        'State transition: draft (engine, transient) -> verified (service) -> '
        'committed (Epic 11 M11) -> reversed (Epic 11 Story 11-3).'
        """
    )

    # ── calc_log (Story 4.2 — Task 1.3) ────────────────────────
    # Audit-first ledger (CR 1.1 lesson). Written BEFORE
    # fiscal_period_snapshots INSERT in the same REPEATABLE READ
    # transaction. `action` is `compute` (first write), `idempotent_skip`
    # (same-hash re-call), or `rollback` (engine error → ROLLBACK).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS calc_log (
            calc_log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            period_key TEXT NOT NULL,
            baseline_revision INTEGER NOT NULL,
            engine_type TEXT NOT NULL DEFAULT 'trad',
            action TEXT NOT NULL CHECK (action IN ('compute', 'idempotent_skip', 'rollback')),
            result_hash TEXT,
            trace_id TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_calc_log_tenant_period
            ON calc_log(tenant_id, period_key, created_at DESC)
        """
    )
    op.execute(
        """
        COMMENT ON TABLE calc_log IS
        'Story 4.2 audit-first ledger (CR 1.1). Written before '
        'fiscal_period_snapshots INSERT in REPEATABLE READ transaction. '
        'Idempotent no-op (same result_hash) writes action=idempotent_skip.'
        """
    )

    # ── RLS policies (CR 0.2 lesson) ─────────────────────────────
    # `current_setting('app.tenant_id', true)` returns NULL if unset
    # (the `true` flag). Combined with `FORCE ROW LEVEL SECURITY`,
    # this guarantees no row is readable without a tenant context.
    op.execute("ALTER TABLE fiscal_period_snapshots ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE fiscal_period_snapshots FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY fiscal_period_snapshots_tenant_isolation ON fiscal_period_snapshots
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )

    op.execute("ALTER TABLE calc_log ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE calc_log FORCE ROW LEVEL SECURITY")
    op.execute(
        """
        CREATE POLICY calc_log_tenant_isolation ON calc_log
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)
        """
    )


def downgrade() -> None:
    # Drop in reverse order to satisfy FK-style dependencies (no actual
    # FKs, but policies + tables should be torn down symmetrically).
    op.execute("DROP POLICY IF EXISTS calc_log_tenant_isolation ON calc_log")
    op.execute("DROP TABLE IF EXISTS calc_log")
    op.execute(
        "DROP POLICY IF EXISTS fiscal_period_snapshots_tenant_isolation ON fiscal_period_snapshots"
    )
    op.execute("DROP TABLE IF EXISTS fiscal_period_snapshots")
