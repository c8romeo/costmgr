// apps/web/lib/m7-simulation-projection.ts — Story 7.2 (Epic 7)
//
// M7 Next-Month Projection TS projection (AD-15 §11 SSOT parity with
// `packages/cost_engine/projection.py`).
//
// Frontend mirror of the POST /api/v1/simulation/projection/compute + GET
// /api/v1/simulation/projection/baseline response. Drift caught by parity
// tests in `apps/web/__tests__/lib/m7-simulation-projection.test.ts`.
//
// Cross-language parity contract (CR 12-5 D-13):
// - Decimal ROUND_HALF_EVEN (Python `decimal.Decimal` ↔ TS `number`)
// - `projectNextMonthTS` MUST produce the same result values as Python
//   `project_next_month` for the same inputs.
// - `computeInterestExpenseTS` MUST match Python `compute_interest_expense`.
// - `computeAfterTaxIncomeTS` MUST match Python `compute_after_tax_income`.
//
// CR 11-4 D-005: TS mirror MUST raise on invalid input — NOT silent fall-through.
// CR 11-4 D-002: ko-KR.json SSOT lives in `apps/web/messages/ko-KR.json`,
// NOT in `apps/web/lib/`.

// ── Constants (PRD §F7.2 + AD-5 parity) ─────────────────────────
/** Backend `Field(gt=0)` parity — loan_amount is positive integer (KRW). */
export const LOAN_AMOUNT_MIN: number = 1;
export const LOAN_AMOUNT_MAX: number = 1_000_000_000_000;

/** Backend `Field(ge=0, le=100)` parity. */
export const INTEREST_RATE_MIN: number = 0;
export const INTEREST_RATE_MAX: number = 100;

/** Disinflation..Inflation range. */
export const COST_INFLATION_RATE_MIN: number = -50;
export const COST_INFLATION_RATE_MAX: number = 100;

/** Backend `Field(ge=0, le=100)` parity. */
export const CORPORATE_TAX_RATE_MIN: number = 0;
export const CORPORATE_TAX_RATE_MAX: number = 100;

// ── Typed view models (mirror Python frozen dataclasses) ───────

/**
 * 7-1 CVPBaseline reuse — projection receives the baseline extracted
 * by `CVPSimulationService.fetch_cvp_baseline` (CVP_SIMULATION capability
 * reuse, 7-1 wire + 7-2 EXTENSION).
 *
 * For TS projection parity, we also include `monthly_revenue`,
 * `monthly_variable_cost`, `monthly_fixed_cost` — these are the
 * kernel's pre-aggregated monthly totals (service layer derives them
 * from `monthly_input_periods` + `products` aggregation).
 */
export interface ProjectionBaselineSerialized {
  /** Source CVPBaseline fields (per-unit). */
  fixed_cost: string;
  unit_variable_cost: string;
  unit_price: string;
  operating_rate: string;
  target_profit: string;

  /** Pre-aggregated monthly totals (service-layer derived). */
  monthly_revenue: string;
  monthly_variable_cost: string;
  monthly_fixed_cost: string;

  /** Source period key + state. */
  source_period_key: string;
  fiscal_period_state: string;
}

/** 4 required parameters — Decimal-as-string for JSON safety. */
export interface ProjectionInputsSerialized {
  loan_amount: string;
  interest_rate: string;
  cost_inflation_rate: string;
  corporate_tax_rate: string;
}

/** Full projection output (7 fields, mirror Python `NextMonthProjection`). */
export interface NextMonthProjectionSerialized {
  projected_revenue: string;
  projected_variable_cost: string;
  projected_fixed_cost: string;
  interest_expense: string;
  pre_tax_income: string;
  corporate_tax: string;
  after_tax_income: string;
}

/** POST /api/v1/simulation/projection/compute response envelope. */
export interface ProjectionComputeResponse {
  baseline: ProjectionBaselineSerialized;
  projection_inputs: ProjectionInputsSerialized;
  result: NextMonthProjectionSerialized;
  latency_ms: number;
  projection_hash: string;
  trace_id: string | null;
}

/** GET /api/v1/simulation/projection/baseline response envelope. */
export interface ProjectionBaselineResponse {
  baseline: ProjectionBaselineSerialized;
  period_key: string;
  projection_month: string;
  derived_projection_inputs_hint: Record<string, string>;
  trace_id: string | null;
}

