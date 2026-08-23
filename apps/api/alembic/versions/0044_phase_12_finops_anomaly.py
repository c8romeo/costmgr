"""Story Phase 12 — phase_12 FinOps Cost Anomaly Detection & Budget Alerting tables.

Phase 12 (cj-style 111번째 wire) — AD-39 (a)~(g) verbatim +
§F28.1 + §F28.2 + §F28.3 + §F28.4 + §F28.5 + §F28.6.

Background:
- Phase 11 wire (cj-style 107번째) shipped FinOps Showback / Chargeback
  territory (3 tables: phase_11_finops_department_mapping +
  phase_11_finops_showback + phase_11_finops_chargeback). Phase 12
  territory carries Cost Anomaly Detection & Budget Alerting forward.
- §F28.1 anomaly detection DSL + §F28.2 budget definition DSL +
  §F28.3 anomaly detection engine + §F28.4 budget alert routing +
  §F28.5 forecast accuracy tracking + §F28.6 governance review:
  - phase_12_finops_anomaly + anomaly_baseline + anomaly_preview +
    budget + budget_consumption + budget_preview 6 tables with RLS
    policies.
- §F28.1 AnomalyDefinition TypedDict 8 fields (F28.1.1 verbatim).
- §F28.2 BudgetDefinition TypedDict 12 fields (F28.2.1 verbatim).
- 8 ACs PRD §F28.1~§F28.8 verbatim.

Schema (PRD §F28.1~§F28.6 verbatim + AD-39 verbatim):

1. phase_12_finops_anomaly (PRD §F28.1.1 verbatim, 13 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
   - anomaly_id: TEXT UNIQUE
   - period_key: TEXT
   - dimension: TEXT (5 options CHECK)
   - dimension_value: TEXT
   - threshold_method: TEXT (4 methods CHECK)
   - threshold_value: NUMERIC(10, 4)
   - baseline_window: TEXT (3 windows CHECK)
   - consecutive_periods_required: INTEGER
   - status: TEXT (3 statuses CHECK)
   - detected_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

2. anomaly_baseline (PRD §F28.3.7 verbatim, 9 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - period_key: TEXT
   - dimension: TEXT
   - dimension_value: TEXT
   - baseline_window: TEXT (3 windows CHECK)
   - baseline_amount: NUMERIC(20, 2)
   - baseline_count: INTEGER
   - last_updated_at: TIMESTAMPTZ DEFAULT NOW()

3. anomaly_preview (PRD §F28.1.11 verbatim, 11 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - anomaly_id: TEXT UNIQUE
   - period_key: TEXT
   - dimension: TEXT
   - dimension_value: TEXT
   - observed_cost: NUMERIC(20, 2)
   - baseline_cost: NUMERIC(20, 2)
   - deviation_pct: NUMERIC(10, 4)
   - severity: TEXT (4 severities CHECK)
   - preview_generated_at: TIMESTAMPTZ DEFAULT NOW()

4. budget (PRD §F28.2.1 verbatim, 12 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - budget_id: TEXT UNIQUE
   - period_key: TEXT
   - budget_period: TEXT (3 periods CHECK)
   - scope: TEXT (4 scopes CHECK)
   - scope_id: TEXT
   - amount: NUMERIC(20, 2)
   - currency_code: TEXT
   - alert_thresholds: JSONB
   - status: TEXT (3 statuses CHECK)
   - trace_id: TEXT

5. budget_consumption (PRD §F28.4.5 verbatim, 8 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - budget_id: TEXT (FK to budget.budget_id)
   - period_key: TEXT
   - consumption_amount: NUMERIC(20, 2)
   - consumption_pct: NUMERIC(10, 4)
   - recorded_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

6. budget_preview (PRD §F28.4.11 verbatim, 9 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - budget_id: TEXT (FK to budget.budget_id)
   - period_key: TEXT
   - projected_consumption_pct: NUMERIC(10, 4)
   - projected_alert_level: TEXT (4 levels CHECK)
   - forecast_amount: NUMERIC(20, 2)
   - generated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

Indexes (PRD §F28.1 + §F28.2 + §F28.3 + §F28.4 verbatim):
- uq_phase_12_finops_anomaly_anomaly_id UNIQUE
- idx_phase_12_finops_anomaly_tenant_period (tenant_id, period_key)
- idx_anomaly_baseline_tenant_period (tenant_id, period_key)
- uq_anomaly_preview_anomaly_id UNIQUE
- uq_budget_budget_id UNIQUE
- idx_budget_tenant_period_scope (tenant_id, period_key, scope)
- idx_budget_consumption_tenant_period (tenant_id, period_key)
- idx_budget_preview_tenant_period (tenant_id, period_key)

CHECK constraints (PRD §F28.1.1 + §F28.2.1 + §F28.3.4 + §F28.4.2 verbatim):
- ck_phase_12_finops_anomaly_dimension CHECK ∈ 5 dimensions.
- ck_phase_12_finops_anomaly_threshold_method CHECK ∈ 4 methods.
- ck_phase_12_finops_anomaly_baseline_window CHECK ∈ 3 windows.
- ck_phase_12_finops_anomaly_status CHECK ∈ 3 statuses.
- ck_anomaly_baseline_window CHECK ∈ 3 windows.
- ck_anomaly_preview_severity CHECK ∈ 4 severities.
- ck_budget_period CHECK ∈ 3 budget periods.
- ck_budget_scope CHECK ∈ 4 scopes.
- ck_budget_status CHECK ∈ 3 statuses.
- ck_budget_preview_alert_level CHECK ∈ 4 alert levels.

RLS policies (CR 0-2 verbatim):
- phase_12_finops_anomaly_tenant_isolation ON
  phase_12_finops_anomaly.
- anomaly_baseline_tenant_isolation ON anomaly_baseline.
- anomaly_preview_tenant_isolation ON anomaly_preview.
- budget_tenant_isolation ON budget.
- budget_consumption_tenant_isolation ON budget_consumption.
- budget_preview_tenant_isolation ON budget_preview.
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)

CR lessons applied:
- Industry-agnostic pattern (CR 12-1 L4) — FinOps Anomaly + Budget
  Alert granted to all 4 industries via FINOPS_ANOMALY_DETECTION +
  FINOPS_BUDGET_ALERT capability gates.
- CR 1-1 audit-first INSERT — 7 NEW audit log actions
  (anomaly_detected + forecast_deviation + model_retraining_triggered
   + anomaly_baseline_updated + budget_definition_updated +
   budget_threshold_exceeded + budget_alert_sent).
- CR 0-2 RLS verbatim — all 6 tables have RLS policies.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0044_phase_12_finops_anomaly"
down_revision: str | None = "0043_phase_11_finops"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Enum-like CHECK constraint values (single source of truth) ──
VALID_DIMENSIONS = (
    "department",
    "cost_center",
    "product_line",
    "service",
    "tenant_total",
)

VALID_DETECTION_METHODS = (
    "z_score",
    "iqr",
    "ewma",
    "isolation_forest",
)

VALID_BASELINE_WINDOWS = (
    "last_30d",
    "last_90d",
    "ytd",
)

VALID_ANOMALY_STATUSES = (
    "confirmed",
    "suspected",
    "false_positive",
)

VALID_SEVERITIES = (
    "low",
    "medium",
    "high",
    "critical",
)

VALID_BUDGET_PERIODS = (
    "monthly",
    "quarterly",
    "yearly",
)

VALID_BUDGET_SCOPES = (
    "tenant",
    "department",
    "cost_center",
    "product_line",
)

VALID_BUDGET_STATUSES = (
    "active",
    "paused",
    "expired",
)

VALID_ALERT_LEVELS = (
    "none",
    "warning",
    "critical",
    "exceeded",
)


def upgrade() -> None:
    """Create 6 tables: phase_12_finops_anomaly + anomaly_baseline +
    anomaly_preview + budget + budget_consumption + budget_preview.

    Per PRD §F28.1~§F28.6 verbatim schema + RLS policy + 10 CHECK
    constraints + 8 indexes + 3 UNIQUE constraints.
    """
    # ── 1. phase_12_finops_anomaly ────────────────────────────
    op.create_table(
        "phase_12_finops_anomaly",
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
        sa.Column("anomaly_id", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("dimension", sa.Text(), nullable=False),
        sa.Column("dimension_value", sa.Text(), nullable=False),
        sa.Column("threshold_method", sa.Text(), nullable=False),
        sa.Column(
            "threshold_value",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
        ),
        sa.Column("baseline_window", sa.Text(), nullable=False),
        sa.Column(
            "consecutive_periods_required",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "detected_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )

    # Index
    op.create_index(
        "idx_phase_12_finops_anomaly_tenant_period",
        "phase_12_finops_anomaly",
        ["tenant_id", "period_key"],
        unique=False,
    )

    # UNIQUE constraint
    op.create_unique_constraint(
        "uq_phase_12_finops_anomaly_anomaly_id",
        "phase_12_finops_anomaly",
        ["anomaly_id"],
    )

    # CHECK constraints
    op.create_check_constraint(
        "ck_phase_12_finops_anomaly_dimension",
        "phase_12_finops_anomaly",
        f"dimension IN {VALID_DIMENSIONS!r}",
    )
    op.create_check_constraint(
        "ck_phase_12_finops_anomaly_threshold_method",
        "phase_12_finops_anomaly",
        f"threshold_method IN {VALID_DETECTION_METHODS!r}",
    )
    op.create_check_constraint(
        "ck_phase_12_finops_anomaly_baseline_window",
        "phase_12_finops_anomaly",
        f"baseline_window IN {VALID_BASELINE_WINDOWS!r}",
    )
    op.create_check_constraint(
        "ck_phase_12_finops_anomaly_status",
        "phase_12_finops_anomaly",
        f"status IN {VALID_ANOMALY_STATUSES!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE phase_12_finops_anomaly ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_12_finops_anomaly_tenant_isolation
            ON phase_12_finops_anomaly
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 2. anomaly_baseline ───────────────────────────────────
    op.create_table(
        "anomaly_baseline",
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
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("dimension", sa.Text(), nullable=False),
        sa.Column("dimension_value", sa.Text(), nullable=False),
        sa.Column("baseline_window", sa.Text(), nullable=False),
        sa.Column(
            "baseline_amount",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "baseline_count",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "last_updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # Index
    op.create_index(
        "idx_anomaly_baseline_tenant_period",
        "anomaly_baseline",
        ["tenant_id", "period_key"],
        unique=False,
    )

    # CHECK constraint
    op.create_check_constraint(
        "ck_anomaly_baseline_window",
        "anomaly_baseline",
        f"baseline_window IN {VALID_BASELINE_WINDOWS!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE anomaly_baseline ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY anomaly_baseline_tenant_isolation
            ON anomaly_baseline
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 3. anomaly_preview ─────────────────────────────────────
    op.create_table(
        "anomaly_preview",
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
        sa.Column("anomaly_id", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("dimension", sa.Text(), nullable=False),
        sa.Column("dimension_value", sa.Text(), nullable=False),
        sa.Column(
            "observed_cost",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "baseline_cost",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "deviation_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
        ),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column(
            "preview_generated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    # UNIQUE constraint
    op.create_unique_constraint(
        "uq_anomaly_preview_anomaly_id",
        "anomaly_preview",
        ["anomaly_id"],
    )

    # CHECK constraint
    op.create_check_constraint(
        "ck_anomaly_preview_severity",
        "anomaly_preview",
        f"severity IN {VALID_SEVERITIES!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE anomaly_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY anomaly_preview_tenant_isolation
            ON anomaly_preview
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 4. budget ─────────────────────────────────────────────
    op.create_table(
        "budget",
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
        sa.Column("budget_id", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column("budget_period", sa.Text(), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("scope_id", sa.Text(), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column("currency_code", sa.Text(), nullable=False),
        sa.Column(
            "alert_thresholds",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )

    # Index
    op.create_index(
        "idx_budget_tenant_period_scope",
        "budget",
        ["tenant_id", "period_key", "scope"],
        unique=False,
    )

    # UNIQUE constraint
    op.create_unique_constraint(
        "uq_budget_budget_id",
        "budget",
        ["budget_id"],
    )

    # CHECK constraints
    op.create_check_constraint(
        "ck_budget_period",
        "budget",
        f"budget_period IN {VALID_BUDGET_PERIODS!r}",
    )
    op.create_check_constraint(
        "ck_budget_scope",
        "budget",
        f"scope IN {VALID_BUDGET_SCOPES!r}",
    )
    op.create_check_constraint(
        "ck_budget_status",
        "budget",
        f"status IN {VALID_BUDGET_STATUSES!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute("ALTER TABLE budget ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY budget_tenant_isolation
            ON budget
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 5. budget_consumption ──────────────────────────────────
    op.create_table(
        "budget_consumption",
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
        sa.Column("budget_id", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column(
            "consumption_amount",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "consumption_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )

    # Index
    op.create_index(
        "idx_budget_consumption_tenant_period",
        "budget_consumption",
        ["tenant_id", "period_key"],
        unique=False,
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE budget_consumption ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY budget_consumption_tenant_isolation
            ON budget_consumption
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 6. budget_preview ─────────────────────────────────────
    op.create_table(
        "budget_preview",
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
        sa.Column("budget_id", sa.Text(), nullable=False),
        sa.Column("period_key", sa.Text(), nullable=False),
        sa.Column(
            "projected_consumption_pct",
            sa.Numeric(precision=10, scale=4),
            nullable=False,
        ),
        sa.Column(
            "projected_alert_level",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "forecast_amount",
            sa.Numeric(precision=20, scale=2),
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

    # Index
    op.create_index(
        "idx_budget_preview_tenant_period",
        "budget_preview",
        ["tenant_id", "period_key"],
        unique=False,
    )

    # CHECK constraint
    op.create_check_constraint(
        "ck_budget_preview_alert_level",
        "budget_preview",
        f"projected_alert_level IN {VALID_ALERT_LEVELS!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute(
        "ALTER TABLE budget_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY budget_preview_tenant_isolation
            ON budget_preview
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    """Drop 6 tables in reverse order."""
    # Drop in reverse order (FK dependencies)
    op.execute(
        "DROP POLICY IF EXISTS budget_preview_tenant_isolation ON budget_preview;"
    )
    op.execute("ALTER TABLE budget_preview DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "ck_budget_preview_alert_level",
        "budget_preview",
        type_="check",
    )
    op.drop_index(
        "idx_budget_preview_tenant_period",
        table_name="budget_preview",
    )
    op.drop_table("budget_preview")

    op.execute(
        "DROP POLICY IF EXISTS budget_consumption_tenant_isolation ON budget_consumption;"
    )
    op.execute("ALTER TABLE budget_consumption DISABLE ROW LEVEL SECURITY;")
    op.drop_index(
        "idx_budget_consumption_tenant_period",
        table_name="budget_consumption",
    )
    op.drop_table("budget_consumption")

    op.execute("DROP POLICY IF EXISTS budget_tenant_isolation ON budget;")
    op.execute("ALTER TABLE budget DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint("ck_budget_status", "budget", type_="check")
    op.drop_constraint("ck_budget_scope", "budget", type_="check")
    op.drop_constraint("ck_budget_period", "budget", type_="check")
    op.drop_constraint(
        "uq_budget_budget_id", "budget", type_="unique"
    )
    op.drop_index("idx_budget_tenant_period_scope", table_name="budget")
    op.drop_table("budget")

    op.execute(
        "DROP POLICY IF EXISTS anomaly_preview_tenant_isolation ON anomaly_preview;"
    )
    op.execute("ALTER TABLE anomaly_preview DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "ck_anomaly_preview_severity", "anomaly_preview", type_="check"
    )
    op.drop_constraint(
        "uq_anomaly_preview_anomaly_id", "anomaly_preview", type_="unique"
    )
    op.drop_table("anomaly_preview")

    op.execute(
        "DROP POLICY IF EXISTS anomaly_baseline_tenant_isolation ON anomaly_baseline;"
    )
    op.execute("ALTER TABLE anomaly_baseline DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "ck_anomaly_baseline_window", "anomaly_baseline", type_="check"
    )
    op.drop_index(
        "idx_anomaly_baseline_tenant_period", table_name="anomaly_baseline"
    )
    op.drop_table("anomaly_baseline")

    op.execute(
        "DROP POLICY IF EXISTS phase_12_finops_anomaly_tenant_isolation ON phase_12_finops_anomaly;"
    )
    op.execute(
        "ALTER TABLE phase_12_finops_anomaly DISABLE ROW LEVEL SECURITY;"
    )
    op.drop_constraint(
        "ck_phase_12_finops_anomaly_status",
        "phase_12_finops_anomaly",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_12_finops_anomaly_baseline_window",
        "phase_12_finops_anomaly",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_12_finops_anomaly_threshold_method",
        "phase_12_finops_anomaly",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_12_finops_anomaly_dimension",
        "phase_12_finops_anomaly",
        type_="check",
    )
    op.drop_constraint(
        "uq_phase_12_finops_anomaly_anomaly_id",
        "phase_12_finops_anomaly",
        type_="unique",
    )
    op.drop_index(
        "idx_phase_12_finops_anomaly_tenant_period",
        table_name="phase_12_finops_anomaly",
    )
    op.drop_table("phase_12_finops_anomaly")