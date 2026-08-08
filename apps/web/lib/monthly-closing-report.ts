// apps/web/lib/monthly-closing-report.ts — Story 6.2 TS mirror.
//
// Monthly closing report TS projection (AD-15 §11 SSOT parity with
// `packages/services/m4_inventory/monthly_closing_report.py`).
//
// Drift caught by `tests/integration/test_monthly_closing_report_label_consistency.py`.
//
// Korean message SSOT (single source of truth for ko-KR.json parity):
// - MONTHLY_CLOSING_REPORT_TITLE_KO mirrors Python
//   `MONTHLY_CLOSING_REPORT_TITLE_KO`.
// - MONTHLY_CLOSING_REPORT_EMPTY_KO mirrors Python
//   `MONTHLY_CLOSING_REPORT_EMPTY_KO`.
//
// Report view mode 3 codes (PRD §F5 + §V4 + §A11):
// - REPORT_VIEW_MODE_READY: closing_snapshot + ledger_events + fiscal_period_snapshots all > 0
// - REPORT_VIEW_MODE_PARTIAL: at least 1 source populated, < 3
// - REPORT_VIEW_MODE_EMPTY: 0 sources populated (no closing data)

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const MONTHLY_CLOSING_REPORT_TITLE_KO = "월 마감 보고서" as const;
export const MONTHLY_CLOSING_REPORT_EMPTY_KO = "마감 데이터 없음" as const;

// V4 fail message Korean SSOT (AD-15 §11 cross-language parity with
// `packages/cost_engine/monthly_closing_report_aggregator.py::V4_FAIL_MESSAGE_KO`).
// Drift caught by `tests/integration/test_monthly_closing_report_label_consistency.py`.
export const V4_FAIL_MESSAGE_KO =
  "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요" as const;

// ── Report view mode 3 codes ──────────────────────────────────────
export const REPORT_VIEW_MODE_READY = "READY" as const;
export const REPORT_VIEW_MODE_PARTIAL = "PARTIAL" as const;
export const REPORT_VIEW_MODE_EMPTY = "EMPTY" as const;

export const REPORT_VIEW_MODES = [
  REPORT_VIEW_MODE_READY,
  REPORT_VIEW_MODE_PARTIAL,
  REPORT_VIEW_MODE_EMPTY,
] as const;

export type ReportViewMode = (typeof REPORT_VIEW_MODES)[number];

// ── CurrencyPair (PRD §F5.2 — tenant_settings.baseline.currency_pair) ──
// Mirrors Python `CurrencyPair` NamedTuple (4 fields).
export interface CurrencyPair {
  base: string;        // e.g. "KRW"
  quote: string;       // e.g. "USD"
  rate: string;        // Decimal string (KRW per 1 USD)
  source: string;      // e.g. "한국은행" / "한국은행 2026-07-25"
}

// ── Ledger event lite (closing_snapshot ledger event 6-1 wire) ──
// Mirrors Python `ClosingSnapshotEventLite` NamedTuple (5 fields).
export interface ClosingSnapshotEventLite {
  product_id: string;
  event_type: "closing_snapshot";
  qty: string;             // Decimal string (AD-8)
  finalized_at: string;    // ISO-8601 UTC
  trace_id: string;
}

// ── Ledger event lite (5-2 wire ledger aggregate) ──
// Mirrors Python `LedgerEventLite` NamedTuple (3 fields).
export interface LedgerEventLite {
  product_id: string;
  event_type: string;      // purchase_inbound / sales_outbound / production_output_inbound / etc.
  qty: string;             // Decimal string (AD-8)
}

// ── Fiscal period snapshot lite (PRD §V4) ──
// Mirrors Python `FiscalPeriodSnapshotLite` NamedTuple (3 fields).
export interface FiscalPeriodSnapshotLite {
  product_id: string;
  period_key: string;
  fiscal_period_qty: string;  // Decimal string (AD-8 — KRW 정수 / qty 소수)
}

// ── Opening inventory entry lite (5-1 wire auto-carry chain) ──
// Mirrors Python `OpeningInventoryEntryLite` NamedTuple (3 fields).
export interface OpeningInventoryEntryLite {
  product_id: string;
  period_key: string;
  opening_qty: string;        // Decimal string (AD-8)
}

// ── Closing per product row (KRW/USD dual display) ──
// Mirrors Python `ClosingPerProductRow` NamedTuple (7 fields).
export interface ClosingPerProductRow {
  product_id: string;
  opening_qty: string;        // Decimal string (AD-8)
  closing_qty: string;        // Decimal string (AD-8 — NUMERIC(18,4))
  delta_qty: string;          // Decimal string (closing - opening)
  closing_qty_krw: string;    // KRW bigint serialized (AD-8)
  closing_qty_usd: string;    // USD Decimal string (AD-8)
  delta_usd: string;          // USD Decimal string
}

// ── MonthlyClosingReportAggregate (4-source read-only aggregate) ──
// Mirrors Python `MonthlyClosingReportAggregate` NamedTuple (12 fields).
export interface MonthlyClosingReportAggregate {
  period_key: string;
  view_mode: ReportViewMode;
  closing_snapshot_count: number;
  ledger_event_count: number;
  fiscal_period_snapshot_count: number;
  opening_inventory_count: number;
  closing_per_product: ClosingPerProductRow[];
  audit_emitted: boolean;       // CR 1.1 idempotent no-op marker
  currency_pair: CurrencyPair | null;
  trace_id: string;
  report_generated_at: string;  // ISO-8601 UTC
}

