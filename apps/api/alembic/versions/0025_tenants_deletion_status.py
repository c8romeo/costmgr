"""Story 12.3 — tenants.status FSM + deletion_consents table.

PRD §F12.3 + epics.md Story 12.3 + NFR4 2절 (5년 audit 보존 + 30일 후
hard delete) + NFR7 (2FA 강제 on destructive endpoint) + AD-9 Seoul region +
AD-2 INSERT-only invariant + AD-3 RLS multi-tenancy.

This migration introduces:

1. `tenants` EXTENSION — 6 NEW columns (Story 12.3 destructive endpoint FSM):
   - `status`                          TEXT NOT NULL DEFAULT 'active'
                                       CHECK in ('active','pending_deletion','deleted')
   - `deletion_requested_at`           TIMESTAMPTZ NULL
   - `deletion_requested_by_user_id`   UUID NULL REFERENCES users(id) ON DELETE SET NULL
   - `deletion_consent_id`             UUID NULL REFERENCES deletion_consents(consent_id)
                                                                  ON DELETE SET NULL
   - `deletion_scheduled_for`          TIMESTAMPTZ NULL  -- 30-day retention anchor
   - `deletion_anonymized_at`          TIMESTAMPTZ NULL  -- cron anonymization marker

2. `deletion_consents` NEW TABLE — 7 columns + 1 unique + 1 hash-length CHECK:
   - `consent_id`                UUID PRIMARY KEY DEFAULT gen_random_uuid()
   - `tenant_id`                 UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
   - `consent_text_hash`         TEXT NOT NULL  -- SHA-256 hex (64 chars)
                                                  CHECK (length = 64)
   - `encrypted_consent_text`    BYTEA NOT NULL  -- AES-256-GCM ciphertext
                                                    (28-byte overhead: 12-nonce + ct + 16-tag)
                                                    Distinct AAD b"deletion_consent" per NFR6.
   - `consent_checked_at`        TIMESTAMPTZ NOT NULL DEFAULT now()
   - `consent_checked_by_user_id` UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT
   - `consent_ip`                TEXT NULL  -- captured for audit (X-Forwarded-For)
   - `consent_user_agent`        TEXT NULL  -- captured for audit
   + UNIQUE INDEX on (tenant_id) WHERE NOT yet soft-retired (future-proof).
   + AD-2 INSERT-only enforced by trigger (mirrors 0024 pattern).

3. AD-2 INSERT-only trigger on `deletion_consents`:
   - `deletion_consents_insert_only` BEFORE UPDATE OR DELETE → raises
     "append-only violation" (mirror audit_logs 0001 pattern).
   - Plaintext consent text is NEVER stored (only SHA-256 hex hash +
     AES-256-GCM ciphertext). AD-15 §6: consent records are immutable
     for forensic chain.

4. Indexes:
   - `tenants_status_idx`           — partial index WHERE status='pending_deletion'
                                       (cron filter for hard-delete sweep).
   - `deletion_consents_tenant_idx` — (tenant_id, consent_checked_at DESC)
                                       (forensic lookup per tenant).

Down revision: 0024_tenant_backups (Story 12.2 wire).

Revision ID: 0025_tenants_deletion_status
Revises:    0024_tenant_backups
Create Date: 2026-08-15
"""

from __future__ import annotations

from alembic import op

