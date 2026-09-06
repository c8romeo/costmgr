-- Story 30.1 — RLS for `cost_records` + `bom_matrix` tables (Epic 30+ Reporting & Export MVP).
--
-- Migration 0060 (apps/api/alembic/versions/0060_cost_records_and_bom_matrix.py,
-- commit `b91906a` from cj-288 wire sprint) added the NEW `cost_records`
-- + `bom_matrix` tables backing the Story 30.1 CSV export endpoint
-- (`apps/api/modules/reports/csv_routes.py`).
--
-- Why RLS is required (AD-3 tenant isolation invariant):
--   1. Both tables are tenant-keyed (`tenant_id` FK to `tenants(id)` ON
--      DELETE CASCADE) but otherwise unfiltered — `csv_routes.py:303-336`
--      queries are read-only against these tables. A misconfigured
--      connection (missing WHERE clause, future bug, or compromised
--      app code) could leak cross-tenant cost data.
--   2. The CSV export endpoint enforces owner-only RBAC at the route
--      layer (`require_any_role("owner", "admin")`) + explicit
--      `WHERE tenant_id = :tenant_id` predicates in the SELECTs. RLS
--      is the THIRD defense-in-depth layer (CR 0-2 RLS lesson + CR 12-5
--      L4 explicit > implicit).
--   3. dev_seed runs under the `postgres` role which has BYPASSRLS,
--      so dev_seed is unaffected. Production application connections
--      run as `costmgr` (NOSUPERUSER NOBYPASSRLS) — these ARE subject
--      to the policies below.
--
-- 4-policy split per AD-3 + AD-2 (read-only at application surface):
--   cost_records NEW (4 NEW policies):
--     1. SELECT same-tenant — 4-role read (owner + member + viewer +
--        consultant_proxy per AD-10 read-mostly scope).
--     2. INSERT blocked — application surface is read-only (csv_routes
--        .py:303 SELECT-only). dev_seed inserts bypass via postgres
--        BYPASSRLS.
--     3. UPDATE blocked — AD-2 INSERT-only soft invariant (cost_records
--        are ledger-style snapshots; mutation not in Story 30.1 scope).
--     4. DELETE blocked — AD-2 INSERT-only soft invariant.
--
--   bom_matrix NEW (4 NEW policies):
--     1. SELECT same-tenant — 4-role read (mirrors cost_records).
--     2. INSERT blocked — same reasoning.
--     3. UPDATE blocked — same reasoning.
--     4. DELETE blocked — same reasoning.
--
-- Service-role bypass: cron / admin scripts can operate cross-tenant
-- under service-role (no NEW service-role policy needed).
--
-- Tenant GUC (AD-3): `current_setting('app.tenant_id', true)::uuid`.
-- `true` makes the call tolerant of missing GUC (returns NULL → no rows
-- match predicate → safe fail-closed). The `attach_tenant_listener` in
-- `apps/api/core/tenant_context.py:191-219` already publishes
-- `app.tenant_id` + `app.user_id` + `request.jwt.claims` per
-- transaction, so this policy resolves correctly for all 4-role traffic
-- (Phase 3-0 listener fix).
--
-- Reversibility: every policy name uses `DROP POLICY IF EXISTS …
-- CREATE POLICY …` so this file is safe to re-apply.
--
-- Reference files:
-- - apps/api/alembic/versions/0060_cost_records_and_bom_matrix.py (cj-288 wire sprint)
-- - apps/api/modules/reports/csv_routes.py (Story 30.1 CSV export endpoint)
-- - supabase/policies/0016_budget_scenarios_rls.sql (GUC pattern template mirror)
-- - supabase/policies/0014_tenant_backups_rls.sql (5-policy split with explicit blocked UPDATE/DELETE)
-- - supabase/policies/0007_bom_lines_rls.sql (verbatim naming convention: NNNN_<table>_rls.sql)

-- ═══════════════════════════════════════════════════════════════════
-- cost_records
-- ═══════════════════════════════════════════════════════════════════

-- ── Enable RLS on cost_records ────────────────────────────────────
ALTER TABLE cost_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_records FORCE ROW LEVEL SECURITY;

-- ── SELECT policy (same-tenant 4-role read) ──────────────────────
-- Owner + member + viewer + consultant_proxy can read cost_records
-- for their own tenant. AD-10 4-role read-mostly scope (CSV export
-- is a planning/audit artifact, not destructive state).
DROP POLICY IF EXISTS cost_records_select_same_tenant ON cost_records;
CREATE POLICY cost_records_select_same_tenant
    ON cost_records
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── INSERT policy (blocked — read-only application surface) ───────
-- Story 30.1 has NO legitimate INSERT path from the application layer.
-- csv_routes.py:298-336 only SELECTs. dev_seed INSERTs bypass RLS via
-- `postgres` role BYPASSRLS. Explicit blocked policy is clearer than
-- "no policy" (CR 12-5 defense-in-depth explicit > implicit).
DROP POLICY IF EXISTS cost_records_insert_blocked ON cost_records;
CREATE POLICY cost_records_insert_blocked
    ON cost_records
    FOR INSERT
    WITH CHECK (false);

-- ── UPDATE policy (blocked — AD-2 INSERT-only soft invariant) ─────
-- F-08: explicit named blocking policy (mirror 0014 + 0016).
-- `USING (false) WITH CHECK (false)` makes UPDATE on cost_records
-- fail-closed for ALL application roles.
DROP POLICY IF EXISTS cost_records_update_blocked ON cost_records;
CREATE POLICY cost_records_update_blocked
    ON cost_records
    FOR UPDATE
    USING (false)
    WITH CHECK (false);

