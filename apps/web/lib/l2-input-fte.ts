/**
 * apps/web/lib/l2-input-fte.ts — TypeScript mirror of the
 * FTE precision pipeline defined in
 * `packages/services/m2_input/labor_conversion.py`.
 *
 * THIS FILE IS NOT THE SOURCE OF TRUTH. The Python module is canonical
 * (AD-23: one enum per module, one NamedTuple per domain constant).
 * Drift between this file and the Python helpers is caught by
 * `tests/integration/test_m2_input_label_consistency.py` (5 new cases
 * added in Story 3.2 — Task 4.2).
 *
 * Cross-language parity discipline (Story 3.2 §Task 4.1 dev notes):
 * - snake_case (Python) ↔ camelCase (TS) at the API boundary
 * - KRW is `bigint` (mirrors Python `int` / DB BIGINT) — see `money.ts`
 * - `company_burden_rate` is `Decimal` from `decimal.js` (mirrors Python
 *   `Decimal` / NUMERIC(5,4)) — `money.ts` already sets ROUND_HALF_EVEN
 * - Banker's rounding: `Math.round` is half-AWAY-FROM-ZERO; we implement
 *   `roundHalfEven` explicitly so cross-language parity is preserved
 *   (e.g., 0.5 → 0, 1.5 → 2, 2.5 → 2)
 * - Decimal operations must read/write through Decimal.js so float drift
 *   is contained (matches `np.quantize` semantics on Python side)
 */

import { Decimal } from "decimal.js";
import type { KRW } from "./money";

// ── PayType enum (PRD §6.1) ──────────────────────────────────────
// Mirrors `packages.services.m2_input.labor_conversion.PayType`.
export const PAY_TYPE_VALUES = ["monthly", "daily"] as const;
export type PayType = (typeof PAY_TYPE_VALUES)[number];

// ── PayrollSettings (PRD §6.1 인건비 정책) ──────────────────────
// All amounts in KRW (`bigint`) except `companyBurdenRate` (Decimal).
export interface PayrollSettings {
  monthlySalaryBasisKrw: KRW;
  workdaysInMonth: number;
  standardMonthlyHours: number;
  companyBurdenRate: Decimal;
}

/**
 * PRD §6.1 default payroll. Mirrors `DEFAULT_PAYROLL` in
 * `labor_conversion.py` exactly:
 *   - monthly_salary_basis_krw: 2,500,000
 *   - workdays_in_month:        22
 *   - standard_monthly_hours:   228 (PRD §6.1 209h → Story 3.2 raised to 228h
 *     = 22 × 8 + 4h weekly휴게 정리; aligned with HRIS baseline)
 *   - company_burden_rate:      0.115 (4대보험 + 퇴직 회사부담 평균)
 */
export const DEFAULT_PAYROLL: PayrollSettings = {
  monthlySalaryBasisKrw: 2_500_000n,
  workdaysInMonth: 22,
  standardMonthlyHours: 228,
  companyBurdenRate: new Decimal("0.115"),
};

/**
 * Per-field merge — partial override takes precedence; missing keys fall
 * back to `base`. Mirrors `merge_payroll_settings` in the Python module.
 *
 * AD-8: rejects out-of-range values (negative, rate ∉ [0,1], non-positive
 * workdays/hours). Mirrors the `ValueError` on the Python side so the
 * service-layer 400 envelope matches.
 */
export function mergePayrollSettings(
  override: Partial<PayrollSettings> | null | undefined,
  base: PayrollSettings = DEFAULT_PAYROLL,
): PayrollSettings {
  if (!override || Object.keys(override).length === 0) {
    return { ...base };
  }
  const settings: PayrollSettings = {
    monthlySalaryBasisKrw:
      override.monthlySalaryBasisKrw !== undefined
        ? BigInt(override.monthlySalaryBasisKrw as unknown as bigint)
        : base.monthlySalaryBasisKrw,
    workdaysInMonth:
      override.workdaysInMonth !== undefined
        ? Number(override.workdaysInMonth)
        : base.workdaysInMonth,
    standardMonthlyHours:
      override.standardMonthlyHours !== undefined
        ? Number(override.standardMonthlyHours)
        : base.standardMonthlyHours,
    companyBurdenRate:
      override.companyBurdenRate !== undefined
        ? new Decimal(override.companyBurdenRate as unknown as string)
        : base.companyBurdenRate,
  };
  // Range validation (mirrors Python `merge_payroll_settings`)
  if (settings.monthlySalaryBasisKrw < 0n) {
    throw new Error(
      `monthlySalaryBasisKrw must be non-negative, got ${settings.monthlySalaryBasisKrw}`,
    );
  }
  if (settings.workdaysInMonth < 1 || settings.workdaysInMonth > 31) {
    throw new Error(
      `workdaysInMonth must be in [1, 31], got ${settings.workdaysInMonth}`,
    );
  }
  if (settings.standardMonthlyHours <= 0) {
    throw new Error(
      `standardMonthlyHours must be > 0, got ${settings.standardMonthlyHours}`,
    );
  }
  if (
    settings.companyBurdenRate.lessThan(0) ||
    settings.companyBurdenRate.greaterThan(1)
  ) {
    throw new Error(
      `companyBurdenRate must be in [0, 1], got ${settings.companyBurdenRate.toString()}`,
    );
  }
  return settings;
}

