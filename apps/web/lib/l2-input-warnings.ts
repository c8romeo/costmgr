/**
 * apps/web/lib/l2-input-warnings.ts — TypeScript mirror of the
 * warning aggregate kernel defined in
 * `packages/services/m2_input/{inventory_projection,operating_rate,warnings}.py`.
 *
 * THIS FILE IS NOT THE SOURCE OF TRUTH. The Python module is canonical
 * (AD-23: one enum per module, one NamedTuple per domain constant).
 * Drift between this file and the Python helpers is caught by
 * `tests/integration/test_m2_input_label_consistency.py` (Story 3.3
 * adds 5 more cases — Task 5).
 *
 * Cross-language parity discipline (Story 3.3 §Task 5 dev notes):
 * - snake_case (Python) ↔ camelCase (TS) at the API boundary
 * - `Decimal` flows through decimal.js with `ROUND_HALF_EVEN` globally
 *   set by `money.ts` — banker's rounding parity with Python
 * - JSON serialization: `qty` / `operating_rate_pct` / etc. are sent
 *   as ISO-8601 strings (decimal.js `toFixed(4)` for qty, `toFixed(2)`
 *   for rates — see test_m2_input_label_consistency for boundary
 *   fixtures). The Python side strips trailing zeros.
 * - `details: { [key: string]: string | number }` — structured payload
 *   for the toast UI to render codes, qty, percentages. Free-form
 *   per the Python `dict` shape.
 * - `trace_id: string` — round-tripped for support diagnostics.
 *
 * MVP scope (Story 3.3):
 * - 2 warning codes: NEGATIVE_CLOSING_INVENTORY, OVERCAPACITY_OPERATING_RATE
 * - aggregate by severity ASC + closing_qty ASC (PRD §A11 §V3 · §V5)
 * - `isBlocked = warnings.length > 0` (PRD §A11 input-time)
 *
 * Epic 5 marker: when Story 5-1 / 5-2 ships, the inventory projection
 * kernel reads from `inventory_ledger`; this file gets a TS mirror too.
 */

import { Decimal } from "decimal.js";

// ── WarningCode enum (PRD §V3 · §V5) ────────────────────────────
// Mirrors `packages.services.m2_input.warnings.WarningCode`.
export const WARNING_CODE_VALUES = [
  "NEGATIVE_CLOSING_INVENTORY",
  "OVERCAPACITY_OPERATING_RATE",
] as const;
export type WarningCodeValue = (typeof WARNING_CODE_VALUES)[number];

// PRD §A11 severity ordering — error=0, warning=1, info=2.
export const SEVERITY_ORDER: Readonly<Record<string, number>> = {
  error: 0,
  warning: 1,
  info: 2,
};

// ── Warning shape (mirrors `Warning` NamedTuple) ────────────────
export interface Warning {
  code: WarningCodeValue;
  severity: "error" | "warning" | "info";
  messageKo: string;
  details: Record<string, string | number>;
  stream: string;
  traceId: string;
  timestamp: string; // ISO-8601 UTC
}

// ── Inventory projection (PRD §6.2 수불부) ──────────────────────
// Inventory-bearing product types (mirrors `INVENTORY_PRODUCT_TYPES`).
export const INVENTORY_PRODUCT_TYPES: ReadonlySet<string> = new Set([
  "material",
  "semi_product",
  "product",
]);

// Decimal quantization for qty — NUMERIC(18,4) per PRD §6.1.
const QTY_QUANTUM = new Decimal("0.0001");

export interface InventoryMovement {
  productId: string; // UUID as string (matches `details.product_id`)
  openingQty: Decimal;
  inboundQty: Decimal;
  outboundQty: Decimal;
}

export interface InventoryProjectionRowLike {
  stream: string;
  productId: string | null;
  qty: Decimal | number | string | null;
  productType: string;
}

/** PRD §6.2: closing = opening + inbound − outbound. */
export function computeClosingInventory(
  opening: Decimal | number | string,
  inbound: Decimal | number | string,
  outbound: Decimal | number | string,
): Decimal {
  const o = new Decimal(opening);
  const i = new Decimal(inbound);
  const out = new Decimal(outbound);
  return o.plus(i).minus(out).toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN);
}

/**
 * Build per-product inventory movements from a list of rows.
 * Mirrors `build_inventory_projection` in the Python module exactly.
 *
 * Stream mapping (PRD §6.2):
 *  - sales → outbound
 *  - purchases → inbound
 *  - production → inbound (output; material consumption = Epic 5)
 *
 * Only rows whose `productType ∈ INVENTORY_PRODUCT_TYPES` are tracked.
 */
