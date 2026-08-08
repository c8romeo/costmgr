// apps/web/lib/closing-period.ts — Story 6.1 TS mirror.
//
// Closing period service TS projection (AD-15 §11 SSOT parity with
// `packages/services/m4_inventory/closing_period.py`).
//
// Drift caught by `tests/integration/test_closing_period_label_consistency.py`.
//
// Korean message SSOT (single source of truth for ko-KR.json parity):
// - CLOSING_PERIOD_CONFIRMATION_KO mirrors Python
//   `CLOSING_PERIOD_CONFIRMATION_KO`.
// - CLOSING_PERIOD_BLOCKED_KO mirrors Python
//   `CLOSING_PERIOD_BLOCKED_KO`.
//
// Status classification 4 codes (PRD §F4.3 + §V4 + §A11):
// - CLOSING_PERIOD_STATUS_READY: invariant OK + ledger events >= 1
// - CLOSING_PERIOD_STATUS_BLOCKED: invariant NEGATIVE_CLOSING
// - CLOSING_PERIOD_STATUS_ALREADY_CLOSED: monthly_input_periods.status='closed'
// - CLOSING_PERIOD_STATUS_EMPTY_PERIOD: ledger events 0건

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const CLOSING_PERIOD_CONFIRMATION_KO = "월 마감 확정: 기말재고 snapshot 저장";
export const CLOSING_PERIOD_BLOCKED_KO = "마감 차단: 기말재고 음수";

// ── Closing period status 4 codes ────────────────────────────────
export const CLOSING_PERIOD_STATUS_READY = "CLOSING_READY" as const;
export const CLOSING_PERIOD_STATUS_BLOCKED = "CLOSING_BLOCKED" as const;
export const CLOSING_PERIOD_STATUS_ALREADY_CLOSED = "ALREADY_CLOSED" as const;
export const CLOSING_PERIOD_STATUS_EMPTY_PERIOD = "EMPTY_PERIOD" as const;

export const CLOSING_PERIOD_STATUSES = [
  CLOSING_PERIOD_STATUS_READY,
  CLOSING_PERIOD_STATUS_BLOCKED,
  CLOSING_PERIOD_STATUS_ALREADY_CLOSED,
  CLOSING_PERIOD_STATUS_EMPTY_PERIOD,
] as const;

export type ClosingPeriodStatus =
  (typeof CLOSING_PERIOD_STATUSES)[number];

// ── ClosingSnapshotEvent (AD-15 snake_case parity) ──────────────
// Mirrors `apps/web/lib/l2-input-inventory-ledger.ts::ClosingSnapshotEvent`
// (5-2 wire SSOT extension). 9 fields total — event_id / product_id /
// period_key / event_type / qty / trace_id / reverses_event_id /
// correction_group_id / finalized_at. Reversal fields (reverses_event_id +
// correction_group_id) are populated by Epic 11 reversal module wire.
export interface ClosingSnapshotEvent {
  event_id: string;
  product_id: string;
  period_key: string;
  event_type: "closing_snapshot";
  qty: string; // Decimal string (AD-8 monetary)
  trace_id: string;
  reverses_event_id: string | null;
  correction_group_id: string | null;
  finalized_at: string; // ISO-8601 UTC
}

// ── ClosingPeriodState (AD-15 parity with Python NamedTuple) ────
export interface ClosingPeriodState {
  status: ClosingPeriodStatus;
  allowed: boolean;
  closing_per_product: Record<string, string>; // product_id (string) → Decimal string
  closing_snapshot_count: number;
  ledger_event_count: number;
  period_key: string;
}

// ── isClosingPeriodAllowed (gate helper) ────────────────────────
export function isClosingPeriodAllowed(status: ClosingPeriodStatus): boolean {
  return status === CLOSING_PERIOD_STATUS_READY;
}

// ── formatClosingPeriodConfirmationKo ──────────────────────────
export function formatClosingPeriodConfirmationKo(
  result: ClosingPeriodState,
): string {
  if (result.status !== CLOSING_PERIOD_STATUS_READY) {
    return "";
  }
  return CLOSING_PERIOD_CONFIRMATION_KO;
}

// ── formatClosingPeriodBlockedKo ───────────────────────────────
export function formatClosingPeriodBlockedKo(
  result: ClosingPeriodState,
): string {
  if (result.status !== CLOSING_PERIOD_STATUS_BLOCKED) {
    return "";
  }
  return CLOSING_PERIOD_BLOCKED_KO;
}

// ── ClosingPeriodResponse (wire envelope — backend ClosingPeriodEvaluateResponse) ──
export interface ClosingPeriodResponse {
  status: ClosingPeriodStatus;
  allowed: boolean;
  closing_per_product: Record<string, string>;
  closing_snapshot_count: number;
  ledger_event_count: number;
  period_key: string;
  trace_id: string;
}

// ── buildClosingPeriodState (wire envelope → projection) ────────
export function buildClosingPeriodState(
  response: ClosingPeriodResponse,
): ClosingPeriodState {
  return {
    status: response.status,
    allowed: response.allowed,
    closing_per_product: response.closing_per_product,
    closing_snapshot_count: response.closing_snapshot_count,
    ledger_event_count: response.ledger_event_count,
    period_key: response.period_key,
  };
}

// ── MonthlyClosingReportView (Story 6.2 T7.3 — view projection) ────────
// Re-exports the monthly closing report aggregate shape so the
// `MonthlyClosingReportPanel` component can accept a single typed view
// without re-importing from `monthly-closing-report.ts`. Single source
// of truth for panel props stays in `monthly-closing-report.ts`.
export type { MonthlyClosingReportAggregate } from "./monthly-closing-report";