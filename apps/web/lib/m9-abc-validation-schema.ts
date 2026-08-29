// apps/web/lib/m9-abc-validation-schema.ts — Story 9.1
//
// Validation schema for the 3 ABC 100% guard input lists (PRD §F9.1 verbatim):
//   - cost_pool.allocation_pcts    (row sum 100%)
//   - activities.activity_pcts     (column sum 100%)
//   - drivers.driver_pcts          (driver sum 100%)
//
// Mirrors the backend Pydantic v2 validation in
// `apps/api/modules/m9_abc/schemas.py` and the service-layer
// `validate_abc_pct_list` 3-layer defense (CR 12-5 L3).
//
// CR 11-4 D-005: validation MUST throw on invalid input — NOT silent
// fall-through. Use `validateAbcPctList(values, target)` to assert validity
// before submitting.

import {
  ABC_ACTIVITY_INVALID_SUM_KO,
  ABC_COST_POOL_INVALID_SUM_KO,
  ABC_DRIVER_INVALID_SUM_KO,
  ABC_VALIDATION_NOT_FOUND_KO,
  VALIDATION_100_PCT_TARGET,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  isValidAbcPct,
  isValidAbcPctList,
  sumPct,
  type ValidationTarget,
} from "./m9-abc-validation";

// ── Typed errors (mirror backend typed exceptions) ─────────────

export class AbcValidationInputError extends Error {
  constructor(
    public readonly target: ValidationTarget,
    public readonly reason: string,
  ) {
    super(`${target}: ${reason}`);
    this.name = "AbcValidationInputError";
  }
}

// ── Per-target validators ──────────────────────────────────────

function assertCostPoolInput(values: string[]): void {
  if (values.length === 0) {
    throw new AbcValidationInputError(
      "cost_pool",
      `${ABC_VALIDATION_NOT_FOUND_KO} (cost_pool)`,
    );
  }
  if (!isValidAbcPctList(values)) {
    throw new AbcValidationInputError(
      "cost_pool",
      "부서별 allocation 퍼센트는 0 이상 100 이하의 숫자여야 합니다",
    );
  }
}

function assertActivityInput(values: string[]): void {
  if (values.length === 0) {
    throw new AbcValidationInputError(
      "activity",
      `${ABC_VALIDATION_NOT_FOUND_KO} (activity)`,
    );
  }
  if (!isValidAbcPctList(values)) {
    throw new AbcValidationInputError(
      "activity",
      "활동별 시간 배분 퍼센트는 0 이상 100 이하의 숫자여야 합니다",
    );
  }
}

function assertDriverInput(values: string[]): void {
  if (values.length === 0) {
    throw new AbcValidationInputError(
      "driver",
      `${ABC_VALIDATION_NOT_FOUND_KO} (driver)`,
    );
  }
  if (!isValidAbcPctList(values)) {
    throw new AbcValidationInputError(
      "driver",
      "동인별 사용량 퍼센트는 0 이상 100 이하의 숫자여야 합니다",
    );
  }
}

// ── Public API ──────────────────────────────────────────────────

/**
 * Validate the 3 ABC 100% guard input lists against backend Pydantic rules.
 * Throws AbcValidationInputError on the first violation (CR 11-4 D-005).
 */
export function validateAbcPctList(
  values: string[],
  target: ValidationTarget,
): void {
  if (target === "cost_pool") {
    assertCostPoolInput(values);
    return;
  }
  if (target === "activity") {
    assertActivityInput(values);
    return;
  }
  assertDriverInput(values);
}

/**
 * Compute the local sum of an allocation list (mirror backend Decimal sum).
 * Returns the sum as a number — useful for the "현재 N%" hint message.
 */
export function computeSumPct(values: string[]): number {
  return sumPct(values);
}

/**
 * Check whether the sum equals 100% (with optional tolerance).
 * Defaults to exact 100% match (no tolerance in MVP).
 */
export function is100Percent(
  values: string[],
  tolerance = 0,
): boolean {
  const s = computeSumPct(values);
  return Math.abs(s - VALIDATION_100_PCT_TARGET) <= tolerance;
}

/**
 * Suggest the Korean SSOT message based on layer + sum_pct mismatch.
 * Used for the inline error hint in the form.
 */
export function buildKoreanMismatchHint(
  target: ValidationTarget,
  sumPctValue: number,
): string {
  if (target === "cost_pool") {
    return `${ABC_COST_POOL_INVALID_SUM_KO} (현재 ${sumPctValue}%)`;
  }
  if (target === "activity") {
    return `${ABC_ACTIVITY_INVALID_SUM_KO} (현재 ${sumPctValue}%)`;
  }
  return `${ABC_DRIVER_INVALID_SUM_KO} (현재 ${sumPctValue}%)`;
}