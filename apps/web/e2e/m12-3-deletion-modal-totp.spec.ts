/**
 * apps/web/e2e/m12-3-deletion-modal-totp.spec.ts — Playwright E2E for M12 account deletion modal TOTP step.
 *
 * Story 12.3 — T7 follow-up sprint (mirror 12-5 T6 atomic pattern).
 * 4 of 16 E2E scenarios — modal TOTP step subset.
 * Run via `pnpm playwright test apps/web/e2e/m12-3-deletion-modal-totp.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_modal_opens_with_totp_step_visible_and_consent_hidden
 *      - [계정 삭제하기] 클릭 → 모달 mount → Step 1 (TOTP 입력) visible, Step 2 (consent) hidden.
 *   2. test_invalid_totp_format_shows_validation_error
 *      - TOTP 5자리 입력 → "6자리 숫자를 입력해 주세요" 에러 → challenge-token 호출 0건.
 *   3. test_valid_totp_submits_challenge_token_and_advances_to_consent
 *      - TOTP 6자리 입력 → POST /challenge-token 200 → Step 2 (consent textarea) visible.
 *   4. test_invalid_totp_code_returns_401_and_shows_korean_error
 *      - TOTP 6자리 입력 → POST /challenge-token 401 → "2FA 인증에 실패했습니다" 에러 표시.
 *
 * CR 12-5 L3 3-layer TOTP defense (UI mirror): route require_role + service verify_totp_challenge
 * (tested via /challenge-token stub) + handler audit-first.
 *
 * Story 0.5 wired the Playwright runner + Supabase test fixtures.
 * Korean (ko-KR) locale + manufacturing tenant.
 *
 * CR 11-3 honest-DEFER discipline 9번째 epic 연속:
 *   - Reuses page.route() interception pattern (Story 11.1, 12.1, 12.5).
 *   - Korean ko-KR.json strings as the canonical assertion target (CR 11-4 D-002).
 *   - selectors from AccountDeletionModal (id="deletion-totp", id="deletion-consent").
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";

const SAMPLE_TENANT_ID = "11111111-1111-1111-1111-111111111111";
const SAMPLE_CHALLENGE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.dGVzdC1jaGFsbGVuZ2U.c2lnbmF0dXJl";
const SAMPLE_EXPIRES_AT = new Date(Date.now() + 5 * 60 * 1000).toISOString();

function buildActiveStatusBody(): Record<string, unknown> {
  return {
    tenant_id: SAMPLE_TENANT_ID,
    status: "active",
    deletion_requested_at: null,
    deletion_requested_by_user_id: null,
    deletion_consent_id: null,
    deletion_scheduled_for: null,
    trace_id: "trace-id-1001",
  };
}

test.describe("M12 account deletion — modal TOTP step", () => {
  // ── Case 1: 모달 mount → TOTP step visible ────────────────────────
  test("modal opens with TOTP step visible and consent step hidden", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildActiveStatusBody()),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    // Click [계정 삭제하기] → modal mount.
    await page.getByRole("button", { name: "계정 삭제하기" }).click();

    // Modal dialog visible with Korean title.
    const dialog = page.locator('div[role="dialog"][aria-labelledby="deletion-modal-title"]');
    await expect(dialog).toBeVisible();
    await expect(dialog.getByText("계정 삭제 — 최종 확인")).toBeVisible();

    // Step 1: TOTP input visible.
    const totpInput = page.locator("#deletion-totp");
    await expect(totpInput).toBeVisible();
    await expect(totpInput).toHaveAttribute("pattern", "\\d{6}");
    await expect(totpInput).toHaveAttribute("maxlength", "6");

    // Step 2: Consent textarea hidden (TOTP step first).
    await expect(page.locator("#deletion-consent")).toHaveCount(0);
  });

  // ── Case 2: TOTP 5자리 → invalid format error (no API call) ───────
  test("invalid TOTP format shows validation error without API call", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildActiveStatusBody()),
      }),
    );

    // Spy on challenge-token endpoint — should NOT be called.
    let challengeTokenCalls = 0;
    await page.route("**/api/v1/account/deletion/challenge-token", (route) => {
      challengeTokenCalls += 1;
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ token: SAMPLE_CHALLENGE_TOKEN, expires_at: SAMPLE_EXPIRES_AT }),
      });
    });

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "계정 삭제하기" }).click();

    // Enter 5-digit (invalid format).
    await page.locator("#deletion-totp").fill("12345");
    await page.getByRole("button", { name: "다음" }).click();

    // Validation error: "6자리 숫자를 입력해 주세요."
    await expect(page.getByText("6자리 숫자를 입력해 주세요.")).toBeVisible();

    // No API call made (client-side validation only).
    expect(challengeTokenCalls).toBe(0);

    // Step 2 (consent) still hidden.
    await expect(page.locator("#deletion-consent")).toHaveCount(0);
  });

  // ── Case 3: TOTP valid → POST /challenge-token 200 → consent step ──
  test("valid TOTP submits challenge token and advances to consent step", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildActiveStatusBody()),
      }),
    );

    await page.route("**/api/v1/account/deletion/challenge-token", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          token: SAMPLE_CHALLENGE_TOKEN,
          expires_at: SAMPLE_EXPIRES_AT,
          trace_id: "trace-id-1002",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "계정 삭제하기" }).click();
    await page.locator("#deletion-totp").fill("123456");
    await page.getByRole("button", { name: "다음" }).click();

    // Advance to Step 2 (consent textarea visible).
    const consentTextarea = page.locator("#deletion-consent");
    await expect(consentTextarea).toBeVisible({ timeout: 5000 });

    // TOTP input no longer visible (replaced by consent step).
    await expect(page.locator("#deletion-totp")).toHaveCount(0);
  });

  // ── Case 4: invalid TOTP → 401 envelope → Korean error ─────────────
  test("invalid TOTP code returns 401 and shows Korean error", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildActiveStatusBody()),
      }),
    );

    await page.route("**/api/v1/account/deletion/challenge-token", (route) =>
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({
          code: "M12_TWO_FACTOR_INVALID",
          message_ko: "2FA 인증에 실패했습니다 — 잠시 후 다시 시도해 주세요.",
          details: { failed_attempts: 1 },
          trace_id: "trace-id-1003",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "계정 삭제하기" }).click();
    await page.locator("#deletion-totp").fill("999999");
    await page.getByRole("button", { name: "다음" }).click();

    // Server-supplied Korean error envelope displayed.
    await expect(
      page.getByText("2FA 인증에 실패했습니다 — 잠시 후 다시 시도해 주세요."),
    ).toBeVisible();

    // Step 2 (consent) NOT advanced — stays in TOTP step.
    await expect(page.locator("#deletion-consent")).toHaveCount(0);
  });
});
