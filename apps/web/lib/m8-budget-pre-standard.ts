// apps/web/lib/m8-budget-pre-standard.ts — Story 8.3 (Epic 8)
//
// M8 budget pre-standard cost preview TS projection (AD-15 §11 SSOT parity with
// `packages/cost_engine/budget_pre_standard.py`).
//
// Frontend mirror of POST /api/v1/budget/pre-standard and
// GET /api/v1/budget/pre-standard?period_key=...
// Drift caught by parity tests in
// `apps/web/__tests__/lib/m8-budget-pre-standard-parity.test.ts`.

// ── Constants (PRD §F8.3 + spec verbatim) ────────────────────────
// VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD mirrors Python.
// AD-24: YYYY-MM#B<n> where n ∈ {1}.
export const VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD: RegExp =
  /^(\d{4})-(0[1-9]|1[0-2])#B([1-9]\d*)$/;

export const DEFAULT_PRE_STANDARD_PERIOD_KEY: string = "2026-07#B1";

// Korean messages for HTTP envelopes (CR 12-5 D-14 typed envelope).
// Mirrors Python `BUDGET_INVALID_PRE_STANDARD_INPUT_KO` etc.
export const BUDGET_INVALID_PRE_STANDARD_INPUT_MESSAGE_KO: string =
  "예산 사전 표준원가 입력값이 올바르지 않습니다";
export const BUDGET_PRE_STANDARD_SNAPSHOT_NOT_FOUND_MESSAGE_KO: string =
  "예산 사전 표준원가 스냅샷을 찾을 수 없습니다";
export const BUDGET_PRE_STANDARD_ALREADY_EXISTS_MESSAGE_KO: string =
  "해당 기간의 예산 사전 표준원가 스냅샷이 이미 존재합니다";
export const BUDGET_VARIANCE_PDF_NOT_READY_MESSAGE_KO: string =
  "예산 사전 표준원가 스냅샷이 없어 PDF를 생성할 수 없습니다";

// ── Constants (PRD §F8.3 verbatim) ──────────────────────────────
// Quantum: KRW integer, BigInteger-as-string (AD-8 / AD-11).
export const PRE_STANDARD_QUANTUM_DECIMAL_PLACES: number = 0;

// Rate quantum: percentage with 4 decimal places.
export const PRE_STANDARD_RATE_DECIMAL_PLACES: number = 4;

// Default overhead rate cap: 100% (PRD §F8.3 verbatim).
export const PRE_STANDARD_OVERHEAD_RATE_MAX_PCT: number = 100;

// Default material/labor unit cost min: 0 KRW (PRD §F8.3 verbatim).
export const PRE_STANDARD_UNIT_COST_MIN: number = 0;

// ── TS view model (mirror BudgetPreStandardSnapshotSerialized) ───
export interface BudgetPreStandardInputs {
  material_unit_cost: string; // KRW integer
  labor_unit_cost: string; // KRW integer
  overhead_rate: string; // percentage (0-100)
  material_qty: string; // KRW integer
  labor_hours: string; // number (decimal hours)
}

export interface BudgetPreStandardSnapshotSerialized {
  period_key: string;
  scenario_index: number; // 1차 MVP = 1 only
  material_cost: string; // KRW integer (material_unit_cost × material_qty)
  labor_cost: string; // KRW integer (labor_unit_cost × labor_hours)
  overhead_cost: string; // KRW integer ((material_cost + labor_cost) × overhead_rate/100)
  manufacturing_cost: string; // KRW integer (sum)
  result_hash: string; // V8 byte-identical determinism
  trace_id: string | null;
}

export interface BudgetPreStandardResponse {
  snapshot: BudgetPreStandardSnapshotSerialized;
  trace_id: string | null;
}

export interface BudgetVariancePdfFromPreStandard {
  period_key: string;
  scenario_index: number;
  pdf_bytes_b64: string; // 8-3 real PDF; not empty
  filename: string;
  envelope: Record<string, unknown>;
  trace_id: string | null;
}

