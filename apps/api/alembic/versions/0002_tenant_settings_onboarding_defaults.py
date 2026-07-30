"""0002 tenant_settings onboarding JSONB defaults + index.

Story 1.1 — Task 7. AD-23: tenant_settings.onboarding is the JSONB namespace
that stores M0 onboarding state (`industry`, `selected_at`, `is_initial`).

This migration:
1. Sets a JSONB DEFAULT of `'{"industry": null, "is_initial": true, "selected_at": null}'`
   on `tenant_settings.onboarding` so new tenants (created via Story 0.2
   signup) get a valid onboarding shape from day one. The `is_initial: true`
   default is critical — it means the FIRST POST industry update is allowed
   without triggering the 7-day grace path (Decision §1).
2. Adds a btree expression index on `onboarding->>'industry'` so the menu
   lookup stays fast as tenant count grows past 100 (Subtask 7.2).

Per AD-15: snake_case identifiers. Per AD-14: Alembic revision follows the
`NNNN_descriptive_slug` convention (docs/conventions.md §3).

F-27 — Manual JSONB edits re-enable the grace window silently.

Operators (or anyone with `UPDATE` privileges) can hand-edit the JSONB
shape, e.g. set `is_initial=true` on a row that already has `selected_at`
older than 7 days. The `SettingsService` reads `is_initial` from the JSONB
as the source of truth, so a hand-edit would re-open the 7-day grace for
a tenant that was previously locked. This is acceptable as an "ops
override" path, but we want it observable:

  - The `audit_logs` table should record any direct DB mutation. Operators
    running ad-hoc SQL must write a corresponding `audit_logs` row tagged
    `action='manual_jsonb_override'` with the before/after JSONB.
  - The `Story 1.4` monitoring job (epics line 738) adds a periodic check
    that flags any row where `is_initial=true AND selected_at < now() - 7d`
    so silent grace-window reopens are visible to admins.

This migration does NOT add database triggers to enforce the invariant
(the application layer is the source of truth). The trigger-based guard
is deferred to a later hardening story.
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_tenant_settings_onboarding_defaults"
down_revision: str | None = "0001_tenants_users_memberships_settings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── 1. Set the onboarding JSONB default ─────────────────
    # `is_initial: true` so the first POST industry is allowed (Decision §1).
    # `selected_at: null` — will be set on first POST.
    op.execute(
        """
        ALTER TABLE tenant_settings
        ALTER COLUMN onboarding
        SET DEFAULT '{"industry": null, "is_initial": true, "selected_at": null}'::jsonb
        """
    )

    # ── 2. Expression index on onboarding.industry ──────────
    # Helps `WHERE onboarding->>'industry' = $1` queries stay O(log n) at scale.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_tenant_settings_onboarding_industry
        ON tenant_settings ((onboarding->>'industry'))
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_tenant_settings_onboarding_industry")
    op.execute(
        """
        ALTER TABLE tenant_settings
        ALTER COLUMN onboarding SET DEFAULT '{}'::jsonb
        """
    )
