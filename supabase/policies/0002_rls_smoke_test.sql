-- ─────────────────────────────────────────────────────────────────
-- 0002_rls_smoke_test.sql — local-dev RLS smoke test (CI only).
--
-- Per CR 2026-07-25 RLS-3: verify every expected (schema, table, policy)
-- triple is present. The previous version checked only `policyname` and
-- would pass vacuously if a policy was missing on some tables.
-- ─────────────────────────────────────────────────────────────────

DO $$
DECLARE
    -- (expected_schema, expected_table, expected_policyname) tuples
    -- Use lowercase `pg_policies` column names (schemaname, tablename, policyname).
    expected_policies TEXT[][] := ARRAY[
        ARRAY['public', 'tenants',            'tenant_isolation_select'],
        ARRAY['public', 'tenants',            'tenant_isolation_insert'],
        ARRAY['public', 'tenants',            'tenant_isolation_update'],
        ARRAY['public', 'tenants',            'tenant_isolation_delete'],
        ARRAY['public', 'users',              'tenant_isolation_select'],
        ARRAY['public', 'users',              'tenant_isolation_insert'],
        ARRAY['public', 'users',              'tenant_isolation_update'],
        ARRAY['public', 'users',              'tenant_isolation_delete'],
        ARRAY['public', 'tenant_memberships', 'tenant_isolation_select'],
        ARRAY['public', 'tenant_memberships', 'tenant_isolation_insert'],
        ARRAY['public', 'tenant_memberships', 'tenant_isolation_update'],
        ARRAY['public', 'tenant_memberships', 'tenant_isolation_delete'],
        ARRAY['public', 'tenant_settings',    'tenant_isolation_select'],
        ARRAY['public', 'tenant_settings',    'tenant_isolation_insert'],
        ARRAY['public', 'tenant_settings',    'tenant_isolation_update'],
        ARRAY['public', 'tenant_settings',    'tenant_isolation_delete'],
        ARRAY['public', 'audit_logs',         'tenant_isolation_select'],
        ARRAY['public', 'audit_logs',         'audit_log_insert'],
        ARRAY['public', 'users',              'tenant_admin_all_users'],
        ARRAY['public', 'tenant_memberships', 'tenant_admin_all_memberships'],
        -- cj-290 RLS EXTENSION wire sprint (commit pending) — Epic 30+
        -- cost_records + bom_matrix 4-policy split per table = 8 NEW triples.
        -- Companion file: supabase/policies/0060_cost_records_and_bom_matrix_rls.sql
        ARRAY['public', 'cost_records',      'cost_records_select_same_tenant'],
        ARRAY['public', 'cost_records',      'cost_records_insert_blocked'],
        ARRAY['public', 'cost_records',      'cost_records_update_blocked'],
        ARRAY['public', 'cost_records',      'cost_records_delete_blocked'],
        ARRAY['public', 'bom_matrix',        'bom_matrix_select_same_tenant'],
        ARRAY['public', 'bom_matrix',        'bom_matrix_insert_blocked'],
        ARRAY['public', 'bom_matrix',        'bom_matrix_update_blocked'],
        ARRAY['public', 'bom_matrix',        'bom_matrix_delete_blocked']
    ];
    p TEXT[];
    found_count INTEGER;
    missing_label TEXT;
BEGIN
    FOREACH p SLICE 1 IN ARRAY expected_policies LOOP
        SELECT COUNT(*) INTO found_count
        FROM pg_policies
        WHERE schemaname = p[1]
          AND tablename  = p[2]
          AND policyname = p[3];
        IF found_count = 0 THEN
            missing_label := p[1] || '.' || p[2] || ' / ' || p[3];
            RAISE EXCEPTION 'RLS smoke test FAILED: policy % not found', missing_label;
        END IF;
    END LOOP;
    RAISE NOTICE 'RLS smoke test OK: % policies present', array_length(expected_policies, 1);
END
$$;
