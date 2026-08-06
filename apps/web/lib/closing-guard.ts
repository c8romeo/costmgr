/**
 * apps/web/lib/closing-guard.ts — Story 5.3 core types + state helpers.
 *
 * AD-15 §11 cross-language parity mirror of
 * `packages/services/m4_inventory/closing_guard.py`. Drift caught by
 * `tests/integration/test_closing_guard_label_consistency.py` (NEW 5-3).
 *
 * P26 (patch): Introduce `ClosingGuardState` aggregate + helpers so the
 * m2-input / m4-inventory tabs share one canonical state shape.
 *
 * P28 (patch): Severity sort uses `new Decimal(a.qty).minus(b.qty)`
 *   instead of `Number()` to avoid precision loss + NaN risk at high
 *   magnitudes (e.g. 1e15 boundaries).
 *
 * Pure-TS projection — no React, no DOM, no I/O. Consumed by:
 * - [수불부] tab red banner component
 * - Manual edit reject UI
 * - sonner toast on 409 NEGATIVE_CLOSING_INVENTORY response
 */

import { Decimal } from "decimal.js";

import {
  isCloseBlocked,
  NEGATIVE_CLOSING_INVENTORY_KO as _NEGATIVE_CLOSING_INVENTORY_KO_SSOT,
  formatNegativeClosingBannerKo as ssotFormatNegativeClosingBannerKo,
  type ClosingInvariant,
} from "./l2-input-inventory-ledger";

// P33+AD-15 §11 parity: inline literal declaration so the drift detector
// (`test_closing_guard_label_consistency.py`) can grep
// `NEGATIVE_CLOSING_INVENTORY_KO\s*=\s*"([^"]+)"` directly. Mirrors the
// Python kernel's `NEGATIVE_CLOSING_INVENTORY_KO: Final[str] = "..."`
// (closing_guard.py) and stays byte-identical. The local name shadows
// the import so this file is the authoritative TS mirror — downstream
// `closing-guard` import sites resolve to THIS value (drift detector
// anchor), which matches the Python SSOT exactly.
export const NEGATIVE_CLOSING_INVENTORY_KO = "기말재고 음수: 마감 불가";

// Re-export the upstream SSOT under a distinct alias for backward
// compatibility with existing call sites that still reference the
// sub-module name. Not a separate anchor — drift detector still uses
// the `NEGATIVE_CLOSING_INVENTORY_KO` local const above.
export const NEGATIVE_CLOSING_INVENTORY_KO_FROM_LEDGER = _NEGATIVE_CLOSING_INVENTORY_KO_SSOT;

export const INVARIANT_CODE_CLOSING_OK = "CLOSING_OK";
export const INVARIANT_CODE_NEGATIVE_CLOSING = "NEGATIVE_CLOSING";
export const INVARIANT_CODE_EMPTY_PERIOD = "EMPTY_PERIOD";

export const INVARIANT_CODES: ReadonlySet<string> = new Set([
  INVARIANT_CODE_CLOSING_OK,
  INVARIANT_CODE_NEGATIVE_CLOSING,
  INVARIANT_CODE_EMPTY_PERIOD,
]);

// ── Wire-format types (Pydantic extra='forbid' parity) ────────────
export interface ClosingGuardEvaluateResponse {
  period_key: string;
  code: string;
  closing_per_product: Record<string, string>;
  negative_products: Array<{ product_id: string; closing_qty: string }>;
  guard_enabled: boolean;
  banner_ko: string;
  trace_id: string;
}

export interface ClosingGuardCloseAttemptResponse {
  allowed: boolean;
  period_key: string;
  closing_per_product: Record<string, string>;
  invariant_code: string;
  trace_id: string;
}

export interface ClosingGuardAuditTrailEntry {
  trace_id: string;
  period_key: string;
  action: string;
  invariant_code: string;
  occurred_at: string;
  payload: Record<string, unknown>;
}

