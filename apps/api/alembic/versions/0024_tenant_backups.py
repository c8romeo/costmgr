"""Story 12.2 — tenant_backups table.

Per NFR4 (PRD §NFR4) "백업 보관 30일(자동)", the system needs a daily
per-tenant JSON dump of operational state. Storage decision per Story 12.2
spec §3 user decision: **Postgres JSONB table** `tenant_backups` (의존성 0 /
STACK_PIN BUMP 0 / 12-5 QR manual-entry decision 패턴).

Why a Postgres JSONB table (not Supabase Storage / S3):
- 의존성 0 — no new bucket, no new SDK, no new env vars
- RLS covers access control (no separate signed URL infra)
- Schema versioning + sha256 in the same row → atomic backup verification
- Same Postgres backup story covers this table (RPO 24h, 30-day retention
  via cron sweep — apps/api/jobs/backup_retention.py)
- AD-2 INSERT-only invariant via 0024 trigger (UPDATE/DELETE forbidden
  except for `purged_at` soft-delete column).

Schema (12 columns + 2 indexes + partial UNIQUE):

  - `backup_id`              UUID PRIMARY KEY DEFAULT uuid_generate_v4()
  - `tenant_id`              UUID NOT NULL FK → tenants(id) ON DELETE CASCADE
  - `backup_date`            TIMESTAMP NOT NULL  — YYYY-MM-DD anchor (KST date)
  - `created_at`             TIMESTAMPTZ NOT NULL DEFAULT now()
  - `schema_version`         TEXT NOT NULL DEFAULT '1.0'  — envelope version
  - `payload`                JSONB NOT NULL  — full backup payload (7 tables)
  - `payload_sha256`         TEXT NOT NULL  — sha256 of payload bytes (hex)
  - `row_count_total`        INTEGER NOT NULL  — total rows in payload
  - `audit_log_exported_rows` INTEGER NOT NULL DEFAULT 0  — audit_logs count
  - `retention_class`        TEXT NOT NULL DEFAULT 'daily'  — 'daily' | 'quarterly'
  - `purged_at`              TIMESTAMPTZ NULL  — 30-day retention soft-delete
  - `triggered_by_user_id`   UUID NULL FK → users(id) ON DELETE SET NULL

Indexes:
- `tenant_backups_tenant_id_backup_date_idx` — (tenant_id, backup_date DESC)
  for the "최근 7일 백업 다운로드" list query.
- `tenant_backups_purged_at_idx` — partial index WHERE purged_at IS NULL
  for the retention sweep filter.
- partial UNIQUE on (tenant_id, backup_date) WHERE purged_at IS NULL —
  ensures ONE active backup per tenant per day. Soft-deleted (purged)
  rows do NOT block a new backup on the same date.

RLS: `supabase/policies/0014_tenant_backups_rls.sql` (5-policy split per
AD-3: same-tenant SELECT + owner-only SELECT + same-tenant INSERT +
UPDATE forbidden + DELETE forbidden). Backup rows are immutable from
the application layer — only the retention cron can soft-delete via
`purged_at` column (UPDATE is blocked by RLS for non-service roles).

Down revision: 0023_used_challenge_tokens (Story 12.4 carry-over sprint).

Revision ID: 0024_tenant_backups
Revises:    0023_used_challenge_tokens
Create Date: 2026-08-12
"""

from __future__ import annotations

from alembic import op

revision = "0024_tenant_backups"
down_revision = "0023_used_challenge_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Table ──────────────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE tenant_backups (
            backup_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            backup_date TIMESTAMP NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            schema_version TEXT NOT NULL DEFAULT '1.0',
            payload JSONB NOT NULL,
            payload_sha256 TEXT NOT NULL,
            row_count_total INTEGER NOT NULL,
            audit_log_exported_rows INTEGER NOT NULL DEFAULT 0,
            retention_class TEXT NOT NULL DEFAULT 'daily',
            purged_at TIMESTAMPTZ NULL,
            triggered_by_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL
        )
        """
    )

    # ── Index: tenant_id + backup_date DESC (list query) ────────────
    op.execute(
        "CREATE INDEX tenant_backups_tenant_id_backup_date_idx "
        "ON tenant_backups (tenant_id, backup_date DESC)"
    )

    # ── Partial index: active (non-purged) backups per tenant ───────
    op.execute(
        "CREATE INDEX tenant_backups_purged_at_idx "
        "ON tenant_backups (tenant_id, purged_at) "
        "WHERE purged_at IS NULL"
    )

    # ── partial UNIQUE: one active backup per tenant per day ────────
    # Soft-deleted (purged) rows do NOT block re-creation on the same
    # date — only one ACTIVE backup is allowed per (tenant, date).
    op.execute(
        "CREATE UNIQUE INDEX tenant_backups_unique_active_per_day "
        "ON tenant_backups (tenant_id, backup_date) "
        "WHERE purged_at IS NULL"
    )

    # ── Documentation ───────────────────────────────────────────────
    op.execute(
        "COMMENT ON TABLE tenant_backups IS "
        "'Story 12.2 — daily per-tenant JSON dump + 30-day retention sweep. "
        "AD-2 INSERT-only (RLS 0014 blocks UPDATE/DELETE for non-service roles). "
        "Cron: apps/api/jobs/backup_daily.py (KST 02:00) + backup_retention.py "
        "(KST 03:00). NFR4: RPO 24h / RTO 4h / 30-day backup retention.'"
    )
    op.execute(
        "COMMENT ON COLUMN tenant_backups.payload IS "
        "'Full backup payload (7 tables: tenant_settings, products, bom_lines, "
        "monthly_input_periods, monthly_input_rows, fiscal_period_snapshots, "
        "audit_logs). JSONB envelope with schema_version=1.0 + 7-table mapping.'"
    )
    op.execute(
        "COMMENT ON COLUMN tenant_backups.payload_sha256 IS "
        "'Hex sha256 of payload bytes (json.dumps sort_keys=True default=str). "
        "Client verifies via X-Backup-SHA256 header on download.'"
    )
    op.execute(
        "COMMENT ON COLUMN tenant_backups.purged_at IS "
        "'30-day retention soft-delete column. UPDATE on this column is "
        "PERMITTED by the 0024 trigger + RLS 0014 retention policy; UPDATE on "
        "other columns is BLOCKED.'"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS tenant_backups")
