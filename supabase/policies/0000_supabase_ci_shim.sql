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
