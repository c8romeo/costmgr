// apps/web/vitest.config.ts — Vitest config (jsdom + MSW + RTL globals + React plugin)
// Story 0.5 — T4.2 (AC #4)
//
// Test runner: vitest 4.x with jsdom environment for DOM-touching component
// tests. The @vitejs/plugin-react plugin provides JSX + automatic runtime
// for tsx test files (otherwise rolldown fails JSX parsing).
//
// cj-268: Replaced `__dirname` with `import.meta.dirname` (ESM-compatible).
// `apps/web/package.json` declares `"type": "module"`, so config files are
// loaded as ESM. `__dirname` is not defined in ESM scope (Node 24.18.0 CI
// runner enforces strict ESM resolution, unlike Vite's bundler which
// substitutes `__dirname` on Windows). Using `import.meta.dirname` works
// on both Windows + Linux runners.

import react from "@vitejs/plugin-react";
import path from "node:path";
import { defineConfig } from "vitest/config";

const r = (p: string) => path.resolve(import.meta.dirname, p);

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./test/setup.ts"],
    include: ["__tests__/**/*.{test,spec}.{ts,tsx}"],
    exclude: ["node_modules", ".next", "e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["html", "json-summary"],
      include: ["components/**/*.{ts,tsx}", "lib/**/*.{ts,tsx}", "hooks/**/*.{ts,tsx}"],
      exclude: ["__tests__/**", "**/*.d.ts", "**/*.config.{ts,mjs}"],
    },
  },
  resolve: {
    alias: {
      "@": r("./"),
    },
  },
});
