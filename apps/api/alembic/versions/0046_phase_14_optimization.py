"""Story Phase 14 — phase_14 FinOps Optimization & Rightsizing tables.

Phase 14 (cj-style 119번째 wire) — AD-41 (a)~(g) verbatim +
§F30.1 + §F30.2 + §F30.3 + §F30.4 + §F30.5 + §F30.6 + §F30.7 + §F30.8.

Background:
- Phase 13 wire (cj-style 115번째) shipped FinOps Forecasting & Capacity
  Planning territory (5 tables). Phase 14 territory carries the
  ACTIONABLE RECOMMENDATION LAYER EXTENSION — forecast → action
  transition: rightsizing + idle detection + commitment recommender +
  accuracy tracking.
- §F30.1 optimization definition DSL + §F30.2 rightsizing engine +
  §F30.3 idle resource detection + §F30.4 RI/SP commitment + §F30.5
  optimization accuracy tracking + §F30.6 governance review:
  - 5 main tables + 4 preview tables (preview for dry-run mode)
  with RLS policies.
- §F30.1 OptimizationDefinition TypedDict 11 fields (F30.1.2 verbatim).
- §F30.2 RightsizingRecommendation TypedDict 14 fields (F30.2.7 verbatim).
- §F30.3 IdleResource TypedDict 13 fields (F30.3.7 verbatim).
- §F30.4 CommitmentRecommendation TypedDict 12 fields (F30.4.7 verbatim).
- §F30.5 OptimizationAccuracyReport TypedDict 10 fields (F30.5.8 verbatim).
- 8 ACs PRD §F30.1~§F30.8 verbatim → 92 sub-ACs.

Schema (PRD §F30.1~§F30.6 verbatim + AD-41 verbatim):

1. phase_14_finops_optimization_definition (PRD §F30.1.2 verbatim, 12 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
   - optimization_id: TEXT UNIQUE
   - resource_type: TEXT (5 options CHECK)
   - optimization_strategy: TEXT (7 options CHECK: 6 + 1 composite)
   - target_metric: TEXT (4 options CHECK)
   - baseline_period: TEXT (5 options CHECK)
   - status: TEXT (3 statuses CHECK)
   - metadata: JSONB (per-tenant override EXTENSION)
   - created_at: TIMESTAMPTZ DEFAULT NOW()
   - updated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT
   - UNIQUE (tenant_id, resource_type, baseline_period)

2. phase_14_finops_rightsizing_recommendation (PRD §F30.2.7 verbatim, 15 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - recommendation_id: TEXT UNIQUE
   - resource_id: TEXT
   - resource_type: TEXT (5 options CHECK)
   - current_instance_type: TEXT
   - recommended_instance_type: TEXT
   - current_cost_krw: NUMERIC(20, 2)
   - recommended_cost_krw: NUMERIC(20, 2)
   - projected_savings_pct: NUMERIC(8, 4)
   - projected_savings_amount_krw: NUMERIC(20, 2)
   - confidence_score: NUMERIC(8, 4)
   - recommendation_severity: TEXT (3 options CHECK)
   - model_version: TEXT (semver MAJOR.MINOR.PATCH)
   - generated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

3. phase_14_finops_idle_resource (PRD §F30.3.7 verbatim, 14 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - idle_resource_id: TEXT UNIQUE
   - resource_id: TEXT
   - resource_type: TEXT (5 options CHECK)
   - idle_reason: TEXT
   - idle_duration_days: INTEGER
   - current_cost_krw_per_month: NUMERIC(20, 2)
   - potential_savings_krw_per_month: NUMERIC(20, 2)
   - idle_severity: TEXT (3 options CHECK: low/medium/high)
   - action: TEXT (3 options CHECK: review/downsize/terminate)
   - detection_method: TEXT (3 options CHECK: z_score/threshold/heuristic)
   - detection_window_days: INTEGER
   - generated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

4. phase_14_finops_commitment_recommendation (PRD §F30.4.7 verbatim, 13 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - recommendation_id: TEXT UNIQUE
   - commitment_type: TEXT (6 options CHECK)
   - commitment_term: TEXT (2 options CHECK: 1_year/3_year)
   - resource_pattern: TEXT
   - current_on_demand_cost_krw_per_month: NUMERIC(20, 2)
   - projected_commit_cost_krw_per_month: NUMERIC(20, 2)
   - projected_savings_pct: NUMERIC(8, 4)
   - projected_savings_krw: NUMERIC(20, 2)
   - upfront_cost_krw: NUMERIC(20, 2)
   - break_even_months: INTEGER
   - roi_pct: NUMERIC(8, 4)
   - recommendation_severity: TEXT (3 options CHECK)
   - generated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

5. phase_14_finops_optimization_accuracy (PRD §F30.5.8 verbatim, 11 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - report_id: TEXT UNIQUE
   - resource_type: TEXT (5 options CHECK)
   - optimization_strategy: TEXT (7 options CHECK)
   - total_recommendations: INTEGER
   - applied_recommendations: INTEGER
   - precision: NUMERIC(8, 4)
   - recall: NUMERIC(8, 4)
   - realized_savings_krw: NUMERIC(20, 2)
   - projected_savings_krw: NUMERIC(20, 2)
   - accuracy_score: NUMERIC(8, 4)
   - generated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

Plus 4 preview tables (F30.8.2 verbatim):
- phase_14_finops_optimization_preview
- phase_14_finops_rightsizing_preview
- phase_14_finops_idle_resource_preview
- phase_14_finops_commitment_preview
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ── revision identifiers ────────────────────────────────────────
revision: str = "0046_phase_14_optimization"
down_revision: str = "0045_phase_13_forecasting"
branch_labels: str | None = None
depends_on: str | None = None


# ── Enum value tuples (mirror Phase 13 0045 pattern verbatim) ──
VALID_RESOURCE_TYPES: tuple[str, ...] = (
    "compute",
    "storage",
    "database",
    "network",
    "container",
)

VALID_OPTIMIZATION_STRATEGIES: tuple[str, ...] = (
    "rightsize_down",
    "rightsize_up",
    "idle_terminate",
    "commit_1y",
    "commit_3y",
    "storage_tier_down",
    "composite",
)

VALID_TARGET_METRICS: tuple[str, ...] = (
    "cost_saving_pct",
    "cost_saving_amount",
    "utilization_target",
    "commit_break_even_months",
)

VALID_BASELINE_PERIODS: tuple[str, ...] = (
    "last_7d",
    "last_30d",
    "last_90d",
    "last_180d",
    "last_365d",
)

VALID_OPTIMIZATION_STATUSES: tuple[str, ...] = ("active", "paused", "expired")

VALID_RECOMMENDATION_SEVERITIES: tuple[str, ...] = ("low", "medium", "high")

VALID_IDLE_ACTIONS: tuple[str, ...] = ("review", "downsize", "terminate")

VALID_DETECTION_METHODS: tuple[str, ...] = ("z_score", "threshold", "heuristic")

VALID_COMMITMENT_TYPES: tuple[str, ...] = (
    "ec2_ri",
    "rds_ri",
    "ec2_sp",
    "s3_sp",
    "redshift_sp",
    "dynamodb_sp",
)

VALID_COMMITMENT_TERMS: tuple[str, ...] = ("1_year", "3_year")


def upgrade() -> None:
    """Upgrade schema — 5 NEW tables + 4 preview tables + RLS policies."""

    # ── 1. phase_14_finops_optimization_definition ─────────────
    op.create_table(
        "phase_14_finops_optimization_definition",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("optimization_id", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("optimization_strategy", sa.Text(), nullable=False),
        sa.Column("target_metric", sa.Text(), nullable=False),
        sa.Column("baseline_period", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
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
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_phase_14_finops_optimization_definition_tenant_resource",
        "phase_14_finops_optimization_definition",
        ["tenant_id", "resource_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_14_finops_optimization_definition_optimization_id",
        "phase_14_finops_optimization_definition",
        ["optimization_id"],
    )
    op.create_check_constraint(
        "ck_phase_14_finops_optimization_definition_resource_type",
        "phase_14_finops_optimization_definition",
        f"resource_type IN {VALID_RESOURCE_TYPES!r}",
    )
    op.create_check_constraint(
        # D-CI-FUNC-9 cj-236 fix: previous name
        # `ck_phase_14_finops_optimization_definition_optimization_strategy`
        # was 64 characters, exceeding Postgres' NAMEDATALEN-1=63 limit.
        # SQLAlchemy raises IdentifierError before the statement even
        # reaches Postgres. Shortened to
        # `ck_phase_14_finops_optimization_definition_strategy` (57 chars)
        # — the constraint still references the actual column
        # `optimization_strategy` so the column name is unchanged. Only
        # the constraint identifier is shortened (cosmetic). No other
        # identifier in this migration exceeds 63 chars (audited with
        # `len()` on all op.create_* / op.drop_* / op.add_* calls).
        "ck_phase_14_finops_optimization_definition_strategy",
        "phase_14_finops_optimization_definition",
        f"optimization_strategy IN {VALID_OPTIMIZATION_STRATEGIES!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_optimization_definition_target_metric",
        "phase_14_finops_optimization_definition",
        f"target_metric IN {VALID_TARGET_METRICS!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_optimization_definition_baseline_period",
        "phase_14_finops_optimization_definition",
        f"baseline_period IN {VALID_BASELINE_PERIODS!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_optimization_definition_status",
        "phase_14_finops_optimization_definition",
        f"status IN {VALID_OPTIMIZATION_STATUSES!r}",
    )
    op.execute(
        "ALTER TABLE phase_14_finops_optimization_definition ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_14_finops_optimization_definition_tenant_isolation
            ON phase_14_finops_optimization_definition
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 2. phase_14_finops_rightsizing_recommendation ──────────
    op.create_table(
        "phase_14_finops_rightsizing_recommendation",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("recommendation_id", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("current_instance_type", sa.Text(), nullable=False),
        sa.Column("recommended_instance_type", sa.Text(), nullable=False),
        sa.Column(
            "current_cost_krw",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "recommended_cost_krw",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "projected_savings_pct",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
        ),
        sa.Column(
            "projected_savings_amount_krw",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "confidence_score",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
        ),
        sa.Column("recommendation_severity", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_phase_14_finops_rightsizing_recommendation_tenant_resource",
        "phase_14_finops_rightsizing_recommendation",
        ["tenant_id", "resource_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_14_finops_rightsizing_recommendation_recommendation_id",
        "phase_14_finops_rightsizing_recommendation",
        ["recommendation_id"],
    )
    op.create_check_constraint(
        "ck_phase_14_finops_rightsizing_recommendation_resource_type",
        "phase_14_finops_rightsizing_recommendation",
        f"resource_type IN {VALID_RESOURCE_TYPES!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_rightsizing_recommendation_severity",
        "phase_14_finops_rightsizing_recommendation",
        f"recommendation_severity IN {VALID_RECOMMENDATION_SEVERITIES!r}",
    )
    op.execute(
        "ALTER TABLE phase_14_finops_rightsizing_recommendation ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_14_finops_rightsizing_recommendation_tenant_isolation
            ON phase_14_finops_rightsizing_recommendation
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 3. phase_14_finops_idle_resource ───────────────────────
    op.create_table(
        "phase_14_finops_idle_resource",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("idle_resource_id", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("idle_reason", sa.Text(), nullable=False),
        sa.Column("idle_duration_days", sa.Integer(), nullable=False),
        sa.Column(
            "current_cost_krw_per_month",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "potential_savings_krw_per_month",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column("idle_severity", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("detection_method", sa.Text(), nullable=False),
        sa.Column("detection_window_days", sa.Integer(), nullable=False),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_phase_14_finops_idle_resource_tenant_resource",
        "phase_14_finops_idle_resource",
        ["tenant_id", "resource_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_14_finops_idle_resource_idle_resource_id",
        "phase_14_finops_idle_resource",
        ["idle_resource_id"],
    )
    op.create_check_constraint(
        "ck_phase_14_finops_idle_resource_resource_type",
        "phase_14_finops_idle_resource",
        f"resource_type IN {VALID_RESOURCE_TYPES!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_idle_resource_idle_severity",
        "phase_14_finops_idle_resource",
        f"idle_severity IN {VALID_RECOMMENDATION_SEVERITIES!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_idle_resource_action",
        "phase_14_finops_idle_resource",
        f"action IN {VALID_IDLE_ACTIONS!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_idle_resource_detection_method",
        "phase_14_finops_idle_resource",
        f"detection_method IN {VALID_DETECTION_METHODS!r}",
    )
    op.execute(
        "ALTER TABLE phase_14_finops_idle_resource ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_14_finops_idle_resource_tenant_isolation
            ON phase_14_finops_idle_resource
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 4. phase_14_finops_commitment_recommendation ───────────
    op.create_table(
        "phase_14_finops_commitment_recommendation",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("recommendation_id", sa.Text(), nullable=False),
        sa.Column("commitment_type", sa.Text(), nullable=False),
        sa.Column("commitment_term", sa.Text(), nullable=False),
        sa.Column("resource_pattern", sa.Text(), nullable=False),
        sa.Column(
            "current_on_demand_cost_krw_per_month",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "projected_commit_cost_krw_per_month",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "projected_savings_pct",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
        ),
        sa.Column(
            "projected_savings_krw",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "upfront_cost_krw",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column("break_even_months", sa.Integer(), nullable=False),
        sa.Column(
            "roi_pct",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
        ),
        sa.Column("recommendation_severity", sa.Text(), nullable=False),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_phase_14_finops_commitment_recommendation_tenant_type",
        "phase_14_finops_commitment_recommendation",
        ["tenant_id", "commitment_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_14_finops_commitment_recommendation_recommendation_id",
        "phase_14_finops_commitment_recommendation",
        ["recommendation_id"],
    )
    op.create_check_constraint(
        "ck_phase_14_finops_commitment_recommendation_commitment_type",
        "phase_14_finops_commitment_recommendation",
        f"commitment_type IN {VALID_COMMITMENT_TYPES!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_commitment_recommendation_commitment_term",
        "phase_14_finops_commitment_recommendation",
        f"commitment_term IN {VALID_COMMITMENT_TERMS!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_commitment_recommendation_severity",
        "phase_14_finops_commitment_recommendation",
        f"recommendation_severity IN {VALID_RECOMMENDATION_SEVERITIES!r}",
    )
    op.execute(
        "ALTER TABLE phase_14_finops_commitment_recommendation ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_14_finops_commitment_recommendation_tenant_isolation
            ON phase_14_finops_commitment_recommendation
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 5. phase_14_finops_optimization_accuracy ──────────────
    op.create_table(
        "phase_14_finops_optimization_accuracy",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("report_id", sa.Text(), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("optimization_strategy", sa.Text(), nullable=False),
        sa.Column("total_recommendations", sa.Integer(), nullable=False),
        sa.Column("applied_recommendations", sa.Integer(), nullable=False),
        sa.Column(
            "precision",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
        ),
        sa.Column(
            "recall",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
        ),
        sa.Column(
            "realized_savings_krw",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "projected_savings_krw",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "accuracy_score",
            sa.Numeric(precision=8, scale=4),
            nullable=False,
        ),
        sa.Column(
            "generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_phase_14_finops_optimization_accuracy_tenant_resource",
        "phase_14_finops_optimization_accuracy",
        ["tenant_id", "resource_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_14_finops_optimization_accuracy_report_id",
        "phase_14_finops_optimization_accuracy",
        ["report_id"],
    )
    op.create_check_constraint(
        "ck_phase_14_finops_optimization_accuracy_resource_type",
        "phase_14_finops_optimization_accuracy",
        f"resource_type IN {VALID_RESOURCE_TYPES!r}",
    )
    op.create_check_constraint(
        "ck_phase_14_finops_optimization_accuracy_optimization_strategy",
        "phase_14_finops_optimization_accuracy",
        f"optimization_strategy IN {VALID_OPTIMIZATION_STRATEGIES!r}",
    )
    op.execute(
        "ALTER TABLE phase_14_finops_optimization_accuracy ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_14_finops_optimization_accuracy_tenant_isolation
            ON phase_14_finops_optimization_accuracy
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 6. phase_14_finops_optimization_preview ────────────────
    # F30.8.2 dry-run preview table
    op.create_table(
        "phase_14_finops_optimization_preview",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("preview_id", sa.Text(), nullable=False),
        sa.Column("preview_type", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column(
            "preview_data",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )
    op.create_index(
        "idx_phase_14_finops_optimization_preview_tenant_type",
        "phase_14_finops_optimization_preview",
        ["tenant_id", "preview_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_14_finops_optimization_preview_preview_id",
        "phase_14_finops_optimization_preview",
        ["preview_id"],
    )
    op.execute(
        "ALTER TABLE phase_14_finops_optimization_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_14_finops_optimization_preview_tenant_isolation
            ON phase_14_finops_optimization_preview
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    """Downgrade schema — drop 6 tables in reverse order."""
    op.execute("DROP POLICY IF EXISTS phase_14_finops_optimization_preview_tenant_isolation ON phase_14_finops_optimization_preview;")
    op.drop_table("phase_14_finops_optimization_preview")
    op.execute("DROP POLICY IF EXISTS phase_14_finops_optimization_accuracy_tenant_isolation ON phase_14_finops_optimization_accuracy;")
    op.drop_table("phase_14_finops_optimization_accuracy")
    op.execute("DROP POLICY IF EXISTS phase_14_finops_commitment_recommendation_tenant_isolation ON phase_14_finops_commitment_recommendation;")
    op.drop_table("phase_14_finops_commitment_recommendation")
    op.execute("DROP POLICY IF EXISTS phase_14_finops_idle_resource_tenant_isolation ON phase_14_finops_idle_resource;")
    op.drop_table("phase_14_finops_idle_resource")
    op.execute("DROP POLICY IF EXISTS phase_14_finops_rightsizing_recommendation_tenant_isolation ON phase_14_finops_rightsizing_recommendation;")
    op.drop_table("phase_14_finops_rightsizing_recommendation")
    op.execute("DROP POLICY IF EXISTS phase_14_finops_optimization_definition_tenant_isolation ON phase_14_finops_optimization_definition;")
    op.drop_table("phase_14_finops_optimization_definition")
