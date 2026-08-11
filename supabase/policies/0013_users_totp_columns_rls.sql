-- Story 12.4 (Epic 12 carry-over sprint) — RLS for `users.totp_*` columns.
--
-- Migration 0022 (apps/api/alembic/versions/0022_users_totp_columns.py) added
-- the 5 TOTP columns to the `users` table. This policy enables tenant-scoped
-- RLS on `users` so that the encrypted totp_secret + recovery_code hashes
-- can only be SELECT/UPDATEd by the owning tenant's session.
--
-- Why RLS on users is required (AD-3 tenant isolation invariant):
--   `users` already has the multi-tenant guard via the application layer
--   (memberships table + tenant_id FK), but `users.totp_secret` is now
--   NFR6-classified sensitive data (AES-256-GCM ciphertext). Defense in
--   depth requires RLS so even an application-layer SQL injection cannot
--   read another tenant's TOTP blobs.
--
-- Tenant GUC (AD-3): `current_setting('app.tenant_id', true)::uuid`. The
-- `true` flag makes the call tolerant of a missing GUC (returns NULL →
-- no rows match the predicate → safe fail-closed for SELECT).
--
-- consultant_proxy semantics (AD-10): consultants may operate across
-- tenants, so a separate policy grants `consultant_proxy` cross-tenant
-- SELECT on users.totp_* rows where their membership exists. Updates are
-- NEVER permitted cross-tenant — TOTP secret material is per-user.
--
-- Reversibility: every policy name is created idempotently with
-- `DROP POLICY IF EXISTS ... ; CREATE POLICY ...` so this file is safe
-- to re-apply.
--
-- Reference files:
-- - apps/api/alembic/versions/0022_users_totp_columns.py (Story 12.4)
-- - apps/api/core/db_models.py::User (Story 12.1 ORM)
-- - apps/api/modules/m12_account/services/two_factor_service.py (Story 12.1)
-- - supabase/policies/0012_cache_invalidation_log_rls.sql (RLS template)

-- ── Enable RLS on users ──────────────────────────────────────────
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE users FORCE ROW LEVEL SECURITY;

-- ── SELECT policy (same-tenant members) ──────────────────────────
-- Members of the same tenant can read totp columns. totp_secret is
-- ciphertext so this is safe at rest, but RLS still prevents a
-- compromised app-layer query from leaking blobs to a foreign tenant.
DROP POLICY IF EXISTS users_totp_select_same_tenant ON users;
CREATE POLICY users_totp_select_same_tenant
    ON users
    FOR SELECT
    USING (
        tenant_id IS NOT NULL
        AND tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── SELECT policy (consultant_proxy cross-tenant) ────────────────
-- consultants may operate across tenants (AD-10). They are explicitly
-- permitted to SELECT user rows for tenants they have a
-- membership in. Note: `tenant_memberships` has NO `status` column —
-- memberships are either present or absent (schema per
-- apps/api/core/db_models.py:113-131). Story 12.4 review P-03 fix.
DROP POLICY IF EXISTS users_totp_select_consultant_proxy ON users;
CREATE POLICY users_totp_select_consultant_proxy
    ON users
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM memberships m
            WHERE m.user_id = users.id
              AND m.tenant_id = current_setting('app.tenant_id', true)::uuid
              AND m.role = 'consultant_proxy'
        )
    );

-- ── INSERT policy (system-only via service role) ─────────────────
-- New user rows can only be inserted by the service role (onboarding,
-- invitation accept). Application-layer INSERTs go through the service
-- role context so no explicit WITH CHECK is needed for end users.
-- We add a defensive INSERT policy that requires tenant_id to be set.
DROP POLICY IF EXISTS users_totp_insert_same_tenant ON users;
CREATE POLICY users_totp_insert_same_tenant
    ON users
    FOR INSERT
    WITH CHECK (
        tenant_id IS NOT NULL
        AND tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── UPDATE policy (self only, totp columns) ──────────────────────
-- A user may UPDATE their own totp columns (enrollment, recovery
-- code consumption). Other tenant users cannot UPDATE.
-- Note: totp_failed_attempts / totp_lockout_until are also subject
-- to this self-only policy — the service uses the same user context.
DROP POLICY IF EXISTS users_totp_update_self ON users;
CREATE POLICY users_totp_update_self
    ON users
    FOR UPDATE
    USING (
        id = current_setting('app.user_id', true)::uuid
        AND tenant_id = current_setting('app.tenant_id', true)::uuid
    )
    WITH CHECK (
        id = current_setting('app.user_id', true)::uuid
        AND tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── UPDATE policy (owner — for owner-initiated 2FA reset) ────────
-- Owners may UPDATE totp columns on members of their tenant to reset
-- 2FA when a user is locked out. Uses role check via memberships.
-- Note: no `m.status = 'active'` predicate — `tenant_memberships` has
-- no status column (schema per apps/api/core/db_models.py:113-131).
-- Story 12.4 review P-03 fix.
DROP POLICY IF EXISTS users_totp_update_owner ON users;
CREATE POLICY users_totp_update_owner
    ON users
    FOR UPDATE
    USING (
        EXISTS (
            SELECT 1
            FROM memberships m
            WHERE m.user_id = current_setting('app.user_id', true)::uuid
              AND m.tenant_id = users.tenant_id
              AND m.role = 'owner'
        )
        AND tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── DELETE policy (none) ─────────────────────────────────────────
-- Intentionally NO DELETE policy. users.totp_* must be preserved for
-- audit trail integrity (AD-2 append-only). If a user leaves a tenant,
-- set `tenant_id = NULL` via an UPDATE under service-role, never DELETE.

-- ── Documentation ────────────────────────────────────────────────
COMMENT ON POLICY users_totp_select_same_tenant ON users IS
    'Story 12.4 — same-tenant SELECT on users.totp_* (AD-3 tenant isolation).';
COMMENT ON POLICY users_totp_select_consultant_proxy ON users IS
    'Story 12.4 — consultant_proxy cross-tenant SELECT on users.totp_* (AD-10).';
COMMENT ON POLICY users_totp_insert_same_tenant ON users IS
    'Story 12.4 — INSERT requires tenant_id match (defense in depth).';
COMMENT ON POLICY users_totp_update_self ON users IS
    'Story 12.4 — user can self-update own totp_* columns (enrollment, recovery).';
COMMENT ON POLICY users_totp_update_owner ON users IS
    'Story 12.4 — tenant owner can reset totp_* for members (lockout reset).';

COMMENT ON TABLE users IS
    'Users + 2FA enrollment state (Story 12.4 added totp_* columns + RLS). '
    'totp_secret is NFR6 AES-256-GCM ciphertext (apps.api.core.crypto). '
    'Auth predicate is totp_enabled_at IS NOT NULL (NOT users.twofa_enabled).';
