"""Story Phase 10 — phase_10 SLO Engineering / Error Budget Management tables.

Phase 10 (cj-style 103번째 wire) — AD-37 (b)(d)(e)(f) verbatim +
§F26.1 + §F26.3 + §F26.4 + §F26.5.

Background:
- Phase 9 wire `e7670e1` (cj-style 99번째) shipped chaos engineering +
  auto-rollback + multi-region chaos. Phase 10 territory carries SLO
  Engineering / Error Budget Management forward.
- §F26.4 tenant-scoped + multi-region SLO aggregation 결정 wire:
  - phase_10_slo_definitions + phase_10_error_budgets + phase_10_slo_overrides
    3 tables with RLS policies.
- §F26.1 SLO definition DSL:
  - SloDefinition TypedDict 13 fields (F26.1.2 verbatim).
- 7 ACs PRD §F26.1~§F26.7 verbatim.

Schema (PRD §F26.4.5~§F26.4.9 verbatim + AD-37 verbatim):

1. phase_10_slo_definitions (PRD §F26.4.5 + §F26.1 verbatim):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
   - slo_id: TEXT UNIQUE
   - service: TEXT
   - sli_type: TEXT enum 5 values (CHECK)
   - objective: NUMERIC(5,2)
   - window: TEXT enum 6 values (CHECK)
   - burn_rate_threshold: NUMERIC(8,2)
   - error_budget_policy: TEXT enum 3 values (CHECK)
   - region: TEXT enum 3 values (CHECK)
   - multi_region_aggregation: TEXT enum 4 values (CHECK)
   - freeze_enabled: BOOLEAN DEFAULT FALSE
   - auto_rollback_trigger: BOOLEAN DEFAULT TRUE
   - governance_required: BOOLEAN DEFAULT FALSE
   - state: TEXT enum 4 values (CHECK) — draft/active/paused/retired
   - actor_id: UUID FK users(id)
   - trace_id: TEXT
   - created_at: TIMESTAMPTZ DEFAULT NOW()
   - updated_at: TIMESTAMPTZ DEFAULT NOW()

2. phase_10_error_budgets (PRD §F26.3.2 verbatim):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - slo_id: TEXT (FK phase_10_slo_definitions.slo_id)
   - budget_total_minutes: NUMERIC(10,2)
   - budget_consumed_minutes: NUMERIC(10,2)
   - budget_remaining_minutes: NUMERIC(10,2)
   - freeze_triggered: BOOLEAN DEFAULT FALSE
   - exhaustion_predicted_at: TIMESTAMPTZ NULL
   - last_evaluated_at: TIMESTAMPTZ DEFAULT NOW()

3. phase_10_slo_overrides (PRD §F26.4.5 verbatim):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - override_id: TEXT UNIQUE
   - slo_id: TEXT
   - objective_override: NUMERIC(5,2) NULL
   - window_override: TEXT NULL
   - effective_from: TIMESTAMPTZ
   - expires_at: TIMESTAMPTZ NULL
   - created_at: TIMESTAMPTZ DEFAULT NOW()

Indexes (PRD §F26.4 verbatim):
- idx_phase_10_slo_definitions_tenant_state (tenant_id, state, updated_at DESC)
- uq_phase_10_slo_definitions_slo_id UNIQUE
- idx_phase_10_error_budgets_tenant_slo (tenant_id, slo_id)
- uq_phase_10_slo_overrides_override_id UNIQUE
- uq_phase_10_slo_overrides_slo_tenant UNIQUE(slo_id, tenant_id)
- idx_phase_10_slo_overrides_tenant_slo (tenant_id, slo_id)

CHECK constraints (PRD §F26.4.5 verbatim):
- ck_phase_10_slo_definitions_sli_type
- ck_phase_10_slo_definitions_window
- ck_phase_10_slo_definitions_error_budget_policy
- ck_phase_10_slo_definitions_region
- ck_phase_10_slo_definitions_multi_region_aggregation
- ck_phase_10_slo_definitions_state

RLS policies (CR 0-2 verbatim):
- phase_10_slo_definitions_tenant_isolation ON phase_10_slo_definitions
- phase_10_error_budgets_tenant_isolation ON phase_10_error_budgets
- phase_10_slo_overrides_tenant_isolation ON phase_10_slo_overrides
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)

CR lessons applied:
- Industry-agnostic pattern (CR 12-1 L4) — SLO engineering granted to
  all 4 industries via SLO_ENGINEERING capability gate.
- CR 1-1 audit-first INSERT — 3 NEW audit log actions (slo_target_updated
  + slo_budget_exhausted + slo_violation_detected).
- CR 0-2 RLS verbatim — all 3 tables have RLS policies.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0042_phase_10_slo_engineering"
down_revision: str | None = "0041_phase_9_chaos_engineering"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Enum-like CHECK constraint values (single source of truth) ──
VALID_SLI_TYPES = (
    "latency",
    "availability",
    "throughput",
    "error_rate",
    "freshness",
)

VALID_WINDOWS = ("1h", "6h", "24h", "3d", "7d", "30d")

VALID_BUDGET_POLICIES = (
    "freeze_on_exhaust",
    "alert_only",
    "auto_rollback",
)

VALID_REGIONS = ("seoul", "tokyo", "all")

VALID_AGGREGATIONS = (
    "weighted_avg",
    "min",
    "max",
    "any_failure",
)

VALID_STATES = (
    "draft",
    "active",
    "paused",
    "retired",
)


def upgrade() -> None:
    """Create `phase_10_slo_definitions` + `phase_10_error_budgets` +
    `phase_10_slo_overrides` 3 tables.

    Per PRD §F26.4.5~§F26.4.9 verbatim schema + RLS policy + 6 CHECK
    constraints + 6 indexes + 1 UNIQUE composite constraint.
    """
    # ── 1. phase_10_slo_definitions ───────────────────────────
    op.create_table(
        "phase_10_slo_definitions",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slo_id", sa.Text(), nullable=False),
        sa.Column("service", sa.Text(), nullable=False),
        sa.Column("sli_type", sa.Text(), nullable=False),
        sa.Column("objective", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("window", sa.Text(), nullable=False),
        sa.Column("burn_rate_threshold", sa.Numeric(precision=8, scale=2), nullable=False),
        sa.Column("error_budget_policy", sa.Text(), nullable=False),
        sa.Column("region", sa.Text(), nullable=False),
        sa.Column("multi_region_aggregation", sa.Text(), nullable=False),
        sa.Column(
            "freeze_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "auto_rollback_trigger",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
        ),
        sa.Column(
            "governance_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column("state", sa.Text(), nullable=False, server_default="draft"),
        sa.Column(
            "actor_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Indexes
    op.create_index(
        "idx_phase_10_slo_definitions_tenant_state",
        "phase_10_slo_definitions",
        ["tenant_id", "state", "updated_at"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_10_slo_definitions_slo_id",
        "phase_10_slo_definitions",
        ["slo_id"],
    )

    # CHECK constraints
    op.create_check_constraint(
        "ck_phase_10_slo_definitions_sli_type",
        "phase_10_slo_definitions",
        f"sli_type IN {VALID_SLI_TYPES!r}",
    )
    op.create_check_constraint(
        "ck_phase_10_slo_definitions_window",
        "phase_10_slo_definitions",
        # D-CI-FUNC-9 cj-235 fix: `window` is a Postgres 15 reserved
        # keyword (per SQL Key Words appendix, "reserved, requires AS").
        # Bare `window IN (...)` aborts with
        # `syntax error at or near "window"`. Quote the column name
        # so Postgres parses it as an identifier, not a clause. Other
        # column names in this file (`state`, `region`, `sli_type`,
        # `multi_region_aggregation`, `error_budget_policy`) are
        # non-reserved and don't need quoting.
        f'"window" IN {VALID_WINDOWS!r}',
    )
    op.create_check_constraint(
        "ck_phase_10_slo_definitions_error_budget_policy",
        "phase_10_slo_definitions",
        f"error_budget_policy IN {VALID_BUDGET_POLICIES!r}",
    )
    op.create_check_constraint(
        "ck_phase_10_slo_definitions_region",
        "phase_10_slo_definitions",
        f"region IN {VALID_REGIONS!r}",
    )
    op.create_check_constraint(
        "ck_phase_10_slo_definitions_multi_region_aggregation",
        "phase_10_slo_definitions",
        f"multi_region_aggregation IN {VALID_AGGREGATIONS!r}",
    )
    op.create_check_constraint(
        "ck_phase_10_slo_definitions_state",
        "phase_10_slo_definitions",
        f"state IN {VALID_STATES!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE phase_10_slo_definitions ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_10_slo_definitions_tenant_isolation
            ON phase_10_slo_definitions
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 2. phase_10_error_budgets ─────────────────────────────
    op.create_table(
        "phase_10_error_budgets",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slo_id", sa.Text(), nullable=False),
        sa.Column("budget_total_minutes", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("budget_consumed_minutes", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column(
            "budget_remaining_minutes",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
        ),
        sa.Column(
            "freeze_triggered",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "exhaustion_predicted_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "last_evaluated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Index
    op.create_index(
        "idx_phase_10_error_budgets_tenant_slo",
        "phase_10_error_budgets",
        ["tenant_id", "slo_id"],
        unique=False,
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE phase_10_error_budgets ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_10_error_budgets_tenant_isolation
            ON phase_10_error_budgets
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 3. phase_10_slo_overrides ─────────────────────────────
    op.create_table(
        "phase_10_slo_overrides",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("tenant_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("override_id", sa.Text(), nullable=False),
        sa.Column("slo_id", sa.Text(), nullable=False),
        sa.Column(
            "objective_override",
            sa.Numeric(precision=5, scale=2),
            nullable=True,
        ),
        sa.Column("window_override", sa.Text(), nullable=True),
        sa.Column(
            "effective_from",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Indexes
    op.create_index(
        "idx_phase_10_slo_overrides_tenant_slo",
        "phase_10_slo_overrides",
        ["tenant_id", "slo_id"],
        unique=False,
    )

    # UNIQUE constraint
    op.create_unique_constraint(
        "uq_phase_10_slo_overrides_override_id",
        "phase_10_slo_overrides",
        ["override_id"],
    )

    # UNIQUE composite (PRD §F26.4.8 verbatim — tenant cannot have multiple
    # overrides for the same SLO)
    op.create_unique_constraint(
        "uq_phase_10_slo_overrides_slo_tenant",
        "phase_10_slo_overrides",
        ["slo_id", "tenant_id"],
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE phase_10_slo_overrides ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_10_slo_overrides_tenant_isolation
            ON phase_10_slo_overrides
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    """Drop `phase_10_slo_overrides` + `phase_10_error_budgets` +
    `phase_10_slo_definitions` 3 tables.
    """
    # Drop in reverse order (FK dependencies)
    op.execute("DROP POLICY IF EXISTS phase_10_slo_overrides_tenant_isolation ON phase_10_slo_overrides;")
    op.execute("ALTER TABLE phase_10_slo_overrides DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "uq_phase_10_slo_overrides_slo_tenant", "phase_10_slo_overrides", type_="unique"
    )
    op.drop_constraint(
        "uq_phase_10_slo_overrides_override_id", "phase_10_slo_overrides", type_="unique"
    )
    op.drop_index(
        "idx_phase_10_slo_overrides_tenant_slo", table_name="phase_10_slo_overrides"
    )
    op.drop_table("phase_10_slo_overrides")

    op.execute("DROP POLICY IF EXISTS phase_10_error_budgets_tenant_isolation ON phase_10_error_budgets;")
    op.execute("ALTER TABLE phase_10_error_budgets DISABLE ROW LEVEL SECURITY;")
    op.drop_index(
        "idx_phase_10_error_budgets_tenant_slo", table_name="phase_10_error_budgets"
    )
    op.drop_table("phase_10_error_budgets")

    op.execute("DROP POLICY IF EXISTS phase_10_slo_definitions_tenant_isolation ON phase_10_slo_definitions;")
    op.execute("ALTER TABLE phase_10_slo_definitions DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "ck_phase_10_slo_definitions_state",
        "phase_10_slo_definitions",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_10_slo_definitions_multi_region_aggregation",
        "phase_10_slo_definitions",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_10_slo_definitions_region",
        "phase_10_slo_definitions",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_10_slo_definitions_error_budget_policy",
        "phase_10_slo_definitions",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_10_slo_definitions_window",
        "phase_10_slo_definitions",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_10_slo_definitions_sli_type",
        "phase_10_slo_definitions",
        type_="check",
    )
    op.drop_constraint(
        "uq_phase_10_slo_definitions_slo_id", "phase_10_slo_definitions", type_="unique"
    )
    op.drop_index(
        "idx_phase_10_slo_definitions_tenant_state",
        table_name="phase_10_slo_definitions",
    )
    op.drop_table("phase_10_slo_definitions")
