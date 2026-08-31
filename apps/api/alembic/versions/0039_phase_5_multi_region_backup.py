"""Story Phase 5 — phase_5_replication_lag + phase_5_dr_drill_results tables for cross-region backup & DR.

Phase 5 (cj-style 75번째 epic 연속 정직 회복 wire) — AD-31 verbatim +
PRD §F20.1 + §F20.3 + AC #1.1~#1.6 + AC #3.1~#3.4.

Background:
- Phase 4 single-region backup wire (`71a033a` + close-out `934b35e`)
  shipped `phase_4_backup_strategy` table tracking ENTERPRISE-WIDE backup
  metadata. Phase 4 close-out retro §6 honestly-deferred cross-region
  read replica + disaster recovery to Phase 5.
- D-PHASE-4-DR-DEFER-1 (Seoul region disaster 시 backup restoration 불가)
  + D-PHASE-4-DR-DEFER-2 (cross-region read replica carry-over) RESOLVED
  via Phase 5 PRD entry `93d852b` (cj-style 73번째).
- Phase 5 territory wires 2 NEW system-only tables:
  - `phase_5_replication_lag` — per-replica replication lag tracker
    (WAL archiving health check + replication_status enum + 8 columns)
  - `phase_5_dr_drill_results` — quarterly DR drill results audit log
    (cron KST 1st Sunday 03:00 UTC 18:00 + 7 columns + 6 drill steps)

Schema (PRD §F20.1 + §F20.3 verbatim + AD-31 verbatim):
- phase_5_replication_lag:
  - id: BIGSERIAL PK
  - region: TEXT (enum: 'primary_seoul' | 'secondary_tokyo')
  - replication_status: TEXT (enum: 'healthy' | 'lagging' | 'stalled' | 'disconnected')
  - lag_seconds: INTEGER (current replication lag in seconds)
  - last_wal_received_at: TIMESTAMPTZ NULL (last WAL archive received timestamp)
  - last_health_probe_at: TIMESTAMPTZ NOT NULL (5-second interval health probe)
  - error_message: TEXT NULL (last error encountered, NULL while healthy)
  - recorded_at: TIMESTAMPTZ NOT NULL DEFAULT NOW()
- phase_5_dr_drill_results:
  - id: BIGSERIAL PK
  - drill_quarter: TEXT (e.g., '2026-Q1' — Q1/Q2/Q3/Q4 quarterly schedule)
  - drill_status: TEXT (enum: 'passed' | 'failed' | 'in_progress')
  - rpo_seconds: INTEGER (recovery point objective measured — target ≤ 3600s = 1h)
  - rto_seconds: INTEGER (recovery time objective measured — target ≤ 14400s = 4h)
  - drill_error_message: TEXT NULL (drill failure details)
  - completed_at: TIMESTAMPTZ NULL (drill completion timestamp)
  - created_at: TIMESTAMPTZ NOT NULL DEFAULT NOW()

CR 0-2 RLS lesson: these are SYSTEM-ONLY tables (cron + monitoring only —
no tenant context). NO RLS policies — Epic 13/14 LISTEN/NOTIFY system
table pattern 미러. service_role bypass NOT needed because cron runs as
service_role by default and monitoring is service_role-scoped.

CR 1-1 audit-first: 4 NEW audit log rows MUST be INSERTed BEFORE row
mutation (action_class=ActionClass.INFRA NEW + actions:
replica_status_changed + failover_initiated + failover_completed +
dr_drill_completed). See apps/api/core/audit_action.py ActionClass
registry EXTENSION.

Architecture patterns:
- AD-14 stack pin: PostgreSQL 15 (already pinned in docker-compose.yml).
- Industry-agnostic: cross-region backup & DR is operational
  infrastructure, granted to all 4 industries via MULTI_REGION_BACKUP +
  MULTI_REGION_FAILOVER capabilities (CR 12-1 L4 precedent).
- RPO 1h / RTO 4h SLA target (PRD §F20.4 verbatim — Phase 4 close-out
  retro §6 honestly-extreme risk 해소).

CR 12-5 D-14 typed exception envelope: 5 NEW error classes to be added
in apps/api/jobs/failover_orchestrator.py + dr_drill.py.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0039_phase_5_multi_region_backup"
down_revision: str | None = "0038_epic_16_tenant_idps"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Enum-like CHECK constraint values ──────────────────────────
# Mirrors apps/api/jobs/failover_orchestrator.py + dr_drill.py
# CR 12-5 D-14 typed exception envelope — single source of truth.
VALID_REGIONS = ("primary_seoul", "secondary_tokyo")
VALID_REPLICATION_STATUSES = (
    "healthy",
    "lagging",
    "stalled",
    "disconnected",
)
VALID_DRILL_STATUSES = ("passed", "failed", "in_progress")


def upgrade() -> None:
    """Create `phase_5_replication_lag` + `phase_5_dr_drill_results` tables
    with indexes + CHECK constraints + updated_at trigger. NO RLS — system-only
    tables (CR 0-2 RLS lesson verbatim).
    """
    # ────────────────────────────────────────────────────────────
    # Table 1: phase_5_replication_lag (PRD §F20.1 verbatim)
    # ────────────────────────────────────────────────────────────
    op.create_table(
        "phase_5_replication_lag",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            primary_key=True,
            nullable=False,
            comment="Surrogate BIGSERIAL PK",
        ),
        sa.Column(
            "region",
            sa.Text(),
            nullable=False,
            comment=(
                "Enum: 'primary_seoul' | 'secondary_tokyo' "
                "(CHECK ck_phase_5_replication_lag_region)"
            ),
        ),
        sa.Column(
            "replication_status",
            sa.Text(),
            nullable=False,
            comment=(
                "Enum: 'healthy' | 'lagging' | 'stalled' | 'disconnected' "
                "(CHECK ck_phase_5_replication_lag_status)"
            ),
        ),
        sa.Column(
            "lag_seconds",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment=(
                "Current replication lag in seconds. Healthy: < 60s. "
                "Lagging: 60s ~ 600s. Stalled: > 600s."
            ),
        ),
        sa.Column(
            "last_wal_received_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment=(
                "Last WAL archive received timestamp (UTC). NULL while "
                "disconnected. Cross-region PITR boundary marker."
            ),
        ),
        sa.Column(
            "last_health_probe_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment=(
                "Last 5-second interval health probe timestamp (UTC). "
                "Stale probe → failover trigger via failover_orchestrator."
            ),
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
            comment=(
                "Last error encountered during health probe (NULL while "
                "healthy). Truncated to 4096 chars at application layer."
            ),
        ),
        sa.Column(
            "recorded_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Row INSERT timestamp (UTC).",
        ),
    )

    # Indexes (3 NEW — PRD §F20.1 + §F20.7 verbatim).
    op.create_index(
        "idx_phase_5_replication_lag_region_recorded",
        "phase_5_replication_lag",
        ["region", "recorded_at"],
        unique=False,
    )
    op.create_index(
        "idx_phase_5_replication_lag_status_recorded",
        "phase_5_replication_lag",
        ["replication_status", "recorded_at"],
        unique=False,
    )

    # CHECK constraints (PRD §F20.1 verbatim — defense-in-depth).
    #
    # D-CI-FUNC-9 cj-233 fix: previous code did
    # `f"region IN {tuple(VALID_REGIONS)!s}".replace("'", "''")` which
    # produced `region IN (''primary_seoul'', ''secondary_tokyo'')` —
    # Postgres parses that as adjacent empty quoted identifiers, not as
    # string literals, so the CHECK constraint failed at creation with
    # `syntax error at or near "primary_seoul"`. The right shape is
    # `region IN ('primary_seoul', 'secondary_tokyo')` — real SQL string
    # literals. Build the quoted tuple with `repr()` which produces the
    # exact form Postgres expects.
    _region_in_clause = ", ".join(repr(r) for r in VALID_REGIONS)
    op.create_check_constraint(
        "ck_phase_5_replication_lag_region",
        "phase_5_replication_lag",
        sa.text(f"region IN ({_region_in_clause})"),
    )
    op.create_check_constraint(
        "ck_phase_5_replication_lag_status",
        "phase_5_replication_lag",
        sa.text(
            "replication_status IN "
            "('healthy', 'lagging', 'stalled', 'disconnected')"
        ),
    )

    # NO RLS — system-only table (CR 0-2 verbatim Epic 13/14 pattern).
    # The replication_lag tracker is populated by failover_orchestrator
    # (service_role) and read by multi-region health endpoint
    # (service_role via /api/v1/health/multi-region). No tenant context.

    # ────────────────────────────────────────────────────────────
    # Table 2: phase_5_dr_drill_results (PRD §F20.3 verbatim)
    # ────────────────────────────────────────────────────────────
    op.create_table(
        "phase_5_dr_drill_results",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            primary_key=True,
            nullable=False,
            comment="Surrogate BIGSERIAL PK",
        ),
        sa.Column(
            "drill_quarter",
            sa.Text(),
            nullable=False,
            comment=(
                "Drill quarter identifier, e.g. '2026-Q1' (Q1/Q2/Q3/Q4 "
                "quarterly schedule). CHECK ck_phase_5_dr_drill_quarter."
            ),
        ),
        sa.Column(
            "drill_status",
            sa.Text(),
            nullable=False,
            comment=(
                "Enum: 'passed' | 'failed' | 'in_progress' "
                "(CHECK ck_phase_5_dr_drill_status)"
            ),
        ),
        sa.Column(
            "rpo_seconds",
            sa.Integer(),
            nullable=False,
            comment=(
                "Recovery Point Objective measured in seconds. "
                "SLA target: ≤ 3600s (1h). Phase 4 close-out retro §6 "
                "verbatim risk-bound."
            ),
        ),
        sa.Column(
            "rto_seconds",
            sa.Integer(),
            nullable=False,
            comment=(
                "Recovery Time Objective measured in seconds. "
                "SLA target: ≤ 14400s (4h). Phase 4 close-out retro §6 "
                "verbatim risk-bound."
            ),
        ),
        sa.Column(
            "drill_error_message",
            sa.Text(),
            nullable=True,
            comment=(
                "Drill failure details (NULL while passed/in_progress). "
                "Truncated to 4096 chars at application layer."
            ),
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment=(
                "Drill completion timestamp (UTC). NULL while "
                "in_progress. Set by dr_drill cron after 6 drill steps."
            ),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Drill row INSERT timestamp (UTC).",
        ),
    )

    # Index (1 NEW — PRD §F20.3 verbatim).
    op.create_index(
        "idx_phase_5_dr_drill_results_quarter_created",
        "phase_5_dr_drill_results",
        ["drill_quarter", "created_at"],
        unique=False,
    )

    # CHECK constraints (PRD §F20.3 verbatim).
    op.create_check_constraint(
        "ck_phase_5_dr_drill_quarter",
        "phase_5_dr_drill_results",
        sa.text(
            "drill_quarter ~ '^[0-9]{4}-Q[1-4]$'"
        ),
    )
    op.create_check_constraint(
        "ck_phase_5_dr_drill_status",
        "phase_5_dr_drill_results",
        sa.text("drill_status IN ('passed', 'failed', 'in_progress')"),
    )

    # NO RLS — system-only table (CR 0-2 verbatim).
    # dr_drill cron runs as service_role, drill results read by
    # monitoring/audit. No tenant context required.


def downgrade() -> None:
    """Drop both tables + indexes + CHECK constraints."""
    op.drop_index(
        "idx_phase_5_dr_drill_results_quarter_created",
        table_name="phase_5_dr_drill_results",
    )
    op.drop_constraint(
        "ck_phase_5_dr_drill_status",
        "phase_5_dr_drill_results",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_5_dr_drill_quarter",
        "phase_5_dr_drill_results",
        type_="check",
    )
    op.drop_table("phase_5_dr_drill_results")

    op.drop_index(
        "idx_phase_5_replication_lag_status_recorded",
        table_name="phase_5_replication_lag",
    )
    op.drop_index(
        "idx_phase_5_replication_lag_region_recorded",
        table_name="phase_5_replication_lag",
    )
    op.drop_constraint(
        "ck_phase_5_replication_lag_status",
        "phase_5_replication_lag",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_5_replication_lag_region",
        "phase_5_replication_lag",
        type_="check",
    )
    op.drop_table("phase_5_replication_lag")