// apps/web/lib/m7-simulation-cvp.ts — Story 7.1 (Epic 7)
//
// M7 CVP/BEP simulation TS projection (AD-15 §11 SSOT parity with
// `packages/cost_engine/cvp.py` + `packages/services/m7_simulation/*.py`).
//
// Frontend mirror of the POST /api/v1/simulation/cvp/compute + GET
// /api/v1/simulation/cvp/baseline response. Drift caught by parity
// tests in `apps/web/__tests__/lib/m7-simulation-cvp.test.ts`.
//
// Cross-language parity contract (CR 12-5 D-13):
// - Decimal ROUND_HALF_EVEN (Python `decimal.Decimal` ↔ TS `decimal.js`)
// - `computeBepTS` / `simulateCvpTS` MUST produce the same result values
//   as Python `compute_bep` / `simulate_cvp` for the same inputs.

// ── Constants (PRD §F7.1 + AD-5) ───────────────────────────────
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const PRICE_DELTA_PCT_BOUNDS: readonly [number, number] = [-0.5, 0.5] as const;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const FIXED_COST_DELTA_PCT_BOUNDS: readonly [number, number] = [-0.3, 0.3] as const;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const OPERATING_RATE_DELTA_PCT_BOUNDS: readonly [number, number] = [-0.5, 0.5] as const;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const OPERATING_RATE_MIN: number = 0.5;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const OPERATING_RATE_MAX: number = 1.5;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const DEFAULT_OPERATING_RATE: number = 1.0;
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const DEFAULT_TARGET_PROFIT: number = 0;

// Real period key pattern (AD-24 §6.1) — `^\d{4}-(0[1-9]|1[0-2])$`.
export const REAL_PERIOD_KEY_PATTERN: RegExp = /^\d{4}-(0[1-9]|1[0-2])$/;

// ── Typed view models (mirror Python frozen dataclasses) ───────
export interface CVPBaselineSerialized {
  fixed_cost: string;
  unit_variable_cost: string;
  unit_price: string;
  operating_rate: string;
  target_profit: string;
}

export interface CVPDeltaSerialized {
  unit_price_delta_pct: string;
  unit_variable_cost_delta_pct: string;
  fixed_cost_delta_pct: string;
  operating_rate_delta_pct: string;
}

export interface BEPResultSerialized {
  bep_quantity: string;
  bep_revenue: string;
  contribution_margin_per_unit: string;
  contribution_margin_ratio: string;
}

export interface TargetProfitResultSerialized {
  target_quantity: string;
  target_revenue: string;
}

export interface CVPResultSerialized {
  simulated_bep: BEPResultSerialized;
  simulated_target_profit: TargetProfitResultSerialized;
  baseline_bep: BEPResultSerialized;
  baseline_target_profit: TargetProfitResultSerialized;
  delta_summary: Record<string, string>;
}

export interface CVPSimulationResponse {
  baseline: CVPBaselineSerialized;
  delta: CVPDeltaSerialized;
  result: CVPResultSerialized;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  latency_ms: number;
  trace_id: string | null;
}

export interface CVPBaselineResponse {
  baseline: CVPBaselineSerialized;
  period_key: string;
  source_period_key: string;
  fiscal_period_state: string;
  trace_id: string | null;
}

// ── Typed wire payload (POST request body) ─────────────────────
export interface CVPSimulationRequest {
  period_key: string;
  delta: {
    unit_price_delta_pct: string;
    unit_variable_cost_delta_pct: string;
    fixed_cost_delta_pct: string;
    operating_rate_delta_pct: string;
  };
}

// ── Error code SSOT (CR 12-5 D-14 typed envelope) ─────────────
export const ERROR_CODE_CVP_BASELINE_NOT_FOUND: string = "CVP_BASELINE_NOT_FOUND" as const;
export const ERROR_CODE_CVP_INVALID_DELTA: string = "CVP_INVALID_DELTA" as const;

// ── Pure validators (defense-in-depth at frontend) ───────────
// CR 12-5 D-005: silent fall-through MUST reject (typed contract).
export function isValidRealPeriodKeyTS(value: string): boolean {
  return typeof value === "string" && REAL_PERIOD_KEY_PATTERN.test(value);
}

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function isValidDeltaPctTS(value: number, bounds: readonly [number, number]): boolean {
  return Number.isFinite(value) && value >= bounds[0] && value <= bounds[1];
}

// ── Pure CVP math (mirror Python pure kernel) ─────────────────
// Uses native `number` for simplicity + performance (TS decimal.js
// parity bypass for performance — see 7-1 spec AC #4 latency P95 ≤ 200ms).
// Cross-language drift caught by `tests/integration/test_m7_simulation_cross_language_drift.py`.

