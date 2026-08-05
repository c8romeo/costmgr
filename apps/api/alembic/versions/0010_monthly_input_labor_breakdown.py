"""Monthly Input Labor Breakdown — Story 3.2 (Task 2.1).

Adds the FTE precision columns to ``monthly_input_rows`` for the
PRD §6.1 인건비 구성 (pay_type 분기 + 5 breakdown fields +
company_burden_rate):

- ``pay_type``                  TEXT NULL CHECK ('monthly' | 'daily')
- ``monthly_salary_basis_krw``  BIGINT NULL CHECK (>= 0)   — monthly mode
- ``overtime_krw``              BIGINT NULL CHECK (>= 0)   — monthly mode
- ``welfare_krw``               BIGINT NULL CHECK (>= 0)   — monthly mode
- ``bonus_krw``                 BIGINT NULL CHECK (>= 0)   — monthly mode
- ``retirement_reserve_krw``    BIGINT NULL CHECK (>= 0)   — monthly mode
- ``company_burden_rate``       NUMERIC(5,4) NULL CHECK [0, 1]

Also adds the tenant-level payroll override JSONB column on
``tenant_settings`` so per-tenant 인건비 정책을 override할 수 있다
(PRD §6.1; Story 3.2 §Task 3.2 `_load_payroll_settings`):

- ``tenant_settings.payroll``    JSONB NULL  — empty dict default
  (per-field fallback to ``DEFAULT_PAYROLL`` in
  ``packages.services.m2_input.labor_conversion``)

All row columns are NULLABLE so the table continues to back all 6
streams (orders / production / sales / purchases / expenses / labor)
without a UNION ALL of sub-tables. Service layer enforces the
per-stream shape (`_validate_labor_shape` in
`monthly_input_service.py` — Task 3.1).

AD-8 monetary parity:
- KRW amounts — BIGINT (no fractional won)
- company_burden_rate — NUMERIC(5,4) with CHECK [0, 1]
  (5 digits total, 4 after decimal — covers 0.0000 to 9.9999, restricted to 0..1)

AD-23 4-namespace: natural key unchanged (Story 3.1 partial unique index).
No new indexes — existing `idx_monthly_input_rows_tenant_period_stream`
covers the per-stream aggregation query (yellow dot decision + FTE
computation both read by `(tenant_id, period_id, stream)`).

Revision ID: 0010_monthly_input_labor_breakdown
Revises:    0009_monthly_input
Create Date: 2026-08-01
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0010_monthly_input_labor_breakdown"
down_revision: str | Sequence[str] | None = "0009_monthly_input"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# PayType enum values — Story 3.2 §Task 1.1 (mirrored in
# `packages.services.m2_input.labor_conversion.PayType` and the TS
# mirror's `PAY_TYPE_VALUES`).
_PAY_TYPE_VALUES = ("monthly", "daily")


def upgrade() -> None:
    # ── pay_type discriminator ──────────────────────────────────
    # Nullable so non-labor rows (orders/production/...) are unaffected.
    # Service layer enforces non-NULL on labor stream.
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS pay_type TEXT NULL
        """
    )
    op.execute("DROP CONSTRAINT IF EXISTS monthly_input_rows_pay_type_check")
    pay_type_list = ", ".join(f"'{p}'" for p in _PAY_TYPE_VALUES)
    op.execute(
        f"""
        ALTER TABLE monthly_input_rows
        ADD CONSTRAINT monthly_input_rows_pay_type_check
        CHECK (pay_type IS NULL OR pay_type IN ({pay_type_list}))
        """
    )

    # ── monthly-mode breakdown fields (PRD §6.1) ──────────────
    # All BIGINT KRW (AD-8). CHECK >= 0 enforces non-negative.
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS monthly_salary_basis_krw BIGINT NULL
        CHECK (monthly_salary_basis_krw IS NULL OR monthly_salary_basis_krw >= 0)
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS overtime_krw BIGINT NULL
        CHECK (overtime_krw IS NULL OR overtime_krw >= 0)
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS welfare_krw BIGINT NULL
        CHECK (welfare_krw IS NULL OR welfare_krw >= 0)
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS bonus_krw BIGINT NULL
        CHECK (bonus_krw IS NULL OR bonus_krw >= 0)
        """
    )
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS retirement_reserve_krw BIGINT NULL
        CHECK (retirement_reserve_krw IS NULL OR retirement_reserve_krw >= 0)
        """
    )

    # ── company_burden_rate (PRD §6.1 4대보험·퇴직 회사부담) ─
    # NUMERIC(5,4) — 4 decimal places, CHECK [0, 1]. Decimal-typed.
    op.execute(
        """
        ALTER TABLE monthly_input_rows
        ADD COLUMN IF NOT EXISTS company_burden_rate NUMERIC(5,4) NULL
        CHECK (company_burden_rate IS NULL
               OR (company_burden_rate >= 0 AND company_burden_rate <= 1))
        """
    )

    # ── tenant_settings.payroll JSONB (PRD §6.1 인건비 override) ──
    # Per-tenant payroll policy override. Empty `{}` default means
    # fall through to `DEFAULT_PAYROLL` in
    # `packages.services.m2_input.labor_conversion` (no-override path).
    # Shape (per-field fallback to default):
    #     {  # noqa: ERA001
    #         "monthly_salary_basis_krw": int (>= 0),  # noqa: ERA001
    #         "workdays_in_month":       int (1..31),  # noqa: ERA001
    #         "standard_monthly_hours":  int (> 0),  # noqa: ERA001
    #         "company_burden_rate":     Decimal/string in [0, 1],  # noqa: ERA001
    #     }  # noqa: ERA001
    op.execute(
        """
        ALTER TABLE tenant_settings
        ADD COLUMN IF NOT EXISTS payroll JSONB NULL DEFAULT '{}'::jsonb
        """
    )


def downgrade() -> None:
    # Drop tenant_settings column first (cross-table dependency order).
    op.execute("ALTER TABLE tenant_settings DROP COLUMN IF EXISTS payroll")
    # Drop in reverse order; CHECK constraints cascade with the columns.
    op.execute("ALTER TABLE monthly_input_rows DROP COLUMN IF EXISTS company_burden_rate")
    op.execute("ALTER TABLE monthly_input_rows DROP COLUMN IF EXISTS retirement_reserve_krw")
    op.execute("ALTER TABLE monthly_input_rows DROP COLUMN IF EXISTS bonus_krw")
    op.execute("ALTER TABLE monthly_input_rows DROP COLUMN IF EXISTS welfare_krw")
    op.execute("ALTER TABLE monthly_input_rows DROP COLUMN IF EXISTS overtime_krw")
    op.execute("ALTER TABLE monthly_input_rows DROP COLUMN IF EXISTS monthly_salary_basis_krw")
    op.execute("ALTER TABLE monthly_input_rows DROP COLUMN IF EXISTS pay_type")
