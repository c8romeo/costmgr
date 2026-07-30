/**
 * Root ESLint flat config — applies to all TS code.
 *
 * Story 0.4 — AD-8 + AD-15 cross-language conventions.
 *
 * ESLint v9 uses flat config (eslint.config.js/.mjs). Legacy .eslintrc.cjs
 * is deprecated.
 *
 * Key rules:
 *   - camelcase on TS variables/functions
 *   - @typescript-eslint/naming-convention enforces PascalCase for type-like
 *   - no-restricted-syntax blocks `import time` / `import { Datetime }`
 *   - no-restricted-types blocks `number` for money (apps/web override)
 */
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import importPlugin from "eslint-plugin-import";

/** @type {import("eslint").Linter.Config[]} */
export default [
  // ── Global ignores ────────────────────────────────────────
  {
    ignores: [
      "**/node_modules/**",
      "**/.next/**",
      "**/dist/**",
      "**/build/**",
      "**/.venv/**",
      "**/scripts/**",
      "**/*.config.js",
      "**/*.config.cjs",
      "**/*.config.mjs",
      "**/pnpm-lock.yaml",
    ],
  },

  // ── Python-only configs (intentionally empty; ruff handles Python) ──

  // ── Default TS / JS rules ────────────────────────────────
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 2022,
        sourceType: "module",
        ecmaFeatures: { jsx: true },
      },
      globals: {
        // Browser
        window: "readonly",
        document: "readonly",
        console: "readonly",
        // Node
        process: "readonly",
        global: "readonly",
        Buffer: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
      import: importPlugin,
    },
    settings: {
      "import/resolver": {
        typescript: true,
        node: true,
      },
    },
    rules: {
      // ── AD-15 Naming ────────────────────────────────
      camelcase: ["error", { properties: "never", allow: ["^_"] }],
      "@typescript-eslint/naming-convention": [
        "error",
        { selector: "typeLike", format: ["PascalCase"] },
        { selector: "variable", format: ["camelCase", "UPPER_CASE", "PascalCase"] },
        { selector: "function", format: ["camelCase", "PascalCase"] },
      ],

      // ── AD-15 Time ──────────────────────────────────
      "no-restricted-syntax": [
        "error",
        {
          selector: "ImportDeclaration[source.value='time']",
          message:
            "AD-15 forbids `import time` — use ISO-8601 strings via Date or Temporal.",
        },
        {
          selector: "ImportDeclaration[source.value='datetime']",
          message:
            "AD-15 forbids `import { Datetime }` — use ISO-8601 strings via Date or Temporal.",
        },
        {
          selector: "ImportDeclaration[source.value=/datetime$/]",
          message:
            "AD-15 forbids `*-datetime` imports — use ISO-8601 strings via Date or Temporal.",
        },
      ],

      // ── AD-8 Money (use TS plugin equivalent; ESLint v9 removed no-restricted-types) ──
      "@typescript-eslint/no-restricted-types": [
        "error",
        {
          types: {
            number:
              "AD-8 forbids `number` for money. Use `bigint` (KRW) or `string` (USD decimal.js).",
          },
        },
      ],

      // ── General hygiene ─────────────────────────────
      "no-console": ["warn", { allow: ["warn", "error", "info"] }],
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "import/order": ["warn", { "newlines-between": "always" }],
    },
  },

  // ── apps/web/lib/money.ts: `number` allowed as INPUT ONLY ──
  // The signatures of toKRW/toUSD accept number|bigint for ergonomics,
  // but the RESULT types are bigint/string. ESLint cannot distinguish
  // input vs output, so we disable the rule for this single file.
  {
    files: ["apps/web/lib/money.ts"],
    rules: {
      "@typescript-eslint/no-restricted-types": "off",
    },
  },

  // ── tests: relaxed rules ──────────────────────────────────
  {
    files: ["**/*.test.ts", "**/*.test.tsx", "**/tests/**/*.{ts,tsx}"],
    rules: {
      "no-console": "off",
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
];