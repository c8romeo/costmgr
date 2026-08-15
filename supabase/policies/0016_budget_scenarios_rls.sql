-- Story 8.1 — RLS for `budget_scenarios` table.
--
-- Migration 0026 (apps/api/alembic/versions/0026_budget_scenarios.py) added the
-- NEW `budget_scenarios` table for AD-24 virtual budget period key + 1차
-- 시나리오 1개 잠금 (PRD §F8.1 + §15 NON-GOAL #2).
--
-- Why RLS is required (AD-3 tenant isolation):
--   1. Budget scenarios are tenant-scoped state — same-tenant SELECT/INSERT
--      must be enforced at the row level (not just at the API layer).
--   2. The 1차 MVP scenario 1개 잠금 is enforced at the service layer
--      (`validate_scenario_uniqueness`) + DB UNIQUE constraint
--      defense-in-depth (CR 12-5 L3). RLS is the third layer.
--
-- 4-policy split (per AD-3 + AD-10):
--   budget_scenarios NEW (4 NEW policies):
--     1. SELECT same-tenant — all 4 roles can read their tenant's
--        scenarios (owner+member+viewer+consultant_proxy per AD-10
--        read-mostly scope).
--     2. INSERT owner+member — only owner and member can create a
--        scenario (viewer + consultant_proxy denied).
--     3. UPDATE blocked — scenarios are read-mostly + 1차 잠금; no
--        legitimate UPDATE path in 8-1 (2차 multi-scenario deferred
--        to Story 8-2).
--     4. DELETE blocked — AD-2 INSERT-only soft invariant (scenario
--        creation is the only mutation; subsequent state is immutable
--        for V8 determinism trace).
--
-- Service-role bypass: cron / admin scripts can operate cross-tenant
-- under service-role (no NEW service-role policy needed).
--
-- Tenant GUC (AD-3): `current_setting('app.tenant_id', true)::uuid`.
-- `true` makes the call tolerant of missing GUC (returns NULL → no rows
-- match predicate → safe fail-closed).
--
-- Reversibility: every policy name uses `DROP POLICY IF EXISTS ...
-- ; CREATE POLICY ...` so this file is safe to re-apply.
--
-- Reference files:
-- - apps/api/alembic/versions/0026_budget_scenarios.py (Story 8.1)
-- - apps/api/core/db_models.py::BudgetScenario (Story 8.1 ORM)
-- - apps/api/modules/m8_budget/services/budget_scenario_service.py
-- - supabase/policies/0014_tenant_backups_rls.sql (RLS template mirror)

-- ── Enable RLS on budget_scenarios ────────────────────────────────
ALTER TABLE budget_scenarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_scenarios FORCE ROW LEVEL SECURITY;

-- ── SELECT policy (same-tenant 4-role read) ─────────────────────
-- Owner + member + viewer + consultant_proxy can read scenarios for
-- their own tenant. AD-10 4-role read-mostly scope (budget is a
-- planning artifact, not destructive state).
DROP POLICY IF EXISTS budget_scenarios_select_same_tenant ON budget_scenarios;
CREATE POLICY budget_scenarios_select_same_tenant
    ON budget_scenarios
    FOR SELECT
    USING (
        tenant_id = current_setting('app.tenant_id', true)::uuid
    );

-- ── INSERT policy (owner+member — write gate) ───────────────────
-- The API layer uses `require_any_role("owner", "member")` for POST.
-- RLS defense-in-depth: viewer + consultant_proxy denied at row level
-- even if the API gate is bypassed.
DROP POLICY IF EXISTS budget_scenarios_insert_owner_member ON budget_scenarios;
CREATE POLICY budget_scenarios_insert_owner_member
    ON budget_scenarios
    FOR INSERT
    WITH CHECK (
        tenant_id = current_setting('app.tenant_id', true)::uuid
        AND EXISTS (
            SELECT 1
            FROM memberships m
            WHERE m.user_id = current_setting('app.user_id', true)::uuid
              AND m.tenant_id = budget_scenarios.tenant_id
              AND m.role IN ('owner', 'member')
        )
    );

-- ── UPDATE policy (blocked — read-mostly invariant) ─────────────
-- F-08: explicit named blocking policy (mirror tenant_backups 0014).
-- `USING (false)` makes UPDATE on budget_scenarios fail-closed for
-- ALL application roles. There is NO legitimate UPDATE path in 8-1
-- (scenarios are immutable from the application layer for V8 trace).
DROP POLICY IF EXISTS budget_scenarios_update_blocked ON budget_scenarios;
CREATE POLICY budget_scenarios_update_blocked
    ON budget_scenarios
    FOR UPDATE
    USING (false)
    WITH CHECK (false);

-- ── DELETE policy (blocked — AD-2 INSERT-only soft invariant) ───
-- F-08: explicit named blocking policy (mirror tenant_backups 0014).
DROP POLICY IF EXISTS budget_scenarios_delete_blocked ON budget_scenarios;
CREATE POLICY budget_scenarios_delete_blocked
    ON budget_scenarios
    FOR DELETE
    USING (false);

-- ── Documentation ────────────────────────────────────────────────
COMMENT ON POLICY budget_scenarios_select_same_tenant ON budget_scenarios IS
    'Story 8.1 — same-tenant SELECT on budget_scenarios (4-role read: owner+member+viewer+consultant_proxy, AD-10).';
COMMENT ON POLICY budget_scenarios_insert_owner_member ON budget_scenarios IS
    'Story 8.1 — owner+member INSERT on budget_scenarios (write gate, AD-10). '
    'Service-role bypasses RLS for cron / admin scripts.';
COMMENT ON POLICY budget_scenarios_update_blocked ON budget_scenarios IS
    'Story 8.1 — UPDATE blocked for ALL app roles. Scenarios are read-mostly + 1차 잠금 '
    '(no legitimate UPDATE path in 8-1; 2차 multi-scenario deferred to Story 8-2).';
COMMENT ON POLICY budget_scenarios_delete_blocked ON budget_scenarios IS
    'Story 8.1 — DELETE blocked for ALL app roles (AD-2 INSERT-only soft invariant). '
    'Use audit trail retention (not row deletion) for V8 determinism trace.';

COMMENT ON TABLE budget_scenarios IS
    'Story 8.1 — AD-24 virtual budget period key + 1차 시나리오 1개 잠금 '
    '(PRD §F8.1 + §15 NON-GOAL #2). 4-policy split (SELECT same-tenant 4-role, '
    'INSERT owner+member, UPDATE blocked, DELETE blocked). Service-layer '
    '`validate_scenario_uniqueness` + DB UNIQUE(tenant_id, real_period_key) 제약 '
    'defense-in-depth (CR 12-5 L3). 2nd scenario creation honestly DEFER to Story 8-2.';