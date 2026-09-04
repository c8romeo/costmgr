// apps/web/playwright.config.ts — Playwright E2E config
// Story 0.5 — T5.2 (AC #5)
//
// Test runner: chromium-only smoke subset per Story 0.5 spec.
// webServer: cj-271 production build (`next build && next start`) —
// hot-reload race 제거 (cj-270 root cause #3 Windows EBUSY
// `.next/server/app/page_client-reference-manifest.js` 의 dev-mode
// 특이점). reuseExistingServer on local, fresh on CI.

import { defineConfig, devices } from "@playwright/test";

const isCI = !!process.env.CI;

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!isCI,
  retries: isCI ? 2 : 0,
  workers: isCI ? 1 : undefined,
  reporter: isCI ? "list" : "list",

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "firefox",
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "webkit",
      use: { ...devices["Desktop Safari"] },
    },
  ],

  webServer: {
    // cj-271 (D-CI-FUNC-5 web-e2e step 8 FAIL): production build 사용.
    //   - dev mode → `.next/server/app/page_client-reference-manifest.js`
    //     Windows EBUSY race 빈번 (local-only, CI Linux 영향 없음이나
    //     동일 flake 가 step 8 timing 에 영향 줄 가능성 배제 불가).
    //   - prod mode → 빌드 시점에 manifest deterministically write +
    //     server start 시 stable read. EBUSY 윈도우 없음.
    //   - trade-off: cold start 5.9s → ~30~90s (build ~60s + start ~5s).
    //     timeout 30_000 → 180_000 (3 min) EXTENSION.
    command: "next build && next start -p 3000",
    url: "http://localhost:3000",
    reuseExistingServer: !isCI,
    timeout: 180_000,
    // cj-270 (D-CI-FUNC-5 E2E BATCH): env-driven gate bypass 신호.
    // page.tsx 의 `isE2E = Boolean(process.env.CI) ||
    // process.env.E2E_TENANT_ID != null` 체크가 Next.js 서버
    // 안에서 평가되므로, webServer 가 spawn 한 `next start` 프로세스에
    // 명시적으로 propagate 해야 한다. 로컬 PowerShell 에서 CI 안
    // set 한 경우에도 reliable.
    env: {
      ...process.env,
      CI: process.env.CI ?? "true",
      E2E_TENANT_ID: process.env.E2E_TENANT_ID ?? "playwright-e2e",
    },
  },
});