/**
 * P26: Aggregate guard state for the closing-guard UI.
 *
 * - `invariant`: full ClosingInvariant (mirrors Python kernel).
 * - `is_blocked`: True iff invariant.code = NEGATIVE_CLOSING.
 * - `negative_count`: number of products with closing < 0.
 * - `top_offenders`: top 5 by severity ASC (qty ASC). Each carries a
 *   `product_name` resolved from `productNames` (or first-8-chars UUID).
 */
export interface ClosingGuardState {
  invariant: ClosingInvariant;
  is_blocked: boolean;
  // AD-8: count (integer) — `number` allowed.
  /* eslint-disable-next-line @typescript-eslint/no-restricted-types */
  negative_count: number;
  top_offenders: Array<{
    product_id: string;
    qty: string;
    product_name: string;
  }>;
}

/**
 * P26: Build a `ClosingGuardState` from an invariant + optional
 * product-name lookup. Top-5 offenders slice (severity ASC) for the
 * banner detail list.
 */
export function buildClosingGuardState(
  invariant: ClosingInvariant,
  productNames: Record<string, string> = {},
): ClosingGuardState {
  const offenders = Object.entries(invariant.negative_products)
    .map(([product_id, qty]) => ({
      product_id,
      qty,
      product_name:
        productNames[product_id] ?? `product-${product_id.slice(0, 8)}`,
    }))
    .sort((a, b) =>
      new Decimal(a.qty).minus(new Decimal(b.qty)).toNumber(),
    )
    .slice(0, 5);
  return {
    invariant,
    is_blocked: isCloseBlocked(invariant),
    negative_count: Object.keys(invariant.negative_products).length,
    top_offenders: offenders,
  };
}

/**
 * P26: True iff the close button should be disabled. Mirrors
 * `shouldDisableCloseButton` Python kernel.
 */
export function shouldDisableCloseButton(state: ClosingGuardState): boolean {
  return state.is_blocked;
}

/**
 * P26: True iff the red banner should be visible. Banner is shown
 * whenever the close is blocked AND at least one product is negative.
 */
export function shouldShowRedBanner(state: ClosingGuardState): boolean {
  return state.is_blocked && state.negative_count > 0;
}

// ── Backward-compatible helpers (pre-P26 API) ─────────────────────

/**
 * Legacy helper preserved for existing call sites. Accepts either a
 * `ClosingInvariant` (NEW shape) or the legacy negative-products list
 * (OLD shape).
 *
 * P27 (patch): Signature matches Python's
 * `format_negative_closing_banner_ko(invariant, *, product_name_lookup=...)`.
 */
export function formatNegativeClosingBannerKo(
  invariantOrNegativeProducts:
    | ClosingInvariant
    | Array<{ product_id: string; closing_qty: string }>,
  productNameLookup: Record<string, string> = {},
): string {
  if (Array.isArray(invariantOrNegativeProducts)) {
    // Legacy: negative products list → derive banner ko
    if (invariantOrNegativeProducts.length === 0) {
      return NEGATIVE_CLOSING_INVENTORY_KO;
    }
    const sorted = [...invariantOrNegativeProducts]
      .map((p) => ({ ...p, _sort: Number(p.closing_qty) }))
      .sort((a, b) => a._sort - b._sort)
      .slice(0, 5);
    const top = sorted[0];
    const name =
      productNameLookup[top.product_id] ??
      `product-${top.product_id.slice(0, 8)}`;
    return `기말재고 음수: 마감 불가: ${name} ${top.closing_qty}개 → 마감 불가`;
  }
  // Forward to the P24/P27 SSOT formatter.
  return ssotFormatNegativeClosingBannerKo(
    invariantOrNegativeProducts,
    productNameLookup,
  );
}

/** Legacy helper preserved for existing call sites. */
export function shouldDisableCloseButtonFromCode(code: string): boolean {
  return code === INVARIANT_CODE_NEGATIVE_CLOSING;
}

/** Legacy helper preserved for existing call sites. */
export function shouldShowClosingGuardBanner(code: string): boolean {
  return code === INVARIANT_CODE_NEGATIVE_CLOSING;
}