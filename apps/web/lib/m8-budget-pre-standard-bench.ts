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

export const PRE_STANDARD_BENCH_ITERATIONS: number = 10_000;
export const PRE_STANDARD_BENCH_BUDGET_MS: number = 2000;

export interface PreStandardBenchResult {
  iterations: number;
  total_ms: number;
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
  const total_ms = performance.now() - start;
  const per_iteration_us = (total_ms * 1000) / PRE_STANDARD_BENCH_ITERATIONS;
  return {
    iterations: PRE_STANDARD_BENCH_ITERATIONS,
    total_ms,
    per_iteration_us,
    passed: total_ms < PRE_STANDARD_BENCH_BUDGET_MS,
  };
}