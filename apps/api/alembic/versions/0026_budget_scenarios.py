r"""Story 8.1 — budget_scenarios table.

PRD §F8.1 + AD-24 virtual budget period key + 1차 시나리오 1개 잠금.
This migration introduces the `budget_scenarios` table for storing
1차 MVP single-scenario-per-tenant budget envelope.

Schema (8 columns + 2 UNIQUE + 3 CHECK + 1 index):

  - `id`              UUID PRIMARY KEY DEFAULT gen_random_uuid()
  - `tenant_id`       UUID NOT NULL FK → tenants(id) ON DELETE CASCADE
  - `period_key`      TEXT NOT NULL  — AD-24 virtual `YYYY-MM#B<n>`
  - `real_period_key` TEXT NOT NULL  — AD-24 real `YYYY-MM`
  - `scenario_index`  INTEGER NOT NULL DEFAULT 1
  - `scenario_hash`   TEXT NOT NULL  — V8 determinism sha256 hexdigest
  - `created_by`      UUID NOT NULL FK → users(id) ON DELETE RESTRICT
  - `created_at_kst`  TIMESTAMPTZ NOT NULL DEFAULT now()

Constraints:
  - UNIQUE(tenant_id, period_key) — `uq_budget_scenarios_tenant_id_period_key`
    (lookup by virtual period_key).
  - UNIQUE(tenant_id, real_period_key) — `uq_budget_scenarios_tenant_id_real_period_key`
    (1차 MVP scenario 1개 잠금 defense-in-depth, CR 12-5 L3).
  - CHECK period_key ~ '^\d{4}-(0[1-9]|1[0-2])#B[1-9]\d*' —
    `ck_budget_scenarios_period_key_pattern`.
  - CHECK real_period_key ~ '^\d{4}-(0[1-9]|1[0-2])' —
    `ck_budget_scenarios_real_period_key_pattern`.
  - CHECK scenario_index >= 1 — `ck_budget_scenarios_scenario_index_positive`.

Index:
  - `idx_budget_scenarios_tenant_id_period_key` — (tenant_id, period_key)
    lookup hot path.

RLS: `supabase/policies/0016_budget_scenarios_rls.sql` (4-policy split per
AD-3 + AD-2 INSERT-only soft invariant — scenario rows are read-mostly,
the 1차 잠금 is enforced at the service layer + DB UNIQUE constraint
defense-in-depth).

Down revision: 0025_tenants_deletion_status (Story 12.3 wire).

Revision ID: 0026_budget_scenarios
Revises:    0025_tenants_deletion_status
Create Date: 2026-08-15
"""

from __future__ import annotations

from alembic import op

revision = "0026_budget_scenarios"
down_revision = "0025_tenants_deletion_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Table ──────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE budget_scenarios (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            period_key TEXT NOT NULL,
            real_period_key TEXT NOT NULL,
            scenario_index INTEGER NOT NULL DEFAULT 1,
            scenario_hash TEXT NOT NULL,
            created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            created_at_kst TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_budget_scenarios_tenant_id_period_key
                UNIQUE (tenant_id, period_key),
            CONSTRAINT uq_budget_scenarios_tenant_id_real_period_key
                UNIQUE (tenant_id, real_period_key),
            CONSTRAINT ck_budget_scenarios_period_key_pattern
                CHECK (period_key ~ '^\\d{4}-(0[1-9]|1[0-2])#B[1-9]\\d*'),
            CONSTRAINT ck_budget_scenarios_real_period_key_pattern
                CHECK (real_period_key ~ '^\\d{4}-(0[1-9]|1[0-2])'),
            CONSTRAINT ck_budget_scenarios_scenario_index_positive
                CHECK (scenario_index >= 1)
        )
        """
    )

    # ── Index: tenant_id + period_key lookup hot path ─────────────
    op.execute(
        "CREATE INDEX idx_budget_scenarios_tenant_id_period_key "
        "ON budget_scenarios (tenant_id, period_key)"
    )

    # ── Documentation ───────────────────────────────────────────────
    op.execute(
        "COMMENT ON TABLE budget_scenarios IS "
        "'Story 8.1 — AD-24 virtual budget period key + 1차 시나리오 1개 잠금 "
        "(PRD §F8.1 + §15 NON-GOAL #2). Service-layer `validate_scenario_uniqueness` "
        "1차 gate + DB UNIQUE(tenant_id, real_period_key) 제약 defense-in-depth "
        "(CR 12-5 L3). 4-role read (owner+member+viewer+consultant_proxy); owner+member write. "
        "2nd scenario creation honestly DEFER to Story 8-2 (cj-style follow-up).'"
    )
    op.execute(
        "COMMENT ON COLUMN budget_scenarios.period_key IS "
        "'AD-24 §6.2 virtual budget period key `YYYY-MM#B<n>` (e.g., `2026-07#B1`). "
        "Real fiscal key (`2026-07`)는 invalid — M8 virtual only.'"
    )
    op.execute(
        "COMMENT ON COLUMN budget_scenarios.real_period_key IS "
        "'AD-24 §6.1 real fiscal period key `YYYY-MM`. 1차 MVP = 1 scenario per real period.'"
    )
    op.execute(
        "COMMENT ON COLUMN budget_scenarios.scenario_hash IS "
        "'V8 determinism sha256 hexdigest (sha256:32hex). Computed via kernel "
        "`packages.cost_engine.budget_period_key.compute_budget_scenario_hash`.'"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS budget_scenarios")
