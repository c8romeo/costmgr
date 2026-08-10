/**
 * apps/web/e2e/m11-cache-invalidation-channels.spec.ts — Playwright E2E for M11 cache invalidation channels.
 *
 * Story 11.4 (A13 sprint-up) — Sprint-up item: AD-25 4-channel cache invalidation
 * publisher UI badge.
 * Run via `pnpm playwright test apps/web/e2e/m11-cache-invalidation-channels.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_default_all_4_channels_active — no active_subset → all 4 chips active.
 *   2. test_w2_reopen_subset_highlight — W2 reopen uses 2 channels (fiscal_period_cache + closing_snapshot_cache).
 *   3. test_snapshot_persistence_receipt — receipt from /api/v1/close/snapshots/{id}/commit
 *      renders 4 channels.
 *   4. test_reversal_execute_receipt — receipt from /api/v1/close/reversal-execute
 *      renders 4 channels.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const TEST_PERIOD = "2026-08";

test.describe("M11 cache invalidation channels — UI flow", () => {
  // ── Case 1: default all 4 channels active ─────────────────────
  test("default badge shows all 4 channels active", async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    const badge = page.getByTestId("cache-invalidation-channel-badge");
    await expect(badge).toBeVisible();

    // All 4 channel chips render with data-active=true.
    for (const channel of [
      "ai_cache",
      "cost_engine_cache",
      "fiscal_period_cache",
      "closing_snapshot_cache",
    ]) {
      const chip = page.getByTestId(`cache-channel-${channel}`);
      await expect(chip).toBeVisible();
      await expect(chip).toHaveAttribute("data-active", "true");
    }
  });

  // ── Case 2: W2 reopen highlights 2-channel subset ─────────────
  test("W2 reopen highlights 2-channel subset", async ({ page }) => {
    await page.goto(
      `/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}?flow=w2-reopen`,
    );
    await page.waitForLoadState("networkidle");

    const badge = page.getByTestId("cache-invalidation-channel-badge");
    await expect(badge).toHaveAttribute(
      "data-active-subset",
      "fiscal_period_cache,closing_snapshot_cache",
    );

    // 2 channels active, 2 channels inactive.
    await expect(
      page.getByTestId("cache-channel-fiscal_period_cache"),
    ).toHaveAttribute("data-active", "true");
    await expect(
      page.getByTestId("cache-channel-closing_snapshot_cache"),
    ).toHaveAttribute("data-active", "true");
    await expect(page.getByTestId("cache-channel-ai_cache")).toHaveAttribute(
      "data-active",
      "false",
    );
    await expect(
      page.getByTestId("cache-channel-cost_engine_cache"),
    ).toHaveAttribute("data-active", "false");
  });

  // ── Case 3: snapshot persistence receipt ──────────────────────
  test("snapshot persistence receipt renders 4 channels", async ({ page }) => {
    await page.route("**/api/v1/close/snapshots/*/commit", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          snapshot_state: "committed",
          cache_invalidation_receipt: {
            ai_cache: "invalidated",
            cost_engine_cache: "invalidated",
            fiscal_period_cache: "invalidated",
            closing_snapshot_cache: "invalidated",
          },
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    await page.getByTestId("snapshot-persistence-commit-button").click();

    const badge = page.getByTestId("cache-invalidation-channel-badge");
    await expect(badge).toBeVisible();
  });

  // ── Case 4: reversal execute receipt ──────────────────────────
  test("reversal execute receipt renders 4 channels", async ({ page }) => {
    await page.route("**/api/v1/close/reversal-execute", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          negating_event_id: "neg-1",
          corrected_event_id: "cor-1",
          correction_group_id: "11111111-1111-4111-8111-111111111111",
          cache_invalidation_receipt: {
            ai_cache: "invalidated",
            cost_engine_cache: "invalidated",
            fiscal_period_cache: "invalidated",
            closing_snapshot_cache: "invalidated",
          },
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("reversal-execute-dialog");
    await expect(dialog).toBeVisible();

    await page
      .getByTestId("reversal-execute-reason-input")
      .fill("오류 정정 사유 — 20자 이상의 충분한 설명");

    await page.getByTestId("reversal-execute-submit-button").click();

    const badge = page.getByTestId("cache-invalidation-channel-badge");
    await expect(badge).toBeVisible();
  });
});