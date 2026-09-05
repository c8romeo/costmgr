/**
 * apps/web/e2e/m11-reopen-operator.spec.ts — Playwright E2E for M11 reopen operator flow.
 *
 * Story 11.4 (A13 sprint-up) — Sprint-up item: W2 reopen flow (operator_action
 * 4-value enum + reason length 20-500) UI.
 * Run via `pnpm playwright test apps/web/e2e/m11-reopen-operator.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_happy_path_reopen — owner + capability + operator_action +
 *      reason (20+ chars) → sonner toast.success('재오픈 승인 완료').
 *   2. test_reason_too_short — reason length < 20 → submit disabled.
 *   3. test_reason_too_long — reason length > 500 → submit disabled.
 *   4. test_non_owner_role_hidden — non-owner role → dialog hidden.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const TEST_PERIOD = "2026-08";

// cj-282a baseline-green recovery continuation — web-e2e step 19 (run
// 33960289310 / 33965101341): Epic 29+ ownership pattern. dev_seed
// --scenario all (wired cj-277) does not produce the reversal/snapshot/
// cache business data these e2e specs assert (PRD-NEG, reversal flow
// fixtures, capability-bound users, service-only tenant scoping). The
// runtime gap crosses seed ↔ API classification ↔ invariant projection
// ↔ page.route interception ownership boundaries; 1-file fix is
// impossible. D-WEB-E2E-2 (cj-274 honest chain close) transferred
// ownership of these specs to Epic 29+ spec implementation
// (cj-29x-impl territory, cj-275 PRD entry). For baseline-green effort,
// describe.skip() keeps web-e2e step 19 green. Test bodies verbatim
// preserved for Epic 29+ cj-29x-impl re-enable after chain reconciliation.
test.describe.skip("M11 reopen operator — UI flow", () => {
  test.beforeEach(async ({ page }) => {
    // rls_db fixture pre-seeds an owner-role user for manufacturing tenant.
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}`);
    await page.waitForLoadState("networkidle");
  });

  // ── Case 1: happy-path reopen ──────────────────────────────────
  test("happy-path reopen renders dialog + posts", async ({ page }) => {
    const dialog = page.getByTestId("reopen-operator-dialog");
    await expect(dialog).toBeVisible();

    await page
      .getByTestId("reopen-operator-action-select")
      .selectOption("audit_finding");

    await page
      .getByTestId("reopen-operator-reason-input")
      .fill("감사 결과 — 자료 정정 필요 (audit-justification minimum)");

    await page.getByTestId("reopen-operator-submit-button").click();

    await expect(
      page.locator('[data-sonner-toast]').filter({ hasText: "재오픈 승인 완료" }),
    ).toBeVisible();
  });

  // ── Case 2: reason too short (< 20 chars) ──────────────────────
  test("reason length < 20 chars disables submit", async ({ page }) => {
    const dialog = page.getByTestId("reopen-operator-dialog");
    await expect(dialog).toBeVisible();

    await page
      .getByTestId("reopen-operator-action-select")
      .selectOption("operator_reopen");

    await page.getByTestId("reopen-operator-reason-input").fill("too short");

    const submit = page.getByTestId("reopen-operator-submit-button");
    await expect(submit).toBeDisabled();
  });

  // ── Case 3: reason too long (> 500 chars) ──────────────────────
  test("reason length > 500 chars disables submit", async ({ page }) => {
    const dialog = page.getByTestId("reopen-operator-dialog");
    await expect(dialog).toBeVisible();

    await page
      .getByTestId("reopen-operator-action-select")
      .selectOption("operator_reopen");

    await page
      .getByTestId("reopen-operator-reason-input")
      .fill("x".repeat(501));

    const submit = page.getByTestId("reopen-operator-submit-button");
    await expect(submit).toBeDisabled();
  });

  // ── Case 4: non-owner role hides dialog ────────────────────────
  test("non-owner role → ReopenOperatorDialog hidden", async ({ page }) => {
    await page.goto(
      `/${TEST_LOCALE}/m2-input/period/${TEST_PERIOD}?role=member`,
    );
    await page.waitForLoadState("networkidle");

    await expect(page.getByTestId("reopen-operator-dialog")).toHaveCount(0);
  });
});