// ── Error code SSOT (CR 12-5 D-14 typed envelope) ────────────────
// Mirrors Python main.py handler `code` field.
export const ERROR_CODE_INVALID_PRE_STANDARD_INPUT: string =
  "INVALID_PRE_STANDARD_INPUT" as const;
export const ERROR_CODE_PRE_STANDARD_SNAPSHOT_NOT_FOUND: string =
  "PRE_STANDARD_SNAPSHOT_NOT_FOUND" as const;
export const ERROR_CODE_PRE_STANDARD_ALREADY_EXISTS: string =
  "PRE_STANDARD_ALREADY_EXISTS" as const;
export const ERROR_CODE_BUDGET_VARIANCE_PDF_NOT_READY: string =
  "BUDGET_VARIANCE_PDF_NOT_READY" as const;

// ── Pure helpers (mirrors Python kernel) ──────────────────────────

/**
 * Validate that a string matches the virtual period key pattern.
 * AD-24: YYYY-MM#B<n>.
 */
export function isValidVirtualBudgetPeriodKeyTS(
  periodKey: string,
): boolean {
  return VIRTUAL_BUDGET_PERIOD_KEY_PATTERN_PRE_STANDARD.test(periodKey);
}

/**
 * Banker's rounding (ROUND_HALF_EVEN) for KRW integer cents → KRW integer.
 * Mirrors Python `Decimal.quantize(Decimal("1"), rounding=ROUND_HALF_EVEN)`.
 *
 * Used by computePreStandardCostTS to ensure decimal.js parity.
 */
function bankersRoundKRW(value: number): number {
  if (Number.isNaN(value)) return 0;
  const floor = Math.floor(value);
  const diff = value - floor;
  if (diff < 0.5) return floor;
  if (diff > 0.5) return floor + 1;
  // exactly 0.5 → round to even.
  return floor % 2 === 0 ? floor : floor + 1;
}

export interface PreStandardCostComputation {
  material_cost: string;
  labor_cost: string;
  overhead_cost: string;
  manufacturing_cost: string;
}

/**
 * Compute pre-standard cost from 5 inputs.
 *
 *   material_cost = material_unit_cost × material_qty
 *   labor_cost = labor_unit_cost × labor_hours
 *   overhead_cost = (material_cost + labor_cost) × overhead_rate / 100
 *   manufacturing_cost = material_cost + labor_cost + overhead_cost
 *
 * Returns null if any input is non-finite or negative.
 */
export function computePreStandardCostTS(
  inputs: BudgetPreStandardInputs,
): PreStandardCostComputation | null {
  const matUnit = Number(inputs.material_unit_cost);
  const labUnit = Number(inputs.labor_unit_cost);
  const rate = Number(inputs.overhead_rate);
  const matQty = Number(inputs.material_qty);
  const labHr = Number(inputs.labor_hours);

  if (
    !Number.isFinite(matUnit) ||
    !Number.isFinite(labUnit) ||
    !Number.isFinite(rate) ||
    !Number.isFinite(matQty) ||
    !Number.isFinite(labHr)
  ) {
    return null;
  }
  if (
    matUnit < PRE_STANDARD_UNIT_COST_MIN ||
    labUnit < PRE_STANDARD_UNIT_COST_MIN ||
    rate < 0 ||
    rate > PRE_STANDARD_OVERHEAD_RATE_MAX_PCT ||
    matQty < 0 ||
    labHr < 0
  ) {
    return null;
  }

  const materialCost = bankersRoundKRW(matUnit * matQty);
  const laborCost = bankersRoundKRW(labUnit * labHr);
  const overheadCost = bankersRoundKRW((materialCost + laborCost) * (rate / 100));
  const manufacturingCost = bankersRoundKRW(
    materialCost + laborCost + overheadCost,
  );

  return {
    material_cost: String(materialCost),
    labor_cost: String(laborCost),
    overhead_cost: String(overheadCost),
    manufacturing_cost: String(manufacturingCost),
  };
}

/**
 * Format KRW integer with 천단위 콤마 (AD-17 BigInteger parity).
 */
export function formatKRWPreStandardTS(valueStr: string): string {
  const num = Number(valueStr);
  if (!Number.isFinite(num)) return valueStr;
  return num.toLocaleString("ko-KR");
}