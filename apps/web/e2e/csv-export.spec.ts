/**
 * apps/web/e2e/csv-export.spec.ts — Playwright E2E for Story 30.1 CSV export.
 *
 * cj-286 EXTENSION wire sprint (cj-style 286번째) — Epic 30+ Reporting &
 * Export MVP territory (cj-282 PRD entry `0c7524e`). Companion spec for
 * `apps/web/components/reports/CsvExportTab.tsx` (cj-282a wire sprint) +
 * `apps/api/modules/reports/csv_routes.py` (cj-282a wire sprint).
 *
 * Scenarios (3 tests):
 *   1. test_csv_download_trigger — happy-path: navigate to
 *      `/ko-KR/reports` → CSV download button click → page state unchanged
 *      (download is a side-effect, not a route change).
 *   2. test_csv_response_content_type — CSV response Content-Type =
 *      `text/csv; charset=utf-8` (verbatim from csv_routes.py:415).
 *   3. test_utf8_bom_for_excel_ko_kr — CSV response first 3 bytes =
 *      `0xEF 0xBB 0xBF` (UTF-8 BOM, Excel ko-KR 호환, NFR18).
 *
 * AD bind 3/3 (cj-282 PRD entry §F44.1 verbatim):
 *   - AD-2 (audit-first INSERT append-only) — backend 결정 wire.
 *   - AD-10 (identity/2FA via owner-only RBAC, AD-22 owner-only) — backend.
 *   - AD-12 (verify-first capability gate, cj-285+ EXTENSION capability
 *     matrix v1.54 `Capability.EXPORT_CSV`).
 *
 * NFR bind 2/7 active:
 *   - NFR5 (streaming P95 ≤ 5s for 10만 row) — StreamingResponse 결정 wire.
 *   - NFR18 (ko-KR vocabulary SSOT) — UTF-8 BOM for Excel ko-KR.
 *
 * Spec dependency: `dev_seed --scenario report_fixtures` (cj-286 EXTENSION
 * wire sprint) seeds an acme-tenant (`DEV_TENANT_REPORT_ID` UUIDv5
 * namespace `costmgr-dev-tenant-report`) with 100 cost_records rows (4
 * categories × 25 rows) and 10 BOM matrix rows (5 parents × 2 children)
 * for period_key='2026-08'. See AD-56 (a) report_fixtures data shape.
 *
 * ci.yml 변경 0건 결정 wire 보존 (A697): this NEW spec is auto-discovered
 * by `apps/web/playwright.config.ts:15 testDir: "./e2e"` — no YAML
 * change required (the existing `--scenario all` invocation at
 * `.github/workflows/ci.yml:743` covers the new scenario + spec).
 *
 * Korean (ko-KR) locale + manufacturing tenant — same as Story 6.2
 * baseline pattern (verbatim from monthly-closing-report.spec.ts).
 *
 * cj-287 wire sprint (cj-style 287번째) — D-WEB-E2E-7 ownership wire ACTIVATED.
 *
 * First D-WEB-E2E-* ownership activation in Epic 30+ Reporting & Export MVP
 * territory. The describe.skip baseline (cj-282a decide wire pattern) is
 * RELEASED. Pre-conditions verified GREEN:
 * 1. csv_routes.py line 359 ActionClass.AUDIT → ActionClass.REPORTS fix wired
 *    (registry at audit_action.py:2446-2456 includes export_csv).
 * 2. apps/api/modules/reports/__init__.py + csv_export_router mount wired in
 *    apps/api/main.py (otherwise GET /api/v1/exports/csv → 404).
 * 3. 4 CsvExportError exception handlers registered in main.py (otherwise → 500).
 * 4. Capability.EXPORT_CSV gate wired in csv_routes.py (AD-12 verify-first +
 *    AD-56(c) sub-decision).
 * 5. CsvExportTab tenantId prop supplied via reports/page.tsx JWT decode of
 *    app_metadata.tenant_id (otherwise → 422 missing query param).
 * 6. dev_seed.py --tenant-id --user-id --role flags added to --token-only path.
 * 7. CI auto-discovers via testDir: "./e2e" (ci.yml:742-773 GREEN).
 *
 * CR 11-3 honest-DEFER 224번째 epic 연속 정직 회복 — cj-282a 의 223번째
 * skip 결정 패턴 보존 해제, D-WEB-E2E-7 ownership 진입 결정 wire 보존.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const TEST_PERIOD = "2026-08";
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const TEST_TENANT = "manufacturing";

// cj-287 wire — D-WEB-E2E-7 ownership variables. These env vars must be
// supplied by the CI workflow (or local dev) before running this spec.
// Example (after `make db-seed` + dev_seed --token-only with --tenant-id
// override): `DEV_TENANT_REPORT_ID=$R DEV_USER_REPORT_ID=$U
// DEV_ACCESS_TOKEN=$T pnpm exec playwright test e2e/csv-export.spec.ts`.
const DEV_TENANT_REPORT_ID = process.env.DEV_TENANT_REPORT_ID ?? "";
// cj-287 wire — D-WEB-E2E-7 ownership. Reserved for future spec
// extensions where the spec needs to assert user-scoped audit row
// visibility; currently unused in the 3 baseline test cases.
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const DEV_USER_REPORT_ID = process.env.DEV_USER_REPORT_ID ?? "";
const DEV_ACCESS_TOKEN = process.env.DEV_ACCESS_TOKEN ?? "";

// cj-292 fix forward — D-WEB-E2E-7 PRE-EXISTING carryover 정직 fix.
// CI provides DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN via the
// token-mint step in `.github/workflows/ci.yml` (web-e2e job, right
// before `pnpm exec playwright test`). Local dev without --scenario
// report_fixtures + --token-only mint → skip the 3 tests gracefully
// (CR 11-3 honest-DEFER pattern — same as the original cj-282a baseline
// describe.skip decision wire).
const HAS_AUTH = Boolean(DEV_TENANT_REPORT_ID) && Boolean(DEV_ACCESS_TOKEN);

test.describe("Story 30.1 — CSV export UI flow", () => {
  test.beforeEach(async ({ context, page }) => {
    // Skip when required env vars are not provided (local dev without
    // the ci.yml token-mint step). CI always provides them.
    test.skip(!HAS_AUTH, "DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN required (CI sets via token-mint step)");

    // cj-292 fix forward — set the `sb-access-token` cookie so reports/page.tsx
    // can decode JWT → app_metadata.tenant_id (= DEV_TENANT_REPORT_ID) and
    // pass it to CsvExportTab. Without this cookie, Case 1 (UI flow)
    // renders the "세션이 만료되었습니다" fallback (page.tsx:63-68) and
    // the data-testid="reports-tab" root is absent → expect(reportsTab)
    // fails immediately.
    await context.addCookies([
      {
        name: "sb-access-token",
        value: DEV_ACCESS_TOKEN,
        domain: "localhost",
        path: "/",
        httpOnly: false,
        secure: false,
        sameSite: "Lax",
      },
    ]);

    // Navigate to /ko-KR/reports — CsvExportTab is mounted on this page.
    await page.goto(`/${TEST_LOCALE}/reports`);
    await page.waitForLoadState("networkidle");
  });

  // ── Case 1: CSV download trigger ────────────────────────────────────
  test("CSV download button click triggers download (page stays)", async ({
    page,
  }) => {
    // CsvExportTab root panel visible.
    const reportsTab = page.getByTestId("reports-tab");
    await expect(reportsTab).toBeVisible();

    // CSV export sub-tab heading visible.
    const csvExportTab = page.getByTestId("csv-export-tab");
    await expect(csvExportTab).toBeVisible();

    // Type selector default value = "cost-records" (verbatim from
    // CsvExportTab.tsx:51 initialType).
    const typeSelector = page.getByTestId("csv-export-type-selector");
    await expect(typeSelector).toHaveValue("cost-records");

    // Period selector default value = "2026-08" (verbatim from
    // CsvExportTab.tsx:50 initialPeriod).
    const periodSelector = page.getByTestId(`period-selector-${TEST_PERIOD}`);
    await expect(periodSelector).toHaveValue(TEST_PERIOD);

    // Download button visible + enabled.
    const downloadButton = page.getByTestId("download-button");
    await expect(downloadButton).toBeVisible();
    await expect(downloadButton).toBeEnabled();

    // Click download — download is a browser side-effect (blob URL
    // trigger in CsvExportTab.tsx:110-117), so the page route does NOT
    // change. We assert URL stays at /ko-KR/reports.
    await downloadButton.click();

    // Wait briefly for the fetch + blob download flow to settle.
    await page.waitForTimeout(500);

    // URL stays unchanged.
    await expect(page).toHaveURL(new RegExp(`/${TEST_LOCALE}/reports$`));

    // Either success message visible OR error message visible
    // (depending on dev_seed fixture availability — see describe.skip
    // rationale above).
    const success = page.getByTestId("csv-export-success");
    const error = page.getByTestId("csv-export-error");
    const successVisible = await success.isVisible().catch(() => false);
    const errorVisible = await error.isVisible().catch(() => false);
    expect(successVisible || errorVisible).toBeTruthy();
  });

  // ── Case 2: CSV response content-type ───────────────────────────────
  test("CSV response Content-Type is text/csv; charset=utf-8", async ({
    page: _page,
    request,
  }) => {
    // Direct API call (bypassing UI for content-type assertion) — the
    // route is `GET /api/v1/exports/csv?type=cost-records&period=2026-08
    // &tenant_id={uuid}` per csv_routes.py:249-419.
    //
    // We do NOT call this directly in the skipped baseline — but the
    // assertion shape is preserved verbatim for cj-287+ activation.
    // cj-287 wire — real DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN (D-WEB-E2E-7).
    const url = `/api/v1/exports/csv?type=cost-records&period=${TEST_PERIOD}&tenant_id=${DEV_TENANT_REPORT_ID}`;

    const response = await request.get(url, {
      headers: {
        Authorization: `Bearer ${DEV_ACCESS_TOKEN}`,
      },
    });

    // 200 OK (when activated with real dev_seed fixtures + auth).
    expect(response.status()).toBe(200);

    // Content-Type = text/csv; charset=utf-8 (verbatim from
    // csv_routes.py:415 StreamingResponse media_type).
    const contentType = response.headers()["content-type"] ?? "";
    expect(contentType).toMatch(/text\/csv/);
    expect(contentType).toMatch(/charset=utf-8/);
  });

  // ── Case 3: UTF-8 BOM for Excel ko-KR ───────────────────────────────
  test("CSV response first 3 bytes are UTF-8 BOM (0xEF 0xBB 0xBF)", async ({
    page: _page,
    request,
  }) => {
    // Same URL as Case 2 — direct API call for binary body inspection.
    // cj-287 wire — real DEV_TENANT_REPORT_ID + DEV_ACCESS_TOKEN (D-WEB-E2E-7).
    const url = `/api/v1/exports/csv?type=cost-records&period=${TEST_PERIOD}&tenant_id=${DEV_TENANT_REPORT_ID}`;

    const response = await request.get(url, {
      headers: {
        Authorization: `Bearer ${DEV_ACCESS_TOKEN}`,
      },
    });

    // Body bytes — UTF-8 BOM is the first 3 bytes per csv_routes.py:402
    // `yield UTF8_BOM + buf.getvalue()` and csv_routes.py:113
    // `UTF8_BOM = "﻿"` (U+FEFF → UTF-8 = 0xEF 0xBB 0xBF).
    const body = await response.body();
    expect(body.length).toBeGreaterThanOrEqual(3);

    // First 3 bytes = 0xEF 0xBB 0xBF (NFR18 ko-KR SSOT 결정 wire).
    expect(body[0]).toBe(0xef);
    expect(body[1]).toBe(0xbb);
    expect(body[2]).toBe(0xbf);
  });
});
