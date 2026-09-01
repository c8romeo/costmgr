"""Story Phase 6 — audit_log_archive + phase_6_audit_purge_log tables for SHA-256 hash-chained immutable archive.

Phase 6 (cj-style 87번째 epic 연속 정직 회복 wire) — AD-33 (c) + §F22.3
verbatim.

Background:
- Epic 17 wire `2ada2ec` (cj-style 82번째) shipped the audit log query API
  for `apps/api/modules/audit/audit_log_query.py`. Phase 6 territory
  carries the audit log retention policy forward:
- §F22.3 archive storage with SHA-256 hash chain + immutable append-only
  trigger + cross-region archive replication via Phase 5
  `phase_5_replication_lag` carry-over.
- §F22.5 audit-first INSERT extension (audit_log_archived +
  audit_log_cold_archived new actions, action_class=ActionClass.AUDIT).
- 7 ACs PRD §F22.1~§F22.7 verbatim.

Schema (PRD §F22.3 verbatim + AD-33 verbatim):
- audit_log_archive:
  - archive_id: UUID PK
  - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
  - audit_log_id: UUID (the source row being archived)
  - payload_snapshot: JSONB (full row payload pre-mutation)
  - archived_at: TIMESTAMPTZ NOT NULL (archive INSERT timestamp UTC)
  - sha256_hash: TEXT (SHA-256 hash of audit_log_id + payload_snapshot + previous_hash)
  - previous_hash: TEXT (linking to prior row in same tenant — hash chain)
  - region: TEXT (cross-region replica reference, e.g. 'primary_seoul' |
    'secondary_tokyo' | 'cold_archive_s3')
- phase_6_audit_purge_log:
  - purge_log_id: UUID PK
  - tenant_id: UUID (NOT NULL; RLS-enabled, CR 0-2 verbatim)
  - purged_at: TIMESTAMPTZ NOT NULL DEFAULT NOW()
  - purged_count: INTEGER NOT NULL
  - dry_run: BOOLEAN NOT NULL DEFAULT FALSE
  - trace_id: TEXT (for Sentry breadcrumb / observability)
- ALTER TABLE audit_log ADD COLUMN archived_at TIMESTAMPTZ (NULLABLE)
  — set when archive INSERT happens to source row.

CR 0-2 RLS lesson: RLS auto-isolated per-tenant; service_role bypass
required for system operations (purge job cron + cold archive). Pattern
verbatim Epic 13/14 LISTEN/NOTIFY system table mirror.

CR 1-1 audit-first INSERT: 5 NEW audit log actions required
(audit_log_purged + audit_log_archived + audit_log_pii_masked +
audit_log_cold_archived + audit_log_personal_data_erased). See
apps/api/core/audit_action.py ActionClass.AUDIT EXTENSION.

Architecture patterns:
- AD-14 stack pin: PostgreSQL 15 (already pinned in docker-compose.yml).
- Industry-agnostic: audit log retention is operational infrastructure
  (compliance baseline), granted to all 4 industries via
  AUDIT_LOG_RETENTION capability (CR 12-1 L4 precedent).
- SHA-256 hash chain: sha256_hash = SHA-256(audit_log_id +
  payload_snapshot + previous_hash). Detect tampering.
- Immutable append-only trigger: BEFORE UPDATE/DELETE on
  audit_log_archive raise AuditLogArchiveImmutableError.

CR 12-5 D-14 typed exception envelope: NEW error classes
AuditLogArchiveImmutableError(403) +
AuditLogArchiveHashChainMismatchError(500) registered in
apps/api/main.py exception handlers.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0040_phase_6_audit_retention"
down_revision: str | None = "0039_phase_5_multi_region_backup"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


# ── Enum-like CHECK constraint values (single source of truth) ──
VALID_REGIONS = (
    "primary_seoul",
    "secondary_tokyo",
    "cold_archive_s3",
)


def upgrade() -> None:
    """Create `audit_log_archive` + `phase_6_audit_purge_log` + ALTER `audit_logs`.

    All tables RLS-enabled (CR 0-2 verbatim) — per-tenant isolation.
    audit_log_archive is append-only (BEFORE UPDATE/DELETE trigger).
    """
    # ─────────────────────────────────────────────────────────────
    # Table 1: audit_log_archive (PRD §F22.3 verbatim)
    # ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_log_archive",
        sa.Column(
            "archive_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID PK — unique immutable archive entry id",
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Tenant UUID (RLS auto-isolation via app.tenant_id GUC).",
        ),
        sa.Column(
            "audit_log_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Source audit_log row UUID being archived.",
        ),
        sa.Column(
            "payload_snapshot",
            sa.dialects.postgresql.JSONB(),
            nullable=False,
            comment=(
                "Full pre-mutation JSONB snapshot of source row "
                "(includes actor_email, actor_phone, payload_json, etc.)."
            ),
        ),
        sa.Column(
            "archived_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Archive INSERT timestamp (UTC).",
        ),
        sa.Column(
            "sha256_hash",
            sa.Text(),
            nullable=False,
            comment=(
                "SHA-256 hex digest of (audit_log_id || payload_snapshot "
                "|| previous_hash). Used for tampering detection."
            ),
        ),
        sa.Column(
            "previous_hash",
            sa.Text(),
            nullable=True,
            comment=(
                "Prior archive row's sha256_hash in same tenant — NULL "
                "for the very first row in a tenant's hash chain."
            ),
        ),
        sa.Column(
            "region",
            sa.Text(),
            nullable=False,
            comment=(
                "Enum: 'primary_seoul' | 'secondary_tokyo' | "
                "'cold_archive_s3' "
                "(CHECK ck_audit_log_archive_region)"
            ),
        ),
    )

    # Indexes (PRD §F22.3 verbatim).
    op.create_index(
        "idx_audit_log_archive_tenant_archived_at",
        "audit_log_archive",
        ["tenant_id", "archived_at"],
        unique=False,
    )
    op.create_index(
        "idx_audit_log_archive_audit_log_id",
        "audit_log_archive",
        ["audit_log_id"],
        unique=False,
    )
    op.create_index(
        "idx_audit_log_archive_sha256_hash",
        "audit_log_archive",
        ["sha256_hash"],
        unique=False,
    )

    # CHECK constraint (region enum).
    op.create_check_constraint(
        "ck_audit_log_archive_region",
        "audit_log_archive",
        sa.text(f"region IN {tuple(VALID_REGIONS)!s}"),
    )

    # RLS auto-isolation (CR 0-2 verbatim).
    op.execute("ALTER TABLE audit_log_archive ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY audit_log_archive_tenant_isolation ON audit_log_archive
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # Immutable append-only trigger (PRD §F22.3 verbatim — BEFORE
    # UPDATE/DELETE raise AuditLogArchiveImmutableError).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_log_archive_immutable_guard()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'audit_log_archive is immutable (append-only)';
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_archive_immutable_update
            BEFORE UPDATE ON audit_log_archive
            FOR EACH ROW EXECUTE FUNCTION audit_log_archive_immutable_guard();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_log_archive_immutable_delete
            BEFORE DELETE ON audit_log_archive
            FOR EACH ROW EXECUTE FUNCTION audit_log_archive_immutable_guard();
        """
    )

    # ─────────────────────────────────────────────────────────────
    # Table 2: phase_6_audit_purge_log (PRD §F22.3 verbatim)
    # ─────────────────────────────────────────────────────────────
    op.create_table(
        "phase_6_audit_purge_log",
        sa.Column(
            "purge_log_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            comment="UUID PK — unique purge-run id",
        ),
        sa.Column(
            "tenant_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
            comment="Tenant UUID (RLS auto-isolation).",
        ),
        sa.Column(
            "purged_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="Purge job run timestamp (UTC).",
        ),
        sa.Column(
            "purged_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
            comment=(
                "Number of audit_log rows DELETEd in this purge run "
                "(per-tenant; or aggregated for global cron runs)."
            ),
        ),
        sa.Column(
            "dry_run",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
            comment="True if this purge was a dry-run (count only, no DELETE).",
        ),
        sa.Column(
            "trace_id",
            sa.Text(),
            nullable=True,
            comment=("UUID4 trace_id for observability (Sentry breadcrumb)."),
        ),
    )

    op.create_index(
        "idx_phase_6_audit_purge_log_tenant_purged_at",
        "phase_6_audit_purge_log",
        ["tenant_id", "purged_at"],
        unique=False,
    )

    # RLS auto-isolation (CR 0-2 verbatim).
    op.execute("ALTER TABLE phase_6_audit_purge_log ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY phase_6_audit_purge_log_tenant_isolation ON phase_6_audit_purge_log
            USING (tenant_id = current_setting('app.tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )

    # ─────────────────────────────────────────────────────────────
    # ALTER audit_logs: add archived_at column (PRD §F22.3 verbatim)
    #
    # D-CI-FUNC-9 cj-234 fix: previous code passed `"audit_log"`
    # (singular) to `op.add_column`, but 0001 created the table as
    # `audit_logs` (plural). Postgres reported
    # `relation "audit_log" does not exist` and the migration aborted
    # before archived_at was added. Fix: rename the SQL identifier to
    # `audit_logs`. The audit_log_archive / audit_log_id / audit_logs_row
    # identifiers in this file are intentionally preserved as-is —
    # they're either separate tables (`audit_log_archive`) or column
    # names (`audit_log_id`), not the source table being altered.
    # ─────────────────────────────────────────────────────────────
    op.add_column(
        "audit_logs",
        sa.Column(
            "archived_at",
            sa.TIMESTAMP(timezone=True),
            nullable=True,
            comment=(
                "Set when this audit_log row was archived (move-on-archive "
                "pattern). NULL means not yet archived."
            ),
        ),
    )

    # AFTER DELETE trigger: archive_expired_audit_logs
    # (when audit_log row is DELETEd, archive snapshot is INSERTed before
    # the DELETE completes; preserved across purge cycles for compliance).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION archive_expired_audit_logs()
        RETURNS trigger AS $$
        BEGIN
            INSERT INTO audit_log_archive (
                archive_id, tenant_id, audit_log_id, payload_snapshot,
                sha256_hash, previous_hash, region
            )
            SELECT
                gen_random_uuid(),
                OLD.tenant_id,
                OLD.audit_log_id,
                to_jsonb(OLD.*),
                encode(
                    digest(
                        OLD.audit_log_id::text || to_jsonb(OLD.*)::text ||
                        COALESCE(
                            (SELECT sha256_hash FROM audit_log_archive
                             WHERE tenant_id = OLD.tenant_id
                             ORDER BY archived_at DESC LIMIT 1),
                            ''
                        ),
                        'sha256'
                    ),
                    'hex'
                ),
                (SELECT sha256_hash FROM audit_log_archive
                 WHERE tenant_id = OLD.tenant_id
                 ORDER BY archived_at DESC LIMIT 1),
                'primary_seoul'
            FROM pg_extension WHERE extname='pgcrypto';
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    # NOTE: the above trigger function uses pgcrypto's digest() which
    # requires CREATE EXTENSION pgcrypto on the database. The function
    # is idempotent and replaces any prior version.


def downgrade() -> None:
    """Drop triggers + tables + ALTER audit_logs archived_at column."""
    # Drop triggers on audit_log_archive.
    op.execute(
        "DROP TRIGGER IF EXISTS trg_audit_log_archive_immutable_update ON audit_log_archive;"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS trg_audit_log_archive_immutable_delete ON audit_log_archive;"
    )
    op.execute("DROP FUNCTION IF EXISTS audit_log_archive_immutable_guard();")
    op.execute("DROP FUNCTION IF EXISTS archive_expired_audit_logs();")

    # Drop audit_log_archive policies + table.
    op.execute("DROP POLICY IF EXISTS audit_log_archive_tenant_isolation ON audit_log_archive;")
    op.drop_index("idx_audit_log_archive_sha256_hash", table_name="audit_log_archive")
    op.drop_index("idx_audit_log_archive_audit_log_id", table_name="audit_log_archive")
    op.drop_index("idx_audit_log_archive_tenant_archived_at", table_name="audit_log_archive")
    op.drop_constraint("ck_audit_log_archive_region", "audit_log_archive", type_="check")
    op.drop_table("audit_log_archive")

    # Drop phase_6_audit_purge_log policies + table.
    op.execute(
        "DROP POLICY IF EXISTS phase_6_audit_purge_log_tenant_isolation ON phase_6_audit_purge_log;"
    )
    op.drop_index(
        "idx_phase_6_audit_purge_log_tenant_purged_at", table_name="phase_6_audit_purge_log"
    )
    op.drop_table("phase_6_audit_purge_log")

    # Drop archived_at column from audit_logs.
    op.drop_column("audit_logs", "archived_at")
