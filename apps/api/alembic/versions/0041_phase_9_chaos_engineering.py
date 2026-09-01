"""Story Phase 9 — phase_9_chaos_experiments table for chaos engineering audit trail.

Phase 9 (cj-style 99번째 wire) — AD-36 (b)(c)(e) verbatim + §F25.1 + §F25.5.

Background:
- Phase 8 wire `60d4ea1` (cj-style 95번째) shipped SLO/SLI + latency
  budget + performance regression gate. Phase 9 territory carries
  chaos engineering forward.
- §F25.5 tenant-scoped + multi-region chaos 결정 wire:
  - phase_9_chaos_experiments table with RLS policy.
- §F25.1 chaos experiment definition:
  - ChaosExperiment TypedDict 13 fields (F25.1.2 verbatim).
- 7 ACs PRD §F25.1~§F25.7 verbatim.

Schema (PRD §F25.5.5 verbatim + AD-36 verbatim):
- phase_9_chaos_experiments:
  - id: BIGSERIAL PK
  - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
  - experiment_id: TEXT UNIQUE
  - experiment_name: TEXT
  - fault_type: TEXT enum 10 values (CHECK)
  - blast_radius: TEXT enum 5 values (CHECK)
  - region: TEXT enum 'seoul' | 'tokyo' | 'all'
  - steady_state_metric: TEXT
  - hypothesis: TEXT
  - duration_seconds: INTEGER
  - intensity: TEXT enum 'low' | 'medium' | 'high'
  - status: TEXT enum 'pending' | 'running' | 'completed' | 'aborted' | 'failed'
  - dry_run: BOOLEAN DEFAULT TRUE
  - started_at: TIMESTAMPTZ
  - completed_at: TIMESTAMPTZ
  - actor_id: UUID FK users(id)
  - trace_id: TEXT
  - created_at: TIMESTAMPTZ DEFAULT NOW()

Indexes (PRD §F25.5.6 verbatim):
- idx_phase_9_chaos_experiments_tenant_status (tenant_id, status, started_at DESC)
- uq_phase_9_chaos_experiments_experiment_id UNIQUE
- idx_phase_9_chaos_experiments_region_status (region, status, started_at DESC)

CHECK constraints (PRD §F25.5.7 verbatim):
- ck_phase_9_chaos_experiments_fault_type (fault_type ∈ 10 values)
- ck_phase_9_chaos_experiments_blast_radius (blast_radius ∈ 5 values)

RLS policy (CR 0-2 verbatim):
- phase_9_chaos_experiments_tenant_isolation ON phase_9_chaos_experiments
  USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid)

CR 5-1 lessons applied:
- Industry-agnostic pattern (CR 12-1 L4) — chaos engineering granted
  to all 4 industries via CHAOS_ENGINEERING capability gate.
- CR 1-1 audit-first INSERT — 4 NEW audit log actions
  (chaos_experiment_started + chaos_experiment_completed +
  chaos_experiment_aborted + chaos_rollback_triggered).

Industry-agnostic per CR 12-1 L4 precedent (mirrors PERFORMANCE_TESTING
Phase 8 wire + OBSERVABILITY_* Phase 7 wire + AUDIT_LOG_RETENTION
Phase 6 wire pattern verbatim). All 4 industries get
CHAOS_ENGINEERING capability.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0041_phase_9_chaos_engineering"
down_revision: str | None = "0040_phase_6_audit_retention"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Enum-like CHECK constraint values (single source of truth) ──
VALID_FAULT_TYPES = (
    "latency",
    "error",
    "resource",
    "network_partition",
    "disk_io",
    "db_connection_pool",
    "cache_failure",
    "dns_failure",
    "process_kill",
    "clock_skew",
)

VALID_BLAST_RADII = (
    "single_request",
    "single_tenant",
    "all_tenants",
    "single_region",
    "multi_region",
)

VALID_REGIONS = ("seoul", "tokyo", "all")

VALID_INTENSITIES = ("low", "medium", "high")

VALID_STATUSES = (
    "pending",
    "running",
    "completed",
    "aborted",
    "failed",
)


def upgrade() -> None:
    """Create `phase_9_chaos_experiments` table.

    Per PRD §F25.5.5 verbatim schema + RLS policy + 2 CHECK constraints +
    3 indexes.
    """
    op.create_table(
        "phase_9_chaos_experiments",
        sa.Column(
            "id",
            sa.BigInteger(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
            comment="BIGSERIAL PK",
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Tenant UUID (RLS auto-isolation via app.tenant_id GUC).",
        ),
        sa.Column(
            "experiment_id",
            sa.Text(),
            nullable=False,
            comment="Stable chaos experiment UUID4 string (UNIQUE).",
        ),
        sa.Column(
            "experiment_name",
            sa.Text(),
            nullable=False,
            comment="Human-readable chaos experiment name.",
        ),
        sa.Column(
            "fault_type",
            sa.Text(),
            nullable=False,
            comment=(
                "Enum: 'latency' | 'error' | 'resource' | 'network_partition' "
                "| 'disk_io' | 'db_connection_pool' | 'cache_failure' | "
                "'dns_failure' | 'process_kill' | 'clock_skew' "
                "(CHECK ck_phase_9_chaos_experiments_fault_type)"
            ),
        ),
        sa.Column(
            "blast_radius",
            sa.Text(),
            nullable=False,
            comment=(
                "Enum: 'single_request' | 'single_tenant' | 'all_tenants' | "
                "'single_region' | 'multi_region' "
                "(CHECK ck_phase_9_chaos_experiments_blast_radius)"
            ),
        ),
        sa.Column(
            "region",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'seoul'"),
            comment="Enum: 'seoul' | 'tokyo' | 'all'",
        ),
        sa.Column(
            "steady_state_metric",
            sa.Text(),
            nullable=False,
            comment="Prometheus metric representing steady state.",
        ),
        sa.Column(
            "hypothesis",
            sa.Text(),
            nullable=False,
            comment="Statement of expected steady state behavior.",
        ),
        sa.Column(
            "duration_seconds",
            sa.Integer(),
            nullable=False,
            comment="Chaos experiment duration in seconds (1~600).",
        ),
        sa.Column(
            "intensity",
            sa.Text(),
            nullable=False,
            comment="Enum: 'low' | 'medium' | 'high'.",
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'pending'"),
            comment=("Enum: 'pending' | 'running' | 'completed' | 'aborted' " "| 'failed'."),
        ),
        sa.Column(
            "dry_run",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("TRUE"),
            comment="True if dry-run (no actual fault injection).",
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Chaos experiment start timestamp (UTC).",
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Chaos experiment completion timestamp (UTC).",
        ),
        sa.Column(
            "actor_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
            comment="User who triggered the chaos experiment.",
        ),
        sa.Column(
            "trace_id",
            sa.Text(),
            nullable=True,
            comment="UUID4 trace_id (CR 1-1 verbatim).",
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Row INSERT timestamp (UTC).",
        ),
    )

    # Indexes (PRD §F25.5.6 verbatim).
    op.create_index(
        "idx_phase_9_chaos_experiments_tenant_status",
        "phase_9_chaos_experiments",
        ["tenant_id", "status", sa.text("started_at DESC")],
        unique=False,
    )
    op.create_index(
        "uq_phase_9_chaos_experiments_experiment_id",
        "phase_9_chaos_experiments",
        ["experiment_id"],
        unique=True,
    )
    op.create_index(
        "idx_phase_9_chaos_experiments_region_status",
        "phase_9_chaos_experiments",
        ["region", "status", sa.text("started_at DESC")],
        unique=False,
    )

    # CHECK constraints (PRD §F25.5.7 verbatim).
    op.create_check_constraint(
        "ck_phase_9_chaos_experiments_fault_type",
        "phase_9_chaos_experiments",
        sa.text(f"fault_type IN {tuple(VALID_FAULT_TYPES)!s}"),
    )
    op.create_check_constraint(
        "ck_phase_9_chaos_experiments_blast_radius",
        "phase_9_chaos_experiments",
        sa.text(f"blast_radius IN {tuple(VALID_BLAST_RADII)!s}"),
    )

    # RLS auto-isolation (CR 0-2 verbatim).
    op.execute("ALTER TABLE phase_9_chaos_experiments ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY phase_9_chaos_experiments_tenant_isolation
            ON phase_9_chaos_experiments
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    """Drop RLS policy + indexes + table."""
    op.execute(
        "DROP POLICY IF EXISTS phase_9_chaos_experiments_tenant_isolation "
        "ON phase_9_chaos_experiments;"
    )
    op.drop_index(
        "idx_phase_9_chaos_experiments_region_status",
        table_name="phase_9_chaos_experiments",
    )
    op.drop_index(
        "uq_phase_9_chaos_experiments_experiment_id",
        table_name="phase_9_chaos_experiments",
    )
    op.drop_index(
        "idx_phase_9_chaos_experiments_tenant_status",
        table_name="phase_9_chaos_experiments",
    )
    op.drop_constraint(
        "ck_phase_9_chaos_experiments_fault_type",
        "phase_9_chaos_experiments",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_9_chaos_experiments_blast_radius",
        "phase_9_chaos_experiments",
        type_="check",
    )
    op.drop_table("phase_9_chaos_experiments")
