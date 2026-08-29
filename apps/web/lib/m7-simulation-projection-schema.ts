// apps/web/lib/m7-simulation-projection-schema.ts — Story 7.2 (Epic 7)
//
// Validation schema for the 4 required parameters (PRD §F7.2 verbatim):
//   - 차입금(원) / 이자율(%) / 원가 상승률(%) / 법인세율(%)
//
// Mirrors the backend Pydantic v2 validation in
// `apps/api/modules/m7_simulation/schemas.py:ProjectionInputsRequest`.
//
// Implementation note (D-7-2-DEFER-7 honestly deferred):
//  - Spec recommended Zod schema (`import { z } from "zod"`), but `zod`
//    is not yet in apps/web/package.json. We provide a plain TypeScript
//    validation module with the same bounds + the same API surface.
//  - Future migration: when `zod` is added, replace `validateProjectionInputs`
//    with `projectionInputsSchema.safeParse(...)` and re-export as before.
//
// CR 11-4 D-005: validation MUST throw on invalid input — NOT silent
// fall-through. Use `validateProjectionInputs(values)` to assert validity
// before submitting.
//
// AD-17 BigInteger parity: `loan_amount` is positive integer (KRW).
// All bounds match backend constants (Pydantic `Field(ge=0, le=100)` etc).

// ── Constants (mirror backend Pydantic Field bounds) ──────────
/** AD-17 BigInteger KRW range — practical upper bound. */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const LOAN_AMOUNT_MIN: number = 1;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const LOAN_AMOUNT_MAX: number = 1_000_000_000_000; // 1조 KRW

/** Backend `Field(ge=0, le=100)` parity. */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const INTEREST_RATE_MIN: number = 0;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const INTEREST_RATE_MAX: number = 100;

/** Disinflation..Inflation range (PRD §F7.2 + backend AC #2). */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const COST_INFLATION_RATE_MIN: number = -50;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const COST_INFLATION_RATE_MAX: number = 100;

/** Backend `Field(ge=0, le=100)` parity. */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const CORPORATE_TAX_RATE_MIN: number = 0;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const CORPORATE_TAX_RATE_MAX: number = 100;

// ── TypeScript view model (mirror Python `ProjectionInputs`) ──
export interface ProjectionInputsSchema {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  loan_amount: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  interest_rate: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  cost_inflation_rate: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  corporate_tax_rate: number;
}

/**
 * Default (empty) form state — all 4 fields undefined until the user
 * fills them. Used as `useState` initial state.
 */
export const PROJECTION_INPUTS_DEFAULTS: Partial<ProjectionInputsSchema> = {
  loan_amount: undefined,
  interest_rate: undefined,
  cost_inflation_rate: undefined,
  corporate_tax_rate: undefined,
} as const;

// ── Validation result type ────────────────────────────────────
export interface ValidationResult {
  success: boolean;
  errors: Partial<Record<keyof ProjectionInputsSchema, string>>;
}

/**
 * Validate the 4 required parameters against backend parity bounds.
 *
 * CR 11-4 D-005: returns `success: false` with field-level errors on
 * invalid input. NEVER silently falls through.
 *
 * Mirrors Zod's `safeParse` API:
 *   const result = validateProjectionInputs(values);
 *   if (result.success) { /* proceed *\/ }
 */
export function validateProjectionInputs(
  values: Partial<ProjectionInputsSchema>,
): ValidationResult {
  const errors: Partial<Record<keyof ProjectionInputsSchema, string>> = {};

  // loan_amount — non-negative integer, KRW (0 = no loan allowed).
  if (values.loan_amount === undefined || values.loan_amount === null) {
    errors.loan_amount = "차입금을 입력해 주세요";
  } else if (!Number.isFinite(values.loan_amount)) {
    errors.loan_amount = "차입금은 숫자여야 합니다";
  } else if (!Number.isInteger(values.loan_amount)) {
    errors.loan_amount = "차입금은 정수여야 합니다 (KRW)";
  } else if (values.loan_amount < 0) {
    errors.loan_amount = "차입금은 0 이상이어야 합니다";
  } else if (values.loan_amount > LOAN_AMOUNT_MAX) {
    errors.loan_amount = "차입금은 1조 원 이하여야 합니다";
  }

  // interest_rate — 0..100
  if (values.interest_rate === undefined || values.interest_rate === null) {
    errors.interest_rate = "이자율을 입력해 주세요";
  } else if (!Number.isFinite(values.interest_rate)) {
    errors.interest_rate = "이자율은 숫자여야 합니다";
  } else if (values.interest_rate < INTEREST_RATE_MIN) {
    errors.interest_rate = "이자율은 0% 이상이어야 합니다";
  } else if (values.interest_rate > INTEREST_RATE_MAX) {
    errors.interest_rate = "이자율은 100% 이하여야 합니다";
  }

  // cost_inflation_rate — -50..100
  if (
    values.cost_inflation_rate === undefined ||
    values.cost_inflation_rate === null
  ) {
    errors.cost_inflation_rate = "원가 상승률을 입력해 주세요";
  } else if (!Number.isFinite(values.cost_inflation_rate)) {
    errors.cost_inflation_rate = "원가 상승률은 숫자여야 합니다";
  } else if (values.cost_inflation_rate < COST_INFLATION_RATE_MIN) {
    errors.cost_inflation_rate = "원가 상승률은 -50% 이상이어야 합니다";
  } else if (values.cost_inflation_rate > COST_INFLATION_RATE_MAX) {
    errors.cost_inflation_rate = "원가 상승률은 100% 이하여야 합니다";
  }

  // corporate_tax_rate — 0..100
  if (
    values.corporate_tax_rate === undefined ||
    values.corporate_tax_rate === null
  ) {
    errors.corporate_tax_rate = "법인세율을 입력해 주세요";
  } else if (!Number.isFinite(values.corporate_tax_rate)) {
    errors.corporate_tax_rate = "법인세율은 숫자여야 합니다";
  } else if (values.corporate_tax_rate < CORPORATE_TAX_RATE_MIN) {
    errors.corporate_tax_rate = "법인세율은 0% 이상이어야 합니다";
  } else if (values.corporate_tax_rate > CORPORATE_TAX_RATE_MAX) {
    errors.corporate_tax_rate = "법인세율은 100% 이하여야 합니다";
  }

  return {
    success: Object.keys(errors).length === 0,
    errors,
  };
}

/**
 * Returns true when all 4 fields are present and pass validation.
 *
 * CR 11-4 patterns: this is the gate that drives
 * `disabled={!allFieldsFilled}` on the [예측 실행] button.
 *
 * - Falsy (undefined / null) → false (button stays disabled).
 * - Validation success → true (button enabled).
 * - Validation failure → false (button disabled).
 */
export function isAllFieldsFilledTS(
  values: Partial<ProjectionInputsSchema>,
): boolean {
  return validateProjectionInputs(values).success;
}
