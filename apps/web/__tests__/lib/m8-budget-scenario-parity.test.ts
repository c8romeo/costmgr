// apps/web/__tests__/lib/m8-budget-scenario-parity.test.ts — Story 8.1 (Epic 8)
//
// Cross-language parity test (Python pure kernel ↔ TS mirror).
// Drift caught between:
// - `packages/cost_engine/budget_period_key.py` (Python pure kernel)
// - `apps/web/lib/m8-budget-scenario.ts` (TS mirror)
//
// SSOT: the Python pure kernel. The TS mirror must match the Python
// verdict for the same input — drift here means the budget scenario
// panel would render a different virtual period key than the backend
// computes.
//
// Run via: `pnpm exec vitest run m8-budget-scenario-parity`

import { describe, expect, it } from "vitest";

import {
  deriveBudgetPeriodKeyTS,
  isValidRealPeriodKeyTS,
  isValidVirtualBudgetPeriodKeyTS,
  MVP_MAX_SCENARIOS_PER_TENANT,
  parseVirtualBudgetPeriodKeyTS,
  SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO,
  validateScenarioUniquenessTS,
} from "../../lib/m8-budget-scenario";

describe("m8-budget-scenario parity — isValidRealPeriodKeyTS", () => {
  it("parity 1: '2026-07' matches real pattern", () => {
    expect(isValidRealPeriodKeyTS("2026-07")).toBe(true);
  });

  it("parity 2: '2026-13' (invalid month) does NOT match", () => {
    expect(isValidRealPeriodKeyTS("2026-13")).toBe(false);
  });

  it("parity 3: '2026-07#B1' (virtual) does NOT match real pattern", () => {
    expect(isValidRealPeriodKeyTS("2026-07#B1")).toBe(false);
  });

  it("parity 4: '2026-7' (1-digit month) does NOT match real pattern", () => {
    expect(isValidRealPeriodKeyTS("2026-7")).toBe(false);
  });
});

describe("m8-budget-scenario parity — isValidVirtualBudgetPeriodKeyTS", () => {
  it("parity 1: '2026-07#B1' matches virtual pattern", () => {
    expect(isValidVirtualBudgetPeriodKeyTS("2026-07#B1")).toBe(true);
  });

  it("parity 2: '2026-07#B2' (scenario 2) matches virtual pattern but exceeds MVP", () => {
    // Virtual pattern matches, but MVP limit is enforced downstream.
    expect(isValidVirtualBudgetPeriodKeyTS("2026-07#B2")).toBe(true);
  });

  it("parity 3: '2026-07' (real key only) does NOT match virtual pattern", () => {
    expect(isValidVirtualBudgetPeriodKeyTS("2026-07")).toBe(false);
  });

  it("parity 4: '2026-07#B0' (zero scenario) does NOT match virtual pattern", () => {
    expect(isValidVirtualBudgetPeriodKeyTS("2026-07#B0")).toBe(false);
  });
});

describe("m8-budget-scenario parity — parseVirtualBudgetPeriodKeyTS", () => {
  it("parity 1: '2026-07#B1' parses to parts (real_period_key, scenario_index=1)", () => {
    const parts = parseVirtualBudgetPeriodKeyTS("2026-07#B1");
    expect(parts).toEqual({
      real_period_key: "2026-07",
      scenario_index: 1,
      scenario_suffix: "#B1",
    });
  });

  it("parity 2: invalid virtual key returns null", () => {
    expect(parseVirtualBudgetPeriodKeyTS("invalid")).toBeNull();
  });

  it("parity 3: '2026-07#B2' parses parts but exceeds MVP limit", () => {
    expect(parseVirtualBudgetPeriodKeyTS("2026-07#B2")).toBeNull();
  });
});

describe("m8-budget-scenario parity — deriveBudgetPeriodKeyTS", () => {
  it("parity 1: derive '2026-07#B1' from real_period_key='2026-07'", () => {
    expect(deriveBudgetPeriodKeyTS("2026-07")).toBe("2026-07#B1");
  });

  it("parity 2: derive with explicit scenario_index=1", () => {
    expect(deriveBudgetPeriodKeyTS("2026-07", 1)).toBe("2026-07#B1");
  });

  it("parity 3: invalid real_period_key returns null", () => {
    expect(deriveBudgetPeriodKeyTS("invalid")).toBeNull();
  });

  it("parity 4: scenario_index=2 exceeds MVP limit returns null", () => {
    expect(deriveBudgetPeriodKeyTS("2026-07", 2)).toBeNull();
  });

  it("parity 5: scenario_index=0 (negative) returns null", () => {
    expect(deriveBudgetPeriodKeyTS("2026-07", 0)).toBeNull();
  });
});

describe("m8-budget-scenario parity — validateScenarioUniquenessTS", () => {
  it("parity 1: existing_count=0 returns null (allow)", () => {
    expect(validateScenarioUniquenessTS(0)).toBeNull();
  });

  it("parity 2: existing_count=1 returns MVP limit message", () => {
    expect(validateScenarioUniquenessTS(1)).toBe(
      SCENARIO_LIMIT_EXCEEDED_MESSAGE_KO,
    );
  });

  it("parity 3: existing_count=-1 returns validation error", () => {
    expect(validateScenarioUniquenessTS(-1)).toBe(
      "existing_count must be a non-negative integer",
    );
  });
});

describe("m8-budget-scenario parity — MVP constants", () => {
  it("MVP_MAX_SCENARIOS_PER_TENANT === 1 (1차 MVP 한도)", () => {
    expect(MVP_MAX_SCENARIOS_PER_TENANT).toBe(1);
  });
});