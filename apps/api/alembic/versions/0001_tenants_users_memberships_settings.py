"""Initial platform schema — tenants, users, memberships, settings, audit_logs.

Story 0.2 — Supabase Multi-Tenancy Schema + RLS Policies.

Tables (AD-3, AD-10, AD-23, AD-2):
- tenants               : tenant registry (industry enum)
- users                 : global users (nullable tenant_id for cross-tenant ops)
- tenant_memberships    : many-to-many tenant <-> user with role per tenant
- tenant_settings       : one row per tenant; JSONB namespaces (AD-23)
- audit_logs            : INSERT-only ledger (RLS policy enforces service_role)

This is the Alembic source-of-truth for the schema. There is NO
`supabase/migrations/*.sql` mirror — `supabase db push` does not run
Alembic. The canonical deployment path is:
    1. uv run alembic -c apps/api/alembic.ini upgrade head
    2. PGPASSWORD=$DB_ADMIN_PW psql $DATABASE_URL \
         -f supabase/policies/0000_supabase_ci_shim.sql  (CI/staging only)
    3. PGPASSWORD=$DB_ADMIN_PW psql $DATABASE_URL \
         -f supabase/policies/0001_rls_policies.sql
    4. PGPASSWORD=$DB_ADMIN_PW psql $DATABASE_URL \
         -f supabase/policies/0002_rls_smoke_test.sql   (CI smoke test)
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_tenants_users_memberships_settings"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# AD-10: role taxonomy for tenant membership
_ROLE_VALUES = ("owner", "member", "viewer", "consultant_proxy")
# AD-10: industry enum for tenant onboarding (M0)
_INDUSTRY_VALUES = ("manufacturing", "manufacturing_retail", "service", "mixed")


def upgrade() -> None:
    # pgcrypto for gen_random_uuid() — portable across Supabase + raw Postgres
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ── tenants ────────────────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenants (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name        TEXT NOT NULL,
            industry    TEXT NOT NULL CHECK (industry IN (
                'manufacturing', 'manufacturing_retail', 'service', 'mixed'
            )),
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at  TIMESTAMPTZ NULL,
            -- D-CI-FUNC-9 cj-231 + cj-232 fix: Epic 16's tenant_idps
            -- seed (0038 line 329 `WHERE t.slug = 'acme'`) and the
            -- application code at
            -- apps/api/modules/auth/sso/tenant_idp_lookup.py:84
            -- (SELECT id FROM public.tenants WHERE slug = <param>)
            -- both reference a `slug` column that was never added in
            -- any alembic revision (codebase grep 0 hit for ADD
            -- COLUMN slug). Add it here at the source so all
            -- downstream code resolves without a new migration.
            -- Nullable + backfilled by the dev seed (which sets
            -- slug='acme' for the seed tenant).
            -- NOTE (cj-232): the `<param>` placeholder above is
            -- written without a leading colon because SQLAlchemy
            -- treats colon-prefixed identifiers anywhere in the SQL
            -- string — including inside `--` comments — as bind
            -- parameters. The previous cj-231 comment used the
            -- colon-prefixed form and caused
            -- `InvalidRequestError: A value is required for bind
            -- parameter 'slug'` before 0001 even reached the
            -- CREATE TABLE body.
            slug        TEXT NULL
        )
        """
    )

    # ── users ──────────────────────────────────────────────
    # tenant_id is NULLABLE for cross-tenant users (e.g. consultant_proxy before
    # they join a tenant). RLS policy filters to current tenant when tenant_id IS NOT NULL.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NULL REFERENCES tenants(id) ON DELETE CASCADE,
            email           TEXT NOT NULL UNIQUE,
            role            TEXT NOT NULL CHECK (role IN (
                'owner', 'member', 'viewer', 'consultant_proxy'
            )),
            twofa_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # ── tenant_memberships ─────────────────────────────────
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_memberships (
            id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id     UUID NOT NULL REFERENCES users(id)  ON DELETE CASCADE,
            role        TEXT NOT NULL,
            joined_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, user_id)
        )
        """
    )

    # ── tenant_settings (AD-23: one row per tenant, JSONB namespaces) ──
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenant_settings (
            tenant_id           UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
            settings_version    INTEGER NOT NULL DEFAULT 1,
            onboarding          JSONB   NOT NULL DEFAULT '{}'::jsonb,
            baseline            JSONB   NOT NULL DEFAULT '{}'::jsonb,
            abc                 JSONB   NOT NULL DEFAULT '{}'::jsonb,
            ai                  JSONB   NOT NULL DEFAULT '{}'::jsonb,
            updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # ── audit_logs (AD-2: append-only foundation) ─────────
    # tenant_id is NULL for platform-level audit (e.g. service_role bypass on
    # cross-tenant ops). tenant_id is INTENTIONALLY NOT a foreign key to
    # tenants(id) — audit logs must survive tenant deletion (compliance
    # retention per AD-2) and FK cascades would either trigger the
    # append-only UPDATE-block trigger (ON DELETE SET NULL → UPDATE)
    # or be blocked by it (ON DELETE CASCADE → DELETE).
    # RLS policy `audit_log_insert` restricts writes to service_role;
    # UPDATE/DELETE are blocked by triggers below (full enforcement lands
    # in Epic 5 Story 5.2).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID NULL,
            actor_id        UUID NULL,
            action          TEXT NOT NULL,
            target_table    TEXT NOT NULL,
            target_id       UUID NULL,
            reason          TEXT NULL,
            payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    # Foundation-level append-only trigger (AD-2).
    # Full enforcement (Epic 5 Story 5.2) adds a service_role audit on this trigger.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION audit_logs_block_update_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'audit_logs is append-only (AD-2): UPDATE/DELETE forbidden';
        END;
        $$ LANGUAGE plpgsql
        """
    )
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs")
    op.execute(
        """
        CREATE TRIGGER audit_logs_no_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_block_update_delete()
        """
    )
    op.execute(
        """
        CREATE TRIGGER audit_logs_no_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION audit_logs_block_update_delete()
        """
    )

    # Helpful indexes for RLS hot-path
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_tenant_memberships_tenant_id "
        "ON tenant_memberships(tenant_id)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant_id " "ON audit_logs(tenant_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_audit_logs_occurred_at " "ON audit_logs(occurred_at DESC)"
    )


def downgrade() -> None:
    # FK-safe drop order: audit_logs → tenant_settings → tenant_memberships → users → tenants
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_update ON audit_logs")
    op.execute("DROP TRIGGER IF EXISTS audit_logs_no_delete ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS audit_logs_block_update_delete()")
    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS tenant_settings")
    op.execute("DROP TABLE IF EXISTS tenant_memberships")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP TABLE IF EXISTS tenants")
    # Note: pgcrypto extension is NOT dropped — other apps may use it.
