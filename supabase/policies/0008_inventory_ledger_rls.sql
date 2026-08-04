-- ───────────────────────────────────────────────────────────────────────
-- supabase/policies/0008_inventory_ledger_rls.sql
-- Story 5.2 — RLS policies for inventory_ledger (PRD §8.M2 + AD-2).
--
-- Companion to `apps/api/alembic/versions/0015_inventory_ledger.py`.
-- Mirrors the 0006 / 0007 / 0009 pattern. Per CR 0-2 lesson (Story 0-2):
-- the canonical 4-policy split (select / insert / update / delete) is
-- applied. Defense in depth — even though the backend API path enforces
-- tenant_id via JWT (AD-3), RLS is the last line of defense against a
-- misconfigured connection.
--
-- AD-2 append-only invariant: UPDATE / DELETE policies are DENIED at the
-- RLS layer (USING clause returns false) so the DB trigger never has
-- to fire for cross-tenant attempts. INSERT is the only allowed mutating
-- operation; corrections flow through AD-22 reversal sequence (Epic 11).
--
-- Tenant isolation: tenant_id = (auth.jwt() -> 'app_metadata' ->>
-- 'tenant_id')::uuid. The JWT is the source of truth — request body
-- tenant_id is ignored (AD-3).
--
-- Role split (mirrors 0009 monthly_input):
--   - select: authenticated + owner + member + viewer
--   - insert: owner only (manual backfill / recovery path)
--   - update: DENIED (AD-2 append-only)
--   - delete: DENIED (AD-2 append-only)
-- ───────────────────────────────────────────────────────────────────────

-- ── inventory_ledger ─────────────────────────────────────────────────
-- ENABLE ROW LEVEL SECURITY is wired in `0015_inventory_ledger.py` migration;
-- FORCE also (so service_role is also subject to tenant_id predicate).
ALTER TABLE inventory_ledger FORCE ROW LEVEL SECURITY;


-- 1) SELECT — every role reads rows in their tenant
DROP POLICY IF EXISTS tenant_isolation_select ON inventory_ledger;
CREATE POLICY tenant_isolation_select
ON inventory_ledger
FOR SELECT
TO authenticated, owner, member, viewer
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 2) INSERT — owner only (manual backfill / recovery entry; service_role
--    bypass via `FORCE ROW LEVEL SECURITY` + audit-first in service layer)
DROP POLICY IF EXISTS tenant_isolation_insert ON inventory_ledger;
CREATE POLICY tenant_isolation_insert
ON inventory_ledger
FOR INSERT
TO owner
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 3) UPDATE — DENIED (AD-2 append-only). USING clause returns false,
--    so cross-tenant UPDATE attempts are denied at RLS layer before
--    reaching the DB trigger. service_role bypass is for migrations +
--    Epic 11 reversal module only.
DROP POLICY IF EXISTS tenant_isolation_update ON inventory_ledger;
CREATE POLICY tenant_isolation_update
ON inventory_ledger
FOR UPDATE
TO authenticated, owner, member, viewer
USING (false)
WITH CHECK (false);


-- 4) DELETE — DENIED (AD-2 append-only). Same rationale as UPDATE.
DROP POLICY IF EXISTS tenant_isolation_delete ON inventory_ledger;
CREATE POLICY tenant_isolation_delete
ON inventory_ledger
FOR DELETE
TO authenticated, owner, member, viewer
USING (false);
