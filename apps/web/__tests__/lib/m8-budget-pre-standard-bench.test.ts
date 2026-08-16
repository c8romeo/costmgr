// apps/web/__tests__/lib/m8-budget-pre-standard-bench.test.ts — Story 8.3
//
// Performance benchmark parity test (TS ↔ Python pure kernel).
// Drift caught between:
// - `tests/api/m8_budget/test_budget_pre_standard_bench.py` (Python pure kernel)
// - `apps/web/lib/m8-budget-pre-standard-bench.ts` (TS mirror)
//
// Both should complete 10,000 iterations under 2000ms budget.

import { describe, expect, it } from "vitest";

import {
  PRE_STANDARD_BENCH_BUDGET_MS,
  PRE_STANDARD_BENCH_ITERATIONS,
  runPreStandardBenchTS,
} from "../../lib/m8-budget-pre-standard-bench";

describe("m8-budget-pre-standard perf bench — constants", () => {
  it("parity 1: iterations == 10000 (PRD §NFR6 perf budget)", () => {
    expect(PRE_STANDARD_BENCH_ITERATIONS).toBe(10_000);
  });

  it("parity 2: budget_ms == 2000 (PRD §NFR6 perf budget)", () => {
    expect(PRE_STANDARD_BENCH_BUDGET_MS).toBe(2000);
  });
});

describe("m8-budget-pre-standard perf bench — runtime", () => {
  it("runtime: 10,000 iterations complete under 2000ms", () => {
    const result = runPreStandardBenchTS();
    expect(result.iterations).toBe(PRE_STANDARD_BENCH_ITERATIONS);
    expect(result.total_ms).toBeLessThan(PRE_STANDARD_BENCH_BUDGET_MS);
    expect(result.passed).toBe(true);
  });
});