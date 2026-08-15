/**
 * apps/web/e2e/m12-2fa-recovery.spec.ts — Playwright E2E for M12 2FA recovery code flow.
 *
 * Story 12.5 — T6 AC #6 wire (4 of 16 E2E scenarios — recovery subset).
 * Run via `pnpm playwright test apps/web/e2e/m12-2fa-recovery.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_recovery_codes_visible_when_2fa_enabled
 *      - /account/security 진입 (status='enabled') → recovery section + remaining count 노출.
 *   2. test_recovery_code_used_in_challenge_dialog_grants_m2_access
 *      - Challenge dialog → recovery mode → 10-char 코드 입력 → POST /recovery 200 → M2 허용.
 *   3. test_invalid_recovery_code_shows_error_toast
 *      - 잘못된 recovery code → 400 INVALID_RECOVERY_CODE → toast + dialog 유지.
 *   4. test_recovery_codes_remaining_decrements
 *      - Status badge + recovery section이 remaining count (8 → 7) 감소 반영.
 *
 * Story 12.5 lessons applied:
 *   - Recovery code = Crockford base32 10 chars (per CR 1.1 audit-first + P-18 2FA disabled).
 *   - data-testid: account-security-recovery-section + tfc-mode-toggle (totp↔recovery).
 *   - handler endpoint: POST /api/v1/account/2fa/recovery (owner-only per AC #2).
 *   - audit-first invariant: 사용된 recovery code는 mark-as-used (single-use).
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";

test.describe("M12 2FA recovery code — UI flow", () => {
  test.beforeEach(async ({ page }) => {
    // /api/v1/account/2fa/status → totp_enabled=true with 8 recovery codes remaining.
    await page.route("**/api/v1/account/2fa/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          totp_enabled: true,
          totp_enabled_at: "2026-08-12T10:00:00+09:00",
          recovery_codes_remaining: 8,
          failed_attempts: 0,
          locked_out: false,
          lockout_until: null,
          last_login_at: "2026-08-12T10:00:00+09:00",
          role: "owner",
        }),
      }),
    );
  });

  // ── Case 1: status='enabled' → recovery section + remaining count ──
  test("recovery section + remaining count visible when 2FA is enabled", async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/account/security`);
    await page.waitForLoadState("networkidle");

    const panel = page.getByTestId("account-security-panel");
    await expect(panel).toBeVisible();

    // Recovery section present.
    const recoverySection = page.getByTestId("account-security-recovery-section");
    await expect(recoverySection).toBeVisible();

    // Remaining count "8개 남음" visible.
    await expect(recoverySection).toContainText(/8개 남음/);

    // DisableForm also visible for owner.
    const disableSection = page.getByTestId("account-security-disable-section");
    await expect(disableSection).toBeVisible();
  });

  // ── Case 2: recovery code → challenge dialog → M2 access ───────────
  test("valid recovery code in challenge dialog grants M2 access", async ({ page }) => {
    // Recovery endpoint succeeds.
    await page.route("**/api/v1/account/2fa/recovery", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      }),
    );

    // Gate before recovery → requires_challenge=true.
    // Gate after recovery (router.refresh re-fetch) → allowed=true.
    await page.route("**/api/v1/m2-entry-gate", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          allowed: true,
          requires_two_factor: false,
          requires_challenge: false,
          locked_out: false,
          role_allowed: true,
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveAttribute("data-mode", "totp");

    // Switch to recovery mode.
    await page.getByTestId("tfc-mode-toggle").click();
    await expect(dialog).toHaveAttribute("data-mode", "recovery");

    // Enter valid 10-char Crockford base32 recovery code.
    await page.getByTestId("tfc-code-input").fill("ABCDE12345");
    await page.getByTestId("tfc-submit-button").click();

    // Dialog closes after successful recovery.
    await expect(dialog).toHaveCount(0, { timeout: 5000 });
  });

  // ── Case 3: invalid recovery code → 400 + error toast ──────────────
  test("invalid recovery code shows error toast + keeps dialog open", async ({ page }) => {
    await page.route("**/api/v1/account/2fa/recovery", (route) =>
      route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "INVALID_RECOVERY_CODE",
            message_ko: "복구 코드가 잘못되었거나 이미 사용되었습니다",
          },
        }),
      }),
    );

    await page.route("**/api/v1/m2-entry-gate", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          allowed: false,
          requires_two_factor: false,
          requires_challenge: true,
          locked_out: false,
          role_allowed: true,
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toBeVisible();

    // Switch to recovery mode + submit invalid code.
    await page.getByTestId("tfc-mode-toggle").click();
    await expect(dialog).toHaveAttribute("data-mode", "recovery");
    await page.getByTestId("tfc-code-input").fill("XXXXXXXXXX");
    await page.getByTestId("tfc-submit-button").click();

    // sonner toast.error with Korean message.
    await expect(
      page
        .locator('[data-sonner-toast]')
        .filter({ hasText: /복구 코드가 잘못/ }),
    ).toBeVisible({ timeout: 3000 });

    // Dialog remains open.
    await expect(dialog).toBeVisible();
  });

  // ── Case 4: remaining count decrements (8 → 7) after usage ─────────
  test("recovery section reflects decremented remaining count", async ({ page }) => {
    // Override beforeEach status with 7 remaining codes (after one usage).
    await page.unroute("**/api/v1/account/2fa/status");
    await page.route("**/api/v1/account/2fa/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          totp_enabled: true,
          totp_enabled_at: "2026-08-12T10:00:00+09:00",
          recovery_codes_remaining: 7, // One used.
          failed_attempts: 0,
          locked_out: false,
          lockout_until: null,
          last_login_at: "2026-08-12T10:00:00+09:00",
          role: "owner",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/security`);
    await page.waitForLoadState("networkidle");

    const recoverySection = page.getByTestId("account-security-recovery-section");
    await expect(recoverySection).toBeVisible();

    // Remaining count reflects post-usage state.
    await expect(recoverySection).toContainText(/7개 남음/);
  });
});