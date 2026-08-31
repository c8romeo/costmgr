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

-- Grant schema usage so the test role can read tenants/users.
GRANT USAGE ON SCHEMA public TO costmgr_test, service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public
    TO costmgr_test;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO costmgr_test;

-- Story 2.2 — bom_lines table mirror (mirrors 0006 products pattern).
-- The shim does not need to mirror the data; it just needs RLS to apply
-- cleanly. The actual bom_lines rows are seeded by the test fixture
-- (test_bom_lines_isolation.py::_seed_bom_rows).
