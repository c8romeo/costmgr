"""Story Phase 4 — phase_4_backup_strategy table for production backup audit.

Phase 4 (cj-style 55번째 epic 연속 정직 회복 wire) — AD-27 verbatim +
PRD §F16.6 + AC #6.1~#6.6.

Background:
- Phase 4 territory = Deployment config + Dockerfile + health check +
  observability + database backup.
- `tenant_backups` table (Epic 12 12.2 wire) tracks PER-TENANT manual
  exports (KST 02:00 daily cron). That table is tenant-scoped.
- Phase 4 introduces a SEPARATE `phase_4_backup_strategy` table that
  tracks ENTERPRISE-WIDE backup metadata (Supabase PITR + admin-only
  manual triggers). This is NOT a tenant-scoped table — it captures
  fleet-wide backup events with optional `tenant_id` for per-tenant
  manual triggers.

Schema (PRD §F16.6 verbatim):
- id: BIGSERIAL primary key
- backup_type: TEXT (enum: 'auto_pitr' | 'manual_admin' | 'manual_export')
- started_at: TIMESTAMPTZ NOT NULL
- completed_at: TIMESTAMPTZ NULL
- size_bytes: BIGINT NULL
- checksum_sha256: TEXT NULL  (SHA-256 of the backup archive)
- storage_url: TEXT NULL      (e.g., s3://costmgr-backups/YYYY-MM-DD/...)
- status: TEXT (enum: 'in_progress' | 'completed' | 'failed')
- tenant_id: UUID NULL        (only set for per-tenant manual exports)
- created_at: TIMESTAMPTZ DEFAULT now()
- updated_at: TIMESTAMPTZ DEFAULT now()

CR 1-1 audit-first: a `backup_created` audit log row MUST be INSERTed
BEFORE the row INSERT in this table (see `apps/api/core/audit_action.py`
for the canonical audit registry).

Architecture patterns:
- AD-14 stack pin: PostgreSQL 15 (already pinned in docker-compose.yml).
- Industry-agnostic: backup is operational infrastructure, granted to
  all 4 industries via `DEPLOYMENT_DATABASE_BACKUP` capability.
- Phase 4 close-out retro deferred decisions:
  - storage_url: `s3://costmgr-backups/YYYY-MM-DD/` vs Supabase Storage
    is decided in Phase 4 close-out retro.
  - Multi-region backup: deferred to Phase 5+.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0036_phase_4_backup_strategy"
down_revision: str | None = "0035_custom_access_token_hook"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    """Create `phase_4_backup_strategy` table + supporting indexes."""
    op.create_table(
        "phase_4_backup_strategy",
        sa.Column(
            "id",
            sa.BigInteger(),
            sa.Identity(always=False),
            primary_key=True,
            nullable=False,
            comment="Surrogate BIGSERIAL PK",
        ),
        sa.Column(
            "backup_type",
            sa.Text(),
            nullable=False,
            comment=(
                "Enum: 'auto_pitr' (Supabase PITR daily), "
                "'manual_admin' (POST /api/v1/admin/backup), "
                "'manual_export' (per-tenant export)"
            ),
        ),
        sa.Column(
            "started_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            comment="Backup start timestamp (UTC)",
        ),
        sa.Column(
            "completed_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment="Backup completion timestamp (NULL while in_progress)",
        ),
        sa.Column(
            "size_bytes",
            sa.BigInteger(),
            nullable=True,
            comment="Backup archive size in bytes (NULL while in_progress)",
        ),
        sa.Column(
            "checksum_sha256",
            sa.Text(),
            nullable=True,
            comment="SHA-256 hex digest of the backup archive (verification)",
        ),
        sa.Column(
            "storage_url",
            sa.Text(),
            nullable=True,
            comment=(
                "Storage URL — s3://costmgr-backups/YYYY-MM-DD/ or "
                "supabase://costmgr-storage/backups/. Determined by "
                "Phase 4 close-out retro (OQ-1)"
            ),
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
            server_default=sa.text("'in_progress'"),
            comment="Enum: 'in_progress' | 'completed' | 'failed'",
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=True,
            comment=(
                "Optional tenant UUID — set only for per-tenant manual "
                "exports. NULL for fleet-wide backups (auto_pitr, "
                "manual_admin)."
            ),
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row creation timestamp (UTC)",
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Row last-update timestamp (UTC)",
        ),
    )

    # Indexes for the common query patterns:
    # 1. status='in_progress' for dashboard polling.
    op.create_index(
        "ix_phase_4_backup_strategy_status",
        "phase_4_backup_strategy",
        ["status"],
        unique=False,
    )
    # 2. (started_at DESC) for "latest backups" dashboard.
    op.create_index(
        "ix_phase_4_backup_strategy_started_at_desc",
        "phase_4_backup_strategy",
        [sa.text("started_at DESC")],
        unique=False,
    )
    # 3. (tenant_id, started_at DESC) for per-tenant backup history.
    op.create_index(
        "ix_phase_4_backup_strategy_tenant_started",
        "phase_4_backup_strategy",
        ["tenant_id", sa.text("started_at DESC")],
        unique=False,
    )
    # 4. (backup_type, status) for "all failed auto_pitr backups" alerting.
    op.create_index(
        "ix_phase_4_backup_strategy_type_status",
        "phase_4_backup_strategy",
        ["backup_type", "status"],
        unique=False,
    )

    # CHECK constraints for enum-like columns (defense-in-depth).
    op.create_check_constraint(
        "ck_phase_4_backup_strategy_backup_type",
        "phase_4_backup_strategy",
        sa.text(
            "backup_type IN ('auto_pitr', 'manual_admin', 'manual_export')"
        ),
    )
    op.create_check_constraint(
        "ck_phase_4_backup_strategy_status",
        "phase_4_backup_strategy",
        sa.text(
            "status IN ('in_progress', 'completed', 'failed')"
        ),
    )
    op.create_check_constraint(
        "ck_phase_4_backup_strategy_completed_after_started",
        "phase_4_backup_strategy",
        sa.text(
            "completed_at IS NULL OR completed_at >= started_at"
        ),
    )


def downgrade() -> None:
    """Drop `phase_4_backup_strategy` table + all indexes."""
    op.drop_constraint(
        "ck_phase_4_backup_strategy_completed_after_started",
        "phase_4_backup_strategy",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_4_backup_strategy_status",
        "phase_4_backup_strategy",
        type_="check",
    )
    op.drop_constraint(
        "ck_phase_4_backup_strategy_backup_type",
        "phase_4_backup_strategy",
        type_="check",
    )
    op.drop_index(
        "ix_phase_4_backup_strategy_type_status",
        table_name="phase_4_backup_strategy",
    )
    op.drop_index(
        "ix_phase_4_backup_strategy_tenant_started",
        table_name="phase_4_backup_strategy",
    )
    op.drop_index(
        "ix_phase_4_backup_strategy_started_at_desc",
        table_name="phase_4_backup_strategy",
    )
    op.drop_index(
        "ix_phase_4_backup_strategy_status",
        table_name="phase_4_backup_strategy",
    )
    op.drop_table("phase_4_backup_strategy")
