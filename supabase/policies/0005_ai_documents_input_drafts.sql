-- ─────────────────────────────────────────────────────────────────
-- 0005_ai_documents_input_drafts.sql
--
-- Story 1.3 — RLS policies for AI document extraction tables.
--
-- Apply AFTER `alembic upgrade head` (i.e. after 0005 creates
-- uploaded_documents + input_drafts). Mirrors the Story 0.2 pattern in
-- 0001_rls_policies.sql.
--
-- Tenant identity comes from auth.jwt() -> 'app_metadata' ->> 'tenant_id'
-- (NEVER user_metadata — user-editable, AD-3 violation).
--
-- Role policy (Task 3.6):
-- - SELECT  : all 4 roles (owner, member, viewer, consultant_proxy) — read-only
-- - INSERT  : owner only (matches Story 1.2 anti-pattern line 335 + AD-10)
-- - UPDATE  : owner only (review/confirmation is owner-only)
-- - DELETE  : service_role only (retention cron in apps/api/jobs/document_retention.py)
-- ─────────────────────────────────────────────────────────────────

-- ── ENABLE + FORCE RLS ───────────────────────────────────────
ALTER TABLE uploaded_documents  ENABLE ROW LEVEL SECURITY;
ALTER TABLE uploaded_documents  FORCE  ROW LEVEL SECURITY;
ALTER TABLE input_drafts         ENABLE ROW LEVEL SECURITY;
ALTER TABLE input_drafts         FORCE  ROW LEVEL SECURITY;

-- ── Idempotent policy drop ───────────────────────────────────
DROP POLICY IF EXISTS tenant_isolation_select         ON uploaded_documents;
DROP POLICY IF EXISTS tenant_isolation_insert         ON uploaded_documents;
DROP POLICY IF EXISTS tenant_isolation_update         ON uploaded_documents;
DROP POLICY IF EXISTS tenant_isolation_delete         ON uploaded_documents;

DROP POLICY IF EXISTS tenant_isolation_select         ON input_drafts;
DROP POLICY IF EXISTS tenant_isolation_insert         ON input_drafts;
DROP POLICY IF EXISTS tenant_isolation_update         ON input_drafts;
DROP POLICY IF EXISTS tenant_isolation_delete         ON input_drafts;

-- ── uploaded_documents ───────────────────────────────────────
-- SELECT: any member of the tenant can see their own documents.
CREATE POLICY tenant_isolation_select ON uploaded_documents
    FOR SELECT
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

-- INSERT: owner only (POST /api/v1/onboarding/ai-documents).
CREATE POLICY tenant_isolation_insert ON uploaded_documents
    FOR INSERT
    WITH CHECK (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    );

-- UPDATE: owner only (job_status transitions + retention soft-delete are
-- owner-initiated; the daily retention cron runs as service_role which
-- bypasses RLS by default in Supabase).
CREATE POLICY tenant_isolation_update ON uploaded_documents
    FOR UPDATE
    USING (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    )
    WITH CHECK (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    );

-- DELETE: no tenant role can DELETE (the 90-day retention cron is the only
-- path; it runs as service_role).
-- (No DELETE policy → RLS denies all DELETE attempts by tenant roles.)

-- ── input_drafts ──────────────────────────────────────────────
-- SELECT: any member of the tenant.
CREATE POLICY tenant_isolation_select ON input_drafts
    FOR SELECT
    USING (tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid);

-- INSERT: owner only (the M10 review endpoint writes `state='reviewed'`
-- rows + the extraction service writes initial `state='draft'` rows —
-- both via service_role, but the API surface uses owner-role JWT).
CREATE POLICY tenant_isolation_insert ON input_drafts
    FOR INSERT
    WITH CHECK (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    );

-- UPDATE: owner only (review/confirmation).
CREATE POLICY tenant_isolation_update ON input_drafts
    FOR UPDATE
    USING (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    )
    WITH CHECK (
        tenant_id = (auth.jwt() -> 'app_metadata' ->> 'tenant_id')::uuid
        AND (auth.jwt() -> 'app_metadata' ->> 'role') = 'owner'
    );

-- DELETE: no tenant role. Retention cron + service_role only.