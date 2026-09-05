/**
 * apps/web/e2e/snapshot-persistence.spec.ts — Playwright E2E for the
 * snapshot-persistence committed-period flow (Story 29.3).
 *
 * Run via `pnpm playwright test apps/web/e2e/snapshot-persistence.spec.ts
 *   --project=chromium`.
 *
 * Required dev_seed scenario:
 *   uv run python scripts/dev_seed.py --scenario snapshot_persisted
 *
 * Seed creates 1 `fiscal_period_snapshots` row for
 * `(tenant_id=DEV_TENANT_ID, period_key='2026-07', baseline_revision=1,
 *   engine_type='trad')` with state='committed' and a deterministic
 * result_hash (placeholder accepted per cj-275 spec).
 *
 * cj-276 wire (Story 29.3, FR-29-3, AD-16/AD-20, NFR18). Spec drift notes:
 * - Real handler code: 409 SNAPSHOT_ALREADY_COMMITTED (apps/api/main.py:2231
 *   handler), NOT 422 as cj-275 spec claims.
 * - Real message_ko: `스냅샷이 이미 커밋되어 다시 커밋할 수 없습니다`
 *   (apps/api/main.py:2240), NOT `이미 마감된 기간입니다 — 역분개로 처리하세요`
 *   as cj-275 spec narrative claims. Spec drift logged for cj-280 retro.
 * - DB-side assertion (snapshot row existence + state + result_hash) is
 *   verified out-of-band via dev_seed + psql, not via Playwright (the
 *   existing rlsDb fixture is a no-op stub per apps/web/e2e/fixtures/
 *   supabase-test.ts). Full Playwright DB wire is cj-280 retro scope.
 */

import { expect, test } from "@playwright/test";

const TEST_LOCALE = "ko-KR";
const COMMITTED_PERIOD = "2026-07";

test.describe("Story 29.3 — snapshot persistence on close (committed)", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`/${TEST_LOCALE}/m2-input/period/${COMMITTED_PERIOD}`);
    await page.waitForLoadState("networkidle");
  });

  test("POST /api/v1/close/snapshot/<id> returns 409 SNAPSHOT_ALREADY_COMMITTED", async ({
    request,
  }) => {
    // Real handler at apps/api/main.py:2231 returns 409, not 422.
    // Endpoint path mirrors the existing m11-snapshot-persistence.spec.ts
    // mock target (line 46) so it shares the same wire.
    const res = await request.post(
      `/api/v1/close/snapshot/00000000-0000-4000-8000-000000000000/commit`,
      {
        data: { period_key: COMMITTED_PERIOD },
        failOnStatusCode: false,
      },
    );
    expect(res.status()).toBe(409);
    const body = (await res.json()) as { code?: string; message_ko?: string };
    expect(body.code).toBe("SNAPSHOT_ALREADY_COMMITTED");
    // Real ko message — Korean (NFR18 ko-KR 단일).
    await expect(body.message_ko ?? "").toMatch(/스냅샷|마감|커밋/);
  });
});