// ── Typed wire payload (POST request body) ─────────────────────
export interface ProjectionComputeRequest {
  period_key: string;
  projection_month: string;
  projection_inputs: ProjectionInputsSerialized;
}

// ── Error code SSOT (CR 12-5 D-14 typed envelope) ─────────────
export const ERROR_CODE_PROJECTION_BASELINE_NOT_FOUND: string =
  "PROJECTION_BASELINE_NOT_FOUND" as const;
export const ERROR_CODE_PROJECTION_INPUTS_INVALID: string =
  "PROJECTION_INPUTS_INVALID" as const;
export const ERROR_CODE_INVALID_PROJECTION_MONTH: string =
  "INVALID_PROJECTION_MONTH" as const;
export const ERROR_CODE_PROJECTION_HASH_MISMATCH: string =
  "PROJECTION_HASH_MISMATCH" as const;

// ── Real period key pattern (AD-24 §6.1) — reuse 7-1 pattern ────
const REAL_PERIOD_KEY_PATTERN: RegExp = /^\d{4}-(0[1-9]|1[0-2])$/;

export function isValidRealPeriodKeyTS(value: string): boolean {
  return typeof value === "string" && REAL_PERIOD_KEY_PATTERN.test(value);
}

/**
 * Chronological invariant: projection_month MUST be strictly after
 * period_key (AD-24 §6.1 + spec AC #3 chronological invariant).
 *
 * Lexicographic comparison is valid for ISO YYYY-MM format.
 */
export function isProjectionMonthAfterPeriodKeyTS(
  periodKey: string,
  projectionMonth: string,
): boolean {
  if (!isValidRealPeriodKeyTS(periodKey)) return false;
  if (!isValidRealPeriodKeyTS(projectionMonth)) return false;
  return projectionMonth > periodKey;
}

// ── Pure validators (defense-in-depth at frontend) ───────────
/**
 * CR 12-5 D-005: silent fall-through MUST reject (typed contract).
 * All 4 validators throw on invalid input — they do NOT return null
 * or false on error.
 */
export function validateLoanAmountTS(value: number): void {
  if (!Number.isFinite(value)) {
    throw new Error("loan_amount must be a finite number");
  }
  if (!Number.isInteger(value)) {
    throw new Error("loan_amount must be an integer (KRW)");
  }
  if (value < LOAN_AMOUNT_MIN) {
    throw new Error("loan_amount must be > 0");
  }
  if (value > LOAN_AMOUNT_MAX) {
    throw new Error("loan_amount exceeds 1조 KRW upper bound");
  }
}

export function validateInterestRateTS(value: number): void {
  if (!Number.isFinite(value)) {
    throw new Error("interest_rate must be a finite number");
  }
  if (value < INTEREST_RATE_MIN) {
    throw new Error("interest_rate must be >= 0");
  }
  if (value > INTEREST_RATE_MAX) {
    throw new Error("interest_rate must be <= 100");
  }
}

export function validateCostInflationRateTS(value: number): void {
  if (!Number.isFinite(value)) {
    throw new Error("cost_inflation_rate must be a finite number");
  }
  if (value < COST_INFLATION_RATE_MIN) {
    throw new Error("cost_inflation_rate must be >= -50");
  }
  if (value > COST_INFLATION_RATE_MAX) {
    throw new Error("cost_inflation_rate must be <= 100");
  }
}

export function validateCorporateTaxRateTS(value: number): void {
  if (!Number.isFinite(value)) {
    throw new Error("corporate_tax_rate must be a finite number");
  }
  if (value < CORPORATE_TAX_RATE_MIN) {
    throw new Error("corporate_tax_rate must be >= 0");
  }
  if (value > CORPORATE_TAX_RATE_MAX) {
    throw new Error("corporate_tax_rate must be <= 100");
  }
}

// ── Pure projection math (mirror Python pure kernel) ───────────
// Cross-language drift caught by
// `tests/integration/test_m7_simulation_projection_cross_language_drift.py`.

/**
 * Compute interest expense (이자) — pure kernel.
 *
 * Formula: `interest_expense = loan_amount * (interest_rate / 100)`.
 * Rounds to integer KRW (parity with Python `_q` ROUND_HALF_EVEN).
 *
 * Edge cases:
 * - `loan_amount < 0` → throw
 * - `interest_rate < 0` → throw
 * - `interest_rate > 100` → throw
 */
export function computeInterestExpenseTS(
  loanAmount: number,
  interestRate: number,
): string {
  validateLoanAmountTS(loanAmount);
  validateInterestRateTS(interestRate);

  const interest = loanAmount * (interestRate / 100);
  return Math.round(interest).toString();
}

