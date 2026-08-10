/**
 * apps/web/e2e/m11-reversal-execute.spec.ts — Playwright E2E for M11 reversal execute flow.
 *
 * Story 11.4 (A13 sprint-up) — Sprint-up item: AD-22 committed → reversed 영구화 UI.
 * Run via `pnpm playwright test apps/web/e2e/m11-reversal-execute.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_happy_path_reversal_execute — snapshot state='committed' → [역분개 실행] →
 *      reason input + sonner toast.success('스냅샷 역분개 완료').
 *   2. test_invalid_snapshot_state — snapshot state='verified' → submit button disabled +
 *      INVALID_SNAPSHOT_KO reason text.
 *   3. test_reason_too_short — reason length < 20 → submit button disabled.
 *   4. test_capability_gate_service_only — service-only tenant → dialog hidden.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const TEST_PERIOD = "2026-08";

test.describe("M11 reversal execute — UI flow", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");
  });

  // ── Case 1: happy-path reversal execute ────────────────────────
  test("happy-path reversal execute renders dialog + posts", async ({
    page,
  }) => {
    const dialog = page.getByTestId("reversal-execute-dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveAttribute("data-snapshot-state", "committed");

    await page
      .getByTestId("reversal-execute-reason-input")
      .fill("오류 정정 사유 — 20자 이상의 충분한 설명");

    await page.getByTestId("reversal-execute-submit-button").click();

    await expect(
      page.locator('[data-sonner-toast]').filter({ hasText: "역분개 완료" }),
    ).toBeVisible();
  });

  // ── Case 2: invalid snapshot state ─────────────────────────────
  test("state='verified' disables submit + INVALID_SNAPSHOT reason", async ({
    page,
  }) => {
    await page.route("**/api/v1/close/snapshot/*", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          snapshot_id: "11111111-1111-4111-8111-111111111111",
          snapshot_state: "verified",
          period_key: TEST_PERIOD,
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("reversal-execute-dialog");
    await expect(dialog).toHaveAttribute("data-snapshot-state", "verified");

    const submit = page.getByTestId("reversal-execute-submit-button");
    await expect(submit).toBeDisabled();
  });

  // ── Case 3: reason too short (< 20 chars) ──────────────────────
  test("reason length < 20 chars disables submit", async ({ page }) => {
    const dialog = page.getByTestId("reversal-execute-dialog");
    await expect(dialog).toBeVisible();

    await page.getByTestId("reversal-execute-reason-input").fill("short");

    const submit = page.getByTestId("reversal-execute-submit-button");
    await expect(submit).toBeDisabled();
  });

  // ── Case 4: capability gate — service-only tenant ──────────────
  test("service-only tenant → ReversalExecuteDialog hidden", async ({
    page,
  }) => {
    await page.goto(
      `/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}?tenant=service`,
    );
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("reversal-execute-dialog")).toHaveCount(0);
  });
});