"""settings_version column type: Integer → BigInteger (F-17).

Story 1.1 — applied alongside the post-review patches. PostgreSQL int4
tops out at ~2.1B; for a long-lived tenant, optimistic-concurrency
bumps could plausibly reach that. BigInteger (int8) gives ~9.2e18 headroom.

Revision ID: 0003_settings_version_bigint
Revises: 0002_tenant_settings_onboarding_defaults
Create Date: 2026-07-29
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_settings_version_bigint"
down_revision = "0002_tenant_settings_onboarding_defaults"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """ALTER COLUMN settings_version TYPE BIGINT."""
    op.alter_column(
        "tenant_settings",
        "settings_version",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=False,
        existing_server_default=sa.text("1"),
    )


def downgrade() -> None:
    """Revert settings_version back to Integer.

    WARNING: if any row already exceeds int4 max (~2.1B), the cast will
    raise. Run a SELECT MAX(settings_version) first if downgrading in prod.
    """
    op.alter_column(
        "tenant_settings",
        "settings_version",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=False,
        existing_server_default=sa.text("1"),
    )