/**
 * apps/web/e2e/m12-2fa-challenge.spec.ts — Playwright E2E for M12 2FA challenge dialog.
 *
 * Story 12.5 — T6 AC #6 wire (4 of 16 E2E scenarios — challenge subset).
 * Run via `pnpm playwright test apps/web/e2e/m12-2fa-challenge.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_2fa_enabled_user_sees_m2_gate_require_challenge
 *      - 2FA 등록 사용자 → /m2-input 진입 시 TwoFactorChallengeDialog mount (requires_challenge=true).
 *   2. test_totp_challenge_success_grants_m2_access
 *      - Dialog에서 6-digit TOTP 입력 → POST /challenge 200 → dialog close + M2 tabs 노출.
 *   3. test_invalid_totp_shows_sonner_toast_error
 *      - 잘못된 코드 → POST /challenge 400 → sonner toast.error 표시 + dialog 유지.
 *   4. test_recovery_code_mode_toggle
 *      - "복구 코드 사용" toggle → mode=totp→recovery 전환 + 10-char 입력 패턴.
 *
 * Story 12.5 lessons applied:
 *   - TwoFactorChallengeDialog는 /m2-input 진입 시 gate boundary에서 마운트.
 *   - data-testid: two-factor-challenge-dialog / tfc-code-input / tfc-submit-button / tfc-mode-toggle.
 *   - data-mode attribute: "totp" | "recovery" — parity case 단일 검증.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";

test.describe("M12 2FA challenge dialog — UI flow", () => {
  test.beforeEach(async ({ page }) => {
    // /m2-entry-gate → requires_challenge=true (2FA 등록 후 첫 진입).
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
          message_ko: "2FA 인증이 필요합니다 — [인증하기]",
        }),
      }),
    );

    // /api/v1/account/2fa/status → totp_enabled=true (challenge mode).
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

  // ── Case 1: 2FA 등록 사용자 → challenge dialog mount ───────────────
  test("2FA-enabled user entering /m2-input sees challenge dialog", async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveAttribute("data-mode", "totp");
    await expect(dialog).toHaveAttribute("role", "dialog");
    await expect(dialog).toHaveAttribute("aria-modal", "true");

    // Code input present + focused.
    const codeInput = page.getByTestId("tfc-code-input");
    await expect(codeInput).toBeVisible();
    await expect(codeInput).toHaveAttribute("pattern", "[0-9]{6}");

    // Submit + cancel + mode toggle buttons present.
    await expect(page.getByTestId("tfc-submit-button")).toBeVisible();
    await expect(page.getByTestId("tfc-cancel-button")).toBeVisible();
    await expect(page.getByTestId("tfc-mode-toggle")).toBeVisible();
  });

  // ── Case 2: TOTP 입력 → challenge 성공 → dialog close ───────────────
  test("valid TOTP challenge closes dialog and allows M2 access", async ({ page }) => {
    // After successful challenge, gate returns allowed=true.
    await page.route("**/api/v1/account/2fa/challenge", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      }),
    );

    await page.route("**/api/v1/m2-entry-gate", (route, req) => {
      // First call (with requires_challenge=true from beforeEach) → POST /challenge was OK,
      // subsequent gate fetches (e.g., on router.refresh) return allowed=true.
      // For simplicity, after challenge, we always return allowed=true here.
      void req;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          allowed: true,
          requires_two_factor: false,
          requires_challenge: false,
          locked_out: false,
          role_allowed: true,
        }),
      });
    });

    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toBeVisible();

    // Enter 6-digit TOTP + submit.
    await page.getByTestId("tfc-code-input").fill("654321");
    await page.getByTestId("tfc-submit-button").click();

    // Dialog closes after successful challenge (parent unmounts on onSuccess).
    await expect(dialog).toHaveCount(0, { timeout: 5000 });
  });

  // ── Case 3: 잘못된 TOTP → 400 → toast error + dialog 유지 ─────────
  test("invalid TOTP shows error toast + keeps dialog open", async ({ page }) => {
    await page.route("**/api/v1/account/2fa/challenge", (route) =>
      route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({
          error: { code: "INVALID_TOTP_CODE", message_ko: "잘못된 인증 코드입니다" },
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toBeVisible();

    // Submit invalid code.
    await page.getByTestId("tfc-code-input").fill("000000");
    await page.getByTestId("tfc-submit-button").click();

    // sonner toast.error appears with Korean message.
    await expect(
      page.locator('[data-sonner-toast]').filter({ hasText: /잘못된/ }),
    ).toBeVisible({ timeout: 3000 });

    // Dialog remains open (no successful challenge → no onSuccess).
    await expect(dialog).toBeVisible();
  });

  // ── Case 4: "복구 코드 사용" → recovery mode 토글 ──────────────────
  test("recovery mode toggle changes data-mode + input pattern", async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/m2-input`);
    await page.waitForLoadState("networkidle");

    const dialog = page.getByTestId("two-factor-challenge-dialog");
    await expect(dialog).toHaveAttribute("data-mode", "totp");

    // Click "복구 코드 사용" toggle.
    await page.getByTestId("tfc-mode-toggle").click();

    // Mode switches to recovery.
    await expect(dialog).toHaveAttribute("data-mode", "recovery");

    // Input pattern changes to allow 10-char base32 recovery codes.
    const codeInput = page.getByTestId("tfc-code-input");
    await expect(codeInput).toHaveAttribute("pattern", "[0-9A-Z]{10}");
    await expect(codeInput).toHaveAttribute("maxlength", "10");

    // Toggle back to totp.
    await page.getByTestId("tfc-mode-toggle").click();
    await expect(dialog).toHaveAttribute("data-mode", "totp");
    await expect(codeInput).toHaveAttribute("pattern", "[0-9]{6}");
  });
});