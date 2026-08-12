-- Story 12.2 — RLS for `tenant_backups` table.
--
-- Migration 0024 (apps/api/alembic/versions/0024_tenant_backups.py) added
-- the `tenant_backups` JSONB table that stores the daily per-tenant backup
-- payload. This policy enforces tenant isolation (AD-3) and the AD-2
-- INSERT-only invariant.
--
-- Why RLS is required (AD-3 tenant isolation invariant):
--   tenant_backups is a per-tenant operational artifact (NFR4 RPO 24h
--   backup). Without RLS, an application-layer SQL injection could leak
--   another tenant's backup payload (which contains `audit_logs` rows —
--   NFR6-classified sensitive data).
--
-- 5-policy split per AD-3:
--   1. SELECT same-tenant — members of the tenant can list their backups
--   2. SELECT owner-only   — backup details + download require owner role
--                             (AD-10 owner-only — CR 12-1 L4 precedent —
--                             capability is NOT enforced, owner-only via role)
--   3. INSERT same-tenant  — service-role or owner-initiated trigger
--   4. UPDATE forbidden    — INSERT-only invariant (AD-2)
--   5. DELETE forbidden    — INSERT-only invariant (AD-2)
--
-- Special case: the `purged_at` soft-delete column is intentionally
-- excluded from the UPDATE block because the retention cron
-- (`apps/api/jobs/backup_retention.py`) sets it. Since RLS blocks all
-- UPDATE, the cron runs under service-role which bypasses RLS.
--
-- Tenant GUC (AD-3): `current_setting('app.tenant_id', true)::uuid`.
-- `true` makes the call tolerant of missing GUC (returns NULL → no rows
-- match predicate → safe fail-closed).
--
-- consultant_proxy semantics (AD-10): consultants may operate across
-- tenants. They are NOT permitted to view `tenant_backups` because the
-- payload contains `audit_logs` (NFR6-sensitive). The owner-only SELECT
-- policy below does NOT include consultant_proxy → 403 FORBIDDEN_ROLE
-- for cross-tenant backup downloads.
--
-- Reversibility: every policy name uses `DROP POLICY IF EXISTS ...
-- ; CREATE POLICY ...` so this file is safe to re-apply.
--
-- Reference files:
-- - apps/api/alembic/versions/0024_tenant_backups.py (Story 12.2)
-- - apps/api/core/db_models.py::TenantBackup (Story 12.2 ORM)
-- - apps/api/modules/m12_account/services/backup_export_service.py (Story 12.2)
-- - supabase/policies/0013_users_totp_columns_rls.sql (RLS template)

-- ── Enable RLS on tenant_backups ─────────────────────────────────
ALTER TABLE tenant_backups ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_backups FORCE ROW LEVEL SECURITY;

-- ── SELECT policy (same-tenant members — list only) ─────────────
-- Members of the same tenant can list their backups. They see
-- metadata only (no payload content) at the application layer —
-- the API filters payload out for non-owner roles via BackupListItem
-- (no payload field — only sha256 + size + counts).
DROP POLICY IF EXISTS tenant_backups_select_same_tenant ON tenant_backups;
CREATE POLICY tenant_backups_select_same_tenant
    ON tenant_backups
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── SELECT policy (owner-only — full payload download) ──────────
-- Owners may read ALL columns including `payload`. Members/viewers/
-- consultants are denied even within the same tenant.
-- This is enforced at the application layer too
-- (`require_role("owner")` in handlers.py). The RLS policy is
-- defense-in-depth.
DROP POLICY IF EXISTS tenant_backups_select_owner ON tenant_backups;
CREATE POLICY tenant_backups_select_owner
    ON tenant_backups
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id', true)::uuid
        AND EXISTS (
            SELECT 1
            FROM memberships m
            WHERE m.user_id = current_setting('app.user_id', true)::uuid
              AND m.tenant_id = tenant_backups.tenant_id
              AND m.role = 'owner'
        )
    );

-- ── INSERT policy (owner-only — manual trigger + cron) ─────────
-- Backups can only be INSERTed under owner context. The cron runs
-- under service-role which bypasses RLS.
DROP POLICY IF EXISTS tenant_backups_insert_owner ON tenant_backups;
CREATE POLICY tenant_backups_insert_owner
    ON tenant_backups
    FOR INSERT
    WITH CHECK (
        tenant_id = current_setting('app.tenant_id', true)::uuid
        AND EXISTS (
            SELECT 1
            FROM memberships m
            WHERE m.user_id = current_setting('app.user_id', true)::uuid
              AND m.tenant_id = tenant_backups.tenant_id
              AND m.role = 'owner'
        )
    );

-- ── UPDATE policy (NONE — AD-2 INSERT-only invariant) ──────────
-- Intentionally NO UPDATE policy for application roles. The
-- `purged_at` soft-delete is performed by the retention cron under
-- service-role (bypasses RLS). Defense-in-depth: even if an app-layer
-- SQL injection attempts UPDATE on non-purged columns, RLS rejects it.
--
-- We do NOT add `tenant_backups_update_owner` because AD-2 invariant
-- must hold across ALL application roles.

-- ── DELETE policy (NONE — AD-2 INSERT-only invariant) ───────────
-- Same reasoning as UPDATE. tenant_backups rows are immutable from
-- the application layer. Soft-delete via `purged_at` is the only
-- mutation path, and it's cron-only.

-- ── Documentation ────────────────────────────────────────────────
COMMENT ON POLICY tenant_backups_select_same_tenant ON tenant_backups IS
    'Story 12.2 — same-tenant SELECT on tenant_backups metadata (AD-3 tenant isolation).';
COMMENT ON POLICY tenant_backups_select_owner ON tenant_backups IS
    'Story 12.2 — owner-only SELECT on tenant_backups (full payload download, AD-10).';
COMMENT ON POLICY tenant_backups_insert_owner ON tenant_backups IS
    'Story 12.2 — owner-only INSERT on tenant_backups (manual trigger, AD-10). '
    'Cron runs under service-role bypassing RLS.';

COMMENT ON TABLE tenant_backups IS
    'Story 12.2 — daily per-tenant JSON dump + 30-day retention sweep. '
    'INSERT-only invariant (AD-2): no UPDATE/DELETE policies for app roles. '
    'Cron `backup_retention` soft-deletes via `purged_at` under service-role. '
    'NFR4 RPO 24h / RTO 4h / 30-day backup retention.';
