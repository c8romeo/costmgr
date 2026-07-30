-- ─────────────────────────────────────────────────────────────────
-- 0001_rls_policies.sql
--
-- Story 0.2 — Supabase RLS policies (AD-3, AD-10, AD-23, AD-2).
--
-- Apply AFTER `alembic upgrade head` (or `supabase db push` of 0001).
-- Order of operations:
--   1. apps/api/alembic/versions/0001_*.py  (creates tables)
--   2. supabase/policies/0001_rls_policies.sql   (this file)
--   3. supabase/policies/0002_rls_smoke_test.sql (local dev only — CI)
--
-- Tenant identity comes from auth.jwt() -> 'app_metadata' ->> 'tenant_id'.
-- NEVER use user_metadata (user-editable — AD-3 violation).
-- ─────────────────────────────────────────────────────────────────

-- ── ENABLE + FORCE RLS on every business table ────────────────
ALTER TABLE tenants              ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenants              FORCE  ROW LEVEL SECURITY;
ALTER TABLE users                ENABLE ROW LEVEL SECURITY;
ALTER TABLE users                FORCE  ROW LEVEL SECURITY;
ALTER TABLE tenant_memberships   ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_memberships   FORCE  ROW LEVEL SECURITY;
ALTER TABLE tenant_settings      ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_settings      FORCE  ROW LEVEL SECURITY;
ALTER TABLE audit_logs           ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs           FORCE  ROW LEVEL SECURITY;

-- ── Idempotent policy drop (CR 2026-07-25 RLS-2) ─────────────
-- Re-running this file drops each policy first, so deployment is
-- safely repeatable (CI re-runs, local dev re-applies).
DROP POLICY IF EXISTS tenant_isolation_select         ON tenants;
DROP POLICY IF EXISTS tenant_isolation_insert         ON tenants;
DROP POLICY IF EXISTS tenant_isolation_update         ON tenants;
DROP POLICY IF EXISTS tenant_isolation_delete         ON tenants;
DROP POLICY IF EXISTS tenant_isolation_select         ON users;
DROP POLICY IF EXISTS tenant_isolation_insert         ON users;
DROP POLICY IF EXISTS tenant_isolation_update         ON users;
DROP POLICY IF EXISTS tenant_isolation_delete         ON users;
DROP POLICY IF EXISTS tenant_isolation_select         ON tenant_memberships;
DROP POLICY IF EXISTS tenant_isolation_insert         ON tenant_memberships;
DROP POLICY IF EXISTS tenant_isolation_update         ON tenant_memberships;
DROP POLICY IF EXISTS tenant_isolation_delete         ON tenant_memberships;
DROP POLICY IF EXISTS tenant_isolation_select         ON tenant_settings;
DROP POLICY IF EXISTS tenant_isolation_insert         ON tenant_settings;
DROP POLICY IF EXISTS tenant_isolation_update         ON tenant_settings;
DROP POLICY IF EXISTS tenant_isolation_delete         ON tenant_settings;
DROP POLICY IF EXISTS tenant_isolation_select         ON audit_logs;
DROP POLICY IF EXISTS audit_log_insert                ON audit_logs;
DROP POLICY IF EXISTS tenant_admin_all_users          ON users;
DROP POLICY IF EXISTS tenant_admin_all_memberships    ON tenant_memberships;

-- ── tenants: select/update only by owner of own tenant ─────────
-- tenants is special: row identity is the tenant itself, so the "tenant_id"
-- of the row IS the tenant. The JWT's app_metadata.tenant_id must match.
CREATE POLICY tenant_isolation_select ON tenants
    FOR SELECT
    USING (id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_insert ON tenants
    FOR INSERT
    WITH CHECK (id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_update ON tenants
    FOR UPDATE
    USING (id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid)
    WITH CHECK (id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_delete ON tenants
    FOR DELETE
    USING (id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

-- ── users: per-tenant isolation ─────────────────────────────────
CREATE POLICY tenant_isolation_select ON users
    FOR SELECT
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_insert ON users
    FOR INSERT
    WITH CHECK (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_update ON users
    FOR UPDATE
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid)
    WITH CHECK (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_delete ON users
    FOR DELETE
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

-- ── tenant_memberships: per-tenant isolation ────────────────────
CREATE POLICY tenant_isolation_select ON tenant_memberships
    FOR SELECT
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_insert ON tenant_memberships
    FOR INSERT
    WITH CHECK (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_update ON tenant_memberships
    FOR UPDATE
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid)
    WITH CHECK (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_delete ON tenant_memberships
    FOR DELETE
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

-- ── tenant_settings: per-tenant isolation ───────────────────────
CREATE POLICY tenant_isolation_select ON tenant_settings
    FOR SELECT
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_insert ON tenant_settings
    FOR INSERT
    WITH CHECK (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_update ON tenant_settings
    FOR UPDATE
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid)
    WITH CHECK (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

CREATE POLICY tenant_isolation_delete ON tenant_settings
    FOR DELETE
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

-- ── audit_logs: INSERT-only, service_role only (AD-2) ──────────
-- Reads by tenant owner (for transparency), writes only by service_role.
CREATE POLICY tenant_isolation_select ON audit_logs
    FOR SELECT
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

-- service_role bypasses RLS by default in Supabase, but we explicitly
-- add a `audit_log_insert` policy for clarity: only service_role can write.
CREATE POLICY audit_log_insert ON audit_logs
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- ── tenant_admin_all: owner can read+manage members of own tenant ─
-- AD-10: owner role can list all members of their own tenant.
CREATE POLICY tenant_admin_all_users ON users
    FOR ALL
    USING (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    )
    WITH CHECK (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    );

CREATE POLICY tenant_admin_all_memberships ON tenant_memberships
    FOR ALL
    USING (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    )
    WITH CHECK (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    );
