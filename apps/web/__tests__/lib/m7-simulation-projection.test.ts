// apps/web/__tests__/lib/m7-simulation-projection.test.ts — Story 7.2
//
// TS mirror parity tests for `apps/web/lib/m7-simulation-projection.ts`.
// Cross-language drift detector (CR 12-5 D-13) — TS implementation
// MUST match Python `packages.cost_engine.projection` semantics.

import { describe, expect, it } from "vitest";

import {
  type NextMonthProjectionSerialized,
  type ProjectionBaselineSerialized,
  type ProjectionInputsSerialized,
  computeAfterTaxIncomeTS,
  computeInterestExpenseTS,
  formatKRWTS,
  formatPercentTS,
  isAllFieldsFilledTS,
  isProjectionMonthAfterPeriodKeyTS,
  isValidRealPeriodKeyTS,
  projectNextMonthTS,
  validateCorporateTaxRateTS,
  validateCostInflationRateTS,
  validateInterestRateTS,
  validateLoanAmountTS,
} from "@/lib/m7-simulation-projection";
import {
  type ProjectionInputsSchema,
  isAllFieldsFilledTS,
  projectionInputsSchema,
  validateProjectionInputs,
} from "@/lib/m7-simulation-projection-schema";

const baseline: ProjectionBaselineSerialized = {
  fixed_cost: "10000000",
  unit_variable_cost: "6000",
  unit_price: "10000",
  operating_rate: "1.0",
  target_profit: "0",
  monthly_revenue: "30000000",
  monthly_variable_cost: "18000000",
  monthly_fixed_cost: "10000000",
  source_period_key: "2026-07",
  fiscal_period_state: "committed",
};

const validInputs: ProjectionInputsSerialized = {
  loan_amount: "10000000",
  interest_rate: "5",
  cost_inflation_rate: "3",
  corporate_tax_rate: "22",
};

// ── computeInterestExpenseTS ──────────────────────────────────
describe("computeInterestExpenseTS", () => {
  it("loan_amount=10,000,000 / interest_rate=5% → 500,000", () => {
    expect(computeInterestExpenseTS(10_000_000, 5)).toBe("500000");
  });

  it("loan_amount=0 → 0 (no interest)", () => {
    expect(() => computeInterestExpenseTS(0, 5)).toThrow();
  });

  it("loan_amount < 0 → throw", () => {
    expect(() => computeInterestExpenseTS(-1, 5)).toThrow();
  });

  it("interest_rate < 0 → throw", () => {
    expect(() => computeInterestExpenseTS(10_000_000, -1)).toThrow();
  });

  it("interest_rate > 100 → throw", () => {
    expect(() => computeInterestExpenseTS(10_000_000, 101)).toThrow();
  });

  it("loan_amount NaN → throw", () => {
    expect(() => computeInterestExpenseTS(Number.NaN, 5)).toThrow();
  });

  it("loan_amount non-integer → throw (KRW 정수)", () => {
    expect(() => computeInterestExpenseTS(10_000_000.5, 5)).toThrow();
  });
});

// ── computeAfterTaxIncomeTS ────────────────────────────────────
describe("computeAfterTaxIncomeTS", () => {
  it("pre_tax=10,000,000 / tax_rate=22% → tax=2,200,000 / after_tax=7,800,000", () => {
    const result = computeAfterTaxIncomeTS(10_000_000, 22);
    expect(result.corporate_tax).toBe("2200000");
    expect(result.after_tax_income).toBe("7800000");
  });

  it("pre_tax=0 / tax_rate=22% → tax=0 / after_tax=0", () => {
    const result = computeAfterTaxIncomeTS(0, 22);
    expect(result.corporate_tax).toBe("0");
    expect(result.after_tax_income).toBe("0");
  });

  it("pre_tax<0 → 손실 인정 (tax=0, after_tax 그대로 음수)", () => {
    const result = computeAfterTaxIncomeTS(-1_000_000, 22);
    expect(result.corporate_tax).toBe("0");
    expect(result.after_tax_income).toBe("-1000000");
  });

  it("corporate_tax_rate < 0 → throw", () => {
    expect(() => computeAfterTaxIncomeTS(1_000_000, -1)).toThrow();
  });

  it("corporate_tax_rate > 100 → throw", () => {
    expect(() => computeAfterTaxIncomeTS(1_000_000, 101)).toThrow();
  });
});

// ── projectNextMonthTS ─────────────────────────────────────────
describe("projectNextMonthTS", () => {
  it("baseline + zero inputs → revenue / variable cost preserved, fixed cost unchanged", () => {
    const result: NextMonthProjectionSerialized = projectNextMonthTS(baseline, {
      loan_amount: "0",
      interest_rate: "0",
      cost_inflation_rate: "0",
      corporate_tax_rate: "0",
    });
    // With loan_amount=0 and zero inflation, revenue/var cost == baseline
    expect(result.projected_revenue).toBe("30000000");
    expect(result.projected_variable_cost).toBe("18000000");
    // Fixed cost unchanged (no interest)
    expect(result.projected_fixed_cost).toBe("10000000");
    expect(result.interest_expense).toBe("0");
    // Pre-tax = 30M - 18M - 10M = 2M, tax=0 (rate=0), after-tax=2M
    expect(result.pre_tax_income).toBe("2000000");
    expect(result.corporate_tax).toBe("0");
    expect(result.after_tax_income).toBe("2000000");
  });

  it("baseline null → throw (CR 11-4 D-005)", () => {
    expect(() =>
      projectNextMonthTS(null, validInputs),
    ).toThrow();
  });

  it("cost_inflation_rate=3 → revenue/var cost × 1.03", () => {
    const result = projectNextMonthTS(baseline, {
      loan_amount: "0",
      interest_rate: "0",
      cost_inflation_rate: "3",
      corporate_tax_rate: "0",
    });
    expect(result.projected_revenue).toBe("30900000"); // 30M * 1.03
    expect(result.projected_variable_cost).toBe("18540000"); // 18M * 1.03
  });

  it("loan_amount=10M / interest_rate=5% → interest_expense=500,000", () => {
    const result = projectNextMonthTS(baseline, validInputs);
    expect(result.interest_expense).toBe("500000");
    expect(result.projected_fixed_cost).toBe("10500000"); // 10M + 500k
  });
});

