# supabase/ — local Supabase config + RLS

Story 0.2 wire-up. Per 2026-07-25 decision: **Supabase deferred to pilot**.
This directory hosts:

- `policies/0001_rls_policies.sql` — production-grade RLS (apply manually or via `supabase db push`)
- `policies/0002_rls_smoke_test.sql` — CI-only smoke test (verifies policies exist)

The Alembic migration `apps/api/alembic/versions/0001_tenants_users_memberships_settings.py`
is the source-of-truth for the schema. Apply migrations in this order:

1. `uv run alembic -c apps/api/alembic.ini upgrade head`
   (creates tables, triggers, indexes)

2. `psql $DATABASE_URL -f supabase/policies/0001_rls_policies.sql`
   (enables RLS + creates policies)

3. `psql $DATABASE_URL -f supabase/policies/0002_rls_smoke_test.sql`
   (CI only — verifies each policy exists)

## Local dev (no Supabase cloud project)

`supabase start` boots the full local stack (Postgres + GoTrue + PostgREST) on
`localhost:54322`. Until the pilot, point `DATABASE_URL` at this local Postgres.

## Pilot migration (deferred)

When the real Supabase project is provisioned in `ap-northeast-2` (Seoul):

1. `supabase link --project-ref <ref>`
2. `supabase db push`  (applies both `alembic upgrade head` outputs and the RLS policies)
3. Configure `auth.hook.custom_access_token` to inject `tenant_id` into `app_metadata`
   on JWT mint (Epic 1 Story 1.3 wires the OAuth hook).
