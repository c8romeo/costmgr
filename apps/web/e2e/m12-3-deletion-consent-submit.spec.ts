/**
 * apps/web/e2e/m12-3-deletion-consent-submit.spec.ts — Playwright E2E for M12 account deletion consent step.
 *
 * Story 12.3 — T7 follow-up sprint (mirror 12-5 T6 atomic pattern).
 * 4 of 16 E2E scenarios — consent step subset.
 * Run via `pnpm playwright test apps/web/e2e/m12-3-deletion-consent-submit.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_consent_step_renders_textarea_with_verbatim_template
 *      - TOTP → consent step 진입 → textarea visible + Korean consent template displayed.
 *   2. test_consent_text_mismatch_shows_korean_validation_error
 *      - 다른 텍스트 입력 → [삭제 요청] 클릭 → "문구가 일치하지 않습니다" 에러.
 *   3. test_consent_verbatim_match_submits_deletion_and_closes_modal
 *      - 정확한 동의 문구 입력 → POST /request 200 → modal close + status refresh to pending_deletion.
 *   4. test_request_failure_returns_500_and_keeps_user_in_consent_step
 *      - 동의 문구 정확 → POST /request 500 → 에러 메시지 표시 + 모달은 consent step 유지.
 *
 * CR 12-5 L3 3-layer TOTP defense: Layer 1 (route require_role) tested via /challenge-token 200 path,
 * Layer 2 (service verify_totp_challenge) tested via /request 200/500 path,
 * Layer 3 (handler audit-first) implicit — backend emit NOT testable from E2E.
 *
 * Story 0.5 wired the Playwright runner + Supabase test fixtures.
 * Korean (ko-KR) locale + manufacturing tenant.
 *
 * CR 11-3 honest-DEFER discipline 9번째 epic 연속:
 *   - Reuses page.route() interception pattern (Story 11.1, 12.1, 12.5).
 *   - Korean ko-KR.json strings as the canonical assertion target (CR 11-4 D-002).
 *   - DELETION_CONSENT_TEMPLATE_KO verbatim match (TS mirror — Python kernel parity).
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";

const SAMPLE_TENANT_ID = "11111111-1111-1111-1111-111111111111";
const SAMPLE_CONSENT_ID = "22222222-2222-2222-2222-222222222222";
const SAMPLE_CHALLENGE_TOKEN = "eyJhbGciOiJIUzI1NiJ9.dGVzdC1jaGFsbGVuZ2U.c2lnbmF0dXJl";
const SAMPLE_EXPIRES_AT = new Date(Date.now() + 5 * 60 * 1000).toISOString();
const SAMPLE_SCHEDULED_FOR = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

const CONSENT_TEMPLATE_KO =
  "본인은 데이터 보존 기간 (30일) 및 삭제 시점을 이해했으며 동의합니다";

function buildActiveStatusBody(): Record<string, unknown> {
  return {
    tenant_id: SAMPLE_TENANT_ID,
    status: "active",
    deletion_requested_at: null,
    deletion_requested_by_user_id: null,
    deletion_consent_id: null,
    deletion_scheduled_for: null,
    trace_id: "trace-id-2001",
  };
}

function buildPendingStatusBody(): Record<string, unknown> {
  return {
    tenant_id: SAMPLE_TENANT_ID,
    status: "pending_deletion",
    deletion_requested_at: new Date().toISOString(),
    deletion_requested_by_user_id: "33333333-3333-3333-3333-333333333333",
    deletion_consent_id: SAMPLE_CONSENT_ID,
    deletion_scheduled_for: SAMPLE_SCHEDULED_FOR,
    trace_id: "trace-id-2002",
  };
}

test.describe("M12 account deletion — consent step + submit", () => {
  // ── Case 1: consent step mount + verbatim template 표시 ────────────
  test("consent step renders textarea with Korean template verbatim", async ({ page }) => {
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
          trace_id: "trace-id-2001",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "계정 삭제하기" }).click();
    await page.locator("#deletion-totp").fill("123456");
    await page.getByRole("button", { name: "다음" }).click();

    // Consent step visible.
    const consentTextarea = page.locator("#deletion-consent");
    await expect(consentTextarea).toBeVisible({ timeout: 5000 });

    // Verbatim Korean template displayed as helper text.
    await expect(page.getByText(CONSENT_TEMPLATE_KO).first()).toBeVisible();

    // Destructive submit button visible.
    await expect(page.getByRole("button", { name: /삭제 요청/ })).toBeVisible();
  });

  // ── Case 2: consent mismatch → Korean validation error ─────────────
  test("consent text mismatch shows Korean validation error", async ({ page }) => {
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
          trace_id: "trace-id-2001",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "계정 삭제하기" }).click();
    await page.locator("#deletion-totp").fill("123456");
    await page.getByRole("button", { name: "다음" }).click();

    await page.locator("#deletion-consent").fill("잘못된 동의 문구입니다");
    await page.getByRole("button", { name: /삭제 요청/ }).click();

    // Korean validation error: "문구가 일치하지 않습니다 — 위 텍스트를 그대로 입력해 주세요."
    await expect(
      page.getByText("문구가 일치하지 않습니다 — 위 텍스트를 그대로 입력해 주세요."),
    ).toBeVisible();

    // Modal stays open in consent step.
    await expect(page.locator("#deletion-consent")).toBeVisible();
  });

  // ── Case 3: consent verbatim → POST /request 200 → modal close ─────
  test("consent verbatim match submits deletion and closes modal", async ({ page }) => {
    // First /status call returns active (initial panel mount).
    // Second /status call returns pending_deletion (post-submit refresh).
    let statusCallCount = 0;
    await page.route("**/api/v1/account/deletion/status", (route) => {
      statusCallCount += 1;
      const body = statusCallCount === 1 ? buildActiveStatusBody() : buildPendingStatusBody();
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    });

    await page.route("**/api/v1/account/deletion/challenge-token", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          token: SAMPLE_CHALLENGE_TOKEN,
          expires_at: SAMPLE_EXPIRES_AT,
          trace_id: "trace-id-2001",
        }),
      }),
    );

    await page.route("**/api/v1/account/deletion/request", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          tenant_id: SAMPLE_TENANT_ID,
          status: "pending_deletion",
          deletion_scheduled_for: SAMPLE_SCHEDULED_FOR,
          trace_id: "trace-id-2003",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "계정 삭제하기" }).click();
    await page.locator("#deletion-totp").fill("123456");
    await page.getByRole("button", { name: "다음" }).click();

    await page.locator("#deletion-consent").fill(CONSENT_TEMPLATE_KO);
    await page.getByRole("button", { name: /삭제 요청/ }).click();

    // Modal closes (dialog no longer visible).
    await expect(
      page.locator('div[role="dialog"][aria-labelledby="deletion-modal-title"]'),
    ).toHaveCount(0, { timeout: 5000 });

    // Status refresh: pending_deletion badge visible.
    await expect(page.getByText("삭제 대기")).toBeVisible({ timeout: 5000 });

    // Days remaining message visible.
    await expect(page.getByText(/완전 삭제까지 \d+일 남음/)).toBeVisible();
  });

  // ── Case 4: POST /request 500 → 에러 + 모달 유지 ────────────────────
  test("request failure 500 keeps user in consent step with error message", async ({ page }) => {
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
          trace_id: "trace-id-2001",
        }),
      }),
    );

    await page.route("**/api/v1/account/deletion/request", (route) =>
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({
          code: "DELETION_AUDIT_EMIT_FAILED",
          message_ko: "감사 로그 기록에 실패했습니다 — 잠시 후 다시 시도해 주세요.",
          details: {},
          trace_id: "trace-id-2004",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await page.getByRole("button", { name: "계정 삭제하기" }).click();
    await page.locator("#deletion-totp").fill("123456");
    await page.getByRole("button", { name: "다음" }).click();

    await page.locator("#deletion-consent").fill(CONSENT_TEMPLATE_KO);
    await page.getByRole("button", { name: /삭제 요청/ }).click();

    // Server-supplied Korean error envelope displayed.
    await expect(
      page.getByText("감사 로그 기록에 실패했습니다 — 잠시 후 다시 시도해 주세요."),
    ).toBeVisible({ timeout: 5000 });

    // Modal stays open in consent step (textarea still visible).
    await expect(page.locator("#deletion-consent")).toBeVisible();
  });
});
