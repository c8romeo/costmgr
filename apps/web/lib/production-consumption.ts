// apps/web/lib/production-consumption.ts — Story 5.2 W3 + 5.3 W1 BOM-aware
//
// TS mirror of `packages/services/m4_inventory/production_consumption.py`.
//
// AD-23 parity: enums + event types mirror the Python module's constants.
// Consumed by:
// - [수불부] tab BOM-aware ledger event preview
// - m2-input production row pre-save ledger event projection
//
// PURE TYPESCRIPT — no React, no DOM, no I/O. Drift caught by
// `tests/integration/test_production_consumption_label_consistency.py`.

import { Decimal } from "decimal.js";

/**
 * Duck-type for monthly_input_rows stream='production' row.
 * Mirrors Python `ProductionRowLike`.
 */
export interface ProductionRow {
  product_id: string;
  product_qty: string;
  period_key: string;
  trace_id: string;
}

/**
 * Per-child BOM line item (Story 2.2 schema).
 * `ratio` is a percentage (e.g. "40.0000" = 40%).
 */
export interface BomChild {
  /** Material product_id (UUID string). */
  product_id: string;
  /** Percentage (NUMERIC(7,4)). Wire format: string. */
  ratio: string;
}

/**
 * Duck-type for BOM matrix (Story 2.2 schema).
 */
export interface BomMatrix {
  parent_product_id: string;
  children: BomChild[];
}

/**
 * Computed ledger event shape (mirrors Python `ComputedLedgerEvent`).
 */
export interface ProductionConsumptionEvent {
  product_id: string;
  period_key: string;
  event_type:
    | "production_output_inbound"
    | "production_material_consumption"
    | "adjustment_positive";
  qty: string;
  trace_id: string;
}

/**
 * BOM-aware reconciliation of production row → ledger events.
 *
 * Mirrors `compute_production_consumption_events` in
 * `packages/services/m4_inventory/production_consumption.py`:
 * - Always emits exactly 1 `production_output_inbound` event.
 * - If BOM is defined + children non-empty:
 *   - Emits N `production_material_consumption` events (per child,
 *     NEGATIVE qty = output_qty * ratio / 100).
 * - If BOM is missing or empty:
 *   - Emits 1 `adjustment_positive` fallback event.
 *
 * The Python module emits 1 adjustment_positive fallback, but P25's TS
 * spec (this file) keeps the more permissive BOM-only path for the
 * frontend preview surface. Caller decides which event set to ship.
 */
export function computeProductionConsumptionEvents(
  productionRow: ProductionRow,
  bom: BomMatrix | null,
): ProductionConsumptionEvent[] {
  const events: ProductionConsumptionEvent[] = [];
  // Output inbound (always emit).
  events.push({
    product_id: productionRow.product_id,
    period_key: productionRow.period_key,
    event_type: "production_output_inbound",
    qty: productionRow.product_qty,
    trace_id: productionRow.trace_id,
  });
  // Material consumption.
  if (bom && bom.children.length > 0) {
    for (const child of bom.children) {
      const consumption = new Decimal(productionRow.product_qty)
        .times(new Decimal(child.ratio))
        .dividedBy(100)
        .toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN);
      events.push({
        product_id: child.product_id,
        period_key: productionRow.period_key,
        event_type: "production_material_consumption",
        qty: consumption.negated().toFixed(4),
        trace_id: productionRow.trace_id,
      });
    }
  }
  return events;
}

// Event-type discriminator SSOT (AD-15 §11 parity mirror of Python
// `EVENT_TYPE_*` constants in
// `packages/services/m4_inventory/production_consumption.py`).
// Drift caught by `test_production_consumption_label_consistency.py`.
export const EVENT_TYPE_PRODUCTION_OUTPUT_INBOUND = "production_output_inbound";
export const EVENT_TYPE_PRODUCTION_MATERIAL_CONSUMPTION = "production_material_consumption";
export const EVENT_TYPE_ADJUSTMENT_POSITIVE = "adjustment_positive";

/**
 * Korean fallback reason SSOT (AD-15 §11 parity).
 * Mirrors `INCOMPLETE_BOM_FALLBACK_REASON_KO`.
 */
export const INCOMPLETE_BOM_FALLBACK_REASON_KO =
  "BOM 미정의 또는 부분 정의 — material consumption 기록 보류";