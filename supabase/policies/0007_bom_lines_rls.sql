-- ───────────────────────────────────────────────────────────────────────
-- supabase/policies/0007_bom_lines_rls.sql
-- Story 2.2 — RLS policies for the bom_lines table (PRD §8.M1(b)).
--
-- Companion to `apps/api/alembic/versions/0007_bom_matrix.py`.
-- Mirrors the 0006 pattern: ENABLE + FORCE RLS, then 3 policies (select,
-- insert, update). DELETE is intentionally absent — append-only-leaning
-- (AD-2). The bulk-replace PUT in `BOMService.set_bom` is the only
-- mutation path. The DELETE /api/v1/baseline/products/{id}/bom endpoint
-- uses a service-layer `DELETE` statement which runs under the owner
-- role + service_role bypass path.
--
-- Per CR 0.2 lesson (Story 0.2): the 4-policy split (select/insert/update)
-- matches the canonical Story 0.2 pattern. Defense in depth — even though
-- the backend API path enforces tenant_id via JWT (AD-3), RLS is the
-- last line of defense against a misconfigured connection.
--
-- Tenant isolation: bom_lines.tenant_id = (auth.jwt() -> 'app_metadata'
-- ->> 'tenant_id')::uuid. UUID v4 (AD-15 variance). The JWT is the source
-- of truth — request body tenant_id is ignored (AD-3).
--
-- Role split (mirrors 0006):
--   - select: authenticated + owner + member + viewer
--   - insert/update: owner only (AC #2, AC #3 — bulk-replace is owner-only)
--   - delete: no policy (append-only-leaning + bulk-replace PUT is the path)
-- ───────────────────────────────────────────────────────────────────────

-- ── Enable + Force RLS ─────────────────────────────────────────────
ALTER TABLE bom_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE bom_lines FORCE ROW LEVEL SECURITY;


-- ── 1) SELECT — every role reads rows in their tenant ──────────────
DROP POLICY IF EXISTS tenant_isolation_select ON bom_lines;
CREATE POLICY tenant_isolation_select
ON bom_lines
FOR SELECT
TO authenticated, owner, member, viewer
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- ── 2) INSERT — owner only, with-with-check tenant match ───────────
DROP POLICY IF EXISTS tenant_isolation_insert ON bom_lines;
CREATE POLICY tenant_isolation_insert
ON bom_lines
FOR INSERT
TO owner
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- ── 3) UPDATE — owner only, both USING + WITH CHECK ────────────────
DROP POLICY IF EXISTS tenant_isolation_update ON bom_lines;
CREATE POLICY tenant_isolation_update
ON bom_lines
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


-- ── 4) DELETE — no policy (append-only-leaning + bulk-replace only) ─
-- Per AD-2: hard delete is reserved for the bulk-replace PUT path which
-- runs under service_role bypass. The RLS-level DELETE policy is
-- intentionally absent so a misconfigured connection cannot leak
-- delete access.