revision = "0025_tenants_deletion_status"
down_revision = "0024_tenant_backups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── tenants EXTENSION (6 NEW columns) ─────────────────────────
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'active'")
    op.execute(
        "ALTER TABLE tenants ADD CONSTRAINT tenants_status_check "
        "CHECK (status IN ('active', 'pending_deletion', 'deleted'))"
    )
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deletion_requested_at TIMESTAMPTZ NULL")
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deletion_requested_by_user_id "
        "UUID NULL REFERENCES users(id) ON DELETE SET NULL"
    )
    op.execute(
        "ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deletion_consent_id UUID NULL"
    )
    # FK to deletion_consents(consent_id) added AFTER deletion_consents table created below.
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deletion_scheduled_for TIMESTAMPTZ NULL")
    op.execute("ALTER TABLE tenants ADD COLUMN IF NOT EXISTS deletion_anonymized_at TIMESTAMPTZ NULL")

    # ── deletion_consents NEW TABLE ───────────────────────────────
    op.execute(
        """
        CREATE TABLE deletion_consents (
            consent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            consent_text_hash TEXT NOT NULL,
            encrypted_consent_text BYTEA NOT NULL,
            consent_checked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            consent_checked_by_user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            consent_ip TEXT NULL,
            consent_user_agent TEXT NULL,
            CONSTRAINT deletion_consents_hash_length_check
                CHECK (length(consent_text_hash) = 64)
        )
        """
    )

    # Now FK from tenants.deletion_consent_id → deletion_consents.consent_id
    # (SET NULL on consent row removal — keeps tenant audit trail intact).
    op.execute(
        "ALTER TABLE tenants ADD CONSTRAINT tenants_deletion_consent_id_fkey "
        "FOREIGN KEY (deletion_consent_id) REFERENCES deletion_consents(consent_id) "
        "ON DELETE SET NULL"
    )

    # ── Index: cron filter for pending_deletion tenants ───────────
    op.execute(
        "CREATE INDEX tenants_status_pending_deletion_idx "
        "ON tenants (deletion_scheduled_for) WHERE status = 'pending_deletion'"
    )

    # ── Index: deletion_consents forensic lookup per tenant ───────
    op.execute(
        "CREATE INDEX deletion_consents_tenant_idx "
        "ON deletion_consents (tenant_id, consent_checked_at DESC)"
    )

    # ── AD-2 INSERT-only trigger (mirror 0024 pattern) ─────────────
    op.execute(
        """
        CREATE OR REPLACE FUNCTION reject_append_only_deletion_consents()
        RETURNS TRIGGER AS $$
        BEGIN
            -- UPDATE always blocked (consent records are immutable).
            IF (TG_OP = 'UPDATE') THEN
                RAISE EXCEPTION
                    'deletion_consents is INSERT-only (AD-2): '
                    'UPDATE is forbidden (consent rows are immutable for forensic chain)';
            END IF;
            -- DELETE always blocked (forensic chain — only tombstone via
            -- consent_text_hash redaction would be a separate audit-first operation).
            IF (TG_OP = 'DELETE') THEN
                RAISE EXCEPTION
                    'deletion_consents is INSERT-only (AD-2): '
                    'DELETE is forbidden (consent rows are immutable for forensic chain)';
            END IF;
            RETURN NULL;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER deletion_consents_insert_only
        BEFORE UPDATE OR DELETE ON deletion_consents
        FOR EACH ROW EXECUTE FUNCTION reject_append_only_deletion_consents();
        """
    )

    # ── Documentation ─────────────────────────────────────────────
    op.execute(
        "COMMENT ON TABLE deletion_consents IS "
        "'Story 12.3 — deletion consent forensic record (AES-256-GCM ciphertext + SHA-256 hash). "
        "AD-2 INSERT-only enforced by trigger. Plaintext consent text is NEVER stored. "
        "Cron: apps/api/jobs/tenant_hard_delete.py (KST 04:00, 30-day sweep after pending_deletion). "
        "NFR4 2절: 5년 audit 보존; NFR6 AES-256-GCM distinct AAD b\"deletion_consent\".'"
    )
    op.execute(
        "COMMENT ON COLUMN deletion_consents.encrypted_consent_text IS "
        "'AES-256-GCM ciphertext (28-byte overhead: 12-nonce + ct + 16-tag). "
        "Distinct AAD b\"deletion_consent\" per NFR6 column-level encryption. "
        "Plaintext consent text is reconstructed in-memory ONLY for the audit envelope dump.'"
    )
    op.execute(
        "COMMENT ON COLUMN deletion_consents.consent_text_hash IS "
        "'SHA-256 hex digest of plaintext consent text (64 chars). Used for "
        "audit trace + future consent-text-equality proofs WITHOUT exposing plaintext.'"
    )
    op.execute(
        "COMMENT ON COLUMN tenants.status IS "
        "'Tenant FSM: active | pending_deletion | deleted. Cron sweeps "
        "pending_deletion tenants whose deletion_scheduled_for <= now() for "
        "hard delete (status → deleted + 30-day purge).'"
    )
    op.execute(
        "COMMENT ON COLUMN tenants.deletion_scheduled_for IS "
        "'30-day retention anchor. Set at request_deletion time. Cron sweeps "
        "tenants WHERE deletion_scheduled_for <= now() for hard delete.'"
    )
    op.execute(
        "COMMENT ON COLUMN tenants.deletion_anonymized_at IS "
        "'Cron anonymization marker. Set when the cron anonymizes PII before "
        "hard delete (separate step before tenant_hard_deleted).'"
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS deletion_consents_insert_only ON deletion_consents")
    op.execute("DROP FUNCTION IF EXISTS reject_append_only_deletion_consents()")
    op.execute("DROP TABLE IF EXISTS deletion_consents")
    op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_deletion_consent_id_fkey")
    op.execute("ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_status_check")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS deletion_anonymized_at")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS deletion_scheduled_for")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS deletion_consent_id")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS deletion_requested_by_user_id")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS deletion_requested_at")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS status")
