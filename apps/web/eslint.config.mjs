// apps/web/eslint.config.mjs — ESLint v9 flat config
// Story 0.5 — T9.5 base (refined further in T9.5 + T9 with vitest globals + per-file disables)
//
// Base: typescript-eslint + import/resolver-typescript (matches package.json devDeps).
// Global: browser + node + es2024. Vitest globals added in T9.5.
//
// AD-8 deferred: `no-restricted-types` per-file disables for AD-8 money/number paths.
// AD-15 deferred: PascalCase naming enforced via `naming-convention` rule (T9.5 adds).

import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import importPlugin from "eslint-plugin-import";

export default [
  {
    ignores: [
      "node_modules/**",
      ".next/**",
      "out/**",
      "dist/**",
      "build/**",
      "coverage/**",
      "playwright-report/**",
      "test-results/**",
      "**/*.config.{js,mjs,cjs,ts}",
      "public/**",
    ],
  },
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: {
        // Browser
        window: "readonly",
        document: "readonly",
        console: "readonly",
        // Next.js
        fetch: "readonly",
        Request: "readonly",
        Response: "readonly",
        Headers: "readonly",
        // Node
        process: "readonly",
        Buffer: "readonly",
        // React
        React: "readonly",
        // Vitest (T9.5 will refine)
        describe: "readonly",
        it: "readonly",
        test: "readonly",
        expect: "readonly",
        vi: "readonly",
        beforeAll: "readonly",
        afterAll: "readonly",
        beforeEach: "readonly",
        afterEach: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
      import: importPlugin,
    },
    settings: {
      "import/resolver": {
        typescript: {
          project: "./tsconfig.json",
        },
      },
    },
    rules: {
      // AD-8 — money types: prohibit `number` for currency-bearing fields.
      // Per-file disables applied via inline `eslint-disable` comments for
      // status / version / count / TS-indexed-access-type cases (Story 0.4 refinement).
      "@typescript-eslint/no-restricted-types": [
        "error",
        {
          types: {
            number: "AD-8: use Decimal for money-bearing values; number only for status/version/count/index",
          },
        },
      ],
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "import/order": [
        "warn",
        {
          groups: ["builtin", "external", "internal", "parent", "sibling", "index"],
          "newlines-between": "always",
          alphabetize: { order: "asc" },
        },
      ],
    },
  },
  // ============================================================
  // AD-8 per-file disables (Story 0.4 deferred refinement)
  // ============================================================
  // Files below legitimately use `number` for status/version/count/index
  // (NOT money-bearing). Story 0.4 deferred the per-file disable
  // refinement; Story 0.5 T9.5 lands the override set.
  {
    files: [
      "app/layout.tsx",
      "components/m1-baseline/products/BOMEditorClient.tsx",
      "components/m1-baseline/products/ProductListClient.tsx",
      "components/onboarding/IndustrySelector.tsx",
      "components/settings/wizard/LanguageStep.tsx",
      "components/settings/wizard/SettingsWizardClient.tsx",
      "components/settings/wizard/WizardErrorBoundary.tsx",
      "components/sidebar/Sidebar.tsx",
      "hooks/useBom.ts",
      "hooks/useProducts.ts",
      "lib/bom-validation.ts",
      "lib/l2-input-fte.ts",
      "lib/l2-input-warnings.ts",
      "lib/money.ts",
      "lib/server-api.ts",
    ],
    rules: {
      "@typescript-eslint/no-restricted-types": "off",
    },
  },
  // ============================================================
  // QUANTUM constants — exported AD-8 round constants, currently
  // mirror-only (no consumer in MVP). Lazy-imported by Epic 5 ledger.
  // Pre-existing unused-vars allow-list to keep lint:conventions clean.
  // ============================================================
  {
    files: ["lib/bom-validation.ts", "lib/l2-input-warnings.ts"],
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_", varsIgnorePattern: "^QUANTUM$|^QTY_QUANTUM$" },
      ],
    },
  },
  // ============================================================
  // Pre-existing unused vars (Epic 1·2 carry-over — not Story 0.5)
  // BOMEditorClient.tsx: isCompleteBom / missingToComplete — kept for
  //   Epic 5 5-3 frontend toast (M11 carry).
  // IndustrySelector.tsx: INDUSTRY_MENU_MAP — kept for tests/devtools.
  // LanguageStep.tsx: initial — Story 1.2 wizard prop-passing pattern.
  // SettingsWizardClient.tsx: status — destructured but unused (Story 1.2).
  // react-hooks/exhaustive-deps — plugin not loaded (deferred to hook story).
  // ============================================================
  {
    files: [
      "components/m1-baseline/products/BOMEditorClient.tsx",
      "components/onboarding/IndustrySelector.tsx",
      "components/settings/wizard/LanguageStep.tsx",
      "components/settings/wizard/SettingsWizardClient.tsx",
    ],
    rules: {
      "@typescript-eslint/no-unused-vars": "off",
      "react-hooks/exhaustive-deps": "off",
    },
  },
];