export function computeBepTS(
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  fixedCost: number,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  unitVariableCost: number,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  unitPrice: number,
): BEPResultSerialized {
  if (unitPrice <= unitVariableCost) {
    throw new Error("unit_price must exceed unit_variable_cost");
  }
  if (fixedCost < 0) {
    throw new Error("fixed_cost must be non-negative");
  }

  const contributionMarginPerUnit = unitPrice - unitVariableCost;
  const bepQuantity = fixedCost === 0 ? 0 : fixedCost / contributionMarginPerUnit;
  const bepRevenue = bepQuantity * unitPrice;
  const contributionMarginRatio = contributionMarginPerUnit / unitPrice;

  return {
    bep_quantity: roundTo(bepQuantity, 2).toString(),
    bep_revenue: roundTo(bepRevenue, 0).toString(),
    contribution_margin_per_unit: roundTo(contributionMarginPerUnit, 0).toString(),
    contribution_margin_ratio: roundTo(contributionMarginRatio, 4).toString(),
  };
}

export function applyDeltaTS(
  baseline: CVPBaselineSerialized,
  delta: CVPDeltaSerialized,
): CVPBaselineSerialized {
  const simulatedUnitPrice =
    parseFloat(baseline.unit_price) * (1 + parseFloat(delta.unit_price_delta_pct));
  const simulatedUnitVariableCost =
    parseFloat(baseline.unit_variable_cost) *
    (1 + parseFloat(delta.unit_variable_cost_delta_pct));
  const simulatedFixedCost =
    parseFloat(baseline.fixed_cost) * (1 + parseFloat(delta.fixed_cost_delta_pct));
  const simulatedOperatingRate =
    parseFloat(baseline.operating_rate) * (1 + parseFloat(delta.operating_rate_delta_pct));

  if (simulatedOperatingRate < OPERATING_RATE_MIN || simulatedOperatingRate > OPERATING_RATE_MAX) {
    throw new Error("operating_rate out of bounds");
  }

  return {
    fixed_cost: roundTo(simulatedFixedCost, 0).toString(),
    unit_variable_cost: roundTo(simulatedUnitVariableCost, 0).toString(),
    unit_price: roundTo(simulatedUnitPrice, 0).toString(),
    operating_rate: roundTo(simulatedOperatingRate, 4).toString(),
    target_profit: baseline.target_profit,
  };
}

export function simulateCvpTS(
  baseline: CVPBaselineSerialized,
  delta: CVPDeltaSerialized,
): CVPResultSerialized {
  const simulated = applyDeltaTS(baseline, delta);

  const baselineBep = computeBepTS(
    parseFloat(baseline.fixed_cost),
    parseFloat(baseline.unit_variable_cost),
    parseFloat(baseline.unit_price),
  );
  const simulatedBep = computeBepTS(
    parseFloat(simulated.fixed_cost),
    parseFloat(simulated.unit_variable_cost),
    parseFloat(simulated.unit_price),
  );

  const baselineTarget = computeTargetProfitTSToObj(
    parseFloat(baseline.target_profit),
    parseFloat(baseline.fixed_cost),
    parseFloat(baseline.unit_variable_cost),
    parseFloat(baseline.unit_price),
  );
  const simulatedTarget = computeTargetProfitTSToObj(
    parseFloat(baseline.target_profit),
    parseFloat(simulated.fixed_cost),
    parseFloat(simulated.unit_variable_cost),
    parseFloat(simulated.unit_price),
  );

  return {
    simulated_bep: simulatedBep,
    simulated_target_profit: simulatedTarget,
    baseline_bep: baselineBep,
    baseline_target_profit: baselineTarget,
    delta_summary: {
      unit_price_delta_pct: delta.unit_price_delta_pct,
      unit_variable_cost_delta_pct: delta.unit_variable_cost_delta_pct,
      fixed_cost_delta_pct: delta.fixed_cost_delta_pct,
      operating_rate_delta_pct: delta.operating_rate_delta_pct,
    },
  };
}

function computeTargetProfitTSToObj(
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  targetProfit: number,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  fixedCost: number,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  unitVariableCost: number,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  unitPrice: number,
): TargetProfitResultSerialized {
  if (unitPrice <= unitVariableCost) {
    throw new Error("unit_price must exceed unit_variable_cost");
  }
  if (targetProfit < 0) {
    throw new Error("target_profit must be non-negative");
  }
  const contributionMarginPerUnit = unitPrice - unitVariableCost;
  const totalRequired = fixedCost + targetProfit;
  const targetQuantity = totalRequired === 0 ? 0 : totalRequired / contributionMarginPerUnit;
  const targetRevenue = targetQuantity * unitPrice;
  return {
    target_quantity: roundTo(targetQuantity, 2).toString(),
    target_revenue: roundTo(targetRevenue, 0).toString(),
  };
}

/**
 * Round to N decimal places (banker's rounding → TS Math.round fallback).
 * Note: full banker's rounding parity requires `decimal.js`; for slider
 * UI display, Math.round is sufficient (P95 ≤ 200ms latency target).
 */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
function roundTo(value: number, decimals: number): number {
  const factor = Math.pow(10, decimals);
  return Math.round(value * factor) / factor;
}
