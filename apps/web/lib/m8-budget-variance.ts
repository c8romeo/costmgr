// apps/web/lib/m8-budget-variance.ts — Story 8.2 (Epic 8)
//
// M8 budget-actual variance TS projection (AD-15 §11 SSOT parity with
// `packages/cost_engine/budget_variance.py`).
//
// Frontend mirror of the GET /api/v1/budget/variance/{period_key} response.
// Drift caught by parity tests in `apps/web/__tests__/lib/m8-budget-variance-parity.test.ts`.

// ── Constants (PRD §F8.2 + spec verbatim) ─────────────────────────
// Severity threshold: ±5% yellow / ±10% red (PRD §F8.2 verbatim).
// Mirrors Python `packages.cost_engine/budget_variance.py::SEVERITY_THRESHOLD_*`.
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const SEVERITY_THRESHOLD_WARNING_PCT: number = 5;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const SEVERITY_THRESHOLD_CRITICAL_PCT: number = 10;

// Variance percentage quantum: 4 decimal places (banker's rounding).
// Mirrors Python `VARIANCE_PCT_QUANTUM`.
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const VARIANCE_PCT_DECIMAL_PLACES: number = 4;

// ABCD disabled note (PRD §15 NON-GOAL #1 + §10 M8 (b) verbatim).
// Mirrors Python `ABCD_DISABLED_NOTE`.
export const ABCD_DISABLED_NOTE: string =
  "[NON-GOAL for MVP: A×B×C×D 엔진 미구현]";

// Korean messages for HTTP envelopes (CR 12-5 D-14).
// Mirrors Python `BUDGET_VARIANCE_NOT_FOUND_KO` + `BUDGET_INVALID_VARIANCE_PERIOD_KO`.
export const BUDGET_VARIANCE_NOT_FOUND_MESSAGE_KO: string =
  "예산-실적 대조 데이터를 찾을 수 없습니다";
export const BUDGET_INVALID_VARIANCE_PERIOD_MESSAGE_KO: string =
  "예산-실적 대조 기간 키가 올바르지 않습니다";

// ── TS view model (mirror VarianceRowSerialized) ──────────────────
export type VarianceSeverity = "normal" | "warning" | "critical";
export type VarianceColor = "gray" | "yellow" | "red";

export interface VarianceRowSerialized {
  label: string;
  budget_value: string; // KRW integer, Decimal-as-string
  actual_value: string;
  difference: string;
  variance_pct: string; // 4 decimal places
  severity: VarianceSeverity;
  color: VarianceColor;
}

export interface ABCDDisabledBadgeSerialized {
  variant: "variance" | "trend" | "sensitivity";
  label: string;
  tooltip: string;
  disabled: true; // always true for 1차 MVP
}

export interface VarianceTableResponse {
  period_key: string; // AD-24 virtual YYYY-MM#B<n>
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  scenario_index: number; // 1차 MVP = 1 only
  rows: VarianceRowSerialized[];
  total_row: VarianceRowSerialized;
  abcd_disabled_badge: ABCDDisabledBadgeSerialized;
  abcd_disabled_note: string;
  trace_id: string | null;
}

export interface BudgetVariancePdfResponse {
  period_key: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  scenario_index: number;
  pdf_bytes_b64: string; // 8-2 placeholder empty; 8-3 follow-up real PDF
  envelope: Record<string, unknown>;
  trace_id: string | null;
}

// ── Error code SSOT (CR 12-5 D-14 typed envelope) ────────────────
// Mirrors Python main.py handler `code` field.
export const ERROR_CODE_BUDGET_VARIANCE_NOT_FOUND: string =
  "BUDGET_VARIANCE_NOT_FOUND" as const;
export const ERROR_CODE_INVALID_VARIANCE_PERIOD: string =
  "INVALID_VARIANCE_PERIOD" as const;

// ── Pure helpers (mirrors Python kernel) ──────────────────────────

/**
 * Compute variance from budget + actual (PRD §F8.2).
 * Returns null if budget is zero or inputs are invalid.
 */
export interface VarianceComputation {
  difference: string;
  variance_pct: string;
  severity: VarianceSeverity;
  color: VarianceColor;
}

export function computeVarianceTSToString(
  budgetValueStr: string,
  actualValueStr: string,
): VarianceComputation {
  const budget = Number(budgetValueStr);
  const actual = Number(actualValueStr);
  if (!Number.isFinite(budget) || !Number.isFinite(actual)) {
    return {
      difference: "0",
      variance_pct: "0",
      severity: "normal",
      color: "gray",
    };
  }
  const diff = actual - budget;
  // Avoid div-by-zero: budget=0 → variance_pct=0 (PRD §F8.2 verbatim).
  const variancePct =
    budget === 0 ? 0 : (diff / budget) * 100;
  const rounded = Number(variancePct.toFixed(VARIANCE_PCT_DECIMAL_PLACES));
  const absPct = Math.abs(rounded);

  let severity: VarianceSeverity = "normal";
  let color: VarianceColor = "gray";
  if (absPct >= SEVERITY_THRESHOLD_CRITICAL_PCT) {
    severity = "critical";
    color = "red";
  } else if (absPct >= SEVERITY_THRESHOLD_WARNING_PCT) {
    severity = "warning";
    color = "yellow";
  }

  return {
    difference: String(diff),
    variance_pct: String(rounded),
    severity,
    color,
  };
}

/**
 * Format KRW integer with 천단위 콤마 (AD-17 BigInteger parity).
 */
export function formatKRWTS(valueStr: string): string {
  const num = Number(valueStr);
  if (!Number.isFinite(num)) return valueStr;
  return num.toLocaleString("ko-KR");
}

/**
 * Format variance percentage with 부호 보존 (PRD §F8.2 verbatim).
 */
export function formatVariancePctTS(pctStr: string): string {
  const num = Number(pctStr);
  if (!Number.isFinite(num)) return pctStr;
  const sign = num > 0 ? "+" : num < 0 ? "" : "";
  return `${sign}${num.toFixed(VARIANCE_PCT_DECIMAL_PLACES)}%`;
}

/**
 * Korean label for 합계 row (PRD §F8.2 verbatim).
 */
export const TOTAL_ROW_LABEL_KO: string = "합계";

/**
 * Get Tailwind color class for variance row background.
 */
export function getVarianceColorClassTS(color: VarianceColor): string {
  switch (color) {
    case "red":
      return "bg-red-50";
    case "yellow":
      return "bg-yellow-50";
    case "gray":
    default:
      return "bg-gray-50";
  }
}

/**
 * Get Tailwind text color class for variance value.
 */
export function getVarianceTextClassTS(color: VarianceColor): string {
  switch (color) {
    case "red":
      return "text-red-700";
    case "yellow":
      return "text-yellow-700";
    case "gray":
    default:
      return "text-gray-700";
  }
}
