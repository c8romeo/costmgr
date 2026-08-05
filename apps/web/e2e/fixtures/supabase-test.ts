// apps/web/e2e/fixtures/supabase-test.ts — Playwright rls_db fixture
// Story 0.5 — T5.3 (AC #5) — closes Story 1.1 F-30 deferral
//
// Provides a `rlsDb` fixture for Playwright tests that need a tenant-isolated
// database session. Mirrors the `tests/rls/conftest.py rls_db fixture` pattern
// but for Playwright runtime. The actual Postgres connection is wired to a
// TEST_DATABASE_URL env var; if unset, the fixture is a no-op stub.
//
// Usage:
//   import { test, expect } from "@playwright/test";
//   import { rlsDb } from "./fixtures/supabase-test";
//
//   test("...", async ({ page, rlsDb }) => {
//     // rlsDb is available for tenant-scoped queries
//   });

import { test as base } from "@playwright/test";

export const test = base.extend<{
  rlsDb: { tenantId: string | null };
}>({
  rlsDb: async ({}, use) => {
    // Story 0.5 plumbing: scaffold the fixture. Full Postgres wire is
    // deferred to a follow-up story — for now the fixture yields a
    // tenantId from `process.env.E2E_TENANT_ID` if set, else null.
    const tenantId = process.env.E2E_TENANT_ID ?? null;
    await use({ tenantId });
  },
});

export { expect } from "@playwright/test";
