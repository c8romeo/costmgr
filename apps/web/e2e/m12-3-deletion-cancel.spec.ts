/**
 * apps/web/e2e/m12-3-deletion-cancel.spec.ts — Playwright E2E for M12 account deletion cancel flow.
 *
 * Story 12.3 — T7 follow-up sprint (mirror 12-5 T6 atomic pattern).
 * 4 of 16 E2E scenarios — cancel subset.
 * Run via `pnpm playwright test apps/web/e2e/m12-3-deletion-cancel.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_cancel_button_visible_only_when_pending_deletion
 *      - status='active' → [취소하기] 버튼 NOT visible; status='pending_deletion' → [취소하기] visible.
 *   2. test_cancel_deletion_happy_path_refreshes_status_to_active
 *      - status='pending_deletion' → [취소하기] 클릭 → POST /cancel 200 → status refresh to 'active'.
 *   3. test_cancel_failure_403_shows_korean_error_and_keeps_pending_status
 *      - [취소하기] 클릭 → POST /cancel 403 → "취소 처리에 실패했습니다" 에러 + status='pending_deletion' 유지.
 *   4. test_cancel_button_disabled_during_request
 *      - [취소하기] 클릭 후 in-flight request 동안 버튼 disabled (t("cancelling") label).
 *
 * CR 12-5 L3 3-layer TOTP defense (cancel path): route require_role("owner") + service guard
 * (status='pending_deletion' required, no token replay) + handler audit-first BEFORE state revert.
 *
 * Story 0.5 wired the Playwright runner + Supabase test fixtures.
 * Korean (ko-KR) locale + manufacturing tenant.
 *
 * CR 11-3 honest-DEFER discipline 9번째 epic 연속:
 *   - Reuses page.route() interception pattern (Story 11.1, 12.1, 12.5).
 *   - Korean ko-KR.json strings as the canonical assertion target (CR 11-4 D-002).
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";

const SAMPLE_TENANT_ID = "11111111-1111-1111-1111-111111111111";
const SAMPLE_CONSENT_ID = "22222222-2222-2222-2222-222222222222";
const SAMPLE_SCHEDULED_FOR = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();

function buildActiveStatusBody(): Record<string, unknown> {
  return {
    tenant_id: SAMPLE_TENANT_ID,
    status: "active",
    deletion_requested_at: null,
    deletion_requested_by_user_id: null,
    deletion_consent_id: null,
    deletion_scheduled_for: null,
    trace_id: "trace-id-3001",
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
    trace_id: "trace-id-3002",
  };
}

test.describe("M12 account deletion — cancel flow", () => {
  // ── Case 1: [취소하기] visibility based on FSM status ──────────────
  test("cancel button visible only when pending deletion", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildActiveStatusBody()),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    // Status='active' → [취소하기] NOT visible.
    await expect(page.getByRole("button", { name: "취소하기" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "계정 삭제하기" })).toBeVisible();

    // Re-stub /status to pending_deletion + reload.
    await page.unroute("**/api/v1/account/deletion/status");
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildPendingStatusBody()),
      }),
    );
    await page.reload();
    await page.waitForLoadState("networkidle");

    // Status='pending_deletion' → [취소하기] visible, [계정 삭제하기] NOT visible.
    await expect(page.getByRole("button", { name: "취소하기" })).toBeVisible();
    await expect(page.getByRole("button", { name: "계정 삭제하기" })).toHaveCount(0);
  });

  // ── Case 2: cancel happy path → status refresh to active ───────────
  test("cancel deletion happy path refreshes status to active", async ({ page }) => {
    // First /status returns pending_deletion (initial).
    // After /cancel success, refreshStatus() called → second /status returns active.
    let statusCallCount = 0;
    await page.route("**/api/v1/account/deletion/status", (route) => {
      statusCallCount += 1;
      const body =
        statusCallCount === 1 ? buildPendingStatusBody() : buildActiveStatusBody();
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(body),
      });
    });

    await page.route("**/api/v1/account/deletion/cancel", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          tenant_id: SAMPLE_TENANT_ID,
          status: "active",
          deletion_scheduled_for: null,
          trace_id: "trace-id-3003",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    // Initial: pending_deletion badge + cancel button.
    await expect(page.getByText("삭제 대기")).toBeVisible();
    await expect(page.getByRole("button", { name: "취소하기" })).toBeVisible();

    // Click [취소하기].
    await page.getByRole("button", { name: "취소하기" }).click();

    // After cancel + refresh: status='active' badge visible.
    await expect(page.getByText("활성")).toBeVisible({ timeout: 5000 });

    // Cancel button no longer visible; [계정 삭제하기] now visible.
    await expect(page.getByRole("button", { name: "취소하기" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "계정 삭제하기" })).toBeVisible();
  });

  // ── Case 3: cancel failure 403 → Korean error + status unchanged ───
  test("cancel failure 403 shows Korean error and keeps pending status", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildPendingStatusBody()),
      }),
    );

    await page.route("**/api/v1/account/deletion/cancel", (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          code: "FORBIDDEN_ROLE",
          message_ko: "owner 권한 필요",
          details: {},
          trace_id: "trace-id-3004",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    await expect(page.getByText("삭제 대기")).toBeVisible();
    await page.getByRole("button", { name: "취소하기" }).click();

    // Korean error envelope displayed.
    await expect(page.getByText("owner 권한 필요")).toBeVisible({ timeout: 5000 });

    // Status unchanged: still pending_deletion + cancel button still visible.
    await expect(page.getByText("삭제 대기")).toBeVisible();
    await expect(page.getByRole("button", { name: "취소하기" })).toBeVisible();
  });

  // ── Case 4: cancel in-flight → button disabled (cancelling label) ──
  test("cancel button shows cancelling label and is disabled during in-flight request", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildPendingStatusBody()),
      }),
    );

    // Slow /cancel endpoint (3-second delay) → button shows "취소 중..." and disabled.
    await page.route("**/api/v1/account/deletion/cancel", async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 3000));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          tenant_id: SAMPLE_TENANT_ID,
          status: "active",
          deletion_scheduled_for: null,
          trace_id: "trace-id-3005",
        }),
      });
    });

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    const cancelButton = page.getByRole("button", { name: "취소하기" });
    await expect(cancelButton).toBeVisible();

    // Click + immediately check that button is disabled and shows "취소 중..." label.
    await cancelButton.click();
    await expect(cancelButton).toBeDisabled();
    await expect(page.getByRole("button", { name: "취소 중..." })).toBeVisible();
  });
});
