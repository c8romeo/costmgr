"""Story 5.2 — inventory_ledger append-only events.

AD-2 append-only-leaning (PRD §6.2 수불부): `inventory_ledger` is the
canonical per-product per-period append-only ledger. INSERT-only at the
DB layer via `BEFORE UPDATE OR DELETE` row-level trigger that raises
custom SQLSTATE `P0001` with a Korean message. Corrections flow
through AD-22 reversal sequence (Epic 11 module authority insert,
5-2 wires the entrypoint stub only).

11-value event_type enum (OQ3 cj-style default — explicit at 5-2
ship, pre-emptive coverage of 5-2 + Epic 11 reversal + Epic 6
close-out + Epic 5 maintenance):

    1.  opening_carried                  (Story 5.1 carry chain 결과)
    2.  opening_carried_stale_overwrite  (Story 5.1 AC #3 silent overwrite)
    3.  purchase_inbound                 (stream='purchases' PRD §6.2 입고)
    4.  sales_outbound                   (stream='sales' PRD §6.2 출고)
    5.  production_output_inbound        (stream='production' output)
    6.  production_material_consumption  (stream='production' input material)
    7.  adjustment_positive              (직접 조정 +)
    8.  adjustment_negative              (직접 조정 −)
    9.  reversal_negating                (AD-22 부호 반전 row — Epic 11)
    10. reversal_corrected               (AD-22 corrected row — Epic 11)
    11. closing_snapshot                 (Epic 6 close-out materialize)

These mirror:
- `packages/services/m4_inventory/ledger.py::INVENTORY_LEDGER_EVENT_TYPES`
- `apps/api/core/audit_action.py::_REGISTRY[ActionClass.INVENTORY_LEDGER]`

3-way drift detector: `tests/integration/test_audit_action_consistency.py`.

AC #3 — append-only 3중 방어:
- (1) DB trigger (this migration) — production gate
- (2) Service-layer AST guard (LedgerService) — early-fail
- (3) Audit log emission — observability (append-only violation
       event written to audit_logs via `inventory_ledger_event_rejected`)

AC #7 — 3중 게이트 (ruff 0 / import-linter 2 KEPT / pytest full).
AC #8 — docs wire (architecture-inventory.md extension).

Revision ID: 0015_inventory_ledger
Revises:    0014_verification_log_v8_audit
Create Date: 2026-08-04
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0015_inventory_ledger"
down_revision: str | Sequence[str] | None = "0014_verification_log_v8_audit"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Create the inventory_ledger table ──────────────────
    op.execute(
        """
        CREATE TABLE inventory_ledger (
            event_id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID NOT NULL
                                REFERENCES tenants(id) ON DELETE RESTRICT,
            product_id          UUID NOT NULL
                                REFERENCES products(id) ON DELETE RESTRICT,
            period_key          TEXT NOT NULL,
            event_type          TEXT NOT NULL,
            -- AD-8 / OQ2: NUMERIC(18,4) NULLABLE for non-quantitative events
            -- (closing_snapshot may have NULL qty).
            qty                 NUMERIC(18, 4) NULL,
            trace_id            UUID NOT NULL,
            -- AD-22 reversal sequence (Epic 11 forward-fill):
            reverses_event_id   UUID NULL,
            correction_group_id UUID NULL,
            payload             JSONB NOT NULL DEFAULT '{}'::jsonb,
            inserted_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )

    # ── 2. AD-24 typed period_key CHECK (real fiscal only) ─────
    op.execute(
        """
        ALTER TABLE inventory_ledger
        ADD CONSTRAINT inventory_ledger_period_key_format_check
        CHECK (period_key ~ '^\\d{4}-(0[1-9]|1[0-2])$')
        """
    )

    # ── 3. 11-value event_type CHECK (OQ3 cj-style default) ────
    op.execute(
        """
        ALTER TABLE inventory_ledger
        ADD CONSTRAINT inventory_ledger_event_type_check
        CHECK (event_type IN (
            'opening_carried',
            'opening_carried_stale_overwrite',
            'purchase_inbound',
            'sales_outbound',
            'production_output_inbound',
            'production_material_consumption',
            'adjustment_positive',
            'adjustment_negative',
            'reversal_negating',
            'reversal_corrected',
            'closing_snapshot'
        ))
        """
    )

    # ── 4. qty signed-coherence + quant-or-null CHECK ──────────
    # PRD §6.2 signed-qty semantics: outbound events carry negative qty.
    # event_type-aware CHECK:
    #   - Negative qty permitted ONLY for: sales_outbound,
    #     production_material_consumption, adjustment_negative,
    #     reversal_negating (AD-22 sign-negating row).
    #   - All other quantitative events require qty >= 0.
    #   - Non-quantitative events (closing_snapshot) may have NULL qty.
    # Banker's rounding enforced at the service-layer (LedgerService),
    # not at the DB layer (NUMERIC(18,4) precision is the storage guarantee).
    op.execute(
        """
        ALTER TABLE inventory_ledger
        ADD CONSTRAINT inventory_ledger_qty_signed_coherence
        CHECK (
            qty IS NULL
            OR (event_type IN (
                'sales_outbound',
                'production_material_consumption',
                'adjustment_negative',
                'reversal_negating'
            ) AND qty < 0)
            OR (event_type NOT IN (
                'sales_outbound',
                'production_material_consumption',
                'adjustment_negative',
                'reversal_negating'
            ) AND qty >= 0)
        )
        """
    )

    op.execute(
        """
        ALTER TABLE inventory_ledger
        ADD CONSTRAINT inventory_ledger_qty_required_for_quantitative_events
        CHECK (
            event_type = 'closing_snapshot'
            OR qty IS NOT NULL
        )
        """
    )

    # ── 5. AD-22 reversal coherence CHECK ──────────────────────
    # reversal_negating MUST have reverses_event_id; reversal_corrected
    # MUST have both reverses_event_id + correction_group_id. Other event
    # types MUST have both NULL (no reversal metadata on flow events).
    op.execute(
        """
        ALTER TABLE inventory_ledger
        ADD CONSTRAINT inventory_ledger_reversal_coherence
        CHECK (
            (event_type = 'reversal_negating'
                AND reverses_event_id IS NOT NULL
                AND correction_group_id IS NULL)
            OR (event_type = 'reversal_corrected'
                AND reverses_event_id IS NOT NULL
                AND correction_group_id IS NOT NULL)
            OR (event_type NOT IN ('reversal_negating', 'reversal_corrected')
                AND reverses_event_id IS NULL
                AND correction_group_id IS NULL)
        )
        """
    )

    # ── 6. Indexes for the 3 hot query paths ───────────────────
    # (a) period-closing aggregate: (tenant_id, product_id, period_key)
    op.execute(
        """
        CREATE INDEX idx_inventory_ledger_tenant_product_period
            ON inventory_ledger (tenant_id, product_id, period_key)
        """
    )
    # (b) carry-chain recursive walk: (tenant_id, product_id, event_type, period_key)
    op.execute(
        """
        CREATE INDEX idx_inventory_ledger_carry_chain
            ON inventory_ledger (tenant_id, product_id, event_type, period_key)
        """
    )
    # (c) reversal lookup by reverses_event_id (Epic 11 forward-fill)
    # AD-22 invariant: each (tenant_id, reverses_event_id) at most one
    # reversal row → UNIQUE (not just INDEX) to prevent double-reversal at DB.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_inventory_ledger_reverses_event_id
            ON inventory_ledger (tenant_id, reverses_event_id)
            WHERE reverses_event_id IS NOT NULL
        """
    )
    # (c.1) Idempotency partial unique index (AC #4):
    # application-layer idempotent re-INSERT detection same
    # (tenant_id, product_id, period_key, event_type, trace_id) tuple.
    # Race-safe via DB UNIQUE constraint; service layer catches
    # IntegrityError on duplicate.
    op.execute(
        """
        CREATE UNIQUE INDEX uq_inventory_ledger_idempotency
            ON inventory_ledger (tenant_id, product_id, period_key, event_type, trace_id)
        """
    )
    # (d) correction_group_id lookup (Epic 11 forward-fill)
    op.execute(
        """
        CREATE INDEX idx_inventory_ledger_correction_group_id
            ON inventory_ledger (correction_group_id)
            WHERE correction_group_id IS NOT NULL
        """
    )

    # ── 7. Append-only trigger function ────────────────────────
    # BEFORE UPDATE OR DELETE row-level trigger that raises custom
    # SQLSTATE P0001 with a Korean message. Corrections flow through
    # AD-22 reversal sequence (Epic 11) — direct UPDATE/DELETE is
    # forbidden at the DB layer (OQ7 cj-style row-level trigger).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION _inventory_ledger_append_only()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $func$
        BEGIN
            RAISE EXCEPTION
                'append-only violation: inventory_ledger table forbids UPDATE/DELETE '
                '(event_id=%, op=%)',
                COALESCE(OLD.event_id::text, '<new>'),
                TG_OP
                USING ERRCODE = 'P0001';
        END;
        $func$
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_inventory_ledger_append_only
        BEFORE UPDATE OR DELETE ON inventory_ledger
        FOR EACH ROW
        EXECUTE FUNCTION _inventory_ledger_append_only()
        """
    )

    # ── 8. Table comment for drift detector + observability ────
    op.execute(
        """
        COMMENT ON TABLE inventory_ledger IS
        'Story 5.2 AD-2 append-only ledger. INSERT-only via PostgreSQL '
        'BEFORE UPDATE OR DELETE row-level trigger (custom SQLSTATE P0001). '
        'Corrections flow through AD-22 reversal sequence (Epic 11 module '
        'authority insert). event_type CHECK constraint is the 11-value enum '
        'mirrored in apps/api/core/audit_action.py registry '
        'ActionClass.INVENTORY_LEDGER. 3-way drift detector: '
        'tests/integration/test_audit_action_consistency.py.'
        """
    )

    # ── 9. RLS enable (CR 0-2 RLS infrastructure pattern) ──────
    # Story 0-2 RLS pattern: AD-3 tenant_id predicate enforced at DB
    # layer. RLS policy file is `supabase/policies/0008_inventory_ledger_rls.sql`
    # (mirrors `0009_monthly_input_rls.sql` for SELECT/INSERT + service_role bypass).
    # service_role bypass is audit-first (Epic 0 pattern).
    op.execute("ALTER TABLE inventory_ledger ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    # Reverse order: trigger → function → indexes → constraints → table.
    op.execute("DROP TRIGGER IF EXISTS trg_inventory_ledger_append_only ON inventory_ledger")
    op.execute("DROP FUNCTION IF EXISTS _inventory_ledger_append_only()")
    op.execute("DROP INDEX IF EXISTS idx_inventory_ledger_correction_group_id")
    op.execute("DROP INDEX IF EXISTS uq_inventory_ledger_reverses_event_id")
    op.execute("DROP INDEX IF EXISTS uq_inventory_ledger_idempotency")
    op.execute("DROP INDEX IF EXISTS idx_inventory_ledger_carry_chain")
    op.execute("DROP INDEX IF EXISTS idx_inventory_ledger_tenant_product_period")
    op.execute("DROP TABLE IF EXISTS inventory_ledger")
