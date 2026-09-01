r"""Story Phase 11 — phase_11 FinOps Showback / Chargeback tables.

Phase 11 (cj-style 107번째 wire) — AD-38 (b)(d)(e)(f) verbatim +
§F27.1 + §F27.2 + §F27.3 + §F27.5.

Background:
- Phase 10 wire (cj-style 103번째) shipped SLO Engineering / Error
  Budget Management + multi-window burn-rate evaluation + auto-
  rollback SLO breach trigger. Phase 11 territory carries FinOps
  Showback / Chargeback forward.
- §F27.3 department mapping + §F27.1 showback + §F27.2 chargeback:
  - phase_11_finops_department_mapping + phase_11_finops_showback +
    phase_11_finops_chargeback 3 tables with RLS policies.
- §F27.1 ShowbackDefinition TypedDict 13 fields (F27.1.1 verbatim).
- 7 ACs PRD §F27.1~§F27.7 verbatim.

Schema (PRD §F27.1~§F27.3 + §F27.5 verbatim + AD-38 verbatim):

1. phase_11_finops_department_mapping (PRD §F27.3.1 verbatim, 9 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
   - department_id: TEXT
   - department_name: TEXT
   - cost_center_id: TEXT (CHECK matches CC-\d{4})
   - auto_created: BOOLEAN DEFAULT FALSE
   - created_by: TEXT
   - updated_by: TEXT
   - updated_at: TIMESTAMPTZ DEFAULT NOW()
   + system: created_at, trace_id, last_access_at (cache TTL).

2. phase_11_finops_showback (PRD §F27.1.1 verbatim, 14 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - showback_id: TEXT UNIQUE
   - group_by: TEXT (5 options CHECK)
   - period_mode: TEXT (6 modes CHECK)
   - period_start: TIMESTAMPTZ
   - period_end: TIMESTAMPTZ
   - comparison_period: TEXT
   - currency_code: TEXT
   - industry: TEXT (4 industries CHECK)
   - governance_required: BOOLEAN DEFAULT FALSE
   - override_applied: BOOLEAN DEFAULT FALSE
   - generated_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

3. phase_11_finops_chargeback (PRD §F27.2.6 verbatim, 12 cols):
   - id: BIGSERIAL PK
   - tenant_id: UUID (NOT NULL; RLS-enabled)
   - chargeback_id: TEXT UNIQUE
   - rule_type: TEXT (3 rule types CHECK)
   - cost_center_id: TEXT
   - base_amount: NUMERIC(14,2)
   - markup_amount: NUMERIC(14,2)
   - tax_amount: NUMERIC(14,2)
   - total_amount: NUMERIC(14,2)
   - currency_code: TEXT
   - computed_at: TIMESTAMPTZ DEFAULT NOW()
   - trace_id: TEXT

Indexes (PRD §F27.3 + §F27.5 verbatim):
- uq_phase_11_finops_department_mapping_dept_tenant UNIQUE
  (tenant_id, department_id) — one department per tenant.
- uq_phase_11_finops_department_mapping_cost_center_id UNIQUE per
  tenant is not enforced to preserve 1:N mapping flex (per PRD
  §F27.3.1 verbatim).
- idx_phase_11_finops_department_mapping_tenant_id (tenant_id)
- uq_phase_11_finops_showback_showback_id UNIQUE
- idx_phase_11_finops_showback_tenant_period (tenant_id,
  period_start, period_end)
- uq_phase_11_finops_chargeback_chargeback_id UNIQUE
- idx_phase_11_finops_chargeback_tenant_center (tenant_id,
  cost_center_id)

CHECK constraints (PRD §F27.3.1 + §F27.1.1 + §F27.2.2 verbatim):
- ck_phase_11_finops_department_mapping_cost_center_id CHECK matches
  CC-\d{4}.
- ck_phase_11_finops_showback_group_by CHECK ∈ 5 group_by options.
- ck_phase_11_finops_showback_period_mode CHECK ∈ 6 period modes.
- ck_phase_11_finops_showback_industry CHECK ∈ 4 industries.
- ck_phase_11_finops_chargeback_rule_type CHECK ∈ 3 rule types.

RLS policies (CR 0-2 verbatim):
- phase_11_finops_department_mapping_tenant_isolation ON
  phase_11_finops_department_mapping.
- phase_11_finops_showback_tenant_isolation ON
  phase_11_finops_showback.
- phase_11_finops_chargeback_tenant_isolation ON
  phase_11_finops_chargeback.
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)

CR lessons applied:
- Industry-agnostic pattern (CR 12-1 L4) — FinOps Showback /
  Chargeback granted to all 4 industries via FINOPS_SHOWBACK +
  FINOPS_CHARGEBACK capability gates.
- CR 1-1 audit-first INSERT — 3 NEW audit log actions
  (showback_generated + department_mapping_updated +
  chargeback_exported).
- CR 0-2 RLS verbatim — all 3 tables have RLS policies.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0043_phase_11_finops"
down_revision: str | None = "0042_phase_10_slo_engineering"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Enum-like CHECK constraint values (single source of truth) ──
VALID_GROUP_BY = (
    "department",
    "cost_center",
    "product_line",
    "service",
    "custom_tag",
)

VALID_PERIOD_MODES = (
    "current_month",
    "previous_month",
    "last_3_months",
    "last_6_months",
    "ytd",
    "custom_range",
)

VALID_INDUSTRIES = (
    "manufacturing",
    "service",
    "manufacturing_service",
    "manufacturing_service_other",
)

VALID_RULE_TYPES = (
    "flat_fee",
    "proportional_allocation",
    "metered",
)

COST_CENTER_ID_PATTERN = r"^CC-\d{4}$"


def upgrade() -> None:
    """Create `phase_11_finops_department_mapping` +
    `phase_11_finops_showback` + `phase_11_finops_chargeback` 3 tables.

    Per PRD §F27.1~§F27.3 + §F27.5 verbatim schema + RLS policy +
    5 CHECK constraints + 4 indexes + 3 UNIQUE constraints.
    """
    # ── 1. phase_11_finops_department_mapping ───────────────────
    op.create_table(
        "phase_11_finops_department_mapping",
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
        sa.Column("department_id", sa.Text(), nullable=False),
        sa.Column("department_name", sa.Text(), nullable=False),
        sa.Column("cost_center_id", sa.Text(), nullable=False),
        sa.Column(
            "auto_created",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column("updated_by", sa.Text(), nullable=False),
        sa.Column(
            "last_access_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
        ),
    )

    # Index
    op.create_index(
        "idx_phase_11_finops_department_mapping_tenant_id",
        "phase_11_finops_department_mapping",
        ["tenant_id"],
        unique=False,
    )

    # UNIQUE composite (PRD §F27.3.1 verbatim — one department per tenant).
    op.create_unique_constraint(
        "uq_phase_11_finops_department_mapping_dept_tenant",
        "phase_11_finops_department_mapping",
        ["tenant_id", "department_id"],
    )

    # CHECK constraint
    op.create_check_constraint(
        "ck_phase_11_finops_department_mapping_cost_center_id",
        "phase_11_finops_department_mapping",
        f"cost_center_id ~ '{COST_CENTER_ID_PATTERN}'",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute("ALTER TABLE phase_11_finops_department_mapping ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY phase_11_finops_department_mapping_tenant_isolation
            ON phase_11_finops_department_mapping
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 2. phase_11_finops_showback ─────────────────────────────
    op.create_table(
        "phase_11_finops_showback",
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
        sa.Column("showback_id", sa.Text(), nullable=False),
        sa.Column("group_by", sa.Text(), nullable=False),
        sa.Column("period_mode", sa.Text(), nullable=False),
        sa.Column(
            "period_start",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "period_end",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
        ),
        sa.Column("comparison_period", sa.Text(), nullable=True),
        sa.Column("currency_code", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=False),
        sa.Column(
            "governance_required",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
        sa.Column(
            "override_applied",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
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
        "idx_phase_11_finops_showback_tenant_period",
        "phase_11_finops_showback",
        ["tenant_id", "period_start", "period_end"],
        unique=False,
    )

    # UNIQUE constraint
    op.create_unique_constraint(
        "uq_phase_11_finops_showback_showback_id",
        "phase_11_finops_showback",
        ["showback_id"],
    )

    # CHECK constraints
    op.create_check_constraint(
        "ck_phase_11_finops_showback_group_by",
        "phase_11_finops_showback",
        f"group_by IN {VALID_GROUP_BY!r}",
    )
    op.create_check_constraint(
        "ck_phase_11_finops_showback_period_mode",
        "phase_11_finops_showback",
        f"period_mode IN {VALID_PERIOD_MODES!r}",
    )
    op.create_check_constraint(
        "ck_phase_11_finops_showback_industry",
        "phase_11_finops_showback",
        f"industry IN {VALID_INDUSTRIES!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute("ALTER TABLE phase_11_finops_showback ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY phase_11_finops_showback_tenant_isolation
            ON phase_11_finops_showback
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ── 3. phase_11_finops_chargeback ───────────────────────────
    op.create_table(
        "phase_11_finops_chargeback",
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
        sa.Column("chargeback_id", sa.Text(), nullable=False),
        sa.Column("rule_type", sa.Text(), nullable=False),
        sa.Column("cost_center_id", sa.Text(), nullable=False),
        sa.Column(
            "base_amount",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column(
            "markup_amount",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column(
            "tax_amount",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column(
            "total_amount",
            sa.Numeric(precision=14, scale=2),
            nullable=False,
        ),
        sa.Column("currency_code", sa.Text(), nullable=False),
        sa.Column(
            "computed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("trace_id", sa.Text(), nullable=True),
    )

    # Index
    op.create_index(
        "idx_phase_11_finops_chargeback_tenant_center",
        "phase_11_finops_chargeback",
        ["tenant_id", "cost_center_id"],
        unique=False,
    )

    # UNIQUE constraint
    op.create_unique_constraint(
        "uq_phase_11_finops_chargeback_chargeback_id",
        "phase_11_finops_chargeback",
        ["chargeback_id"],
    )

    # CHECK constraint
    op.create_check_constraint(
        "ck_phase_11_finops_chargeback_rule_type",
        "phase_11_finops_chargeback",
        f"rule_type IN {VALID_RULE_TYPES!r}",
    )

    # RLS policy (CR 0-2 verbatim)
    op.execute("ALTER TABLE phase_11_finops_chargeback ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY phase_11_finops_chargeback_tenant_isolation
            ON phase_11_finops_chargeback
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    """Drop `phase_11_finops_chargeback` + `phase_11_finops_showback` +
    `phase_11_finops_department_mapping` 3 tables.
    """
    # Drop in reverse order (FK dependencies)
    op.execute(
        "DROP POLICY IF EXISTS phase_11_finops_chargeback_tenant_isolation ON phase_11_finops_chargeback;"
    )
    op.execute("ALTER TABLE phase_11_finops_chargeback DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "ck_phase_11_finops_chargeback_rule_type",
        "phase_11_finops_chargeback",
        type_="check",
    )
    op.drop_constraint(
        "uq_phase_11_finops_chargeback_chargeback_id",
        "phase_11_finops_chargeback",
        type_="unique",
    )
    op.drop_index(
        "idx_phase_11_finops_chargeback_tenant_center",
        table_name="phase_11_finops_chargeback",
    )
    op.drop_table("phase_11_finops_chargeback")

    op.execute(
        "DROP POLICY IF EXISTS phase_11_finops_showback_tenant_isolation ON phase_11_finops_showback;"
    )
    op.execute("ALTER TABLE phase_11_finops_showback DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "ck_phase_11_finops_showback_industry",
        "phase_11_finops_showback",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_11_finops_showback_period_mode",
        "phase_11_finops_showback",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_11_finops_showback_group_by",
        "phase_11_finops_showback",
        type_="check",
    )
    op.drop_constraint(
        "uq_phase_11_finops_showback_showback_id",
        "phase_11_finops_showback",
        type_="unique",
    )
    op.drop_index(
        "idx_phase_11_finops_showback_tenant_period",
        table_name="phase_11_finops_showback",
    )
    op.drop_table("phase_11_finops_showback")

    op.execute(
        "DROP POLICY IF EXISTS phase_11_finops_department_mapping_tenant_isolation ON phase_11_finops_department_mapping;"
    )
    op.execute("ALTER TABLE phase_11_finops_department_mapping DISABLE ROW LEVEL SECURITY;")
    op.drop_constraint(
        "ck_phase_11_finops_department_mapping_cost_center_id",
        "phase_11_finops_department_mapping",
        type_="check",
    )
    op.drop_constraint(
        "uq_phase_11_finops_department_mapping_dept_tenant",
        "phase_11_finops_department_mapping",
        type_="unique",
    )
    op.drop_index(
        "idx_phase_11_finops_department_mapping_tenant_id",
        table_name="phase_11_finops_department_mapping",
    )
    op.drop_table("phase_11_finops_department_mapping")
