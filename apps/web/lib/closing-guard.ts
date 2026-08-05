/**
 * apps/web/lib/closing-guard.ts — Story 5.3 TS projection of closing_guard pure kernel.
 *
 * AD-15 §11 cross-language parity mirror of
 * `packages/services/m4_inventory/closing_guard.py`. Drift caught by
 * `tests/integration/test_closing_guard_label_consistency.py` (NEW 5-3).
 *
 * Pure-TS projection — no React, no DOM, no I/O. Consumed by:
 * - [수불부] tab red banner component (T9 shadcn Tabs)
 * - Manual edit reject UI (T9 closing-guard gate)
 * - sonner toast on 409 NEGATIVE_CLOSING_INVENTORY response
 *
 * Invariant codes mirror the Python `INVARIANT_CODES` frozenset.
 * Korean message SSOT mirrors `NEGATIVE_CLOSING_INVENTORY_KO`.
 */

// ── Constants (Korean message SSOT — AD-15 §11) ─────────────────
export const NEGATIVE_CLOSING_INVENTORY_KO = "기말재고 음수: 마감 불가";

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

// ── AD-15 §11 parity: format_negative_closing_banner_ko ──────────
// Mirrors `packages.services.m4_inventory.closing_guard.format_negative_closing_banner_ko`.
export function formatNegativeClosingBannerKo(
  negativeProducts: Array<{ product_id: string; closing_qty: string }>,
): string {
  if (negativeProducts.length === 0) {
    return NEGATIVE_CLOSING_INVENTORY_KO;
  }
  // Top offender by severity ASC (closing_qty ASC — same as Python).
  // Sort numerically; pure-TS uses string-compare with locale-aware sort.
  const sorted = [...negativeProducts].sort((a, b) => {
    const aQty = Number(a.closing_qty);
    const bQty = Number(b.closing_qty);
    return aQty - bQty;
  });
  const top = sorted[0];
  const label = formatProductLabel(top.product_id);
  return `${NEGATIVE_CLOSING_INVENTORY_KO}: ${label} ${top.closing_qty}개 → 마감 불가`;
}

// ── Helper: short product label (mirrors Python `_format_uuid_label`) ──
function formatProductLabel(productId: string): string {
  return `product-${productId.slice(0, 8)}`;
}

// ── is_close_blocked mirror ─────────────────────────────────────
export function shouldDisableCloseButton(code: string): boolean {
  return code === INVARIANT_CODE_NEGATIVE_CLOSING;
}

// ── Tab red banner visibility ────────────────────────────────────
export function shouldShowClosingGuardBanner(code: string): boolean {
  return code === INVARIANT_CODE_NEGATIVE_CLOSING;
}