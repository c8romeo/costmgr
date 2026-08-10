/**
 * apps/web/e2e/m11-snapshot-persistence.spec.ts — Playwright E2E for M11 snapshot persistence flow.
 *
 * Story 11.4 (A13 sprint-up) — Sprint-up item: AD-20 verified → committed transition UI.
 * Run via `pnpm playwright test apps/web/e2e/m11-snapshot-persistence.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_happy_path_commit — snapshot state='verified' → [스냅샷 영구화] →
 *      sonner toast.success('스냅샷 영구화 완료').
 *   2. test_idempotent_no_op — snapshot state='committed' → button disables +
 *      sonner toast.success('멱등 처리').
 *   3. test_draft_rejection — snapshot state='draft' → panel button disabled.
 *   4. test_capability_gate_service_only — service-only tenant → panel hidden.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const TEST_PERIOD = "2026-08";
const TEST_TENANT = "manufacturing";

test.describe("M11 snapshot persistence — UI flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");
  });

  // ── Case 1: happy-path commit (verified → committed) ──────────
  test("happy-path commit renders panel + posts", async ({ page }) => {
    const panel = page.getByTestId("snapshot-persistence-panel");
    await expect(panel).toBeVisible();
    await expect(panel).toHaveAttribute("data-current-state", "verified");

    await page.getByTestId("snapshot-persistence-commit-button").click();

    await expect(
      page
        .locator('[data-sonner-toast]')
        .filter({ hasText: "스냅샷 영구화 완료" }),
    ).toBeVisible();
  });

  // ── Case 2: idempotent no-op (state='committed') ───────────────
  test("idempotent no-op when state='committed'", async ({ page }) => {
    // Intercept GET snapshot state to return 'committed'.
    await page.route("**/api/v1/close/snapshot/*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          snapshot_id: "11111111-1111-4111-8111-111111111111",
          snapshot_state: "committed",
          period_key: TEST_PERIOD,
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    const panel = page.getByTestId("snapshot-persistence-panel");
    await expect(panel).toHaveAttribute("data-current-state", "committed");

    await page.getByTestId("snapshot-persistence-commit-button").click();
    await expect(
      page.locator('[data-sonner-toast]').filter({ hasText: "멱등 처리" }),
    ).toBeVisible();
  });

  // ── Case 3: draft rejection (state='draft') ────────────────────
  test("state='draft' disables commit button", async ({ page }) => {
    await page.route("**/api/v1/close/snapshot/*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          snapshot_id: "11111111-1111-4111-8111-111111111111",
          snapshot_state: "draft",
          period_key: TEST_PERIOD,
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    const panel = page.getByTestId("snapshot-persistence-panel");
    await expect(panel).toHaveAttribute("data-current-state", "draft");

    const button = page.getByTestId("snapshot-persistence-commit-button");
    await expect(button).toBeDisabled();
  });

  // ── Case 4: capability gate — service-only tenant ──────────────
  test("service-only tenant → SnapshotPersistencePanel hidden", async ({
    page,
  }) => {
    await page.goto(
      `/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}?tenant=${TEST_TENANT === "manufacturing" ? "service" : "manufacturing"}`,
    );
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("snapshot-persistence-panel")).toHaveCount(0);
  });
});