export function buildInventoryProjection(
  rows: InventoryProjectionRowLike[],
  openingBalance: Record<string, Decimal | number | string> | null,
): InventoryMovement[] {
  // product_id → running aggregate
  const bucket = new Map<
    string,
    { inbound: Decimal; outbound: Decimal }
  >();

  for (const row of rows) {
    if (row.productId === null || row.qty === null) continue;
    if (!INVENTORY_PRODUCT_TYPES.has(row.productType)) continue;
    const qty = new Decimal(row.qty);
    if (qty.isZero()) continue;

    let slot = bucket.get(row.productId);
    if (!slot) {
      slot = { inbound: new Decimal(0), outbound: new Decimal(0) };
      bucket.set(row.productId, slot);
    }

    if (row.stream === "sales") {
      slot.outbound = slot.outbound.plus(qty);
    } else if (row.stream === "purchases") {
      slot.inbound = slot.inbound.plus(qty);
    } else if (row.stream === "production") {
      slot.inbound = slot.inbound.plus(qty);
    }
    // orders / expenses / labor → ignored
  }

  const sortedKeys = Array.from(bucket.keys()).sort();
  const out: InventoryMovement[] = [];
  for (const productId of sortedKeys) {
    const slot = bucket.get(productId)!;
    const opening = openingBalance?.[productId]
      ? new Decimal(openingBalance[productId])
      : new Decimal(0);
    out.push({
      productId,
      openingQty: opening.toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN),
      inboundQty: slot.inbound.toDecimalPlaces(
        4,
        Decimal.ROUND_HALF_EVEN,
      ),
      outboundQty: slot.outbound.toDecimalPlaces(
        4,
        Decimal.ROUND_HALF_EVEN,
      ),
    });
  }
  return out;
}

// ── Operating rate (PRD §6.1 (2) 조업도) ─────────────────────────
const DEFAULT_UNIT_TIME_HOURS = new Decimal("1.0");
const OPERATING_RATE_LIMIT_PCT = new Decimal("100");

export function computeTotalAvailableHours(
  totalFteHeadcount: Decimal | number | string,
  standardMonthlyHours: number,
): Decimal {
  const fte = new Decimal(totalFteHeadcount);
  if (fte.lte(0) || standardMonthlyHours <= 0) {
    return new Decimal("0.00");
  }
  return fte
    .mul(standardMonthlyHours)
    .toDecimalPlaces(2, Decimal.ROUND_HALF_EVEN);
}

export function computeProductionRequiredHours(
  productionRows: Array<{ qty: Decimal | number | string | null }>,
  unitTimeHours: Decimal | number | string = DEFAULT_UNIT_TIME_HOURS,
): Decimal {
  if (productionRows.length === 0) return new Decimal("0.00");
  const u = new Decimal(unitTimeHours);
  if (u.lte(0)) return new Decimal("0.00");
  let total = new Decimal(0);
  for (const row of productionRows) {
    if (row.qty !== null && row.qty !== undefined) {
      total = total.plus(new Decimal(row.qty));
    }
  }
  return total.mul(u).toDecimalPlaces(2, Decimal.ROUND_HALF_EVEN);
}

export function computeOperatingRate(
  availableHours: Decimal | number | string,
  requiredHours: Decimal | number | string,
): Decimal {
  const a = new Decimal(availableHours);
  const r = new Decimal(requiredHours);
  if (a.lte(0) || r.lte(0)) return new Decimal("0.00");
  return r.div(a).mul(100).toDecimalPlaces(2, Decimal.ROUND_HALF_EVEN);
}

// ── Trailing-zero strip (matches Python `_strip_zeros`) ─────────
// Cross-language parity helper. AC #1 spec uses "100" not "100.00".
function stripZeros(d: Decimal | number | string): string {
  const fixed = new Decimal(d).toFixed(2);
  if (!fixed.includes(".")) return fixed;
  return fixed.replace(/0+$/, "").replace(/\.$/, "") || "0";
}

// ── Korean message formatters (PRD §V3 · §V5) ───────────────────
export interface ProductLikeForWarning {
  productCode: string;
  nameKo: string;
}

export function formatInventoryWarningKo(
  product: ProductLikeForWarning,
  projection: InventoryMovement,
): string {
  const closing = computeClosingInventory(
    projection.openingQty,
    projection.inboundQty,
    projection.outboundQty,
  );
  const name = product.nameKo || "";
  if (name) {
    return `${product.productCode}(${name}) 기말재고 ${stripZeros(
      closing,
    )} → 음수 경고`;
  }
  return `${product.productCode} 기말재고 ${stripZeros(closing)} → 음수 경고`;
}

export interface FormatOperatingRateArgs {
  totalFteHeadcount: Decimal | number | string;
  standardMonthlyHours: number;
  totalAvailableHours: Decimal | number | string;
  productionRequiredHours: Decimal | number | string;
  operatingRatePct: Decimal | number | string;
}

export function formatOperatingRateKo(args: FormatOperatingRateArgs): string {
  return (
    `총작업가능시간 ${stripZeros(args.totalAvailableHours)}h` +
    `(${stripZeros(args.totalFteHeadcount)} × ${args.standardMonthlyHours}) ` +
    `< 생산요구시간 ${stripZeros(args.productionRequiredHours)}h ` +
    `→ ${stripZeros(args.operatingRatePct)}% (한도 초과)`
  );
}

