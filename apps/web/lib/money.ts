/**
 * apps/web/lib/money.ts — AD-8 monetary types for the web side.
 *
 * AD-8 summary:
 *   - KRW ↔ `bigint` (1원 precision)
 *   - USD ↔ `string` (decimal.js serialized, NUMERIC(18,2) precision)
 *   - `number` is forbidden in money display / API code (ESLint
 *     `no-restricted-types` blocks it; this file has an override
 *     to allow `number` ONLY as the *input* to `toKRW` / `toUSD`).
 *
 * Display formatters centralize Intl.NumberFormat calls so locale
 * changes touch one place.
 */

import Decimal from "decimal.js";

/** KRW — wraps `bigint`. 1원 precision. Mirrors Python `int` (BIGINT in DB). */
export type KRW = bigint;

/** USD — wraps `string` (decimal.js serialized). Mirrors Python `Decimal` (NUMERIC(18,2) in DB). */
export type USD = string;

/** Money union type. */
export type Money = KRW | USD;

/**
 * Convert to KRW. Accepts `bigint | number | string` for input ergonomics
 * but the *result* is `bigint`. Fractional input is rounded to nearest int
 * (matches Python `round()` behavior at 0.5 boundaries).
 */
export function toKRW(value: bigint | number | string): KRW {
  if (typeof value === "bigint") return value;
  const n = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(n)) {
    throw new Error(`toKRW: input must be finite, got ${value}`);
  }
  return BigInt(Math.round(n));
}

/**
 * Convert to USD. Accepts `number | string` and produces a 2-decimal
 * decimal.js string (e.g. "1000.50"). Uses ROUND_HALF_EVEN (banker's
 * rounding) — matches Python `Decimal.quantize(Decimal("0.01"))`.
 */
export function toUSD(value: number | string): USD {
  return new Decimal(value).toFixed(2);
}

/** Format KRW with Korean locale: `1,000,000원`. */
export function formatKRW(krw: KRW): string {
  return `${krw.toLocaleString("ko-KR")}원`;
}

/** Format USD with US locale: `$1,000.00`. */
export function formatUSD(usd: USD): string {
  return `$${new Decimal(usd).toFixed(2)}`;
}

/**
 * Convert KRW to USD using an injected exchange rate (AD-9).
 * The rate is *not* hardcoded — callers must inject it from a market
 * data source (Story 6.2 KRW/USD dual display).
 *
 * @param krw   KRW integer (bigint)
 * @param rate  KRW per 1 USD (e.g. 1300.5 means 1 USD = 1,300.50 KRW)
 */
export function krwToUSD(krw: KRW, rate: number | string): USD {
  const r = new Decimal(rate);
  if (r.lte(0)) {
    throw new Error(`krwToUSD: rate must be positive, got ${rate}`);
  }
  return new Decimal(krw.toString()).div(r).toFixed(2);
}

/**
 * Convert USD to KRW using an injected exchange rate (AD-9).
 * Inverse of `krwToUSD`.
 */
export function usdToKRW(usd: USD, rate: number | string): KRW {
  const r = new Decimal(rate);
  if (r.lte(0)) {
    throw new Error(`usdToKRW: rate must be positive, got ${rate}`);
  }
  return BigInt(new Decimal(usd).mul(r).toFixed(0));
}

/**
 * Serialize KRW to string for API responses (JSON.stringify cannot
 * serialize BigInt directly). The inverse is `toKRW(stringValue)`.
 */
export function krwToString(krw: KRW): string {
  return krw.toString();
}

/**
 * Parse a serialized KRW string back to KRW.
 */
export function krwFromString(value: string): KRW {
  return BigInt(value);
}