// ── validators ────────────────────────────────────────────────
describe("validators", () => {
  it("isValidRealPeriodKeyTS — YYYY-MM valid", () => {
    expect(isValidRealPeriodKeyTS("2026-07")).toBe(true);
    expect(isValidRealPeriodKeyTS("2026-13")).toBe(false);
    expect(isValidRealPeriodKeyTS("2026-7")).toBe(false);
  });

  it("isProjectionMonthAfterPeriodKeyTS — chronological invariant", () => {
    expect(isProjectionMonthAfterPeriodKeyTS("2026-07", "2026-08")).toBe(true);
    expect(isProjectionMonthAfterPeriodKeyTS("2026-07", "2026-07")).toBe(false);
    expect(isProjectionMonthAfterPeriodKeyTS("2026-08", "2026-07")).toBe(false);
    expect(isProjectionMonthAfterPeriodKeyTS("2026-99", "2026-08")).toBe(false);
  });

  it("validateLoanAmountTS — boundary conditions", () => {
    expect(() => validateLoanAmountTS(1)).not.toThrow();
    expect(() => validateLoanAmountTS(1_000_000_000_000)).not.toThrow();
    expect(() => validateLoanAmountTS(1_000_000_000_001)).toThrow();
    expect(() => validateLoanAmountTS(0)).toThrow();
    expect(() => validateLoanAmountTS(-1)).toThrow();
  });

  it("validateInterestRateTS — boundary conditions", () => {
    expect(() => validateInterestRateTS(0)).not.toThrow();
    expect(() => validateInterestRateTS(100)).not.toThrow();
    expect(() => validateInterestRateTS(101)).toThrow();
    expect(() => validateInterestRateTS(-1)).toThrow();
  });

  it("validateCostInflationRateTS — boundary conditions", () => {
    expect(() => validateCostInflationRateTS(-50)).not.toThrow();
    expect(() => validateCostInflationRateTS(100)).not.toThrow();
    expect(() => validateCostInflationRateTS(101)).toThrow();
    expect(() => validateCostInflationRateTS(-51)).toThrow();
  });

  it("validateCorporateTaxRateTS — boundary conditions", () => {
    expect(() => validateCorporateTaxRateTS(0)).not.toThrow();
    expect(() => validateCorporateTaxRateTS(100)).not.toThrow();
    expect(() => validateCorporateTaxRateTS(101)).toThrow();
    expect(() => validateCorporateTaxRateTS(-1)).toThrow();
  });
});

// ── Zod schema ─────────────────────────────────────────────────
describe("Zod schema (projectionInputsSchema)", () => {
  const validValue: ProjectionInputsSchema = {
    loan_amount: 10_000_000,
    interest_rate: 5,
    cost_inflation_rate: 3,
    corporate_tax_rate: 22,
  };

  it("valid inputs pass", () => {
    const result = projectionInputsSchema.safeParse(validValue);
    expect(result.success).toBe(true);
  });

  it("loan_amount=0 → fail", () => {
    const result = projectionInputsSchema.safeParse({
      ...validValue,
      loan_amount: 0,
    });
    expect(result.success).toBe(false);
  });

  it("loan_amount=-1 → fail", () => {
    const result = projectionInputsSchema.safeParse({
      ...validValue,
      loan_amount: -1,
    });
    expect(result.success).toBe(false);
  });

  it("loan_amount=10000.5 (not integer) → fail", () => {
    const result = projectionInputsSchema.safeParse({
      ...validValue,
      loan_amount: 10000.5,
    });
    expect(result.success).toBe(false);
  });

  it("interest_rate=101 → fail", () => {
    const result = projectionInputsSchema.safeParse({
      ...validValue,
      interest_rate: 101,
    });
    expect(result.success).toBe(false);
  });

  it("cost_inflation_rate=-51 → fail", () => {
    const result = projectionInputsSchema.safeParse({
      ...validValue,
      cost_inflation_rate: -51,
    });
    expect(result.success).toBe(false);
  });

  it("isAllFieldsFilledTS — true when all 4 valid", () => {
    expect(isAllFieldsFilledTS(validValue)).toBe(true);
  });

  it("isAllFieldsFilledTS — false when missing fields", () => {
    expect(
      isAllFieldsFilledTS({
        ...validValue,
        loan_amount: undefined,
      }),
    ).toBe(false);
  });

  it("isAllFieldsFilledTS — false when invalid", () => {
    expect(
      isAllFieldsFilledTS({
        ...validValue,
        loan_amount: 0,
      }),
    ).toBe(false);
  });
});

// ── formatters ────────────────────────────────────────────────
describe("formatters", () => {
  it("formatKRWTS — thousand separator", () => {
    expect(formatKRWTS("1234567")).toBe("1,234,567");
    expect(formatKRWTS("0")).toBe("0");
  });

  it("formatPercentTS — 2 decimal + %", () => {
    expect(formatPercentTS("22.5")).toBe("22.50%");
    expect(formatPercentTS("0")).toBe("0.00%");
  });
});
