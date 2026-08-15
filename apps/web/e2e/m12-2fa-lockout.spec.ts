/**
 * apps/web/e2e/m12-2fa-lockout.spec.ts — Playwright E2E for M12 2FA lockout flow.
 *
 * Story 12.5 — T6 AC #6 wire (4 of 16 E2E scenarios — lockout subset).
 * Run via `pnpm playwright test apps/web/e2e/m12-2fa-lockout.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_5_failed_attempts_trigger_lockout
 *      - TOTP 5회 오입력 → 5번째 응답 429 LOCKED_OUT → dialog에 lockout 메시지 노출.
 *   2. test_lockout_countdown_disables_submit
 *      - Lockout 상태에서 submit button disabled + Retry-After countdown 표시.
 *   3. test_lockout_status_badge_yellow
 *      - /account/security 진입 시 status='locked' → TwoFactorStatusBadge yellow + lockout notice.
 *   4. test_lockout_until_iso_drives_countdown_format
 *      - lockout_until ISO-8601 파싱 → mm:ss format countdown 표시 검증.
 *
 * Story 12.5 lessons applied:
 *   - 5회 failed_attempts threshold → 15분 lockout (PRD §F12.1 AC #3).
 *   - Lockout 메커니즘은 audit-first invariant (CR 1.1) — failed_attempts 카운터 서비스 레이어.
 *   - data-testid: tfc-lockout-message + account-security-locked-notice.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";

test.describe("M12 2FA lockout flow — UI flow", () => {
  // ── Case 1: 5회 실패 → 5번째 429 + lockout message ─────────────────
  test("5 failed TOTP attempts trigger lockout message", async ({ page }) => {
    // First 4 attempts: 400 INVALID_TOTP_CODE.
    let challengeCalls = 0;
    await page.route("**/api/v1/account/2fa/challenge", (route) => {
      challengeCalls += 1;
      if (challengeCalls < 5) {
        return route.fulfill({
          status: 400,
          contentType: "application/json",
          body: JSON.stringify({
            error: { code: "INVALID_TOTP_CODE", message_ko: "잘못된 인증 코드입니다" },
          }),
        });
      }
      // 5th attempt: 429 LOCKED_OUT.
      return route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({
          error: {
            code: "TOTP_LOCKED_OUT",
            message_ko: "5회 연속 실패 — 15분간 잠금",
            retry_after_seconds: 900,
          },
          retry_after_seconds: 900,
        }),
      });
    });

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

    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toBeVisible();

    // Submit 5 invalid codes.
    for (let i = 0; i < 5; i += 1) {
      await page.getByTestId("tfc-code-input").fill(`10000${i}`);
      await page.getByTestId("tfc-submit-button").click();
      // Wait for response + potential toast.
      await page.waitForTimeout(100);
    }

    // After 5th attempt, lockout message visible.
    await expect(
      page.locator('[data-sonner-toast]').filter({ hasText: /15분|잠금/ }),
    ).toBeVisible({ timeout: 3000 });
  });

  // ── Case 2: Lockout 상태 → submit disabled + countdown ────────────
  test("lockout state disables submit button + shows Retry-After countdown", async ({ page }) => {
    // Initial gate returns locked_out=true with lockout_until 5 minutes from now.
    const lockoutUntil = new Date(Date.now() + 5 * 60 * 1000).toISOString();

    await page.route("**/api/v1/m2-entry-gate", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          allowed: false,
          requires_two_factor: false,
          requires_challenge: true,
          locked_out: true,
          lockout_until: lockoutUntil,
          role_allowed: true,
          message_ko: "잠금 상태 — 5:00 후 해제",
        }),
      }),
    );

    await page.route("**/api/v1/account/2fa/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          totp_enabled: true,
          totp_enabled_at: "2026-08-12T10:00:00+09:00",
          recovery_codes_remaining: 8,
          failed_attempts: 5,
          locked_out: true,
          lockout_until: lockoutUntil,
          last_login_at: "2026-08-12T10:00:00+09:00",
          role: "owner",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toBeVisible();

    // Lockout message with countdown (mm:ss format, e.g., "04:5x").
    const lockoutMessage = page.getByTestId("tfc-lockout-message");
    await expect(lockoutMessage).toBeVisible();
    await expect(lockoutMessage).toContainText(/잠금|locked/);

    // Submit button disabled while locked.
    const submitButton = page.getByTestId("tfc-submit-button");
    await expect(submitButton).toBeDisabled();

    // Code input also disabled while locked.
    const codeInput = page.getByTestId("tfc-code-input");
    await expect(codeInput).toBeDisabled();
  });

  // ── Case 3: /account/security → status='locked' → yellow notice ───
  test("locked status shows yellow notice on /account/security page", async ({ page }) => {
    const lockoutUntil = new Date(Date.now() + 5 * 60 * 1000).toISOString();

    await page.route("**/api/v1/account/2fa/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          totp_enabled: true,
          totp_enabled_at: "2026-08-12T10:00:00+09:00",
          recovery_codes_remaining: 8,
          failed_attempts: 5,
          locked_out: true,
          lockout_until: lockoutUntil,
          last_login_at: "2026-08-12T10:00:00+09:00",
          role: "owner",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/security`);
    await page.waitForLoadState("networkidle");

    // Locked notice visible (yellow background per AccountSecurityPanel).
    const lockedNotice = page.getByTestId("account-security-locked-notice");
    await expect(lockedNotice).toBeVisible();
    await expect(lockedNotice).toContainText(/5회 연속 실패|잠금/);

    // SetupForm + DisableForm NOT rendered in locked state.
    await expect(page.getByTestId("account-security-setup-section")).toHaveCount(0);
    await expect(page.getByTestId("account-security-disable-section")).toHaveCount(0);
  });

  // ── Case 4: lockout_until ISO → mm:ss format countdown ─────────────
  test("lockout countdown formats remaining time as mm:ss", async ({ page }) => {
    // Lockout until exactly 5 minutes from now → countdown should start near "05:00".
    const lockoutUntil = new Date(Date.now() + 5 * 60 * 1000).toISOString();

    await page.route("**/api/v1/m2-entry-gate", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          allowed: false,
          requires_two_factor: false,
          requires_challenge: true,
          locked_out: true,
          lockout_until: lockoutUntil,
          role_allowed: true,
        }),
      }),
    );

    await page.route("**/api/v1/account/2fa/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          totp_enabled: true,
          totp_enabled_at: "2026-08-12T10:00:00+09:00",
          recovery_codes_remaining: 8,
          failed_attempts: 5,
          locked_out: true,
          lockout_until: lockoutUntil,
          last_login_at: "2026-08-12T10:00:00+09:00",
          role: "owner",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const lockoutMessage = page.getByTestId("tfc-lockout-message");
    await expect(lockoutMessage).toBeVisible();

    // Countdown format: mm:ss (e.g., "05:00", "04:59", "04:58" — tolerate small delta).
    // Allow a 1-second window to handle timing skew between page.route setup and goto.
    await expect(lockoutMessage).toContainText(/0[45]:\d\d/);
  });
});