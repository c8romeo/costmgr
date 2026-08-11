"""Story 12.4 (Epic 12 carry-over sprint) — users TOTP columns for 2FA.

Story 12.1 wired the pure kernel (`packages/services/m12_account/totp.py`),
the service layer (`apps/api/modules/m12_account/services/`), and the ORM
model extension (`apps/api/core/db_models.py::User.totp_*`) — but the
Alembic migration was honestly DEFERred (T4). This migration closes that
gap so the ORM columns actually exist in the database.

5 NEW columns on `users`:

  - `totp_secret`              BYTEA       — AES-256-GCM ciphertext blob
                                            (nonce || ciphertext || tag),
                                            NEVER the raw base32 secret.
  - `totp_enabled_at`          TIMESTAMPTZ — set when verify_and_enable_totp
                                            succeeds; NULL while unenrolled.
  - `totp_failed_attempts`     INTEGER     — consecutive challenge failures,
                                            reset to 0 on success.
  - `totp_lockout_until`       TIMESTAMPTZ — set when failed_attempts hits
                                            MAX_FAILED_ATTEMPTS (5); lockout
                                            window is LOCKOUT_DURATION_SECONDS
                                            (900s = 15min).
  - `totp_recovery_codes_hash` JSONB       — array of 8 PBKDF2-SHA256 entries
                                            `{"salt": hex, "hash": hex,
                                              "used_at": ""}`.

NFR6 (AES-256-GCM column-level encryption): `totp_secret` stores only the
ciphertext produced by `apps.api.core.crypto.encrypt_at_rest` with
`key_id=DEFAULT_KEY_ID` and `aad=b"totp_secret"`. The AAD binds the
ciphertext to its column so a blob lifted from another column cannot be
decrypted here.

`users.twofa_enabled` (BOOLEAN, Alembic 0001) is retained and NOT dropped —
it is the coarse legacy flag. `totp_enabled_at IS NOT NULL` is the
authoritative 2FA-enrolled predicate from Story 12.1 onward; the two are
kept in sync by `TwoFactorService`.

Down revision: 0021_cache_invalidation_multi_channel (Story 11.3 tip).

Revision ID: 0022_users_totp_columns
Revises:    0021_cache_invalidation_multi_channel
Create Date: 2026-08-11
"""

from __future__ import annotations

from alembic import op

revision = "0022_users_totp_columns"
down_revision = "0021_cache_invalidation_multi_channel"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the 5 TOTP columns to `users`.

    All columns are added as nullable (or with a server default) so the
    migration is safe on a populated `users` table — existing rows become
    "2FA not enrolled" without a backfill.
    """
    op.execute(
        """
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS totp_secret              BYTEA       NULL,
            ADD COLUMN IF NOT EXISTS totp_enabled_at          TIMESTAMPTZ NULL,
            ADD COLUMN IF NOT EXISTS totp_failed_attempts     INTEGER     NOT NULL DEFAULT 0,
            ADD COLUMN IF NOT EXISTS totp_lockout_until       TIMESTAMPTZ NULL,
            ADD COLUMN IF NOT EXISTS totp_recovery_codes_hash JSONB       NULL
        """
    )

    # Non-negative invariant for the failure counter. The service resets to
    # 0 on success and increments by 1 on failure, so a negative value can
    # only come from a bug or a manual UPDATE.
    op.execute(
        """
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_totp_failed_attempts_non_negative
        """
    )
    op.execute(
        """
        ALTER TABLE users
        ADD CONSTRAINT users_totp_failed_attempts_non_negative
        CHECK (totp_failed_attempts >= 0)
        """
    )

    # Partial index for the lockout-cleanup cron (AD-9, KST 02:00 daily):
    # `SELECT … WHERE totp_lockout_until IS NOT NULL AND totp_lockout_until < now()`.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_users_totp_lockout_until
        ON users (totp_lockout_until)
        WHERE totp_lockout_until IS NOT NULL
        """
    )

    # Partial index for "is this user enrolled?" lookups on the M2 entry gate.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_users_totp_enabled_at
        ON users (tenant_id, totp_enabled_at)
        WHERE totp_enabled_at IS NOT NULL
        """
    )

    # ── Column documentation (NFR6 contract) ──────────────────
    op.execute(
        """
        COMMENT ON COLUMN users.totp_secret IS
        'NFR6 AES-256-GCM ciphertext blob (nonce || ciphertext || tag) of the '
        'base32 TOTP secret. Encrypted via apps.api.core.crypto.encrypt_at_rest '
        'with key_id=DEFAULT_KEY_ID and aad=''totp_secret''. NEVER stores plaintext.'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN users.totp_enabled_at IS
        'Authoritative 2FA-enrolled predicate from Story 12.1 onward. '
        'NULL = not enrolled. Kept in sync with the legacy users.twofa_enabled flag.'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN users.totp_failed_attempts IS
        'Consecutive TOTP challenge failures. Reset to 0 on success. '
        'Reaching MAX_FAILED_ATTEMPTS (5) sets totp_lockout_until.'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN users.totp_lockout_until IS
        'Lockout expiry. Set to now() + LOCKOUT_DURATION_SECONDS (900s) on the '
        '5th consecutive failure. NULL when not locked out.'
        """
    )
    op.execute(
        """
        COMMENT ON COLUMN users.totp_recovery_codes_hash IS
        'JSONB array of 8 PBKDF2-SHA256 recovery-code entries: '
        '{"salt": hex, "hash": hex, "used_at": "" | ISO-8601}. '
        'A non-empty used_at marks the code as consumed (single-use).'
        """
    )


def downgrade() -> None:
    """Drop the 5 TOTP columns.

    WARNING: this is destructive — every enrolled user's TOTP secret and
    recovery-code hashes are lost, and all users revert to "not enrolled".
    Operators MUST export `users.totp_*` before downgrading if re-enrolment
    is not acceptable.
    """
    op.execute("DROP INDEX IF EXISTS ix_users_totp_enabled_at")
    op.execute("DROP INDEX IF EXISTS ix_users_totp_lockout_until")
    op.execute(
        """
        ALTER TABLE users
        DROP CONSTRAINT IF EXISTS users_totp_failed_attempts_non_negative
        """
    )
    op.execute(
        """
        ALTER TABLE users
            DROP COLUMN IF EXISTS totp_recovery_codes_hash,
            DROP COLUMN IF EXISTS totp_lockout_until,
            DROP COLUMN IF EXISTS totp_failed_attempts,
            DROP COLUMN IF EXISTS totp_enabled_at,
            DROP COLUMN IF EXISTS totp_secret
        """
    )
