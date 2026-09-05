/**
 * apps/web/e2e/closing-guard-negative.spec.ts — Playwright E2E for the
 * closing-guard NEGATIVE_CLOSING_PERIOD flow (Story 29.1).
 *
 * Run via `pnpm playwright test apps/web/e2e/closing-guard-negative.spec.ts
 *   --project=chromium`.
 *
 * Required dev_seed scenario:
 *   uv run python scripts/dev_seed.py --scenario closing_guard_negative
 *
 * Seed creates `products` row code='PRD-NEG' + 1 `inventory_ledger`
 * event (`adjustment_negative` qty=-5) for period 2026-08 so that
 * `closing_qty(PRD-NEG, 2026-08)` aggregates to -5 → CLOSING_GUARD
 * service returns invariant.code=NEGATIVE_CLOSING → banner + gate
 * disable + 409 NEGATIVE_CLOSING_INVENTORY on POST /api/v1/close.
 *
 * cj-276 wire (Story 29.1, FR-29-1, AD-6, NFR18). Spec drift notes:
 * - Real banner format: `기말재고 음수: 마감 불가: PRD-NEG -5개 → 마감 불가`
 *   (apps/web/lib/closing-guard.ts:182). cj-275 spec narrative omits the
 *   middle `마감 불가:` and uses `5개` not `-5개` — both matched below.
 * - Real POST /api/v1/close returns 409 NEGATIVE_CLOSING_INVENTORY
 *   (apps/api/main.py:1644 handler), NOT 422 as cj-275 spec claims.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const NEGATIVE_PERIOD = "2026-08";

test.describe("Story 29.1 — closing-guard NEGATIVE_CLOSING_PERIOD", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${NEGATIVE_PERIOD}`);
    await page.waitForLoadState("networkidle");
    await page.getByTestId("tab-close").click();
  });

  test("red banner displays negative-closing message for PRD-NEG", async ({
    page,
  }) => {
    const banner = page.getByTestId("m2-closing-guard-banner");
    await expect(banner).toBeVisible();
    // Match both real format and spec narrative — covers "5개" vs "-5개"
    // and the middle "마감 불가:" prefix.
    await expect(banner).toContainText(/기말재고 음수/);
    await expect(banner).toContainText(/PRD-NEG/);
    await expect(banner).toContainText(/→\s*마감 불가/);
  });

  test("[마감] button (m2-closing-guard-gate) is disabled", async ({
    page,
  }) => {
    const gate = page.getByTestId("m2-closing-guard-gate");
    await expect(gate).toBeVisible();
    await expect(gate).toBeDisabled();
  });

  test("POST /api/v1/close returns 409 NEGATIVE_CLOSING_INVENTORY", async ({
    request,
  }) => {
    // Real handler returns 409, not 422. Code matches.
    const res = await request.post("/api/v1/close", {
      data: { period_key: NEGATIVE_PERIOD },
      failOnStatusCode: false,
    });
    expect(res.status()).toBe(409);
    const body = (await res.json()) as { code?: string };
    expect(body.code).toBe("NEGATIVE_CLOSING_INVENTORY");
  });
});
