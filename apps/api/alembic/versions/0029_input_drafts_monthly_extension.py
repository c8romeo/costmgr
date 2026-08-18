"""Story 10.1 — input_drafts monthly extension (cj-style 28번째 epic 연속).

D-10-1-DEFER-2 해소: AD-7 strict invariant enforcement + confidence precision
upgrade + period_key attribution + INSERT-only trigger EXTENSION.

Schema changes (input_drafts table):
- ADD COLUMN target_table VARCHAR(32) NOT NULL DEFAULT 'onboarding_inputs'
  — discriminator column marking which aggregate a draft is for. ALLOWED
    set enforced via CHECK constraint (onboarding_inputs | monthly_inputs).
    Per AD-7, 'confirmed_inputs' is EXPLICITLY EXCLUDED (M10 NEVER promotes
    → that promotion is M2/InputPromoter.promote()).
    DEFAULT chosen so existing Story 1.3 onboarding document-extraction
    rows get a valid value without backfill (PG 11+ atomic DEFAULT fill).

- ADD COLUMN extraction_confidence NUMERIC(4,3)
  — verbatim spec: 3 decimal places matches packages kernel
    compute_extraction_confidence precision. Range CHECK [0.000, 1.000].

- ADD COLUMN extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
  — differentiates "when M10 saw it" from existing requested_at
    (which the user manual review timestamp anchors).

- ADD COLUMN period_key VARCHAR(32)
  — NULLABLE since onboarding_inputs rows do NOT carry a period_key.
    Monthly rows WILL populate it via the discriminated union
    (target_table='monthly_inputs' → period_key NOT NULL enforced via
    ck_input_drafts_period_key_consistency CHECK).

- ADD CONSTRAINT ck_input_drafts_target_table
  CHECK (target_table IN ('onboarding_inputs', 'monthly_inputs'))
  — AD-7 ADMIT list (confirmed_inputs EXPLICITLY excluded).

- ADD CONSTRAINT ck_input_drafts_period_key_consistency
  CHECK ((target_table='monthly_inputs' AND period_key IS NOT NULL)
      OR (target_table='onboarding_inputs' AND period_key IS NULL))
  — period_key MUST be set for monthly drafts, MUST be NULL for onboarding.

- CREATE INDEX idx_input_drafts_tenant_target_period
  ON input_drafts (tenant_id, target_table, period_key)
  — composite BTREE index for M3/M2 service hot path queries.

- INSERT-time trigger EXTENSION trg_input_drafts_monthly_ext
  BEFORE INSERT — validates period_key NOT NULL when target_table='monthly_inputs'
  (defense-in-depth alongside the CHECK constraint; the CHECK also covers
  this case but the trigger raises a more informative ERRCODE 23514).

Down revision: 0028_abc_fiscal_period_breakdown.

NFR18 lock: column semantics captured in DB schema (NFR18 lock policy).
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "0029_input_drafts_monthly_extension"
down_revision = "0028_abc_fiscal_period_breakdown"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add 4 NEW columns (atomic DEFAULT fill — PG 11+ safe).
    op.execute(
        "ALTER TABLE input_drafts "
        "ADD COLUMN target_table VARCHAR(32) NOT NULL DEFAULT 'onboarding_inputs'"
    )
    op.execute(
        "COMMENT ON COLUMN input_drafts.target_table IS "
        "'AD-7 strict invariant discriminator (onboarding_inputs | monthly_inputs). "
        "confirmed_inputs EXPLICITLY EXCLUDED. NFR18 lock.'"
    )
    op.execute(
        "ALTER TABLE input_drafts "
        "ADD COLUMN extraction_confidence NUMERIC(4,3)"
    )
    op.execute(
        "COMMENT ON COLUMN input_drafts.extraction_confidence IS "
        "'AI confidence 0.000-1.000 (3 decimal precision matches kernel). NFR18 lock.'"
    )
    op.execute(
        "ALTER TABLE input_drafts "
        "ADD COLUMN extracted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()"
    )
    op.execute(
        "COMMENT ON COLUMN input_drafts.extracted_at IS "
        "'When M10 saw the document (DIFFERENT from requested_at which anchors user review). NFR18 lock.'"
    )
    op.execute(
        "ALTER TABLE input_drafts "
        "ADD COLUMN period_key VARCHAR(32)"
    )
    op.execute(
        "COMMENT ON COLUMN input_drafts.period_key IS "
        "'Monthly period attribution (e.g. 2026-08). NULL for onboarding_inputs rows. NFR18 lock.'"
    )

    # 2. CHECK constraint — target_table discriminator (AD-7 ADMIT list).
    op.execute(
        "ALTER TABLE input_drafts "
        "ADD CONSTRAINT ck_input_drafts_target_table "
        "CHECK (target_table IN ('onboarding_inputs', 'monthly_inputs'))"
    )

    # 3. CHECK constraint — period_key consistency between discriminator values.
    op.execute(
        "ALTER TABLE input_drafts "
        "ADD CONSTRAINT ck_input_drafts_period_key_consistency "
        "CHECK ("
        "(target_table = 'monthly_inputs' AND period_key IS NOT NULL) OR "
        "(target_table = 'onboarding_inputs' AND period_key IS NULL)"
        ")"
    )

    # 4. Composite BTREE index for M3/M2 service hot path queries.
    op.execute(
        "CREATE INDEX idx_input_drafts_tenant_target_period "
        "ON input_drafts (tenant_id, target_table, period_key)"
    )

    # 5. INSERT-time trigger EXTENSION — defense-in-depth alongside the
    #    CHECK constraint. The CHECK already covers the same logic, but
    #    the trigger raises ERRCODE 23514 (check_violation) with a more
    #    informative message for ops debugging.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION fn_input_drafts_monthly_ext_trigger()
        RETURNS trigger AS $$
        BEGIN
          IF NEW.target_table = 'monthly_inputs' AND NEW.period_key IS NULL THEN
            RAISE EXCEPTION
              'input_drafts INSERT rejected: target_table=''monthly_inputs'' requires period_key NOT NULL (AD-7 + Story 10.1)'
              USING ERRCODE = '23514';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
        """
    )
    # NOTE: asyncpg cannot run multi-statement prepared statements, so
    # DROP and CREATE must be in separate op.execute() calls (matches the
    # downgrade pattern in this same migration). Verified by smoke 2026-08-18.
    op.execute("DROP TRIGGER IF EXISTS trg_input_drafts_monthly_ext ON input_drafts")
    op.execute(
        """
        CREATE TRIGGER trg_input_drafts_monthly_ext
          BEFORE INSERT ON input_drafts
          FOR EACH ROW
          EXECUTE FUNCTION fn_input_drafts_monthly_ext_trigger()
        """
    )


def downgrade() -> None:
    # Reverse order: trigger → index → CHECK constraints → columns
    op.execute("DROP TRIGGER IF EXISTS trg_input_drafts_monthly_ext ON input_drafts")
    op.execute("DROP FUNCTION IF EXISTS fn_input_drafts_monthly_ext_trigger()")
    op.execute("DROP INDEX IF EXISTS idx_input_drafts_tenant_target_period")
    op.execute(
        "ALTER TABLE input_drafts DROP CONSTRAINT IF EXISTS ck_input_drafts_period_key_consistency"
    )
    op.execute(
        "ALTER TABLE input_drafts DROP CONSTRAINT IF EXISTS ck_input_drafts_target_table"
    )
    op.execute("ALTER TABLE input_drafts DROP COLUMN IF EXISTS period_key")
    op.execute("ALTER TABLE input_drafts DROP COLUMN IF EXISTS extracted_at")
    op.execute("ALTER TABLE input_drafts DROP COLUMN IF EXISTS extraction_confidence")
    op.execute("ALTER TABLE input_drafts DROP COLUMN IF EXISTS target_table")
