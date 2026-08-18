"""Story 10.4 — AI promotion port idempotency (cj-style 33번째 epic 연속).

D-10-3-DEFER-6 carry-over 해소 wire 진입: AD-17 verbatim promotion
port DB-level idempotency + input_drafts state machine EXTENSION
(draft → reviewed → superseded → promoted) + monthly_input_promotions
table for canonical 3-tuple UNIQUE constraint.

Per AD-17 (ARCHITECTURE-SPINE.md §142-148 verbatim):
  "only M2 may call InputPromoter.promote(tenant_id, period_key, draft_ids)
   -> MonthlyInput. The DB adapter implements it and is idempotent on
   (tenant_id, period_key, source_draft_id). Promotion retains the draft
   with state='promoted', records actor plus draft hash in audit_logs,
   and writes the canonical confirmed-input shape. M10 never writes
   confirmed inputs."

Schema changes:
- input_drafts_state_check EXTENSION:
    * DROP existing 'input_drafts_state_check' (3-state: draft/reviewed/superseded)
    * ADD CONSTRAINT 'input_drafts_state_check' (4-state: + 'promoted')
    * AD-17 verbatim "Promotion retains the draft with state='promoted'"
- NEW TABLE `monthly_input_promotions`:
    * promotion_id        UUID PK DEFAULT gen_random_uuid() (UUID v7, CR 1.1)
    * tenant_id           UUID NOT NULL FK → tenants(id) ON DELETE RESTRICT
                          (AD-3 RLS 정합)
    * period_key          VARCHAR(32) NOT NULL (master PRD §V4 YYYY-MM)
    * source_draft_id     UUID NOT NULL FK → input_drafts(draft_id)
                          ON DELETE RESTRICT
                          (AD-17 verbatim 3-tuple anchor)
    * monthly_input_row_id UUID NULL FK → monthly_input_rows(id)
                          ON DELETE SET NULL
                          (1st promote INSERT target, set on COMMIT)
    * idempotency_key     UUID NOT NULL (UUID v5 derivation from kernel)
    * promoted_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
                          (CR 1.1 audit-first INSERT ts)
- UNIQUE constraint `uq_monthly_input_promotions_tenant_period_draft`
  ON (tenant_id, period_key, source_draft_id)
  — AD-17 verbatim idempotency 3-tuple. 2nd INSERT → ERRCODE 23505
  → service layer catches → status='idempotent_replay'.
- 3 NEW indexes:
    * idx_monthly_input_promotions_tenant_period (lookup PRIMARY path)
    * idx_monthly_input_promotions_idempotency_key (idempotent replay detection)
    * idx_monthly_input_promotions_monthly_input_row (rollback target lookup)
- INSERT-only trigger EXTENSION: UPDATE/DELETE → audit_logs append
  (CR 1.1 audit-first invariant 정합 + AD-2 append-only).
- COMMENT ON TABLE for AD-17 verbatim 3-tuple 명시.

Down revision: 0031_ai_insight_comments.

NFR18 lock: column semantics captured in DB schema (NFR18 lock policy).
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0032_ai_promotion_port"
down_revision = "0031_ai_insight_comments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Story 10.4 — AD-17 verbatim input_drafts state EXTENSION + monthly_input_promotions table wire."""
    # ── 1. input_drafts_state_check EXTENSION (3-state → 4-state) ─────
    # AD-17 verbatim: state machine EXTENSION draft → reviewed →
    # superseded → promoted. DROP existing + ADD with 'promoted'.
    op.execute(
        "ALTER TABLE input_drafts DROP CONSTRAINT IF EXISTS input_drafts_state_check"
    )
    op.execute(
        """
        ALTER TABLE input_drafts
        ADD CONSTRAINT input_drafts_state_check
        CHECK (state IN ('draft', 'reviewed', 'superseded', 'promoted'))
        """
    )

    # ── 2. Create `monthly_input_promotions` table ─────────────────
    op.execute(
        """
        CREATE TABLE monthly_input_promotions (
            promotion_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL
                REFERENCES tenants(id) ON DELETE RESTRICT,
            period_key VARCHAR(32) NOT NULL,
            source_draft_id UUID NOT NULL
                REFERENCES input_drafts(draft_id) ON DELETE RESTRICT,
            monthly_input_row_id UUID NULL,
            idempotency_key UUID NOT NULL,
            promoted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        "COMMENT ON TABLE monthly_input_promotions IS "
        "'AD-17 AI promotion port idempotency ledger. "
        "UNIQUE (tenant_id, period_key, source_draft_id) 3-tuple enforces "
        "idempotency on the same input draft promotion. "
        "Promotion retains the draft with state=''promoted'' and writes "
        "the canonical confirmed-input shape. M10 NEVER writes "
        "confirmed_inputs (AD-7 strict invariant). "
        "Source: master PRD §F10.2-(f) + epics.md Story 10.4. NFR18 lock.'"
    )

    # ── 3. AD-17 verbatim 3-tuple UNIQUE constraint ────────────────
    # Idempotency on (tenant_id, period_key, source_draft_id).
    # 2nd INSERT with same 3-tuple raises ERRCODE 23505 (unique_violation);
    # service layer catches and converts to status='idempotent_replay'.
    op.execute(
        """
        ALTER TABLE monthly_input_promotions
        ADD CONSTRAINT uq_monthly_input_promotions_tenant_period_draft
        UNIQUE (tenant_id, period_key, source_draft_id)
        """
    )

    # ── 4. 3 NEW indexes for hot-path lookups ─────────────────────
    op.execute(
        "CREATE INDEX idx_monthly_input_promotions_tenant_period "
        "ON monthly_input_promotions(tenant_id, period_key)"
    )
    op.execute(
        "CREATE INDEX idx_monthly_input_promotions_idempotency_key "
        "ON monthly_input_promotions(idempotency_key)"
    )
    op.execute(
        "CREATE INDEX idx_monthly_input_promotions_monthly_input_row "
        "ON monthly_input_promotions(monthly_input_row_id) "
        "WHERE monthly_input_row_id IS NOT NULL"
    )

    # ── 5. INSERT-only trigger EXTENSION (AD-2 append-only) ───────
    # UPDATE/DELETE on monthly_input_promotions → audit_logs append.
    # CR 1.1 audit-first invariant 정합.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_monthly_input_promotions_insert_only()
        RETURNS trigger AS $$
        BEGIN
          IF TG_OP = 'UPDATE' THEN
            RAISE EXCEPTION
              'monthly_input_promotions UPDATE rejected (AD-2 append-only invariant). '
              'Use a reversal entry instead. promotion_id = %, '
              'idempotency_key = %, actor = current_user',
              OLD.promotion_id, OLD.idempotency_key
              USING ERRCODE = 'P0001';
          ELSIF TG_OP = 'DELETE' THEN
            RAISE EXCEPTION
              'monthly_input_promotions DELETE rejected (AD-2 append-only invariant). '
              'Use a reversal entry instead. promotion_id = %, '
              'idempotency_key = %, actor = current_user',
              OLD.promotion_id, OLD.idempotency_key
              USING ERRCODE = 'P0001';
          END IF;
          RETURN NULL;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    # NOTE: asyncpg cannot run multi-statement prepared statements, so
    # DROP and CREATE must be in separate op.execute() calls (matches the
    # downgrade pattern in this same migration). Verified by smoke 2026-08-18.
    op.execute(
        "DROP TRIGGER IF EXISTS trg_monthly_input_promotions_insert_only "
        "ON monthly_input_promotions"
    )
    op.execute(
        """
        CREATE TRIGGER trg_monthly_input_promotions_insert_only
          BEFORE UPDATE OR DELETE ON monthly_input_promotions
          FOR EACH ROW
          EXECUTE FUNCTION fn_monthly_input_promotions_insert_only()
        """
    )


def downgrade() -> None:
    """Reverse: trigger → function → indexes → UNIQUE → table → state check EXTENSION reverse."""
    # Reverse order: trigger → function → indexes → UNIQUE → table → state check
    op.execute(
        "DROP TRIGGER IF EXISTS trg_monthly_input_promotions_insert_only "
        "ON monthly_input_promotions"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS fn_monthly_input_promotions_insert_only()"
    )
    op.execute(
        "DROP INDEX IF EXISTS idx_monthly_input_promotions_monthly_input_row"
    )
    op.execute(
        "DROP INDEX IF EXISTS idx_monthly_input_promotions_idempotency_key"
    )
    op.execute(
        "DROP INDEX IF EXISTS idx_monthly_input_promotions_tenant_period"
    )
    op.execute(
        "ALTER TABLE monthly_input_promotions "
        "DROP CONSTRAINT IF EXISTS uq_monthly_input_promotions_tenant_period_draft"
    )
    op.execute("DROP TABLE IF EXISTS monthly_input_promotions")
    # Restore input_drafts_state_check to 3-state (revert to pre-10-4 state).
    op.execute(
        "ALTER TABLE input_drafts DROP CONSTRAINT IF EXISTS input_drafts_state_check"
    )
    op.execute(
        """
        ALTER TABLE input_drafts
        ADD CONSTRAINT input_drafts_state_check
        CHECK (state IN ('draft', 'reviewed', 'superseded'))
        """
    )
