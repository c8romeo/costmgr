// apps/web/lib/m11-reversal-parity.ts — Story 11.1 TS↔Python SSOT parity helper.
//
// Decimal serialization + sign-negating arithmetic + banker's rounding
// parity with Python `packages/services/m11_close/reversal_negating.py`
// + `reversal_corrected.py`. CR 0-4 / CR 5-2 lesson: banker's rounding
// (ROUND_HALF_EVEN) at QTY_QUANTUM = Decimal("0.0001") (NUMERIC(18,4)).
//
// Drift caught by `tests/integration/test_m11_reversal_label_consistency.py`.

import { Decimal } from "decimal.js";

// ── Constants ──────────────────────────────────────────────────
export const QTY_QUANTUM = "0.0001" as const;

// ── quantizeDecimal (banker's rounding parity helper) ──────────
// Mirrors Python `Decimal.quantize(QTY_QUANTUM, rounding=ROUND_HALF_EVEN)`.
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function quantizeDecimal(value: string | number): string {
  return new Decimal(value).toFixed(4, Decimal.ROUND_HALF_EVEN);
}

// ── negateQty (sign-negating arithmetic — banker's rounding) ──
// Mirrors Python `(-target.qty).quantize(QTY_QUANTUM, ROUND_HALF_EVEN)`.
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function negateQty(targetQty: string | number): string {
  const negated = new Decimal(targetQty).negated();
  return negated.toFixed(4, Decimal.ROUND_HALF_EVEN);
}

// ── correctedQty (corrected row qty — banker's rounding) ──────
// Mirrors Python `corrected_qty.quantize(QTY_QUANTUM, ROUND_HALF_EVEN)`.
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function correctedQty(inputQty: string | number): string {
  return quantizeDecimal(inputQty);
}

// ── isReversalQtyParity (parity check — TS vs Python wire shape) ──
// Verifies that two qty strings (TS computed + Python wire) match
// exactly at NUMERIC(18,4) precision + ROUND_HALF_EVEN rounding.
export function isReversalQtyParity(
  tsQty: string,
  pythonQty: string,
): boolean {
  return quantizeDecimal(tsQty) === quantizeDecimal(pythonQty);
}

// ── formatReversalParityAssertionKo (Korean parity error message) ──
export function formatReversalParityAssertionKo(
  field: string,
  tsValue: string,
  pythonValue: string,
): string {
  return `AD-15 §11 parity mismatch — ${field}: TS=${tsValue}, Python=${pythonValue}`;
}