// ── PeriodClosingDisplay (KRW/USD dual display formatting result) ──
// Mirrors Python `PeriodClosingDisplay` NamedTuple (5 fields).
export interface PeriodClosingDisplay {
  amount_krw: string;          // KRW bigint serialized
  amount_usd: string;          // USD Decimal string
  rate: string;                // Decimal string (KRW per 1 USD)
  rate_source: string;         // e.g. "한국은행 2026-07-25"
  display: string;             // formatted ko-KR string
}

// ── isMonthlyClosingReportAllowed (gate helper) ──
export function isMonthlyClosingReportAllowed(mode: ReportViewMode): boolean {
  return mode === REPORT_VIEW_MODE_READY;
}

// ── classifyReportViewMode (helper — pure) ──
// Mirrors Python `classify_report_view_mode` logic.
export function classifyReportViewMode(
  ledgerEventCount: number,
  closingSnapshotCount: number,
  fiscalPeriodSnapshotCount: number,
): ReportViewMode {
  const populated =
    (ledgerEventCount > 0 ? 1 : 0) +
    (closingSnapshotCount > 0 ? 1 : 0) +
    (fiscalPeriodSnapshotCount > 0 ? 1 : 0);
  if (populated === 3) return REPORT_VIEW_MODE_READY;
  if (populated === 0) return REPORT_VIEW_MODE_EMPTY;
  return REPORT_VIEW_MODE_PARTIAL;
}

// ── formatCurrencyPairDisplayKo (Korean formatter) ──
// Mirrors Python `format_currency_pair_display_ko`.
export function formatCurrencyPairDisplayKo(pair: CurrencyPair): string {
  return `1 ${pair.quote} = ${pair.rate} ${pair.base} (${pair.source})`;
}

// ── MonthlyClosingReportRow (Pydantic MonthlyClosingReportRow) ──
// Wire envelope — backend `MonthlyClosingReportRow` Pydantic v2.
export interface MonthlyClosingReportRow {
  product_id: string;
  opening_qty: string;
  closing_qty: string;
  delta_qty: string;
  closing_qty_krw: string;
  closing_qty_usd: string;
  delta_usd: string;
}

// ── MonthlyClosingReportResponse (wire envelope — backend Pydantic) ──
export interface MonthlyClosingReportResponse {
  period_key: string;
  view_mode: ReportViewMode;
  closing_snapshot_count: number;
  ledger_event_count: number;
  fiscal_period_snapshot_count: number;
  opening_inventory_count: number;
  closing_per_product: MonthlyClosingReportRow[];
  currency_pair: CurrencyPair | null;
  trace_id: string;
  report_generated_at: string;
}

// ── MonthlyClosingReportAuditEntry (audit trail wire) ──
export interface MonthlyClosingReportAuditEntry {
  id: string;
  action: string;
  actor_id: string | null;
  created_at: string;
  payload: Record<string, unknown>;
}

// ── MonthlyClosingReportAuditTrailResponse (wire envelope) ──
export interface MonthlyClosingReportAuditTrailResponse {
  period_key: string;
  entries: MonthlyClosingReportAuditEntry[];
  trace_id: string;
}

// ── MonthlyClosingReportV4Verdict (V4 wire envelope — 6-1 carry-over) ──
// NOTE (bmad-code-review D1 결정, 2026-08-08): 3-source contract —
// `fiscal_period_snapshot_qty` 필드 제거, source_count 2.
export interface MonthlyClosingReportV4Verdict {
  status: "PASS" | "FAIL" | "SKIP";
  code: string;
  failures: Array<{
    product_id: string;
    ledger_qty: string;
    closing_snapshot_qty: string;
    message_ko: string;
  }>;
  verified_at: string;
  product_whitelist_size: number;
  skip_reason_ko: string | null;
  source_count: 2;
}

// ── MonthlyClosingReportV4VerdictResponse (wire envelope) ──
export interface MonthlyClosingReportV4VerdictResponse {
  period_key: string;
  verdict: MonthlyClosingReportV4Verdict;
  trace_id: string;
}

// ── buildMonthlyClosingReportAggregate (wire envelope → projection) ──
export function buildMonthlyClosingReportAggregate(
  response: MonthlyClosingReportResponse,
): MonthlyClosingReportAggregate {
  const closing_per_product: ClosingPerProductRow[] =
    response.closing_per_product.map((row) => ({
      product_id: row.product_id,
      opening_qty: row.opening_qty,
      closing_qty: row.closing_qty,
      delta_qty: row.delta_qty,
      closing_qty_krw: row.closing_qty_krw,
      closing_qty_usd: row.closing_qty_usd,
      delta_usd: row.delta_usd,
    }));

  return {
    period_key: response.period_key,
    view_mode: response.view_mode,
    closing_snapshot_count: response.closing_snapshot_count,
    ledger_event_count: response.ledger_event_count,
    fiscal_period_snapshot_count: response.fiscal_period_snapshot_count,
    opening_inventory_count: response.opening_inventory_count,
    closing_per_product,
    audit_emitted: false,
    currency_pair: response.currency_pair,
    trace_id: response.trace_id,
    report_generated_at: response.report_generated_at,
  };
}