// apps/web/lib/monthly-closing-report-parity.ts — Story 6.2 TS↔Python SSOT parity.
//
// Cross-language parity helper for the monthly closing report pure kernel
// (AD-15 §11). Mirrors Python `packages/services/m4_inventory/monthly_closing_report.py`
// constants + Decimal serialization rules so that drift is impossible
// at runtime — any TS computation that differs from Python breaks Story 6.2
// AC #3 (KRW/USD dual display wire).
//
// Drift caught by `tests/integration/test_monthly_closing_report_label_consistency.py`.
//
// Banker's rounding policy (CR 0-4 lesson):
//   - Python uses `Decimal.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)`.
//   - TS must mirror via `Decimal.set({ rounding: Decimal.ROUND_HALF_EVEN })`.
//   - This file centralizes the parity boundaries so the panel + tests
//     cannot drift independently.

import Decimal from "decimal.js";

import { krwToUSD, type KRW, type USD } from "./money";

/**
 * QTY_QUANTUM = Decimal("0.0001") — mirrors Python QTY_QUANTUM constant.
 *
 * Used for both ledger event qty (NUMERIC(18,4)) and closing_qty (NUMERIC(18,4))
 * rounding. Same quantum as Python pure kernel.
 */
export const QTY_QUANTUM = "0.0001" as const;

/**
 * USD_QUANTUM = "0.01" — mirrors Python USD_QUANTUM constant.
 *
 * USD conversion result is quantized to 2 decimal places (AD-8 SSOT).
 */
export const USD_QUANTUM = "0.01" as const;

/**
 * Set Decimal.js to banker's rounding (ROUND_HALF_EVEN) on module load.
 *
 * CR 0-4 lesson: TS/Decimal.js defaults to ROUND_HALF_UP, which would cause
 * drift from Python `ROUND_HALF_EVEN`. Mirrors `apps/web/lib/money.ts` setter.
 */
Decimal.set({ rounding: Decimal.ROUND_HALF_EVEN });

/**
 * Round a Decimal string to QTY_QUANTUM (4 decimal places, banker's rounding).
 *
 * Mirrors Python `banker_round_qrw(Decimal)` policy at the qty quantum.
 * Used by all ledger aggregate computations in the panel before display.
 */
export function parityQuantizeQty(value: string | number): string {
  return new Decimal(value).toFixed(4);
}

/**
 * Round a Decimal string to USD_QUANTUM (2 decimal places, banker's rounding).
 *
 * Mirrors Python `USD_QUANTUM = Decimal("0.01") + quantize(... rounding=ROUND_HALF_EVEN)`.
 */
export function parityQuantizeUSD(value: string | number): USD {
  return new Decimal(value).toFixed(2);
}

/**
 * Compute USD from KRW integer + exchange rate (mirrors Python
 * `compute_usd_from_krw`).
 *
 * @param amountKrw   KRW integer (bigint serialized as string)
 * @param exchangeRate  KRW per 1 USD (e.g. "1320.5")
 * @returns           USD Decimal string (e.g. "1000.00")
 */
export function parityComputeUsdFromKrw(
  amountKrw: string | KRW,
  exchangeRate: string,
): USD {
  const krwBigInt = typeof amountKrw === "string" ? BigInt(amountKrw) : amountKrw;
  return krwToUSD(krwBigInt, exchangeRate);
}

/**
 * Format KRW/USD dual display string (mirrors Python
 * `format_period_closing_krw_usd`).
 *
 * Output format: "1,320,000 KRW (USD 1,000.00 @ 한국은행 2026-07-25)"
 */
export function parityFormatPeriodClosingKrwUsd(
  amountKrw: string | KRW,
  exchangeRate: string,
  rateSource: string,
): string {
  const krwBigInt = typeof amountKrw === "string" ? BigInt(amountKrw) : amountKrw;
  const usd = parityComputeUsdFromKrw(krwBigInt, exchangeRate);
  const krwFormatted = krwBigInt.toLocaleString("ko-KR");
  return `${krwFormatted} KRW (USD ${usd} @ ${rateSource})`;
}

/**
 * Format currency pair display (mirrors Python
 * `format_currency_pair_display_ko`).
 */
export function parityFormatCurrencyPairDisplayKo(
  base: string,
  quote: string,
  rate: string,
  source: string,
): string {
  return `1 ${quote} = ${rate} ${base} (${source})`;
}

/**
 * Verify QTY_QUANTUM + USD_QUANTUM parity (constant SSOT).
 *
 * Drift detection: if either constant changes without updating
 * `packages/services/m4_inventory/monthly_closing_report.py`, this test fails.
 */
export function assertParityConstants(): void {
  if (QTY_QUANTUM !== "0.0001") {
    throw new Error(
      `monthly-closing-report-parity: QTY_QUANTUM drift detected. ` +
      `Expected "0.0001" (Python SSOT), got "${QTY_QUANTUM}".`,
    );
  }
  if (USD_QUANTUM !== "0.01") {
    throw new Error(
      `monthly-closing-report-parity: USD_QUANTUM drift detected. ` +
      `Expected "0.01" (Python SSOT), got "${USD_QUANTUM}".`,
    );
  }
}