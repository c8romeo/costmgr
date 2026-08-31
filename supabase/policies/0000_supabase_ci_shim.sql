-- ─────────────────────────────────────────────────────────────────
-- 0000_supabase_ci_shim.sql — CI-only shim for plain postgres:15.
--
-- Story 0.2 — RLS tests run in CI on a stock `postgres:15` image (per
-- HANDOFF Decision 2: Docker CI-only). Stock Postgres does NOT ship
-- with Supabase's `auth.jwt()` function or the `service_role` role.
-- This shim provides minimal stubs that let the RLS policy SQL
-- (0001_rls_policies.sql) apply cleanly.
--
-- SECURITY: this file is INTENDED for the CI rls-tests job ONLY.
-- Production uses Supabase's real `auth.jwt()` and `service_role`.
-- CI must not leak this shim into the production schema.
-- ─────────────────────────────────────────────────────────────────

-- Create the service_role role (idempotent).
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'service_role') THEN
        CREATE ROLE service_role NOLOGIN NOINHERIT;
    END IF;
END
$$;

-- D-CI-FUNC-9 cj-228 fix: the alembic chain reached
-- 0037_epic_15_sso_external_identities (and downstream 0038+) which
-- CREATE POLICY ... TO anon. The previous shim only created
-- service_role + costmgr_test, so the migration aborted with
-- 'role "anon" does not exist'. RLS policies in supabase/policies/
-- also reference authenticated / owner / member / viewer. Create all
-- five idempotently so the migrations and the downstream RLS step
-- both succeed.
--
-- D-CI-FUNC-9 cj-229 fix: 0038_epic_16_tenant_idps.py attaches
-- `EXECUTE FUNCTION public.set_updated_at()` to an
-- `updated_at_auto_update_trg` BEFORE UPDATE trigger on tenant_idps.
-- The function is NEVER defined in any alembic revision (codebase
-- grep 0 hit — it was assumed to exist). CI stock postgres has no
-- such helper, so the migration aborted with
-- `function public.set_updated_at() does not exist`. Define the
-- canonical BEFORE UPDATE trigger helper idempotently. Production
-- uses Supabase's real set_updated_at() if present; CI shim supplies
-- the same signature so migrations + downstream triggers resolve.
--
-- D-CI-FUNC-9 cj-231 fix: 0038_epic_16_tenant_idps.py seeds the
-- `acme` row by `WHERE t.slug = 'acme'`. The `tenants` table (0001)
-- has no `slug` column — it was never added in any alembic revision
-- (codebase grep 0 hit for ADD COLUMN slug). The application code at
-- apps/api/modules/auth/sso/tenant_idp_lookup.py:84 also queries
-- `WHERE slug = :slug`, so Epic 16 was wired against a column that
-- does not exist. The correct production fix is a new alembic
-- migration that adds the column + backfills `slug='acme'` for the
-- seed tenant — but the alembic chain itself has 7+ blockers in
-- 0038-0059 (VARCHAR(32), op.execute signature, etc.) and adding a
-- new migration to a broken chain is high risk. CI-only mitigation:
-- add the column to the shim so the migrations + downstream app code
-- resolve. Production deployment requires a follow-up alembic
-- migration (tracked separately, post chain-unblock).

-- Create the anon role (idempotent). Supabase uses this for unauthenticated
-- web requests; CI shim mirrors the contract.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'anon') THEN
        CREATE ROLE anon NOLOGIN NOINHERIT;
    END IF;
END
$$;

-- Create the authenticated role (idempotent). Supabase uses this for
-- logged-in users; CI shim mirrors the contract.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated NOLOGIN NOINHERIT;
    END IF;
END
$$;

-- Create the tenant-scoped role markers (owner / member / viewer).
-- These are PG roles (NOT just `tenant_memberships.role` enum values)
-- because supabase/policies/0006..0011 reference them in `TO owner` /
-- `TO member` / `TO viewer` clauses.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'owner') THEN
        CREATE ROLE owner NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'member') THEN
        CREATE ROLE member NOLOGIN NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'viewer') THEN
        CREATE ROLE viewer NOLOGIN NOINHERIT;
    END IF;
END
$$;

-- Create a costmgr_test role that does NOT bypass RLS, used by
-- tenant_isolation tests so the policies actually filter rows.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'costmgr_test') THEN
        CREATE ROLE costmgr_test LOGIN PASSWORD 'costmgr_test'
            NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE;
    END IF;
END
$$;

-- Minimal auth.jwt() stub: reads `request.jwt.claims` (a JSON string
-- set by tests via `SET LOCAL`). On Supabase, this function is
-- implemented in the auth schema; here we recreate the contract.
CREATE SCHEMA IF NOT EXISTS auth;

CREATE OR REPLACE FUNCTION auth.jwt()
RETURNS JSONB
LANGUAGE sql
STABLE
AS $$
    -- In CI, tests pre-set `request.jwt.claims` via `SET LOCAL`.
    -- In production, Supabase sets this at the API gateway.
    SELECT COALESCE(
        current_setting('request.jwt.claims', true)::jsonb,
        '{}'::jsonb
    );
$$;

-- D-CI-FUNC-9 cj-229 fix: canonical BEFORE UPDATE trigger helper for
-- `updated_at = NOW()` columns. Created with CREATE OR REPLACE so
-- reruns of the shim are no-ops, and so this declaration coexists
-- with any pre-existing set_updated_at() in the target schema (the
-- REPLACE wins, which is the desired behavior for CI).
CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

-- D-CI-FUNC-9 cj-231 fix attempt 2 (rejected): wrapping
-- `ALTER TABLE public.tenants ADD COLUMN IF NOT EXISTS slug` in an
-- `IF EXISTS` DO block made the shim idempotent on re-run but
-- defeated the purpose on a fresh DB: the shim runs BEFORE
-- `Apply Alembic migration`, so `tenants` doesn't exist yet and
-- the column addition silently no-ops. Reverted.
--
-- Correct fix is in 0001_tenants_users_memberships_settings.py —
-- add `slug TEXT NULL` to the CREATE TABLE so the column exists
-- once 0001 runs (no new migration, no chain break, no CI workflow
-- change).

-- Grant schema usage so the test role can read tenants/users.
GRANT USAGE ON SCHEMA public TO costmgr_test, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
    TO costmgr_test;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO costmgr_test;

-- Story 2.2 — bom_lines table mirror (mirrors 0006 products pattern).
-- The shim does not need to mirror the data; it just needs RLS to apply
-- cleanly. The actual bom_lines rows are seeded by the test fixture
-- (test_bom_lines_isolation.py::_seed_bom_rows).