/**
 * Round to 2 dp with ROUND_HALF_EVEN (banker's rounding).
 *
 * `Math.round` is HALF-AWAY-FROM-ZERO (0.5 → 1, -0.5 → 0), but
 * `Decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)` is
 * HALF-EVEN (0.5 → 0, 1.5 → 2, 2.5 → 2). Without this explicit helper
 * cross-language parity is broken at 0.5 boundaries — caught by the
 * `test_compute_fte_for_daily_matches_python` case.
 */
export function roundHalfEven2(n: Decimal | number): Decimal {
  const d = n instanceof Decimal ? n : new Decimal(n);
  // decimal.js `Decimal.ROUND_HALF_EVEN` set globally in `money.ts`
  return d.toDecimalPlaces(2, Decimal.ROUND_HALF_EVEN);
}

/**
 * PRD §6.1 인건비 breakdown for `pay_type='monthly'` rows.
 *
 * totalKrw = baseKrw + overtimeKrw + welfareKrw + bonusKrw
 *          + retirementReserveKrw × companyBurdenRate
 *
 * Mirrors `compute_pay_type_breakdown` exactly (single source of truth
 * — drift prevention).
 */
export interface PayTypeBreakdown {
  baseKrw: KRW;
  overtimeKrw: KRW;
  welfareKrw: KRW;
  bonusKrw: KRW;
  retirementReserveKrw: KRW;
  retirementBurdenKrw: KRW;
  companyBurdenRate: Decimal;
  totalKrw: KRW;
}

export function computePayTypeBreakdown(args: {
  monthlySalaryBasisKrw: KRW;
  overtimeKrw: KRW | 0;
  welfareKrw: KRW | 0;
  bonusKrw: KRW | 0;
  retirementReserveKrw: KRW | 0;
  companyBurdenRate: Decimal;
}): PayTypeBreakdown {
  const baseKrw = args.monthlySalaryBasisKrw;
  const overtimeKrw = BigInt(args.overtimeKrw ?? 0);
  const welfareKrw = BigInt(args.welfareKrw ?? 0);
  const bonusKrw = BigInt(args.bonusKrw ?? 0);
  const retirementReserveKrw = BigInt(args.retirementReserveKrw ?? 0);

  // retirement_burden = reserve × rate — round half-even to integer KRW
  const burden = new Decimal(retirementReserveKrw.toString())
    .mul(args.companyBurdenRate)
    .toDecimalPlaces(0, Decimal.ROUND_HALF_EVEN);
  const retirementBurdenKrw = BigInt(burden.toString());

  // total = base + overtime + welfare + bonus + burden
  const total = new Decimal(baseKrw.toString())
    .plus(new Decimal(overtimeKrw.toString()))
    .plus(new Decimal(welfareKrw.toString()))
    .plus(new Decimal(bonusKrw.toString()))
    .plus(burden)
    .toDecimalPlaces(0, Decimal.ROUND_HALF_EVEN);

  return {
    baseKrw,
    overtimeKrw,
    welfareKrw,
    bonusKrw,
    retirementReserveKrw,
    retirementBurdenKrw,
    companyBurdenRate: args.companyBurdenRate,
    totalKrw: BigInt(total.toString()),
  };
}

/**
 * FTE 환산 for `pay_type='daily'` rows.
 *
 *   fte_headcount = workers × daysPerWorker / payroll.workdaysInMonth
 *
 * Returns Decimal rounded to 2 dp (HALF_EVEN). String for serialization
 * stability — JS `Number` would lose precision on 0.01 boundary.
 *
 * Mirrors `compute_fte_for_daily` in the Python module.
 */
export function computeFteForDaily(
  workers: number,
  daysPerWorker: number,
  workdaysInMonth: number = DEFAULT_PAYROLL.workdaysInMonth,
): Decimal {
  if (workers <= 0 || daysPerWorker <= 0) return new Decimal("0.00");
  if (workdaysInMonth <= 0) {
    throw new Error(`workdaysInMonth must be > 0, got ${workdaysInMonth}`);
  }
  const raw = new Decimal(workers)
    .mul(daysPerWorker)
    .div(workdaysInMonth);
  return roundHalfEven2(raw);
}

/**
 * FTE 환산 for `pay_type='monthly'` rows.
 *
 *   fte_headcount = workers as-is (정규직 normalized)
 *
 * Mirrors `compute_fte_for_monthly` exactly. Note: Story 3.1's
 * `format_fte_headcount` was per-row aggregates only; Story 3.2 adds
 * per-pay-type dispatch here.
 */
export function computeFteForMonthly(workers: number): Decimal {
  if (workers <= 0) return new Decimal("0.00");
  return roundHalfEven2(workers);
}

