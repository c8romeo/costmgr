/**
 * apps/web/lib/bom-validation.ts — TS mirror of `packages/services/m1_baseline/bom_validation.py`.
 *
 * Story 2.2 — Task 5.5 mirror (drift-checked by `tests/integration/test_bom_validation_consistency.py`).
 *
 * Pure functions only — no DOM, no fetch, no clock. The matrix UI calls
 * these for the live "is_complete" check + "missing %" toast.
 *
 * Cross-language parity with Python:
 * - TARGET_TOTAL === Decimal("100.0000")
 * - sumRatios quantizes to 4 decimal places (ROUND_HALF_EVEN equivalent)
 * - isCompleteBom === sumRatios(...) === TARGET_TOTAL
 *
 * Uses `decimal.js` for arithmetic (AD-8 deferred — money paths use it;
 * ratio follows the same rule).
 */

import Decimal from "decimal.js";

// Configure Decimal for AD-8 + Story 0.4 chunk-B parity:
// ROUND_HALF_EVEN (= banker's rounding) for quantization.
Decimal.set({ rounding: Decimal.ROUND_HALF_EVEN });

/** Target total — 100.0000% (NUMERIC(7,4) precision). */
export const TARGET_TOTAL = new Decimal("100.0000");

/** Quantum — 4 decimal places. */
const QUANTUM = new Decimal("0.0001");

/**
 * Sum an iterable of ratios as Decimal with 4-decimal precision.
 *
 * Accepts `number`, `string`, or `Decimal`. Strings are parsed via
 * `Decimal(value)` so `"12.3456"` works. Non-numeric inputs throw.
 */
export function sumRatios(
  rows: Iterable<number | string | Decimal>,
): Decimal {
  let total = new Decimal(0);
  for (const r of rows) {
    if (r instanceof Decimal) {
      total = total.plus(r);
    } else if (typeof r === "number") {
      // Decimal() traps NaN / Infinity.
      total = total.plus(new Decimal(r));
    } else if (typeof r === "string") {
      total = total.plus(new Decimal(r));
    } else {
      throw new TypeError(
        `ratio must be Decimal, number, or string; got ${typeof r}`,
      );
    }
  }
  return total.toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN);
}

/**
 * Is the BOM complete? (A6 axiom: `sum === 100.0000`).
 *
 * Empty BOM is NOT complete. Over-100 is NOT complete. Only exactly
 * 100.0000 is complete.
 */
export function isCompleteBom(
  rows: Iterable<number | string | Decimal>,
): boolean {
  return sumRatios(rows).equals(TARGET_TOTAL);
}

/**
 * How much is needed to reach 100.0000%? Clamped at zero.
 */
export function missingToComplete(
  rows: Iterable<number | string | Decimal>,
): Decimal {
  const total = sumRatios(rows);
  const delta = TARGET_TOTAL.minus(total);
  if (delta.lessThanOrEqualTo(0)) return new Decimal("0.0000");
  return delta.toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN);
}

/**
 * Quantize a single ratio to 4 decimal places (ROUND_HALF_EVEN).
 *
 * Defense-in-depth — Pydantic should have caught invalid ratios at the
 * wire boundary. This is the last layer before the API call.
 */
export function quantizeRatio(value: Decimal | number | string): Decimal {
  if (value instanceof Decimal) {
    return value.toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN);
  }
  return new Decimal(value).toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN);
}

// ── BOM type rules (PRD §6.1) ───────────────────────────────────
// Mirrors `packages/services/m1_baseline/schemas.py::BOMParentType` / `BOMChildType`.

export const BOMParentTypes: ReadonlySet<ProductType> = new Set([
  "product",
  "semi_product",
]);

export const BOMChildTypes: ReadonlySet<ProductType> = new Set([
  "material",
  "semi_product",
]);

export function isValidBomParent(productType: ProductType): boolean {
  return BOMParentTypes.has(productType);
}

export function isValidBomChild(productType: ProductType): boolean {
  return BOMChildTypes.has(productType);
}

// We intentionally do NOT import ProductType to keep this module free of
// circular imports; the TS ProductType literal union lives in
// `apps/web/lib/api-client.ts`. The mirror test only checks string
// equality, so the union membership is implicit.
type ProductType =
  | "product"
  | "semi_product"
  | "material"
  | "goods"
  | "service";