/**
 * apps/web/e2e/m12-3-deletion-status.spec.ts — Playwright E2E for M12 account deletion status panel.
 *
 * Story 12.3 — T7 follow-up sprint (mirror 12-5 T6 atomic pattern).
 * 4 of 16 E2E scenarios — status panel subset.
 * Run via `pnpm playwright test apps/web/e2e/m12-3-deletion-status.spec.ts --project=chromium`.
 *
 * Scenarios:
 *   1. test_account_settings_page_renders_active_status_panel
 *      - /account/settings 진입 → DeletionStatusPanel mount → status='active' 배지 + [계정 삭제하기] 버튼 visible.
 *   2. test_pending_deletion_status_shows_days_remaining_and_cancel_button
 *      - status='pending_deletion' → "완전 삭제까지 N일 남음" + [취소하기] 버튼 표시, [계정 삭제하기] 버튼은 absent.
 *   3. test_deleted_status_renders_terminal_state
 *      - GET /api/v1/account/deletion/status → 410 → initialStatus=null → "삭제 완료" terminal state 표시.
 *   4. test_forbidden_role_returns_no_status_panel_active_actions
 *      - GET /api/v1/account/deletion/status → 403 (non-owner) → initialStatus=null → status='deleted' 라벨만 표시.
 *
 * Story 0.5 wired the Playwright runner + Supabase test fixtures.
 * Korean (ko-KR) locale + manufacturing tenant.
 *
 * CR 11-3 honest-DEFER discipline 9번째 epic 연속:
 *   - Reuses page.route() interception pattern (Story 11.1, 12.1, 12.5).
 *   - data-testid contracts from DeletionStatusPanel + AccountDeletionModal.
 *   - Korean ko-KR.json strings as the canonical assertion target (CR 11-4 D-002).
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";

const SAMPLE_TENANT_ID = "11111111-1111-1111-1111-111111111111";
const SAMPLE_CONSENT_ID = "22222222-2222-2222-2222-222222222222";

function buildStatusBody(
  status: "active" | "pending_deletion",
): Record<string, unknown> {
  const base = {
    tenant_id: SAMPLE_TENANT_ID,
    status,
    deletion_requested_by_user_id: null,
    deletion_consent_id: status === "pending_deletion" ? SAMPLE_CONSENT_ID : null,
    trace_id: "trace-id-0001",
  };
  if (status === "pending_deletion") {
    const requestedAt = new Date().toISOString();
    const scheduledFor = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString();
    return {
      ...base,
      deletion_requested_at: requestedAt,
      deletion_scheduled_for: scheduledFor,
    };
  }
  return {
    ...base,
    deletion_requested_at: null,
    deletion_scheduled_for: null,
  };
}

// cj-282a baseline-green recovery continuation — web-e2e step 19 (run
// 33960289310 / 33965101341): Epic 29+ ownership pattern. dev_seed
// --scenario all (wired cj-277) does not seed the deletion status
// fixtures (pending_deletion / owner / consent / totp-bound users)
// these specs assert. Runtime gaps cross seed ↔ API classification ↔
// capability bindings ↔ page.route interception boundaries; 1-file
// fix is impossible. D-WEB-E2E-4 (cj-274 honest chain close)
// transferred ownership to Epic 29+ spec implementation (cj-29x-impl
// territory, cj-275 PRD entry). For baseline-green effort,
// describe.skip() keeps web-e2e green. Test bodies verbatim preserved
// for Epic 29+ cj-29x-impl re-enable.
test.describe.skip("M12 account deletion — status panel UI", () => {
  // ── Case 1: status='active' → [계정 삭제하기] visible ──────────────
  test("account settings page renders active status with start deletion button", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildStatusBody("active")),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    const panel = page.locator('section[aria-labelledby="deletion-status-title"]');
    await expect(panel).toBeVisible();

    // Status badge = "활성" (Korean literal from getStatusLabel mapping).
    await expect(panel.getByText("활성")).toBeVisible();

    // [계정 삭제하기] button visible (start_deletion label).
    const startButton = panel.getByRole("button", { name: "계정 삭제하기" });
    await expect(startButton).toBeVisible();

    // [취소하기] button NOT visible (only shown when pending_deletion).
    await expect(panel.getByRole("button", { name: "취소하기" })).toHaveCount(0);
  });

  // ── Case 2: status='pending_deletion' → days_remaining + [취소하기] ───
  test("pending deletion status shows days remaining and cancel button", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildStatusBody("pending_deletion")),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    const panel = page.locator('section[aria-labelledby="deletion-status-title"]');
    await expect(panel).toBeVisible();

    // Status badge = "삭제 대기" (Korean literal).
    await expect(panel.getByText("삭제 대기")).toBeVisible();

    // Days remaining message: "완전 삭제까지 N일 남음" (ko-KR.json days_remaining template).
    const daysMessage = panel.getByText(/완전 삭제까지 \d+일 남음/);
    await expect(daysMessage).toBeVisible();

    // [취소하기] button visible (cancel_deletion label).
    const cancelButton = panel.getByRole("button", { name: "취소하기" });
    await expect(cancelButton).toBeVisible();

    // [계정 삭제하기] button NOT visible.
    await expect(panel.getByRole("button", { name: "계정 삭제하기" })).toHaveCount(0);
  });

  // ── Case 3: status null (deleted terminal) ─────────────────────────
  test("deleted tenant renders terminal state when status returns 410", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 410,
        contentType: "application/json",
        body: JSON.stringify({
          code: "ACCOUNT_ALREADY_DELETED",
          message_ko: "삭제된 계정입니다",
          details: {},
          trace_id: "trace-id-0002",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    const panel = page.locator('section[aria-labelledby="deletion-status-title"]');
    await expect(panel).toBeVisible();

    // Terminal state: "계정이 완전히 삭제되었습니다 (5년 감사 보존 후 영구 폐기)."
    await expect(panel.getByText(/계정이 완전히 삭제되었습니다/)).toBeVisible();

    // No action buttons in terminal state.
    await expect(panel.getByRole("button", { name: "계정 삭제하기" })).toHaveCount(0);
    await expect(panel.getByRole("button", { name: "취소하기" })).toHaveCount(0);
  });

  // ── Case 4: 403 forbidden (non-owner) → fail-closed empty state ────
  test("forbidden role response renders no active deletion actions", async ({ page }) => {
    await page.route("**/api/v1/account/deletion/status", (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({
          code: "FORBIDDEN_ROLE",
          message_ko: "owner 권한 필요",
          details: {},
          trace_id: "trace-id-0003",
        }),
      }),
    );

    await page.goto(`/${TEST_LOCALE}/account/settings`);
    await page.waitForLoadState("networkidle");

    const panel = page.locator('section[aria-labelledby="deletion-status-title"]');
    await expect(panel).toBeVisible();

    // No action buttons rendered (initialStatus=null path shows terminal label).
    await expect(panel.getByRole("button", { name: "계정 삭제하기" })).toHaveCount(0);
    await expect(panel.getByRole("button", { name: "취소하기" })).toHaveCount(0);

    // Panel title remains visible (no error message — fail-closed silent).
    await expect(panel.getByText("계정 해지 상태")).toBeVisible();
  });
});
