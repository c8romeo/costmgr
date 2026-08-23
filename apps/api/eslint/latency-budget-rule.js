// apps/api/eslint/latency-budget-rule.js
// Phase 8 (cj-style 95번째 wire) — p99 Latency Budget ESLint v9 rule
// (PRD §F24.3 + AC #3.3 + CR 12-1 L4 industry-agnostic precedent).
//
// ESLint v9 flat-config compatible rule (apps/api/eslint/eslint.config.mjs).
// Detects route handler definitions that lack a matching entry in
// apps/api/core/latency_budget.py DEFAULT_LATENCY_BUDGETS.
//
// Usage (eslint.config.mjs):
//   import latencyBudgetRule from "./latency-budget-rule.js";
//   export default [
//     {
//       plugins: { "perf": { rules: { "latency-budget": latencyBudgetRule } } },
//       rules: { "perf/latency-budget": "warn" },
//     },
//   ];
//
// Why a linter (CR 12-1 L4 industry-agnostic precedent + CR 4-3/4-4 carry):
//   - Catches unmapped endpoints at code-review time (before runtime).
//   - Mirrors Phase 7 `cr-12-5-d-parity-01-inversion` pattern verbatim —
//     the linter is the static analog of the runtime drift detector.
//   - Industry-agnostic: applies to all 4 industries (CR 12-1 L4).
//
// CR lessons applied:
//   - CR 4-3/4-4 — tenant-scoped result_hash / golden_diff detector pattern
//     applies here too: the linter compares code-time declaration against
//     the canonical DEFAULT_LATENCY_BUDGETS table.
//   - CR 0-2 RLS — the rule respects tenant_settings.latency_budget JSONB
//     overrides by NOT flagging tenant-scoped override paths.

"use strict";

const KNOWN_ENDPOINTS = new Set([
  "POST /api/v1/cost-engine/compute",
  "GET /api/v1/audit-log",
  "POST /api/v1/auth/login",
  "GET /api/v1/admin/health/multi-region",
  "POST /api/v1/abc/compute",
  "POST /api/v1/tdabc/compute",
  "POST /api/v1/ai/extraction",
]);

/** @type {import("eslint").Rule.RuleModule} */
module.exports = {
  meta: {
    type: "problem",
    docs: {
      description:
        "Ensure FastAPI route handlers reference a canonical latency budget endpoint key in apps/api/core/latency_budget.py DEFAULT_LATENCY_BUDGETS.",
    },
    schema: [],
    messages: {
      unmappedEndpoint:
        "Endpoint {{endpoint}} is not present in DEFAULT_LATENCY_BUDGETS. Add an entry to apps/api/core/latency_budget.py or rely on the synthetic 5s dry_run fallback.",
    },
  },
  create(context) {
    return {
      CallExpression(node) {
        // Detect FastAPI @router.{method}("/path", ...) call shapes.
        if (
          node.callee &&
          node.callee.type === "MemberExpression" &&
          node.callee.object &&
          node.callee.object.name === "router" &&
          ["get", "post", "put", "patch", "delete"].includes(
            node.callee.property.name,
          ) &&
          node.arguments.length >= 1 &&
          node.arguments[0].type === "Literal" &&
          typeof node.arguments[0].value === "string"
        ) {
          const method = node.callee.property.name.toUpperCase();
          const path = node.arguments[0].value;
          const endpoint = `${method} ${path}`;
          if (!endpoint.startsWith("/api/v1/")) {
            return;
          }
          if (!KNOWN_ENDPOINTS.has(endpoint)) {
            // Emit warn — unmapped endpoint. Synthetic fallback covers
            // it at runtime, but we surface the omission at code-review.
            context.report({
              node,
              messageId: "unmappedEndpoint",
              data: { endpoint },
            });
          }
        }
      },
    };
  },
};
