// apps/web/__tests__/lib/m8-budget-pre-standard-schema-parity.test.ts — Story 8.3
//
// Validation parity test (plain TS module mirror) — verify that the TS
// validators reject the same inputs that the Python Pydantic schema rejects
// (AD-15 §11 SSOT parity).
//
// Drift caught between:
// - `apps/api/modules/m8_budget/schemas_pre_standard.py` (Python Pydantic)
// - `apps/web/lib/m8-budget-pre-standard-schema.ts` (TS validators)
//
// D-7-2-DEFER-7 / 8-3: Zod schema honestly DEFERred — uses plain TS instead.

import { describe, expect, it } from "vitest";

import {
  InvalidPreStandardInputError,
  isBudgetPreStandardRequest,
  isValidPreStandardPeriodKey,
  isValidPreStandardResultHash,
  validatePreStandardInputs,
} from "../../lib/m8-budget-pre-standard-schema";

describe("m8-budget-pre-standard schema parity — period key (AD-24)", () => {
  it("parity 1: YYYY-MM#B<n> accepted", () => {
    expect(isValidPreStandardPeriodKey("2026-07#B1")).toBe(true);
  });

  it("parity 2: invalid format rejected", () => {
    expect(isValidPreStandardPeriodKey("2026-07")).toBe(false);
    expect(isValidPreStandardPeriodKey("2026-07#B0")).toBe(false);
  });
});

describe("m8-budget-pre-standard schema parity — validatePreStandardInputs", () => {
  it("parity 1: valid request accepted", () => {
    expect(() =>
      validatePreStandardInputs({
        period_key: "2026-07#B1",
        scenario_index: 1,
        material_unit_cost: "1000",
        labor_unit_cost: "50000",
        overhead_rate: "12.5",
        material_qty: "10",
        labor_hours: "8",
      }),
    ).not.toThrow();
  });

  it("parity 2: negative material_unit_cost rejected", () => {
    expect(() =>
      validatePreStandardInputs({
        period_key: "2026-07#B1",
        scenario_index: 1,
        material_unit_cost: "-100",
        labor_unit_cost: "50000",
        overhead_rate: "12.5",
        material_qty: "10",
        labor_hours: "8",
      }),
    ).toThrow(InvalidPreStandardInputError);
  });

  it("parity 3: non-numeric material_unit_cost rejected", () => {
    expect(() =>
      validatePreStandardInputs({
        period_key: "2026-07#B1",
        scenario_index: 1,
        material_unit_cost: "abc",
        labor_unit_cost: "50000",
        overhead_rate: "12.5",
        material_qty: "10",
        labor_hours: "8",
      }),
    ).toThrow(InvalidPreStandardInputError);
  });

  it("parity 4: scenario_index != 1 rejected (MVP hard-limit)", () => {
    expect(() =>
      validatePreStandardInputs({
        period_key: "2026-07#B1",
        scenario_index: 2 as unknown as 1,
        material_unit_cost: "1000",
        labor_unit_cost: "50000",
        overhead_rate: "12.5",
        material_qty: "10",
        labor_hours: "8",
      }),
    ).toThrow(InvalidPreStandardInputError);
  });

  it("parity 5: overhead_rate > 100 rejected", () => {
    expect(() =>
      validatePreStandardInputs({
        period_key: "2026-07#B1",
        scenario_index: 1,
        material_unit_cost: "1000",
        labor_unit_cost: "50000",
        overhead_rate: "150",
        material_qty: "10",
        labor_hours: "8",
      }),
    ).toThrow(InvalidPreStandardInputError);
  });

  it("parity 6: missing field rejected", () => {
    expect(() =>
      validatePreStandardInputs({
        period_key: "2026-07#B1",
        scenario_index: 1,
        material_unit_cost: "1000",
        labor_unit_cost: "50000",
        overhead_rate: "12.5",
        material_qty: "10",
        labor_hours: "" as string,
      }),
    ).toThrow(InvalidPreStandardInputError);
  });
});

describe("m8-budget-pre-standard schema parity — result_hash (SHA-256)", () => {
  it("parity 1: valid 64-char hex accepted", () => {
    expect(isValidPreStandardResultHash("a".repeat(64))).toBe(true);
  });

  it("parity 2: short hash rejected", () => {
    expect(isValidPreStandardResultHash("short")).toBe(false);
  });

  it("parity 3: 64-char non-hex rejected", () => {
    expect(isValidPreStandardResultHash("z".repeat(64))).toBe(false);
  });
});

describe("m8-budget-pre-standard schema parity — isBudgetPreStandardRequest", () => {
  it("parity 1: valid object accepted", () => {
    const obj = {
      period_key: "2026-07#B1",
      scenario_index: 1,
      material_unit_cost: "1000",
      labor_unit_cost: "50000",
      overhead_rate: "12.5",
      material_qty: "10",
      labor_hours: "8",
    };
    expect(isBudgetPreStandardRequest(obj)).toBe(true);
  });

  it("parity 2: invalid object rejected", () => {
    expect(isBudgetPreStandardRequest(null)).toBe(false);
    expect(isBudgetPreStandardRequest({})).toBe(false);
    expect(isBudgetPreStandardRequest("not-an-object")).toBe(false);
  });
});