"""AI document extraction persistence — Story 1.3 (Task 1.2).

Adds two tables that back the AI document-extraction feature:

- ``uploaded_documents`` — one row per uploaded file (PDF / image). Carries
  the Supabase Storage path + sha256 of the bytes (for the
  ``409 DOCUMENT_ALREADY_EXISTS`` re-upload guard) + retention metadata.

- ``input_drafts`` — one row per AI-extracted field. AD-7 + the new
  ``docs/architecture-decisions/AD-7-ai-extraction-table-naming.md``
  declare ``input_drafts`` canonical (supersedes the ERD's
  ``ai_extractions``). The companion ``supabase/policies/0005_…sql``
  file adds RLS.

Per AD-15 (``docs/conventions.md §3`` + ``AD-15-tenant-id-variance.md``):
- business IDs (``document_id``, ``draft_id``) — UUID **v7** (time-ordered)
- ``tenant_id`` — UUID **v4** (derived from JWT, never from request body)

Per AD-7: ``input_drafts`` holds AI output. The draft ``state`` is the
single source of truth — AD-17's ``InputPromoter`` is reserved for
Epic 3 monthly-input promotion and is NOT reused here. Confirmed company
fields land in ``tenant_settings.onboarding.company_subblock`` (Option C)
via ``SettingsService.update_onboarding_field`` — see Task 3.4.

Story 1.3 also creates ``apps/api/core/confidence.py::REVIEW_THRESHOLD``
= ``Decimal("0.70")`` and an ``ai_documents_jobs`` row is added in a
later migration; for now this revision covers ``uploaded_documents``
+ ``input_drafts`` only.

State machine (AC #4 / Task 1.3):
    draft → reviewed → superseded
Provider job status (separate column on ``uploaded_documents``):
    queued | processing | completed | failed

Indexes (Task 1.2):
- ``(tenant_id, uploaded_at)`` — newest-first dashboard query
- ``(tenant_id, content_sha256)`` — re-upload guard (409 DOCUMENT_ALREADY_EXISTS)
- ``(tenant_id, document_id, field_name)`` — draft lookup; uniqueness
- ``(tenant_id, state)`` — review-queue scan

Revision ID: 0005_ai_documents_input_drafts
Revises:    0004_tenant_settings_onboarding_extend
Create Date: 2026-07-31
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005_ai_documents_input_drafts"
down_revision: str | Sequence[str] | None = "0004_tenant_settings_onboarding_extend"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# State values for `input_drafts.state` (AD-7 + spec Task 1.2).
# `promoted` is intentionally absent — that's an AD-17 monthly-input semantic
# that does NOT apply to AI company-identity drafts.
_DRAFT_STATES = ("draft", "reviewed", "superseded")

# Job status values for `uploaded_documents.job_status`. These are
# independent of `input_drafts.state` per Task 1.2.
_JOB_STATUSES = ("queued", "processing", "completed", "failed")


def upgrade() -> None:
    # ── uploaded_documents ────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS uploaded_documents (
            document_id      UUID PRIMARY KEY,                 -- UUID v7 (time-ordered)
            tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            storage_path     TEXT NOT NULL,                    -- Supabase Storage key
            mime_type        TEXT NOT NULL,                    -- server-validated
            byte_size        BIGINT NOT NULL CHECK (byte_size > 0),
            content_sha256   BYTEA NOT NULL,                   -- sha256(document_bytes)
            page_count       INTEGER NULL,                     -- PDFs only
            job_status       TEXT NOT NULL DEFAULT 'queued' CHECK (job_status IN (
                'queued', 'processing', 'completed', 'failed'
            )),
            uploaded_by      UUID NOT NULL,
            uploaded_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            reviewed_at      TIMESTAMPTZ NULL,                 -- set on first reviewed draft
            deleted_at       TIMESTAMPTZ NULL,                 -- soft-delete (90-day retention)
            error_code       TEXT NULL,                        -- structured failure code
            error_message_ko TEXT NULL                         -- AD-15 localized message
        )
        """
    )

    # ── input_drafts ──────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS input_drafts (
            draft_id          UUID PRIMARY KEY,                 -- UUID v7
            tenant_id         UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            document_id       UUID NOT NULL REFERENCES uploaded_documents(document_id) ON DELETE CASCADE,
            field_name        TEXT NOT NULL,
            ai_value          JSONB NOT NULL,                   -- typed: string/number/decimal/date
            confirmed_value   JSONB NULL,                       -- set on user review
            confidence        NUMERIC(4,3) NULL CHECK (
                                  confidence IS NULL
                                  OR (confidence >= 0 AND confidence <= 1)
                              ),
            state             TEXT NOT NULL DEFAULT 'draft' CHECK (state IN (
                'draft', 'reviewed', 'superseded'
            )),
            evidence          JSONB NOT NULL DEFAULT '{}'::jsonb,  -- text max 200 chars (app-enforced)
            draft_hash        BYTEA NOT NULL,                   -- sha256(canonical_json(payload))
            version           INTEGER NOT NULL DEFAULT 1,
            requested_by      UUID NOT NULL,
            requested_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
            reviewed_by       UUID NULL,
            reviewed_at       TIMESTAMPTZ NULL
        )
        """
    )

    # ── Indexes ────────────────────────────────────────────────
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_uploaded_documents_tenant_uploaded_at "
        "ON uploaded_documents(tenant_id, uploaded_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_uploaded_documents_tenant_sha "
        "ON uploaded_documents(tenant_id, content_sha256)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_input_drafts_tenant_requested_at "
        "ON input_drafts(tenant_id, requested_at DESC)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_input_drafts_tenant_state "
        "ON input_drafts(tenant_id, state)"
    )

    # Unique constraint on (tenant_id, document_id, field_name) — at most
    # one draft per (document, field). The non-unique lookup index from
    # the spec is folded into this unique index (Postgres can use it for
    # both purposes). Re-uploads of the same document (same content_sha256)
    # get 409 DOCUMENT_ALREADY_EXISTS at the API boundary; this index
    # makes the lookup fast.
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_input_drafts_tenant_doc_field
        ON input_drafts(tenant_id, document_id, field_name)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS input_drafts")
    op.execute("DROP TABLE IF EXISTS uploaded_documents")
