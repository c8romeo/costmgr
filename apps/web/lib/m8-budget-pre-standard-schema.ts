// apps/web/lib/m8-budget-pre-standard-schema.ts — Story 8.3
//
// Validation schema for the 5 required parameters (PRD §F8.3 verbatim):
//   - material_unit_cost / labor_unit_cost (KRW integer)
//   - overhead_rate (%) / material_qty (KRW integer) / labor_hours (decimal)
//
// Mirrors the backend Pydantic v2 validation in
// `apps/api/modules/m8_budget/schemas_pre_standard.py`.
//
// Implementation note (D-7-2-DEFER-7 honestly deferred — also 8-3):
//  - Spec recommended Zod schema (`import { z } from "zod"`), but `zod`
//    is not yet in apps/web/package.json. We provide a plain TypeScript
//    validation module with the same bounds + the same API surface.
//  - Future migration: when `zod` is added, replace `validatePreStandardInputs`
//    with `budgetPreStandardRequestSchema.safeParse(...)` and re-export as before.
//
// CR 11-4 D-005: validation MUST throw on invalid input — NOT silent
// fall-through. Use `validatePreStandardInputs(values)` to assert validity
// before submitting.

import {
  PRE_STANDARD_OVERHEAD_RATE_MAX_PCT,
  PRE_STANDARD_UNIT_COST_MIN,
  VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD,
} from "./m8-budget-pre-standard";

// ── Period key (AD-24 mirror) ──────────────────────────────────
export function isValidPreStandardPeriodKey(periodKey: string): boolean {
  return VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD.test(periodKey);
}

// ── Regexes for KRW integer / decimal / rate ──────────────────
const KRW_INTEGER_REGEX: RegExp = /^\d+$/;
const RATE_PERCENT_REGEX: RegExp = /^\d{1,3}(\.\d{1,4})?$/;
const LABOR_HOURS_REGEX: RegExp = /^\d+(\.\d{1,2})?$/;

// ── Validators (mirror backend Pydantic Field bounds) ──────────
export class InvalidPreStandardInputError extends Error {
  constructor(
    public readonly field: string,
    public readonly reason: string,
  ) {
    super(`${field}: ${reason}`);
    this.name = "InvalidPreStandardInputError";
  }
}

function assertKRWInteger(value: string, field: string): void {
  if (!KRW_INTEGER_REGEX.test(value)) {
    throw new InvalidPreStandardInputError(
      field,
      "must be a non-negative KRW integer (string)",
    );
  }
}

function assertRatePercent(value: string, field: string): void {
  if (!RATE_PERCENT_REGEX.test(value)) {
    throw new InvalidPreStandardInputError(
      field,
      "must be a percentage 0-100 (string)",
    );
  }
  const num = Number(value);
  if (num < 0 || num > PRE_STANDARD_OVERHEAD_RATE_MAX_PCT) {
    throw new InvalidPreStandardInputError(
      field,
      `must be in range [0, ${PRE_STANDARD_OVERHEAD_RATE_MAX_PCT}]`,
    );
  }
}

function assertLaborHours(value: string, field: string): void {
  if (!LABOR_HOURS_REGEX.test(value)) {
    throw new InvalidPreStandardInputError(
      field,
      "must be a non-negative number with up to 2 decimals (string)",
    );
  }
}

function assertUnitCostMin(value: string, field: string): void {
  const num = Number(value);
  if (num < PRE_STANDARD_UNIT_COST_MIN) {
    throw new InvalidPreStandardInputError(
      field,
      `must be >= ${PRE_STANDARD_UNIT_COST_MIN}`,
    );
  }
}

// ── Public API ──────────────────────────────────────────────────
export interface BudgetPreStandardRequestParsed {
  period_key: string;
  scenario_index: 1;
  material_unit_cost: string;
  labor_unit_cost: string;
  overhead_rate: string;
  material_qty: string;
  labor_hours: string;
}

/**
 * Validate the 5 pre-standard inputs against backend Pydantic rules.
 * Throws InvalidPreStandardInputError on the first violation (CR 11-4 D-005).
 */
export function validatePreStandardInputs(
  values: BudgetPreStandardRequestParsed,
): void {
  if (!isValidPreStandardPeriodKey(values.period_key)) {
    throw new InvalidPreStandardInputError(
      "period_key",
      "must match YYYY-MM#B<n>",
    );
  }
  if (values.scenario_index !== 1) {
    throw new InvalidPreStandardInputError(
      "scenario_index",
      "must equal 1 (MVP hard-limit)",
    );
  }
  assertKRWInteger(values.material_unit_cost, "material_unit_cost");
  assertUnitCostMin(values.material_unit_cost, "material_unit_cost");
  assertKRWInteger(values.labor_unit_cost, "labor_unit_cost");
  assertUnitCostMin(values.labor_unit_cost, "labor_unit_cost");
  assertRatePercent(values.overhead_rate, "overhead_rate");
  assertKRWInteger(values.material_qty, "material_qty");
  assertLaborHours(values.labor_hours, "labor_hours");
}

// ── Snapshot deserializers (mirror BudgetPreStandardSnapshotSerialized) ──
export function isValidPreStandardSnapshotField(
  value: string,
  field: "material_cost" | "labor_cost" | "overhead_cost" | "manufacturing_cost",
): boolean {
  return KRW_INTEGER_REGEX.test(value);
}

export function isValidPreStandardResultHash(hash: string): boolean {
  return hash.length === 64 && /^[0-9a-f]{64}$/.test(hash);
}

// ── Object-shape validators (for type-narrowed test assertions) ──
export function isBudgetPreStandardRequest(
  obj: unknown,
): obj is BudgetPreStandardRequestParsed {
  if (typeof obj !== "object" || obj === null) return false;
  const o = obj as Record<string, unknown>;
  return (
    typeof o.period_key === "string" &&
    isValidPreStandardPeriodKey(o.period_key) &&
    o.scenario_index === 1 &&
    typeof o.material_unit_cost === "string" &&
    typeof o.labor_unit_cost === "string" &&
    typeof o.overhead_rate === "string" &&
    typeof o.material_qty === "string" &&
    typeof o.labor_hours === "string"
  );
}