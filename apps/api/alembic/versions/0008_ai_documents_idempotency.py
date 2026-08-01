"""AI document idempotency key — Story 1.3 (Task 1.2 follow-up).

Adds:
- ``uploaded_documents.idempotency_key`` — TEXT column for the client's
  ``Idempotency-Key`` header. Network retries with the same key collapse
  to a single document row (Task 3.1 / AC #2).
- Partial unique index
  ``uq_uploaded_documents_tenant_idempotency`` — keyed on
  ``(tenant_id, idempotency_key) WHERE idempotency_key IS NOT NULL``
  so non-idempotent uploads (no header sent) still get a unique row.

Why a partial index (vs a full unique on the pair):
- The Idempotency-Key header is OPTIONAL — clients without retry
  behavior may omit it. A full unique index would force NULL vs NULL
  comparisons in Postgres, which always return ``NULL`` (i.e. not
  unique). The partial index excludes NULLs entirely.
- TTL of 24 hours (`apps/api/modules/m10_ai.config.IDEMPOTENCY_KEY_TTL_HOURS`)
  is enforced by a future cleanup job (out of scope here).

Per AD-15: ``idempotency_key`` is TEXT (no length cap at DB level) so
clients can use UUIDs / opaque tokens / ULIDs. The application enforces
a sensible max in handlers.py (32 chars) before persisting.

Revision ID: 0008_ai_documents_idempotency
Revises:    0007_bom_matrix
Create Date: 2026-08-01
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0008_ai_documents_idempotency"
down_revision: str | Sequence[str] | None = "0007_bom_matrix"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE uploaded_documents "
        "ADD COLUMN IF NOT EXISTS idempotency_key TEXT NULL"
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_uploaded_documents_tenant_idempotency
        ON uploaded_documents(tenant_id, idempotency_key)
        WHERE idempotency_key IS NOT NULL
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_uploaded_documents_tenant_idempotency")
    op.execute("ALTER TABLE uploaded_documents DROP COLUMN IF EXISTS idempotency_key")
