-- ───────────────────────────────────────────────────────────────────────
-- supabase/policies/0006_products_rls.sql
-- Story 2.1 — RLS policies for the products table (PRD §8.M1).
--
-- Companion to `apps/api/alembic/versions/0006_products_item_master.py`.
-- Mirrors the 0005 pattern: ENABLE + FORCE RLS, then 3 policies (select,
-- insert, update). DELETE is intentionally absent — soft-delete only
-- (AC #5; AD-2 append-only-leaning).
--
-- Per CR 0.2 lesson (Story 0.2): the 4-policy split (select/insert/update)
-- matches the canonical Story 0.2 pattern. Defense in depth — even though
-- the backend API path enforces tenant_id via JWT (AD-3), RLS is the
-- last line of defense against a misconfigured connection.
--
-- Tenant isolation: products.tenant_id = (auth.jwt() -> 'app_metadata'
-- ->> 'tenant_id')::uuid. UUID v4 (AD-15 variance). The JWT is the source
-- of truth — request body tenant_id is ignored (AD-3).
--
-- Role split (mirrors 0005):
--   - select: authenticated + owner + member + viewer
--   - insert/update: owner only (AC #1, AC #4)
--   - delete: no policy (soft-delete only)
-- ───────────────────────────────────────────────────────────────────────

-- ── Enable + Force RLS ─────────────────────────────────────────────
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE products FORCE ROW LEVEL SECURITY;


-- ── 1) SELECT — every role reads rows in their tenant ──────────────
DROP POLICY IF EXISTS tenant_isolation_select ON products;
CREATE POLICY tenant_isolation_select
ON products
FOR SELECT
TO authenticated, owner, member, viewer
USING (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- ── 2) INSERT — owner only, with-with-check tenant match ───────────
DROP POLICY IF EXISTS tenant_isolation_insert ON products;
CREATE POLICY tenant_isolation_insert
ON products
FOR INSERT
TO owner
WITH CHECK (
    tenant_id = (
        (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
    )
);


-- ── 3) UPDATE — owner only, both USING + WITH_CHECK ────────────────
DROP POLICY IF EXISTS tenant_isolation_update ON products;
CREATE POLICY tenant_isolation_update
ON products
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


-- ── 4) DELETE — no policy (soft-delete only) ───────────────────────
-- Per AC #5: hard delete is forbidden because BOM/ledger may reference
-- the product. The `is_active=false` path is enforced at the API
-- boundary; this RLS policy does not surface a delete option.
