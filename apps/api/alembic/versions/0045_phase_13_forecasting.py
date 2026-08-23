"""Story Phase 13 — phase_13 FinOps Forecasting & Capacity Planning tables.

Phase 13 (cj-style 115번째 wire) — AD-39 (a)~(g) verbatim +
§F29.1 + §F29.2 + §F29.3 + §F29.4 + §F29.5 + §F29.6.

Background:
- Phase 12 wire (cj-style 111번째) shipped FinOps Cost Anomaly
  Detection & Budget Alerting territory (6 tables). Phase 13 territory
  carries Forecasting & Capacity Planning forward — extends the
  forecast_deviation baseline into 4-model parallel prediction
  (ARIMA + Prophet + LSTM + ensemble) + 90일 capacity headroom +
  4-input budget burn-rate projection.
- §F29.1 forecast definition DSL + §F29.2 forecast engine +
  §F29.3 capacity headroom analysis + §F29.4 budget burn-rate +
  §F29.5 forecast accuracy tracking + §F29.6 governance review:
  - phase_13_finops_forecast_definition + forecast_result +
    capacity_headroom + budget_burnrate + forecast_preview 5 tables
    with RLS policies.
- §F29.1 ForecastDefinition TypedDict 11 fields (F29.1.1 verbatim).
- §F29.2 ForecastResult TypedDict 10 fields (F29.2.3 verbatim).
- §F29.3 CapacityHeadroomReport TypedDict 14 fields (F29.3.2 verbatim).
- §F29.4 BurnRateProjection TypedDict 12 fields (F29.4.1 verbatim).
- 8 ACs PRD §F29.1~§F29.8 verbatim → 92 sub-ACs.

Schema (PRD §F29.1~§F29.6 verbatim + AD-39 verbatim):

1. phase_13_finops_forecast_definition (PRD §F29.1.1 verbatim, 12 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
   - forecast_id: TEXT UNIQUE
   - target_metric: TEXT (5 options CHECK)
   - dimension_value: TEXT
   - horizon_months: TEXT (4 options CHECK)
   - model_type: TEXT (4 options CHECK)
   - confidence_level: TEXT (4 options CHECK)
   - retraining_cron: TEXT
   - status: TEXT (3 statuses CHECK)
   - created_at: TIMESTAMPTZ DEFAULT NOW()
   - updated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

2. phase_13_finops_forecast_result (PRD §F29.2.3 verbatim, 14 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - forecast_id: TEXT UNIQUE
   - target_metric: TEXT (5 options CHECK)
   - horizon_months: TEXT (4 options CHECK)
   - predicted_values: JSONB (list of floats)
   - confidence_lower: JSONB (list of floats)
   - confidence_upper: JSONB (list of floats)
   - model_type: TEXT (4 options CHECK)
   - model_version: TEXT (semver MAJOR.MINOR.PATCH)
   - generated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT
   - UNIQUE (tenant_id, target_metric, horizon_months)

3. phase_13_finops_capacity_headroom (PRD §F29.3.2 verbatim, 16 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - report_id: TEXT UNIQUE
   - resource_type: TEXT (3 options CHECK: compute/storage/network)
   - saturation_pct: NUMERIC(5, 2)
   - saturation_level: TEXT (3 options CHECK: ok/warning/critical)
   - lookahead_days: INTEGER
   - predicted_utilization: JSONB (list of floats)
   - headroom_pct: NUMERIC(5, 2)
   - primary_model: TEXT
   - ensemble_predicted: JSONB (list of floats)
   - recommendation: TEXT
   - trace_id: TEXT
   - created_at: TIMESTAMPTZ DEFAULT NOW()
   - expires_at: TIMESTAMPTZ
   - UNIQUE (tenant_id, resource_type, lookahead_days)

4. phase_13_finops_budget_burnrate (PRD §F29.4.1 verbatim, 14 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - projection_id: TEXT UNIQUE
   - budget_id: TEXT
   - consumed_budget: NUMERIC(20, 2)
   - total_budget: NUMERIC(20, 2)
   - elapsed_days: INTEGER
   - remaining_days: INTEGER
   - burn_rate_pct: NUMERIC(7, 2)
   - severity: TEXT (4 options CHECK: normal/warning/critical/exceeded)
   - alert_required: BOOLEAN
   - predicted_end_period_spend: NUMERIC(20, 2)
   - trace_id: TEXT
   - projected_at: TIMESTAMPTZ DEFAULT NOW()

5. phase_13_finops_forecast_preview (PRD §F29.1.11 verbatim, 10 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - preview_id: TEXT UNIQUE
   - forecast_id: TEXT
   - horizon_months: TEXT (4 options CHECK)
   - target_metric: TEXT (5 options CHECK)
   - preview_payload: JSONB
   - dry_run: BOOLEAN
   - trace_id: TEXT
   - previewed_at: TIMESTAMPTZ DEFAULT NOW()
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# ── revision identifiers ────────────────────────────────────────
revision: str = "0045_phase_13_forecasting"
down_revision: str = "0044_phase_12_finops_anomaly"
branch_labels: str | None = None
depends_on: str | None = None


# ── Enum value tuples (mirror Phase 12 0044 pattern verbatim) ──
VALID_TARGET_METRICS: tuple[str, ...] = (
    "department",
    "cost_center",
    "product_line",
    "service",
    "tenant_total",
)

VALID_HORIZON_MONTHS: tuple[str, ...] = ("3m", "6m", "12m", "24m")

VALID_MODEL_TYPES: tuple[str, ...] = (
    "arima",
    "prophet",
    "lstm",
    "ensemble",
)

VALID_CONFIDENCE_LEVELS: tuple[str, ...] = ("80", "90", "95", "99")

VALID_FORECAST_STATUSES: tuple[str, ...] = ("active", "paused", "expired")

VALID_RESOURCE_TYPES: tuple[str, ...] = ("compute", "storage", "network")

VALID_SATURATION_LEVELS: tuple[str, ...] = ("ok", "warning", "critical")

VALID_SEVERITY_LEVELS: tuple[str, ...] = (
    "normal",
    "warning",
    "critical",
    "exceeded",
)


def upgrade() -> None:
    """Upgrade schema — 5 NEW tables + RLS policies verbatim Phase 12 pattern."""

    # ── 1. phase_13_finops_forecast_definition ────────────────
    op.create_table(
        "phase_13_finops_forecast_definition",
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
        sa.Column("forecast_id", sa.Text(), nullable=False),
        sa.Column("target_metric", sa.Text(), nullable=False),
        sa.Column("dimension_value", sa.Text(), nullable=False),
        sa.Column("horizon_months", sa.Text(), nullable=False),
        sa.Column("model_type", sa.Text(), nullable=False),
        sa.Column("confidence_level", sa.Text(), nullable=False),
        sa.Column("retraining_cron", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
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
        "idx_phase_13_finops_forecast_definition_tenant_metric",
        "phase_13_finops_forecast_definition",
        ["tenant_id", "target_metric"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_13_finops_forecast_definition_forecast_id",
        "phase_13_finops_forecast_definition",
        ["forecast_id"],
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_definition_target_metric",
        "phase_13_finops_forecast_definition",
        f"target_metric IN {VALID_TARGET_METRICS!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_definition_horizon_months",
        "phase_13_finops_forecast_definition",
        f"horizon_months IN {VALID_HORIZON_MONTHS!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_definition_model_type",
        "phase_13_finops_forecast_definition",
        f"model_type IN {VALID_MODEL_TYPES!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_definition_confidence_level",
        "phase_13_finops_forecast_definition",
        f"confidence_level IN {VALID_CONFIDENCE_LEVELS!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_definition_status",
        "phase_13_finops_forecast_definition",
        f"status IN {VALID_FORECAST_STATUSES!r}",
    )
    op.execute(
        "ALTER TABLE phase_13_finops_forecast_definition ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_13_finops_forecast_definition_tenant_isolation
            ON phase_13_finops_forecast_definition
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 2. phase_13_finops_forecast_result ─────────────────────
    op.create_table(
        "phase_13_finops_forecast_result",
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
        sa.Column("forecast_id", sa.Text(), nullable=False),
        sa.Column("target_metric", sa.Text(), nullable=False),
        sa.Column("horizon_months", sa.Text(), nullable=False),
        sa.Column(
            "predicted_values",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "confidence_lower",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "confidence_upper",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("model_type", sa.Text(), nullable=False),
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
        "idx_phase_13_finops_forecast_result_tenant_metric_horizon",
        "phase_13_finops_forecast_result",
        ["tenant_id", "target_metric", "horizon_months"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_13_finops_forecast_result_forecast_id",
        "phase_13_finops_forecast_result",
        ["forecast_id"],
    )
    op.create_unique_constraint(
        "uq_phase_13_finops_forecast_result_tenant_metric_horizon",
        "phase_13_finops_forecast_result",
        ["tenant_id", "target_metric", "horizon_months"],
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_result_target_metric",
        "phase_13_finops_forecast_result",
        f"target_metric IN {VALID_TARGET_METRICS!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_result_horizon_months",
        "phase_13_finops_forecast_result",
        f"horizon_months IN {VALID_HORIZON_MONTHS!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_result_model_type",
        "phase_13_finops_forecast_result",
        f"model_type IN {VALID_MODEL_TYPES!r}",
    )
    op.execute(
        "ALTER TABLE phase_13_finops_forecast_result ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_13_finops_forecast_result_tenant_isolation
            ON phase_13_finops_forecast_result
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 3. phase_13_finops_capacity_headroom ───────────────────
    op.create_table(
        "phase_13_finops_capacity_headroom",
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
        sa.Column(
            "saturation_pct",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
        ),
        sa.Column("saturation_level", sa.Text(), nullable=False),
        sa.Column("lookahead_days", sa.Integer(), nullable=False),
        sa.Column(
            "predicted_utilization",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "headroom_pct",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
        ),
        sa.Column("primary_model", sa.Text(), nullable=False),
        sa.Column(
            "ensemble_predicted",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "expires_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_phase_13_finops_capacity_headroom_tenant_resource",
        "phase_13_finops_capacity_headroom",
        ["tenant_id", "resource_type"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_13_finops_capacity_headroom_report_id",
        "phase_13_finops_capacity_headroom",
        ["report_id"],
    )
    op.create_unique_constraint(
        "uq_phase_13_finops_capacity_headroom_tenant_resource_lookahead",
        "phase_13_finops_capacity_headroom",
        ["tenant_id", "resource_type", "lookahead_days"],
    )
    op.create_check_constraint(
        "ck_phase_13_finops_capacity_headroom_resource_type",
        "phase_13_finops_capacity_headroom",
        f"resource_type IN {VALID_RESOURCE_TYPES!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_capacity_headroom_saturation_level",
        "phase_13_finops_capacity_headroom",
        f"saturation_level IN {VALID_SATURATION_LEVELS!r}",
    )
    op.execute(
        "ALTER TABLE phase_13_finops_capacity_headroom ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_13_finops_capacity_headroom_tenant_isolation
            ON phase_13_finops_capacity_headroom
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 4. phase_13_finops_budget_burnrate ─────────────────────
    op.create_table(
        "phase_13_finops_budget_burnrate",
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
        sa.Column("projection_id", sa.Text(), nullable=False),
        sa.Column("budget_id", sa.Text(), nullable=False),
        sa.Column(
            "consumed_budget",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column(
            "total_budget",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column("elapsed_days", sa.Integer(), nullable=False),
        sa.Column("remaining_days", sa.Integer(), nullable=False),
        sa.Column(
            "burn_rate_pct",
            sa.Numeric(precision=7, scale=2),
            nullable=False,
        ),
        sa.Column("severity", sa.Text(), nullable=False),
        sa.Column(
            "alert_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "predicted_end_period_spend",
            sa.Numeric(precision=20, scale=2),
            nullable=False,
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "projected_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_phase_13_finops_budget_burnrate_tenant_budget",
        "phase_13_finops_budget_burnrate",
        ["tenant_id", "budget_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_13_finops_budget_burnrate_projection_id",
        "phase_13_finops_budget_burnrate",
        ["projection_id"],
    )
    op.create_check_constraint(
        "ck_phase_13_finops_budget_burnrate_severity",
        "phase_13_finops_budget_burnrate",
        f"severity IN {VALID_SEVERITY_LEVELS!r}",
    )
    op.execute(
        "ALTER TABLE phase_13_finops_budget_burnrate ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_13_finops_budget_burnrate_tenant_isolation
            ON phase_13_finops_budget_burnrate
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 5. phase_13_finops_forecast_preview ────────────────────
    op.create_table(
        "phase_13_finops_forecast_preview",
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
        sa.Column("forecast_id", sa.Text(), nullable=False),
        sa.Column("horizon_months", sa.Text(), nullable=False),
        sa.Column("target_metric", sa.Text(), nullable=False),
        sa.Column(
            "preview_payload",
            sa.dialects.postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "dry_run",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
        sa.Column(
            "previewed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "idx_phase_13_finops_forecast_preview_tenant_forecast",
        "phase_13_finops_forecast_preview",
        ["tenant_id", "forecast_id"],
        unique=False,
    )
    op.create_unique_constraint(
        "uq_phase_13_finops_forecast_preview_preview_id",
        "phase_13_finops_forecast_preview",
        ["preview_id"],
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_preview_horizon_months",
        "phase_13_finops_forecast_preview",
        f"horizon_months IN {VALID_HORIZON_MONTHS!r}",
    )
    op.create_check_constraint(
        "ck_phase_13_finops_forecast_preview_target_metric",
        "phase_13_finops_forecast_preview",
        f"target_metric IN {VALID_TARGET_METRICS!r}",
    )
    op.execute(
        "ALTER TABLE phase_13_finops_forecast_preview ENABLE ROW LEVEL SECURITY;"
    )
    op.execute(
        """
        CREATE POLICY phase_13_finops_forecast_preview_tenant_isolation
            ON phase_13_finops_forecast_preview
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    """Downgrade schema — drop 5 tables in reverse order."""
    op.execute("DROP POLICY IF EXISTS phase_13_finops_forecast_preview_tenant_isolation ON phase_13_finops_forecast_preview;")
    op.drop_table("phase_13_finops_forecast_preview")
    op.execute("DROP POLICY IF EXISTS phase_13_finops_budget_burnrate_tenant_isolation ON phase_13_finops_budget_burnrate;")
    op.drop_table("phase_13_finops_budget_burnrate")
    op.execute("DROP POLICY IF EXISTS phase_13_finops_capacity_headroom_tenant_isolation ON phase_13_finops_capacity_headroom;")
    op.drop_table("phase_13_finops_capacity_headroom")
    op.execute("DROP POLICY IF EXISTS phase_13_finops_forecast_result_tenant_isolation ON phase_13_finops_forecast_result;")
    op.drop_table("phase_13_finops_forecast_result")
    op.execute("DROP POLICY IF EXISTS phase_13_finops_forecast_definition_tenant_isolation ON phase_13_finops_forecast_definition;")
    op.drop_table("phase_13_finops_forecast_definition")
