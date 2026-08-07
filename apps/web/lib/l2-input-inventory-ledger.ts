// apps/web/lib/l2-input-inventory-ledger.ts — Story 5.2 W2 + Story 5.3 wire
//
// TS mirror of `packages/services/m4_inventory/closing_guard.py` + `ledger.py`.
// Consumed by:
// - [수불부] ClosingGuardBanner (red alert + top-5 offenders)
// - MonthlyInputTabs ([마감] gate)
// - ClosingGuardEvaluateResponse parsing (api-client.ts)
//
// AD-15 §11 parity: NEGATIVE_CLOSING_INVENTORY_KO constant + Python
// `format_negative_closing_banner_ko` mirror.
//
// PURE TYPESCRIPT — no React, no DOM, no I/O. Drift between this file
// and the Python helpers is caught by
// `tests/integration/test_closing_guard_label_consistency.py`.

import { Decimal } from "decimal.js";

/**
 * Korean message SSOT (AD-15 §11 parity).
 * Mirrors `packages.services.m4_inventory.closing_guard.NEGATIVE_CLOSING_INVENTORY_KO`.
 */
export const NEGATIVE_CLOSING_INVENTORY_KO = "기말재고 음수: 마감 불가";

/**
 * Ledger event-type discriminators (5-2 wire — 11-value whitelist).
 * Mirrors `EVENT_TYPE_*` constants in `packages/services/m4_inventory/ledger.py`.
 */
export type LedgerEventType =
  | "opening_carried"
  | "opening_carried_stale_overwrite"
  | "purchase_inbound"
  | "sales_outbound"
  | "production_output_inbound"
  | "production_material_consumption"
  | "adjustment_positive"
  | "adjustment_negative"
  | "reversal_negating"
  | "reversal_corrected"
  | "closing_snapshot";

/**
 * Ledger event shape (mirrors `InventoryLedgerEvent` 5-2 schema).
 * Wire format — every Decimal is serialized as a string.
 */
export interface LedgerEvent {
  event_id: string;
  product_id: string;
  period_key: string;
  event_type: LedgerEventType;
  qty: string | null;
  trace_id: string;
  reverses_event_id: string | null;
  correction_group_id: string | null;
}

/**
 * Closing balance per product (PRD §V3 — closing ≥ 0 invariant).
 */
export interface ClosingBalance {
  product_id: string;
  closing_qty: string;
}

/**
 * Closing invariant classification result (PRD §F4.2 + §V3).
 *
 * Mirrors Python `ClosingInvariant` NamedTuple:
 * - `code`: one of CLOSING_OK / NEGATIVE_CLOSING / EMPTY_PERIOD.
 * - `negative_products`: product_id → qty mapping (empty when not NEGATIVE_CLOSING).
 * - `closing_per_product`: product_id → qty mapping (empty when EMPTY_PERIOD).
 * - `guard_enabled`: True (service layer adjusts for industry skip matrix).
 */
export type ClosingInvariantCode =
  | "CLOSING_OK"
  | "NEGATIVE_CLOSING"
  | "EMPTY_PERIOD"
  // 5-3 P3-3rd-sweep P32: service-only tenant skip code (industry=SERVICE
  // → guard_enabled=false, no clamp). Mirrors
  // `packages/services/m4_inventory/closing_guard.py` SERVICE_ONLY_TENANT_SKIPPED.
  | "SERVICE_ONLY_TENANT_SKIPPED";

export interface ClosingInvariant {
  code: ClosingInvariantCode;
  negative_products: Record<string, string>;
  closing_per_product: Record<string, string>;
  guard_enabled: boolean;
}

/**
 * Classify closing balance per product (PRD §V3 + §F4.2).
 *
 * Mirrors `classify_closing_invariant` in
 * `packages/services/m4_inventory/closing_guard.py`:
 * - empty → `EMPTY_PERIOD`.
 * - any closing < 0 → `NEGATIVE_CLOSING`.
 * - all closing ≥ 0 → `CLOSING_OK`.
 */
export function classifyClosingInvariant(
  closing: ClosingBalance[],
): ClosingInvariant {
  const closing_per_product: Record<string, string> = {};
  const negative_products: Record<string, string> = {};
  for (const b of closing) {
    closing_per_product[b.product_id] = b.closing_qty;
    const qty = new Decimal(b.closing_qty);
    if (qty.isNegative()) {
      negative_products[b.product_id] = b.closing_qty;
    }
  }
  if (closing.length === 0) {
    return {
      code: "EMPTY_PERIOD",
      negative_products,
      closing_per_product,
      guard_enabled: true,
    };
  }
  if (Object.keys(negative_products).length > 0) {
    return {
      code: "NEGATIVE_CLOSING",
      negative_products,
      closing_per_product,
      guard_enabled: true,
    };
  }
  return {
    code: "CLOSING_OK",
    negative_products,
    closing_per_product,
    guard_enabled: true,
  };
}

/**
 * True iff `invariant.code === "NEGATIVE_CLOSING"` (PRD §F4.2 close-time gate).
 * Mirrors Python `is_close_blocked`.
 */
export function isCloseBlocked(invariant: ClosingInvariant): boolean {
  return invariant.code === "NEGATIVE_CLOSING";
}

/**
 * Build the Korean red-banner message for the closing-guard UI.
 *
 * P27 (patch): signature matches Python's
 * `format_negative_closing_banner_ko(invariant, *, product_name_lookup=...)`.
 *
 * Args:
 * - `invariant`: from `classifyClosingInvariant`. NEGATIVE_CLOSING for
 *   meaningful output; other codes → returns SSOT constant.
 * - `productNameLookup`: optional product_id → name_ko mapping.
 *   Missing keys fall back to first-8-chars UUID slice.
 *
 * Returns Korean message like
 *   `"기말재고 음수: 마감 불가: product-1234abcd -5개 → 마감 불가"`.
 */
export function formatNegativeClosingBannerKo(
  invariant: ClosingInvariant,
  productNameLookup: Record<string, string> = {},
): string {
  if (invariant.code !== "NEGATIVE_CLOSING") return NEGATIVE_CLOSING_INVENTORY_KO;
  const offenders = Object.entries(invariant.negative_products)
    .slice(0, 5)
    .map(([pid, qty]) => {
      const name = productNameLookup[pid] ?? `product-${pid.slice(0, 8)}`;
      return `${name} ${qty}개`;
    });
  if (offenders.length === 0) return NEGATIVE_CLOSING_INVENTORY_KO;
  return `${NEGATIVE_CLOSING_INVENTORY_KO}: ${offenders.join(", ")} → 마감 불가`;
}