-- ── DELETE policy (blocked — AD-2 INSERT-only soft invariant) ─────
-- F-08: explicit named blocking policy (mirror 0014 + 0016).
DROP POLICY IF EXISTS cost_records_delete_blocked ON cost_records;
CREATE POLICY cost_records_delete_blocked
    ON cost_records
    FOR DELETE
    USING (false);

-- ═══════════════════════════════════════════════════════════════════
-- bom_matrix
-- ═══════════════════════════════════════════════════════════════════

-- ── Enable RLS on bom_matrix ──────────────────────────────────────
ALTER TABLE bom_matrix ENABLE ROW LEVEL SECURITY;
ALTER TABLE bom_matrix FORCE ROW LEVEL SECURITY;

-- ── SELECT policy (same-tenant 4-role read) ──────────────────────
-- Owner + member + viewer + consultant_proxy can read bom_matrix
-- for their own tenant. AD-10 4-role read-mostly scope (BOM is a
-- planning artifact, not destructive state).
DROP POLICY IF EXISTS bom_matrix_select_same_tenant ON bom_matrix;
CREATE POLICY bom_matrix_select_same_tenant
    ON bom_matrix
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── INSERT policy (blocked — read-only application surface) ───────
-- Story 30.1 has NO legitimate INSERT path from the application layer.
-- csv_routes.py only SELECTs (lines 298-336). dev_seed INSERTs bypass
-- RLS via `postgres` role BYPASSRLS.
DROP POLICY IF EXISTS bom_matrix_insert_blocked ON bom_matrix;
CREATE POLICY bom_matrix_insert_blocked
    ON bom_matrix
    FOR INSERT
    WITH CHECK (false);

-- ── UPDATE policy (blocked — AD-2 INSERT-only soft invariant) ─────
-- F-08: explicit named blocking policy (mirror 0014 + 0016).
DROP POLICY IF EXISTS bom_matrix_update_blocked ON bom_matrix;
CREATE POLICY bom_matrix_update_blocked
    ON bom_matrix
    FOR UPDATE
    USING (false)
    WITH CHECK (false);

-- ── DELETE policy (blocked — AD-2 INSERT-only soft invariant) ─────
-- F-08: explicit named blocking policy (mirror 0014 + 0016).
DROP POLICY IF EXISTS bom_matrix_delete_blocked ON bom_matrix;
CREATE POLICY bom_matrix_delete_blocked
    ON bom_matrix
    FOR DELETE
    USING (false);

-- ── Documentation ────────────────────────────────────────────────
COMMENT ON POLICY cost_records_select_same_tenant ON cost_records IS
    'Story 30.1 — same-tenant SELECT on cost_records (4-role read: owner+member+viewer+consultant_proxy, AD-10). '
    'GUC: current_setting(''app.tenant_id'', true)::uuid (Phase 3-0 listener).';
COMMENT ON POLICY cost_records_insert_blocked ON cost_records IS
    'Story 30.1 — INSERT blocked for ALL app roles (read-only application surface). '
    'dev_seed inserts bypass RLS via postgres role BYPASSRLS.';
COMMENT ON POLICY cost_records_update_blocked ON cost_records IS
    'Story 30.1 — UPDATE blocked for ALL app roles (AD-2 INSERT-only soft invariant). '
    'csv_routes.py:298-336 is SELECT-only.';
COMMENT ON POLICY cost_records_delete_blocked ON cost_records IS
    'Story 30.1 — DELETE blocked for ALL app roles (AD-2 INSERT-only soft invariant). '
    'csv_routes.py:298-336 is SELECT-only.';

COMMENT ON POLICY bom_matrix_select_same_tenant ON bom_matrix IS
    'Story 30.1 — same-tenant SELECT on bom_matrix (4-role read: owner+member+viewer+consultant_proxy, AD-10). '
    'GUC: current_setting(''app.tenant_id'', true)::uuid (Phase 3-0 listener).';
COMMENT ON POLICY bom_matrix_insert_blocked ON bom_matrix IS
    'Story 30.1 — INSERT blocked for ALL app roles (read-only application surface). '
    'dev_seed inserts bypass RLS via postgres role BYPASSRLS.';
COMMENT ON POLICY bom_matrix_update_blocked ON bom_matrix IS
    'Story 30.1 — UPDATE blocked for ALL app roles (AD-2 INSERT-only soft invariant). '
    'csv_routes.py:298-336 is SELECT-only.';
COMMENT ON POLICY bom_matrix_delete_blocked ON bom_matrix IS
    'Story 30.1 — DELETE blocked for ALL app roles (AD-2 INSERT-only soft invariant). '
    'csv_routes.py:298-336 is SELECT-only.';

COMMENT ON TABLE cost_records IS
    'Story 30.1 CSV export source (cost-records type). 4-policy split '
    '(SELECT same-tenant 4-role, INSERT blocked, UPDATE blocked, DELETE blocked). '
    'AD-3 tenant isolation (RLS row-level). Application-layer csv_routes.py:298-336 '
    'is SELECT-only — explicit blocked policies match the read-only surface. '
    'dev_seed bypasses RLS via postgres role BYPASSRLS. '
    'NFR5 streaming P95 ≤ 5s backed by idx_cost_records_tenant_period.';
COMMENT ON TABLE bom_matrix IS
    'Story 30.1 CSV export source (bom type, level 1 only). 4-policy split '
    '(SELECT same-tenant 4-role, INSERT blocked, UPDATE blocked, DELETE blocked). '
    'AD-3 tenant isolation (RLS row-level). Application-layer csv_routes.py:298-336 '
    'is SELECT-only — explicit blocked policies match the read-only surface. '
    'dev_seed bypasses RLS via postgres role BYPASSRLS. '
    'NFR5 streaming P95 ≤ 5s backed by idx_bom_matrix_tenant_period.';
