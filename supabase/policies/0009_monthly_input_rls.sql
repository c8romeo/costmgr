-- ───────────────────────────────────────────────────────────────────────
-- supabase/policies/0009_monthly_input_rls.sql
-- Story 3.1 — RLS policies for monthly_input_periods + monthly_input_rows
-- (PRD §8.M2).
--
-- Companion to `apps/api/alembic/versions/0009_monthly_input.py`.
-- Mirrors the 0006 / 0007 pattern: ENABLE + FORCE RLS, then 4 policies
-- per table (select / insert / update / delete — DELETE allowed because
-- monthly_input_rows is USER-INPUT data, not a ledger; PRD §8.M2
-- intentionally diverges from AD-2 append-only here).
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
-- Role split (mirrors 0006 / 0007):
--   - select: authenticated + owner + member + viewer
--   - insert / update / delete: owner only (AC #4 — user-input ledger
--     requires explicit ownership; m2_input is owner-only in MVP)
--   - delete: ALLOWED (PRD §8.M2 — not a ledger; AC #4 allows DELETE for
--     user correction; audit-first ensures a deletion row appears in
--     audit_logs)
-- ───────────────────────────────────────────────────────────────────────

-- ── monthly_input_periods ──────────────────────────────────────────
ALTER TABLE monthly_input_periods ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_input_periods FORCE ROW LEVEL SECURITY;


-- 1) SELECT — every role reads rows in their tenant
DROP POLICY IF EXISTS tenant_isolation_select ON monthly_input_periods;
CREATE POLICY tenant_isolation_select
ON monthly_input_periods
FOR SELECT
TO authenticated, owner, member, viewer
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 2) INSERT — owner only, with-with-check tenant match
DROP POLICY IF EXISTS tenant_isolation_insert ON monthly_input_periods;
CREATE POLICY tenant_isolation_insert
ON monthly_input_periods
FOR INSERT
TO owner
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 3) UPDATE — owner only, both USING + WITH CHECK
DROP POLICY IF EXISTS tenant_isolation_update ON monthly_input_periods;
CREATE POLICY tenant_isolation_update
ON monthly_input_periods
FOR UPDATE
TO owner
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
)
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 4) DELETE — owner only (append-only-leaning applies; Epic 4 first_calc
--    sets `locked_by_calculation=true` and the service layer refuses
--    DELETE in that state. RLS allows owner DELETE as the primary path).
DROP POLICY IF EXISTS tenant_isolation_delete ON monthly_input_periods;
CREATE POLICY tenant_isolation_delete
ON monthly_input_periods
FOR DELETE
TO owner
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- ── monthly_input_rows ────────────────────────────────────────────
ALTER TABLE monthly_input_rows ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_input_rows FORCE ROW LEVEL SECURITY;


-- 1) SELECT — every role reads rows in their tenant
DROP POLICY IF EXISTS tenant_isolation_select ON monthly_input_rows;
CREATE POLICY tenant_isolation_select
ON monthly_input_rows
FOR SELECT
TO authenticated, owner, member, viewer
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 2) INSERT — owner only
DROP POLICY IF EXISTS tenant_isolation_insert ON monthly_input_rows;
CREATE POLICY tenant_isolation_insert
ON monthly_input_rows
FOR INSERT
TO owner
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 3) UPDATE — owner only
DROP POLICY IF EXISTS tenant_isolation_update ON monthly_input_rows;
CREATE POLICY tenant_isolation_update
ON monthly_input_rows
FOR UPDATE
TO owner
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
)
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- 4) DELETE — owner only (user-input data correction path; PRD §8.M2)
DROP POLICY IF EXISTS tenant_isolation_delete ON monthly_input_rows;
CREATE POLICY tenant_isolation_delete
ON monthly_input_rows
FOR DELETE
TO owner
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);