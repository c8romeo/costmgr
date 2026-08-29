// apps/web/lib/m8-budget-pre-standard-bench.ts — Story 8.3
//
// Performance benchmark for computePreStandardCostTS.
// Mirrors `tests/api/m8_budget/test_budget_pre_standard_bench.py`.
//
// Bench scope: 10,000 iterations of computePreStandardCostTS on realistic input.
// Asserts total < 2000 ms (PRD §NFR6 perf budget, TS-side parity).

import {
  computePreStandardCostTS,
  type BudgetPreStandardInputs,
} from "./m8-budget-pre-standard";

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const PRE_STANDARD_BENCH_ITERATIONS: number = 10_000;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const PRE_STANDARD_BENCH_BUDGET_MS: number = 2000;

export interface PreStandardBenchResult {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  iterations: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total_ms: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  per_iteration_us: number;
  passed: boolean;
}

/**
 * Run the TS-side computePreStandardCostTS benchmark.
 * Returns an object with iterations, total_ms, per_iteration_us, passed.
 */
export function runPreStandardBenchTS(
  inputs: BudgetPreStandardInputs = {
    material_unit_cost: "1000",
    labor_unit_cost: "50000",
    overhead_rate: "12.5",
    material_qty: "10",
    labor_hours: "8",
  },
): PreStandardBenchResult {
  const start = performance.now();
  for (let i = 0; i < PRE_STANDARD_BENCH_ITERATIONS; i += 1) {
    computePreStandardCostTS(inputs);
  }
  // eslint-disable-next-line camelcase
  const total_ms = performance.now() - start;
  // eslint-disable-next-line camelcase
  const per_iteration_us = (total_ms * 1000) / PRE_STANDARD_BENCH_ITERATIONS;
  return {
    iterations: PRE_STANDARD_BENCH_ITERATIONS,
    // eslint-disable-next-line camelcase
    total_ms,
    // eslint-disable-next-line camelcase
    per_iteration_us,
    // eslint-disable-next-line camelcase
    passed: total_ms < PRE_STANDARD_BENCH_BUDGET_MS,
  };
}