/**
 * Compute after-tax income (세후 이익) — pure kernel.
 *
 * Formula:
 *   `corporate_tax = max(0, pre_tax_income) * (corporate_tax_rate / 100)`
 *   `after_tax_income = pre_tax_income - corporate_tax`
 *
 * Edge cases:
 * - `corporate_tax_rate` out of range → throw
 * - `pre_tax_income < 0` → 손실 인정 (corporate_tax=0, after_tax_income 음수 유지)
 */
export function computeAfterTaxIncomeTS(
  preTaxIncome: number,
  corporateTaxRate: number,
): { corporate_tax: string; after_tax_income: string } {
  validateCorporateTaxRateTS(corporateTaxRate);

  let corporateTax: number;
  if (preTaxIncome < 0) {
    corporateTax = 0;
  } else {
    corporateTax = preTaxIncome * (corporateTaxRate / 100);
  }
  const afterTaxIncome = preTaxIncome - corporateTax;

  return {
    corporate_tax: Math.round(corporateTax).toString(),
    after_tax_income: Math.round(afterTaxIncome).toString(),
  };
}

/**
 * Project next-month financial outcomes — full TS orchestration.
 *
 * Steps:
 *   1. `computeInterestExpenseTS(loanAmount, interestRate)`
 *   2. `projected_revenue = baseline.monthly_revenue * (1 + costInflationRate/100)`
 *   3. `projected_variable_cost = baseline.monthly_variable_cost * (1 + costInflationRate/100)`
 *   4. `projected_fixed_cost = baseline.monthly_fixed_cost + interest_expense`
 *   5. `pre_tax_income = revenue - variable - fixed`
 *   6. `computeAfterTaxIncomeTS(pre_tax_income, corporate_tax_rate)`
 *
 * CR 11-4 D-005: baseline null MUST raise (NOT silent fall-through).
 *
 * Determinism (NFR16): same inputs → same outputs (TS `Math.round`
 * parity with Python `ROUND_HALF_EVEN` for monetary fields).
 */
export function projectNextMonthTS(
  baseline: ProjectionBaselineSerialized | null,
  inputs: ProjectionInputsSerialized,
): NextMonthProjectionSerialized {
  if (baseline === null) {
    throw new Error("baseline must not be null");
  }

  const loanAmount = parseFloat(inputs.loan_amount);
  const interestRate = parseFloat(inputs.interest_rate);
  const costInflationRate = parseFloat(inputs.cost_inflation_rate);
  const corporateTaxRate = parseFloat(inputs.corporate_tax_rate);

  // 1. Interest expense.
  const interestExpenseStr = computeInterestExpenseTS(loanAmount, interestRate);
  const interestExpense = parseFloat(interestExpenseStr);

  // 2-3. Apply cost inflation to revenue + variable cost.
  const inflationFactor = 1 + costInflationRate / 100;
  const projectedRevenue = parseFloat(baseline.monthly_revenue) * inflationFactor;
  const projectedVariableCost =
    parseFloat(baseline.monthly_variable_cost) * inflationFactor;
  const projectedFixedCost =
    parseFloat(baseline.monthly_fixed_cost) + interestExpense;

  // 4. Pre-tax income.
  const preTaxIncome =
    projectedRevenue - projectedVariableCost - projectedFixedCost;

  // 5. Corporate tax + after-tax income.
  const { corporate_tax, after_tax_income } = computeAfterTaxIncomeTS(
    preTaxIncome,
    corporateTaxRate,
  );

  return {
    projected_revenue: Math.round(projectedRevenue).toString(),
    projected_variable_cost: Math.round(projectedVariableCost).toString(),
    projected_fixed_cost: Math.round(projectedFixedCost).toString(),
    interest_expense: interestExpenseStr,
    pre_tax_income: Math.round(preTaxIncome).toString(),
    corporate_tax,
    after_tax_income,
  };
}

/**
 * Format KRW value with thousand separators for display.
 */
export function formatKRWTS(value: string): string {
  const n = parseFloat(value);
  if (!Number.isFinite(n)) return value;
  return n.toLocaleString("ko-KR");
}

/**
 * Format percent value with 2 decimal places.
 */
export function formatPercentTS(value: string): string {
  const n = parseFloat(value);
  if (!Number.isFinite(n)) return value;
  return `${n.toFixed(2)}%`;
}