// ── build_inventory_warnings ─────────────────────────────────────
export interface BuildInventoryWarningsArgs {
  projection: InventoryMovement[];
  productMap: Record<string, ProductLikeForWarning>;
  traceId?: string;
  now?: () => Date;
}

/**
 * Build NEGATIVE_CLOSING_INVENTORY warnings (PRD §V3).
 * Mirrors `build_inventory_warnings` in `warnings.py` exactly.
 */
export function buildInventoryWarnings(
  args: BuildInventoryWarningsArgs,
): Warning[] {
  const { projection, productMap, traceId = "", now = () => new Date() } = args;
  const ts = now().toISOString();
  const warnings: Warning[] = [];
  for (const m of projection) {
    const closing = computeClosingInventory(
      m.openingQty,
      m.inboundQty,
      m.outboundQty,
    );
    if (closing.gte(0)) continue;
    const product = productMap[m.productId] ?? {
      productCode: m.productId,
      nameKo: "",
    };
    warnings.push({
      code: "NEGATIVE_CLOSING_INVENTORY",
      severity: "error",
      messageKo: formatInventoryWarningKo(product, m),
      details: {
        product_id: m.productId,
        product_code: product.productCode,
        opening_qty: stripZeros(m.openingQty),
        inbound_qty: stripZeros(m.inboundQty),
        outbound_qty: stripZeros(m.outboundQty),
        closing_qty: stripZeros(closing),
        stream: "sales",
      },
      stream: "sales",
      traceId,
      timestamp: ts,
    });
  }
  // Sort by closing_qty ASC (most negative first) — same as Python.
  warnings.sort((a, b) => {
    const ca = Number(a.details.closing_qty);
    const cb = Number(b.details.closing_qty);
    return ca - cb;
  });
  return warnings;
}

// ── build_operating_rate_warning ─────────────────────────────────
export interface BuildOperatingRateWarningArgs {
  operatingRatePct: Decimal | number | string;
  totalFteHeadcount: Decimal | number | string;
  standardMonthlyHours: number;
  totalAvailableHours: Decimal | number | string;
  productionRequiredHours: Decimal | number | string;
  periodKey: string;
  traceId?: string;
  now?: () => Date;
}

export function buildOperatingRateWarning(
  args: BuildOperatingRateWarningArgs,
): Warning | null {
  const {
    operatingRatePct,
    totalFteHeadcount,
    standardMonthlyHours,
    totalAvailableHours,
    productionRequiredHours,
    periodKey,
    traceId = "",
    now = () => new Date(),
  } = args;
  const rate = new Decimal(operatingRatePct);
  if (rate.lte(OPERATING_RATE_LIMIT_PCT)) return null;
  return {
    code: "OVERCAPACITY_OPERATING_RATE",
    severity: "error",
    messageKo: formatOperatingRateKo({
      totalFteHeadcount,
      standardMonthlyHours,
      totalAvailableHours,
      productionRequiredHours,
      operatingRatePct,
    }),
    details: {
      total_fte_headcount: new Decimal(totalFteHeadcount).toString(),
      standard_monthly_hours: standardMonthlyHours,
      total_available_hours: new Decimal(totalAvailableHours).toString(),
      production_required_hours: new Decimal(productionRequiredHours).toString(),
      operating_rate_pct: rate.toString(),
      limit_pct: "100",
      period_key: periodKey,
    },
    stream: "production",
    traceId,
    timestamp: now().toISOString(),
  };
}

// ── aggregate_warnings ───────────────────────────────────────────
/**
 * Aggregate inventory + overcapacity warnings (PRD §A11 sort).
 * Mirrors `aggregate_warnings` exactly: severity ASC; inventory
 * warnings (closing_qty ASC) come BEFORE operating_rate at the same
 * severity.
 */
export function aggregateWarnings(
  inventoryWarnings: Warning[],
  operatingRateWarning: Warning | null,
): Warning[] {
  const out: Warning[] = [...inventoryWarnings];
  if (operatingRateWarning !== null) out.push(operatingRateWarning);
  out.sort((a, b) => {
    const sa = SEVERITY_ORDER[a.severity] ?? 99;
    const sb = SEVERITY_ORDER[b.severity] ?? 99;
    if (sa !== sb) return sa - sb;
    // Same severity: inventory first (closing_qty ASC), then operating_rate
    const aIsInv = a.code === "NEGATIVE_CLOSING_INVENTORY" ? 0 : 1;
    const bIsInv = b.code === "NEGATIVE_CLOSING_INVENTORY" ? 0 : 1;
    if (aIsInv !== bIsInv) return aIsInv - bIsInv;
    if (aIsInv === 0) {
      return (
        Number(a.details.closing_qty) - Number(b.details.closing_qty)
      );
    }
    return 0;
  });
  return out;
}
