/**
 * apps/web/lib/labels-ko.ts — ko-KR label formatters (Story 6.3 W3 close).
 *
 * Centralized Korean label helpers for closing period / monthly closing
 * report surfaces. Mirrors `packages/services/m4_inventory/closing_pdf_export.py`
 * Korean SSOT (CLOSING_PDF_EXPORT_TITLE_KO, CLOSING_PDF_EXPORT_EMPTY_KO) +
 * `apps/web/messages/ko-KR.json` namespace coverage.
 *
 * W3 close-out: panel `formatKrwUsd` parity helper consolidated into
 * the labels-ko module per AC #3.2 / AC #4.3 in Story 6.3 spec.
 *
 * AD-15 §11 cross-language parity: ko-KR strings identical across
 * Python (packages/services) + TS mirror + ko-KR.json surfaces.
 */

import "server-only";

import { formatKRW, krwFromString } from "./money";

/** KRW/USD dual display formatter — parity with MonthlyClosingReportPanel. */
export function formatKrwUsd(krw: string, usd: string): string {
  const krwFmt = formatKRW(krwFromString(krw));
  return `${krwFmt} / ${usd}`;
}

/** Closing period label — Korean SSOT. */
export const CLOSING_PERIOD_LABEL_KO = "마감 기간";

/** Closing snapshot event label — Korean SSOT. */
export const CLOSING_SNAPSHOT_EVENT_LABEL_KO = "마감 스냅샷";

/** Currency pair label — Korean SSOT. */
export const CURRENCY_PAIR_LABEL_KO = "환율 (KRW/USD)";

/** Operator action labels — 4-value enum (reopen operator). */
export const OPERATOR_ACTION_LABELS_KO: Record<string, string> = {
  reopen_requested: "재오픈 요청",
  reopen_approved: "재오픈 승인",
  reopen_rejected: "재오픈 거부",
  reopen_executed: "재오픈 실행",
};

export function formatClosingPeriodLabelKo(periodKey: string): string {
  return `${CLOSING_PERIOD_LABEL_KO}: ${periodKey}`;
}

export function formatClosingSnapshotEventLabelKo(count: number): string {
  return `${CLOSING_SNAPSHOT_EVENT_LABEL_KO} ${count}건`;
}

export function formatCurrencyPairKo(pair: string): string {
  return `${CURRENCY_PAIR_LABEL_KO}: ${pair}`;
}

export function formatOperatorActionKo(action: string): string {
  return OPERATOR_ACTION_LABELS_KO[action] ?? action;
}