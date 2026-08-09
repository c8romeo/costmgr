-- supabase/policies/0012_cache_invalidation_log_rls.sql
--
-- Story 11.3 — AD-25 cache invalidation multi-channel publisher RLS.
--
-- Story 11.1 wire (`0019_m11_reversal_ledger`) introduced
-- `cache_invalidation_log` with 1-channel constraint + no RLS policy.
-- Story 11.3 wire adds 4-policy split + FORCE ROW LEVEL SECURITY.
--
-- 4-policy split (mirror of 5-2/6-1/11-2 RLS pattern):
--   1. tenant_select_own — tenant can SELECT its own cache_invalidation_log rows
--   2. tenant_insert_own — tenant can INSERT rows with matching tenant_id
--   3. tenant_update_blocked — UPDATE forbidden for tenants (insert-only)
--   4. tenant_delete_blocked — DELETE forbidden for tenants (insert-only)
--
-- AD-2 + AD-3 binding: append-only ledger + tenant isolation.
-- `cache_invalidation_log` is INSERT-only — the publisher writes receipts,
-- the audit trail is immutable thereafter. Tenants cannot mutate past
-- receipts (no UPDATE / DELETE policy granted).
--
-- Defense-in-depth: FORCE ROW LEVEL SECURITY ensures no row is readable
-- without a tenant context, even for the table owner. Combined with the
-- GUC `current_setting('app.tenant_id', true)::uuid` pattern (set by
-- `attach_tenant_listener` on every session), this guarantees tenant
-- isolation at the DB layer.

ALTER TABLE cache_invalidation_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE cache_invalidation_log FORCE ROW LEVEL SECURITY;

-- 1. tenant_select_own: tenant can SELECT its own rows
DROP POLICY IF EXISTS cache_invalidation_log_tenant_select_own
    ON cache_invalidation_log;
CREATE POLICY cache_invalidation_log_tenant_select_own
    ON cache_invalidation_log
    FOR SELECT
    USING (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- 2. tenant_insert_own: tenant can INSERT rows with matching tenant_id
DROP POLICY IF EXISTS cache_invalidation_log_tenant_insert_own
    ON cache_invalidation_log;
CREATE POLICY cache_invalidation_log_tenant_insert_own
    ON cache_invalidation_log
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true)::uuid);

-- 3. tenant_update_blocked: no UPDATE policy granted (insert-only)
--    Tenants cannot mutate published receipts (AD-2 append-only invariant).
-- DROP POLICY IF EXISTS cache_invalidation_log_tenant_update_own
--     ON cache_invalidation_log;
-- (intentionally absent — UPDATE forbidden)

-- 4. tenant_delete_blocked: no DELETE policy granted (insert-only)
--    Tenants cannot delete published receipts.
-- DROP POLICY IF EXISTS cache_invalidation_log_tenant_delete_own
--     ON cache_invalidation_log;
-- (intentionally absent — DELETE forbidden)

-- Documentation comment (helpful for psql describe + future audit).
COMMENT ON TABLE cache_invalidation_log IS
    'Story 11.3 AD-25 multi-channel cache invalidation audit log. '
    '4 channels: ai_cache (11-1 보존) + cost_engine_cache + fiscal_period_cache + '
    'closing_snapshot_cache. INSERT-only (AD-2 append-only invariant). '
    '4-policy RLS split: tenant_select_own + tenant_insert_own + '
    'tenant_update_blocked + tenant_delete_blocked.';