// apps/web/playwright.config.ts — Playwright E2E config
// Story 0.5 — T5.2 (AC #5)
//
// Test runner: chromium-only smoke subset per Story 0.5 spec.
// webServer: `pnpm dev` with reuseExistingServer on local, fresh on CI.

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
    command: "pnpm dev",
    url: "http://localhost:3000",
    reuseExistingServer: !isCI,
    timeout: 30_000,
    // cj-270 (D-CI-FUNC-5 E2E BATCH): env-driven gate bypass 신호.
    // page.tsx 의 `isE2E = Boolean(process.env.CI) ||
    // process.env.E2E_TENANT_ID != null` 체크가 Next.js dev server
    // 안에서 평가되므로, webServer 가 spawn 한 `pnpm dev` 프로세스에
    // 명시적으로 propagate 해야 한다. 로컬 PowerShell 에서 CI 안
    // set 한 경우에도 reliable.
    env: {
      ...process.env,
      CI: process.env.CI ?? "true",
      E2E_TENANT_ID: process.env.E2E_TENANT_ID ?? "playwright-e2e",
    },
  },
});
