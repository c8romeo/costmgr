"""Story 12.4 (Epic 12 carry-over sprint) — used_challenge_tokens table.

Challenge tokens (HS256 JWT) are issued and consumed by TwoFactorChallengeService
when a user passes the 2FA challenge before M2 entry. Without a replay guard,
a token captured by an attacker (or replayed by a buggy client) could be
consumed multiple times within the 5-min TTL window.

This migration adds a `used_challenge_tokens` table that records the
`jti` (JWT ID) of every consumed challenge token. The service does
INSERT followed by a uniqueness check — a duplicate `jti` raises
`ChallengeTokenAlreadyConsumedError` → 401 CHALLENGE_TOKEN_ALREADY_CONSUMED.

Schema:

  - `jti`        TEXT PRIMARY KEY — JWT ID (uuid4 hex from issue step)
  - `user_id`    UUID NOT NULL     — user that consumed the token
  - `tenant_id`  UUID NOT NULL     — tenant context (AD-3 tenant isolation)
  - `used_at`    TIMESTAMPTZ NOT NULL DEFAULT now() — when the consume completed

Index considerations:
  - PK on `jti` is sufficient for the replay check (PK lookup).
  - `used_at` is indexed so a periodic GC sweep can drop rows older than
    the TTL window (5 min) + a safety margin (e.g. 1 hour).

Why a separate table (not a column on `users`):
  - A single user may have multiple in-flight challenge tokens (e.g. issue
    one, refresh browser, issue another). The token identity is `jti`,
    not `user_id`.
  - GC is trivial: DELETE WHERE used_at < now() - interval '1 hour'.

Down revision: 0022_users_totp_columns (Story 12.4 tip).

Revision ID: 0023_used_challenge_tokens
Revises:    0022_users_totp_columns
Create Date: 2026-08-11
"""

from __future__ import annotations

from alembic import op

revision = "0023_used_challenge_tokens"
down_revision = "0022_users_totp_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE used_challenge_tokens (
            jti TEXT PRIMARY KEY,
            user_id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            used_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX used_challenge_tokens_used_at_idx "
        "ON used_challenge_tokens (used_at)"
    )
    # tenant_id index helps per-tenant GC sweeps (DELETE WHERE tenant_id = ...).
    op.execute(
        "CREATE INDEX used_challenge_tokens_tenant_id_idx "
        "ON used_challenge_tokens (tenant_id)"
    )
    op.execute(
        "COMMENT ON TABLE used_challenge_tokens IS "
        "'Story 12.4 — 2FA challenge token replay guard. INSERT with jti as PK; "
        "duplicate key (jti) triggers 401 CHALLENGE_TOKEN_ALREADY_CONSUMED. "
        "GC sweep: DELETE WHERE used_at < now() - interval ''1 hour''.'"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS used_challenge_tokens")
