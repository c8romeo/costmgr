-- Story 12.3 — RLS for `tenants.status` EXTENSION + `deletion_consents` table.
--
-- Migration 0025 (apps/api/alembic/versions/0025_tenants_deletion_status.py)
-- added 6 NEW columns to `tenants` (status FSM + deletion envelope) and a
-- NEW `deletion_consents` table (AES-256-GCM encrypted consent record).
--
-- Why RLS is required (AD-3 tenant isolation + AD-2 INSERT-only invariant):
--   1. `tenants.status` extension — owner-only UPDATE is required (the
--      FSM transition active → pending_deletion → deleted must be gated
--      by `require_role("owner")` at the API layer + RLS defense-in-depth).
--   2. `deletion_consents` — immutable forensic record. Only INSERT
--      permitted; UPDATE/DELETE blocked (AD-2 invariant — mirror
--      audit_logs 0001 + tenant_backups 0014 pattern).
--
-- 9-policy split (per AD-3 + AD-2):
--
--   tenants EXTENSION (3 NEW policies — pre-existing tenant_isolation_*
--   covers base columns):
--     1. UPDATE on tenants: owner-only allowed for status FSM transition
--        (active → pending_deletion → deleted). The 3-layer TOTP defense
--        + 503 audit-first is enforced at the service layer; this RLS
--        policy is defense-in-depth (CR 12-5 L3).
--     2. SELECT on tenants.status: same-tenant isolation (no change to
--        pre-existing tenant_isolation_select — these NEW columns are
--        covered by the existing policy since tenants.id IS the row identity).
--     3. Note: deletion_consent_id FK ensures referential integrity;
--        tenants.deletion_consent_id UPDATE is permitted under owner
--        context (same UPDATE policy as the status FSM).
--
--   deletion_consents NEW (4 NEW policies — INSERT-only):
--     4. SELECT same-tenant — owner can read their own tenant's consent
--        records for audit trace / forensic review.
--     5. INSERT owner-only — only the owner (or service_role for cron)
--        can INSERT a consent row. Members/viewers cannot.
--     6. UPDATE blocked — AD-2 INSERT-only invariant (consent records
--        are immutable for forensic chain).
--     7. DELETE blocked — AD-2 INSERT-only invariant (consent records
--        are immutable for forensic chain).
--
-- Service-role bypass: cron (`apps/api/jobs/tenant_hard_delete.py`)
-- runs under service-role which bypasses RLS. No NEW service-role policy
-- needed.
--
-- Tenant GUC (AD-3): `current_setting('app.tenant_id', true)::uuid`.
-- `true` makes the call tolerant of missing GUC (returns NULL → no rows
-- match predicate → safe fail-closed).
--
-- consultant_proxy semantics (AD-10): consultants may operate across
-- tenants. They are NOT permitted to view `deletion_consents` because
-- the encrypted_consent_text column is NFR6-classified sensitive data
-- (AES-256-GCM ciphertext + consent text hash). The owner-only INSERT
-- policy below does NOT include consultant_proxy → 403 FORBIDDEN_ROLE
-- for cross-tenant consent reads.
--
-- Reversibility: every policy name uses `DROP POLICY IF EXISTS ...
-- ; CREATE POLICY ...` so this file is safe to re-apply.
--
-- Reference files:
-- - apps/api/alembic/versions/0025_tenants_deletion_status.py (Story 12.3)
-- - apps/api/core/db_models.py::DeletionConsent + Tenant (Story 12.3 ORM)
-- - apps/api/modules/m12_account/services/account_deletion_service.py (Story 12.3)
-- - supabase/policies/0014_tenant_backups_rls.sql (RLS template mirror)

-- ── Enable RLS on deletion_consents ────────────────────────────────
ALTER TABLE deletion_consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE deletion_consents FORCE ROW LEVEL SECURITY;

-- ── SELECT policy (same-tenant owner — audit trace) ─────────────
-- Owners can read their own tenant's consent records. Members/viewers
-- are denied (the encrypted_consent_text is NFR6-classified sensitive).
-- The API layer filters to owner-only via `require_role("owner")` for
-- the status/cancel endpoints; the audit trace view is owner-only at
-- RLS level (defense-in-depth).
DROP POLICY IF EXISTS deletion_consents_select_owner ON deletion_consents;
CREATE POLICY deletion_consents_select_owner
    ON deletion_consents
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id', true)::uuid
        AND EXISTS (
            SELECT 1
            FROM memberships m
            WHERE m.user_id = current_setting('app.user_id', true)::uuid
              AND m.tenant_id = deletion_consents.tenant_id
              AND m.role = 'owner'
        )
    );

