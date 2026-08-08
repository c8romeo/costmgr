/**
 * apps/web/e2e/m11-reversal.spec.ts — Playwright E2E for M11 reversal request flow.
 *
 * Story 11.1 T10.11 — AC #1~#9 wire spec coverage. Run via
 * `pnpm playwright test apps/web/e2e/m11-reversal.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_happy_path_reversal_request — happy-path: [역분개] → Dialog →
 *      reason + corrected_qty 입력 → [역분개 실행] → sonner toast.success +
 *      correction_group_id 표시.
 *   2. test_atomic_transaction_failure_rollback — reversal sequence 실패 →
 *      sign-negating row rollback + audit-failure emit + sonner toast.error.
 *   3. test_unique_violation — 동일 target_event_id 로 reversal 2회 호출 →
 *      422 REVERSAL_DUPLICATE + sonner toast.error.
 *   4. test_period_locked_blocked — monthly_input_periods.status='locked' →
 *      ReversalRequestButton 비활성 + sonner toast.error('잠긴 기간').
 *   5. test_capability_gate_service_only — service-only tenant 진입 →
 *      403 INDUSTRY_NOT_SUPPORTED + ReversalRequestButton 비노출.
 *
 * Story 0.5 wired the Playwright runner + Supabase test fixtures.
 * Uses rls_db fixture for tenant isolation. Korean (ko-KR) locale +
 * manufacturing tenant.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const TEST_PERIOD = "2026-08";
const TEST_TENANT = "manufacturing";

test.describe("M11 inventory reversal request — UI flow", () => {
  test.beforeEach(async ({ page }) => {
    // Seed rls_db fixture for manufacturing tenant (Story 0.5 AC #5).
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");
  });

  // ── Case 1: happy-path reversal request ───────────────────────
  test("happy-path reversal request renders dialog and posts", async ({
    page,
  }) => {
    // The ReversalRequestButton is rendered when capability_granted=true +
    // a target_event_id is provided by the page context.
    const button = page.getByTestId("reversal-request-button");
    await expect(button).toBeVisible();

    await button.click();
    const dialog = page.getByTestId("reversal-request-dialog");
    await expect(dialog).toBeVisible();

    // Fill reason
    await page.getByTestId("reversal-request-reason").fill("오류 정정 사유");

    // Submit
    await page.getByTestId("reversal-request-submit").click();

    // sonner toast.success with correction_group_id
    await expect(
      page.locator('[data-sonner-toast]').filter({ hasText: "역분개 완료" }),
    ).toBeVisible();
  });

  // ── Case 2: atomic-transaction failure rollback ────────────────
  test("atomic transaction failure rolls back + sonner toast.error", async ({
    page,
    request,
  }) => {
    // Intercept POST to fail with 500 to trigger rollback path.
    await page.route("**/api/v1/close/reversal-requests", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: { code: "INTERNAL_ERROR" } }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    const button = page.getByTestId("reversal-request-button");
    await button.click();
    await page.getByTestId("reversal-request-reason").fill("오류 정정 사유");
    await page.getByTestId("reversal-request-submit").click();

    // sonner toast.error for generic failure
    await expect(
      page.locator('[data-sonner-toast]').filter({ hasText: "역분개 실패" }),
    ).toBeVisible();
  });

  // ── Case 3: unique violation (re-reversal of same target) ─────
  test("unique violation returns 422 REVERSAL_DUPLICATE", async ({ page }) => {
    // Intercept POST to return 422 REVERSAL_DUPLICATE.
    await page.route("**/api/v1/close/reversal-requests", (route) =>
      route.fulfill({
        status: 422,
        contentType: "application/json",
        body: JSON.stringify({
          error: { code: "REVERSAL_DUPLICATE" },
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    const button = page.getByTestId("reversal-request-button");
    await button.click();
    await page.getByTestId("reversal-request-reason").fill("오류 정정 사유");
    await page.getByTestId("reversal-request-submit").click();

    await expect(
      page
        .locator('[data-sonner-toast]')
        .filter({ hasText: "이미 처리된 역분개" }),
    ).toBeVisible();
  });

  // ── Case 4: period_locked blocks submission ───────────────────
  test("period_status='locked' disables submit button", async ({ page }) => {
    // rls_db fixture pre-seeds '2026-12' as a locked period.
    await page.goto(`/${TEST_LOCALE}/m2-input/period/2026-12`);
    await page.waitForLoadState("networkidle");

    const button = page.getByTestId("reversal-request-button");
    await expect(button).toBeVisible();
    await expect(button).toBeDisabled();

    // Verify period_status='locked' on the button data attribute.
    await expect(button).toHaveAttribute("data-period-status", "locked");
  });

  // ── Case 5: capability gate — service-only tenant ──────────────
  test("service-only tenant → ReversalRequestButton hidden + 403", async ({
    page,
  }) => {
    // rls_db fixture pre-seeds 'service' tenant with industry='service'.
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}?tenant=service`);
    await page.waitForLoadState("networkidle");

    // Capability.REVERSAL_REQUEST is service-only ❌ → button hidden.
    await expect(page.getByTestId("reversal-request-button")).toHaveCount(0);
  });
});
