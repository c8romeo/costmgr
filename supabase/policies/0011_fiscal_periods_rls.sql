-- ───────────────────────────────────────────────────────────────────────
-- supabase/policies/0011_fiscal_periods_rls.sql
-- Story 11.2 — RLS policies for fiscal_periods (PRD §F11.1 + AD-6).
--
-- Companion to `apps/api/alembic/versions/0020_fiscal_periods_close_sequence.py`.
-- Mirrors the 0005 / 0008 / 0009 pattern: ENABLE + FORCE RLS, then 4
-- policies per table (select / insert / update / delete — DELETE blocked
-- because fiscal_periods is AD-6 close-lock state; mutations route through
-- close_sequence_service which emits audit rows via audit_logs).
--
-- Per CR 0.2 lesson (Story 0.2): the 4-policy split matches the canonical
-- Story 0.2 pattern. Defense in depth — even though the backend API path
-- enforces tenant_id via JWT (AD-3), RLS is the last line of defense
-- against a misconfigured connection.
--
-- Tenant isolation: tenant_id = (auth.jwt() -> 'app_metadata' ->>
-- 'tenant_id')::uuid. UUID v4 (AD-15 variance). The JWT is the source of
-- truth — request body tenant_id is ignored (AD-3).
--
-- Role split (mirrors 0008 / 0009):
--   - select: authenticated + owner + member + viewer
--   - insert: owner only (initial INSERT during initiate_close_sequence)
--   - update: owner only (status machine transitions + step timestamps)
--     UPDATE on status='closed' is blocked at the WITH CHECK level —
--     status='closed' is final until Epic 11 close reopen flow wires
--     (W2 deferral — see Epic 5 close-out retro §6).
--   - delete: BLOCKED (AD-6 close lock — fiscal_periods is append-only-
--     leaning; reopen requires operator action + reason + audit row +
--     AD-25 invalidation, not DELETE).
-- ───────────────────────────────────────────────────────────────────────

-- ── fiscal_periods ──────────────────────────────────────────────
ALTER TABLE fiscal_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE fiscal_periods FORCE ROW LEVEL SECURITY;


-- 1) SELECT — every role reads rows in their tenant
DROP POLICY IF EXISTS tenant_select_own ON fiscal_periods;
CREATE POLICY tenant_select_own
ON fiscal_periods
FOR SELECT
TO authenticated, owner, member, viewer
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 2) INSERT — owner only, with-with-check tenant match
DROP POLICY IF EXISTS tenant_insert_own ON fiscal_periods;
CREATE POLICY tenant_insert_own
ON fiscal_periods
FOR INSERT
TO owner
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 3) UPDATE — owner only, blocks writes when status='closed'.
--    status='closed' is final until Epic 11 reopen flow wires (W2 deferral).
--    Defense-in-depth on top of service-layer guard.
DROP POLICY IF EXISTS tenant_update_own_blocked_status ON fiscal_periods;
CREATE POLICY tenant_update_own_blocked_status
ON fiscal_periods
FOR UPDATE
TO owner
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
    AND status != 'closed'
)
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 4) DELETE — BLOCKED (AD-6 close lock — fiscal_periods is append-only)
DROP POLICY IF EXISTS tenant_delete_blocked ON fiscal_periods;
CREATE POLICY tenant_delete_blocked
ON fiscal_periods
FOR DELETE
TO authenticated, owner, member, viewer
USING (false);