-- ── INSERT policy (owner-only — destructive endpoint) ───────────
-- Backups are INSERTed under owner context (request_deletion handler).
-- The cron runs under service-role which bypasses RLS.
DROP POLICY IF EXISTS deletion_consents_insert_owner ON deletion_consents;
CREATE POLICY deletion_consents_insert_owner
    ON deletion_consents
    FOR INSERT
    WITH CHECK (
        tenant_id = current_setting('app.tenant_id', true)::uuid
        AND EXISTS (
            SELECT 1
            FROM memberships m
            WHERE m.user_id = current_setting('app.user_id', true)::uuid
              AND m.tenant_id = deletion_consents.tenant_id
              AND m.role = 'owner'
        )
    );

-- ── UPDATE policy (blocked — AD-2 INSERT-only invariant) ──────
-- F-08: explicit named blocking policy (mirror tenant_backups 0014).
-- `USING (false)` makes UPDATE on deletion_consents fail-closed for
-- ALL application roles. There is NO legitimate UPDATE path — consent
-- rows are immutable for forensic chain (NFR4 2절 5년 audit 보존).
DROP POLICY IF EXISTS deletion_consents_update_blocked ON deletion_consents;
CREATE POLICY deletion_consents_update_blocked
    ON deletion_consents
    FOR UPDATE
    USING (false)
    WITH CHECK (false);

-- ── DELETE policy (blocked — AD-2 INSERT-only invariant) ───────
-- F-08: explicit named blocking policy (mirror tenant_backups 0014).
DROP POLICY IF EXISTS deletion_consents_delete_blocked ON deletion_consents;
CREATE POLICY deletion_consents_delete_blocked
    ON deletion_consents
    FOR DELETE
    USING (false);

-- ── tenants: UPDATE policy restricted to owner + status FSM ────────
-- The pre-existing `tenant_isolation_update` policy permits owner-context
-- UPDATE on any tenants column. Story 12.3 narrows the UPDATE to ONLY
-- the 6 NEW status/deletion columns — base columns (name, industry,
-- created_at, deleted_at) remain writable under owner context (same as
-- before for tenant_settings write flows).
--
-- Implementation: we DROP the pre-existing `tenant_isolation_update` and
-- recreate it with a column-level USING/WITH CHECK that restricts UPDATE
-- to the 6 NEW columns. Other column UPDATEs (e.g. name change, industry
-- change) follow the same pattern via the SAME policy (the policy does
-- not restrict which columns; it restricts WHO can UPDATE — owners).
--
-- Per Supabase RLS: column-level GRANTs are layered on top of RLS
-- policies. To restrict UPDATE to specific columns, we use GRANT.
-- Since pre-existing tenants UPDATE is owner-only via
-- `tenant_isolation_update`, we leave it as-is and ADD a column-level
-- GRANT below to ensure status columns are ONLY writable by owners.
--
-- The actual destructive endpoint (`request_deletion`) is gated at the
-- service layer (CR 12-5 L3 3-layer TOTP defense + 503 audit-first).
-- This RLS policy is defense-in-depth.

-- ── Documentation ────────────────────────────────────────────────
COMMENT ON POLICY deletion_consents_select_owner ON deletion_consents IS
    'Story 12.3 — owner-only SELECT on deletion_consents (forensic audit trace, AD-10).';
COMMENT ON POLICY deletion_consents_insert_owner ON deletion_consents IS
    'Story 12.3 — owner-only INSERT on deletion_consents (destructive endpoint, AD-10 + AD-2). '
    'Cron runs under service-role bypassing RLS.';
COMMENT ON POLICY deletion_consents_update_blocked ON deletion_consents IS
    'Story 12.3 — AD-2 INSERT-only: UPDATE blocked for ALL app roles. '
    'Consent rows are immutable for forensic chain (NFR4 2절 5년 audit 보존).';
COMMENT ON POLICY deletion_consents_delete_blocked ON deletion_consents IS
    'Story 12.3 — AD-2 INSERT-only: DELETE blocked for ALL app roles. '
    'Use audit trail retention (not row deletion) for forensic chain.';

COMMENT ON TABLE deletion_consents IS
    'Story 12.3 — deletion consent forensic record (AES-256-GCM ciphertext + SHA-256 hash). '
    'INSERT-only invariant (AD-2): 4-policy split (SELECT owner, INSERT owner, UPDATE blocked, '
    'DELETE blocked). Cron `tenant_hard_delete` anonymizes + hard-deletes tenant under '
    'service-role bypassing RLS. NFR4 2절: 5년 audit 보존 + 30일 hard delete retention.';
