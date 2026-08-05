// apps/web/tailwind.config.ts — Tailwind 4 content paths
// Story 0.5 — T1.3 (AC #1)
//
// Note: Tailwind 4 is CSS-first (@theme in globals.css). This config file
// only declares content scanning + exposes hooks for IDE IntelliSense.
// Design tokens (colors / spacing / radius) live in app/globals.css via
// `@theme` block (shadcn convention).

import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./hooks/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};

export default config;