/**
 * Direct-sum FTE wage for `pay_type='daily'` rows.
 *
 *   fte_wage_krw = daily_wage_krw × workers × days_per_worker
 *
 * NOTE: NOT multiplied by `monthly_salary_basis_krw` — that is only for
 * the 환산 path (basis 환산). The daily mode uses the actual wage
 * summed across workers/days. Mirrors `compute_fte_wage_for_daily`.
 */
export function computeFteWageForDaily(
  dailyWageKrw: KRW | number,
  workers: number,
  daysPerWorker: number,
): KRW {
  if (dailyWageKrw < 0 || workers < 0 || daysPerWorker < 0) {
    throw new Error(
      `daily_wage_krw/workers/days_per_worker must be non-negative, got ` +
        `(${dailyWageKrw}, ${workers}, ${daysPerWorker})`,
    );
  }
  if (dailyWageKrw === 0 || workers === 0 || daysPerWorker === 0) return 0n;
  const wage = BigInt(dailyWageKrw as unknown as bigint);
  return wage * BigInt(workers) * BigInt(daysPerWorker);
}

/**
 * Basis 환산 FTE wage for `pay_type='monthly'` rows.
 *
 *   fte_wage_krw = workers × breakdown.total_krw
 *
 * Mirrors `compute_fte_wage_for_monthly` exactly. Uses the breakdown's
 * total (which already includes the company burden).
 */
export function computeFteWageForMonthly(
  workers: number,
  breakdown: PayTypeBreakdown,
): KRW {
  if (workers <= 0) return 0n;
  if (workers < 0) {
    throw new Error(`workers must be non-negative, got ${workers}`);
  }
  return breakdown.totalKrw * BigInt(workers);
}

/**
 * Per-day roll-up for `mode='daily'` rows. Returns sum (NOT average —
 * month has 22 workdays, days × workers is the actual).
 *
 * Mirrors `rollup_daily_fte` in the Python module.
 */
export function rollupDailyFte(
  perDay: Array<{ fte: Decimal | string; wage: KRW | number }>,
): { fte: Decimal; wage: KRW } {
  if (perDay.length === 0) return { fte: new Decimal("0.00"), wage: 0n };
  let fteSum = new Decimal(0);
  let wageSum = 0n;
  for (const entry of perDay) {
    fteSum = fteSum.plus(new Decimal(entry.fte as unknown as string));
    wageSum = wageSum + BigInt(entry.wage as unknown as bigint);
  }
  return { fte: roundHalfEven2(fteSum), wage: wageSum };
}

/**
 * Compose `FteDisplay` from raw inputs — single composition function
 * mirroring `build_fte_display` in the Python module.
 */
export interface FteDisplay {
  payType: PayType;
  fteHeadcount: Decimal;
  fteWageKrw: KRW;
  breakdown: PayTypeBreakdown | null;
  sourceRows: number;
}

export function buildFteDisplay(args: {
  payType: PayType;
  workers: number;
  daysPerWorker: number | null;
  dailyWageKrw: KRW | null;
  monthlySalaryBasisKrw: KRW | null;
  overtimeKrw: KRW | null;
  welfareKrw: KRW | null;
  bonusKrw: KRW | null;
  retirementReserveKrw: KRW | null;
  companyBurdenRate: Decimal | null;
  payroll: PayrollSettings;
  sourceRows: number;
}): FteDisplay {
  if (args.payType === "daily") {
    if (
      args.dailyWageKrw === null ||
      args.daysPerWorker === null
    ) {
      throw new Error(
        "daily mode requires dailyWageKrw and daysPerWorker",
      );
    }
    const fteHeadcount = computeFteForDaily(
      args.workers,
      args.daysPerWorker,
      args.payroll.workdaysInMonth,
    );
    const fteWageKrw = computeFteWageForDaily(
      args.dailyWageKrw,
      args.workers,
      args.daysPerWorker,
    );
    return {
      payType: "daily",
      fteHeadcount,
      fteWageKrw,
      breakdown: null,
      sourceRows: args.sourceRows,
    };
  }
  // payType === 'monthly'
  if (
    args.monthlySalaryBasisKrw === null ||
    args.monthlySalaryBasisKrw < 0n
  ) {
    throw new Error(
      "monthly mode requires monthlySalaryBasisKrw >= 0",
    );
  }
  const breakdown = computePayTypeBreakdown({
    monthlySalaryBasisKrw: args.monthlySalaryBasisKrw,
    overtimeKrw: args.overtimeKrw ?? 0n,
    welfareKrw: args.welfareKrw ?? 0n,
    bonusKrw: args.bonusKrw ?? 0n,
    retirementReserveKrw: args.retirementReserveKrw ?? 0n,
    companyBurdenRate: args.companyBurdenRate ?? args.payroll.companyBurdenRate,
  });
  const fteHeadcount = computeFteForMonthly(args.workers);
  const fteWageKrw = computeFteWageForMonthly(args.workers, breakdown);
  return {
    payType: "monthly",
    fteHeadcount,
    fteWageKrw,
    breakdown,
    sourceRows: args.sourceRows,
  };
}
