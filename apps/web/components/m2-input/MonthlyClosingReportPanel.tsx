/**
 * apps/web/components/m2-input/MonthlyClosingReportPanel.tsx — Story 6.2 T7.4
 *
 * Monthly closing report visualization panel — read-only aggregator view
 * (PRD §F5 + §F5.2 + §V4 + §A11 Layer 4). Renders 4 KPI cards +
 * closing_per_product Table + V4 verdict envelope.
 *
 * Report view mode 3 codes (AD-15 §11 parity):
 * - REPORT_VIEW_MODE_READY   → green Alert + full table + V4 verdict
 * - REPORT_VIEW_MODE_PARTIAL → amber Alert + KPI 표시 + "잠시 후 갱신" sonner toast
 * - REPORT_VIEW_MODE_EMPTY   → muted Alert + "마감 데이터 없음" 표시
 *
 * Capability gate (A10) — when `capability_granted=false`, panel is hidden entirely
 * (service-only tenant → INDUSTRY_NOT_SUPPORTED).
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";
import { toast } from "sonner";
import { FileText, AlertCircle, CheckCircle2, FileX } from "lucide-react";

import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  type MonthlyClosingReportAggregate,
  REPORT_VIEW_MODES,
  REPORT_VIEW_MODE_READY,
  REPORT_VIEW_MODE_PARTIAL,
  REPORT_VIEW_MODE_EMPTY,
  type MonthlyClosingReportV4Verdict,
} from "@/lib/monthly-closing-report";
import { formatKRW, formatUSD, krwFromString } from "@/lib/money";
import { cn } from "@/lib/utils";

export interface MonthlyClosingReportPanelProps {
  /** Monthly closing report aggregate (4-source read-only join). */
  aggregate: MonthlyClosingReportAggregate;
  /** V4 verdict (6-1 wire + 6-2 wire extension). */
  v4_verdict?: MonthlyClosingReportV4Verdict | null;
  /** Audit trail entries (last 10 — CR 1.1 observability). */
  audit_trail?: Array<{
    id: string;
    action: string;
    actor_id: string | null;
    created_at: string;
  }>;
  /**
   * Capability gate (A10 MONTHLY_CLOSING_REPORT). When false, panel is hidden entirely
   * (service-only tenant → INDUSTRY_NOT_SUPPORTED).
   */
  capability_granted?: boolean;
  /** Optional className override. */
  className?: string;
}

/**
 * MonthlyClosingReportPanel — Story 6.2 read-only closing report visualization.
 *
 * Renders 4 KPI cards (closing_snapshot_count + ledger_event_count +
 * fiscal_period_snapshot_count + V4 verdict) + closing_per_product Table
 * + audit-trail list. The panel is hidden when `capability_granted=false`
 * (A10) or `aggregate.view_mode` is not one of the 3 SSOT codes (drift
 * detector backstop).
 */
export function MonthlyClosingReportPanel({
  aggregate,
  v4_verdict,
  audit_trail,
  capability_granted = false,
  className,
}: MonthlyClosingReportPanelProps): React.ReactElement | null {
  const t = useTranslations("monthly_closing_report");

  // A10 capability gate — service-only tenant → hidden entirely.
  if (!capability_granted) {
    return null;
  }

  // Defensive default — unknown view mode codes (drift detector backstop).
  if (!REPORT_VIEW_MODES.includes(aggregate.view_mode)) {
    return null;
  }

  const is_ready = aggregate.view_mode === REPORT_VIEW_MODE_READY;
  const is_partial = aggregate.view_mode === REPORT_VIEW_MODE_PARTIAL;
  const is_empty = aggregate.view_mode === REPORT_VIEW_MODE_EMPTY;

  // OQ1 cj-style default — partial-path 시 sonner toast.info "잠시 후 갱신".
  // Effect는 1회만 발동 (idempotent no-op skip).
  React.useEffect(() => {
    if (is_partial) {
      toast.info(t("toast_view_partial"));
    } else if (is_empty) {
      toast.warning(t("toast_view_empty"));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [aggregate.view_mode]);

  // OQ2 cj-style default — V4 fail 시 KPI FAIL 빨강 + audit-trail 표시.
  const v4_status = v4_verdict?.status ?? null;
  const v4_failure_count = v4_verdict?.failures.length ?? 0;

  // ── Variant + icon + title per view_mode code (AD-15 §11 SSOT) ──
  let variant: "default" | "destructive" = "default";
  let icon: React.ReactElement = (
    <CheckCircle2 className="h-4 w-4" aria-hidden="true" />
  );
  let title = "";

  if (is_ready) {
    variant = "default";
    icon = <CheckCircle2 className="h-4 w-4" aria-hidden="true" />;
    title = t("panel_title_ko");
  } else if (is_partial) {
    variant = "default";
    icon = <AlertCircle className="h-4 w-4" aria-hidden="true" />;
    title = t("panel_title_ko") + " (PARTIAL)";
  } else if (is_empty) {
    variant = "default";
    icon = <FileX className="h-4 w-4" aria-hidden="true" />;
    title = t("panel_title_ko") + " (EMPTY)";
  }

  // KRW/USD dual display formatter helper (AD-8 SSOT).
  const formatKrwUsd = (krw: string, usd: string): string => {
    const krwFmt = formatKRW(krwFromString(krw));
    const usdFmt = formatUSD(usd);
    return `${krwFmt} / ${usdFmt}`;
  };

  return (
    <div
      data-testid="monthly-closing-report-panel"
      data-view-mode={aggregate.view_mode}
      data-capability-granted={capability_granted}
      data-v4-status={v4_status ?? "none"}
      className={cn("flex flex-col gap-3", className)}
    >
      <Alert
        variant={variant}
        role={is_empty ? "status" : "status"}
        aria-live="polite"
      >
        {icon}
        <AlertTitle>{title}</AlertTitle>
        <AlertDescription>
          <span data-testid="panel-subtitle">{t("panel_subtitle_ko")}</span>
          {aggregate.currency_pair ? (
            <span
              data-testid="currency-pair-display"
              className="ml-2 text-muted-foreground"
            >
              ({aggregate.currency_pair.base}/{aggregate.currency_pair.quote} @{" "}
              {aggregate.currency_pair.source})
            </span>
          ) : null}
        </AlertDescription>
      </Alert>

      {/* ── 4 KPI Cards ── */}
      <div
        data-testid="kpi-cards"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"
      >
        <div
          data-testid="kpi-closing-snapshot-count"
          className="rounded-md border bg-white p-3"
        >
          <div className="text-xs text-muted-foreground">
            {t("kpi_closing_snapshot_count")}
          </div>
          <div className="text-2xl font-semibold">
            {aggregate.closing_snapshot_count}
          </div>
        </div>
        <div
          data-testid="kpi-ledger-event-count"
          className="rounded-md border bg-white p-3"
        >
          <div className="text-xs text-muted-foreground">
            {t("kpi_ledger_event_count")}
          </div>
          <div className="text-2xl font-semibold">
            {aggregate.ledger_event_count}
          </div>
        </div>
        <div
          data-testid="kpi-fiscal-period-snapshot-count"
          className="rounded-md border bg-white p-3"
        >
          <div className="text-xs text-muted-foreground">
            {t("kpi_fiscal_period_snapshot_count")}
          </div>
          <div className="text-2xl font-semibold">
            {aggregate.fiscal_period_snapshot_count}
          </div>
        </div>
        <div
          data-testid="kpi-v4-verdict"
          data-status={v4_status ?? "none"}
          className={cn(
            "rounded-md border p-3",
            v4_status === "FAIL" && "border-red-500 bg-red-50",
            v4_status === "PASS" && "border-green-500 bg-green-50",
          )}
        >
          <div className="text-xs text-muted-foreground">
            {t("kpi_v4_verdict")}
          </div>
          <div
            className={cn(
              "text-2xl font-semibold",
              v4_status === "FAIL" && "text-red-700",
              v4_status === "PASS" && "text-green-700",
            )}
          >
            {v4_status ?? "—"}
            {v4_status === "FAIL" && (
              <span data-testid="v4-failure-count" className="ml-2 text-sm">
                ({v4_failure_count})
              </span>
            )}
          </div>
        </div>
      </div>

      {/* ── Closing per-product Table ── */}
      {is_ready && aggregate.closing_per_product.length > 0 && (
        <div
          data-testid="closing-per-product-table-container"
          className="rounded-md border bg-white overflow-x-auto"
        >
          <table
            data-testid="closing-per-product-table"
            className="w-full text-sm"
          >
            <thead>
              <tr className="border-b bg-slate-50">
                <th className="px-3 py-2 text-left">product_id</th>
                <th className="px-3 py-2 text-right">
                  {t("table_opening_qty")}
                </th>
                <th className="px-3 py-2 text-right">
                  {t("table_closing_qty")}
                </th>
                <th className="px-3 py-2 text-right">
                  {t("table_closing_qty_usd")}
                </th>
                <th className="px-3 py-2 text-right">{t("table_delta")}</th>
                <th className="px-3 py-2 text-right">{t("table_delta_usd")}</th>
              </tr>
            </thead>
            <tbody>
              {aggregate.closing_per_product.map((row) => (
                <tr
                  key={row.product_id}
                  data-testid={`closing-row-${row.product_id}`}
                  className="border-b"
                >
                  <td className="px-3 py-2 font-mono text-xs">
                    {row.product_id.slice(0, 8)}
                  </td>
                  <td className="px-3 py-2 text-right">{row.opening_qty}</td>
                  <td className="px-3 py-2 text-right">{row.closing_qty}</td>
                  <td
                    data-testid={`closing-row-usd-${row.product_id}`}
                    className="px-3 py-2 text-right"
                  >
                    {formatKrwUsd(row.closing_qty_krw, row.closing_qty_usd)}
                  </td>
                  <td className="px-3 py-2 text-right">{row.delta_qty}</td>
                  <td className="px-3 py-2 text-right">{row.delta_usd}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* ── V4 failures list (OQ2 default — KPI 빨강 + audit-trail 표시) ── */}
      {v4_verdict && v4_verdict.failures.length > 0 && (
        <div
          data-testid="v4-failures-list"
          className="rounded-md border border-red-500 bg-red-50 p-3"
        >
          <h3 className="font-medium text-red-700">V4 FAIL — {v4_failure_count}건</h3>
          <ul className="mt-2 space-y-1 text-sm">
            {v4_verdict.failures.map((f, idx) => (
              <li
                key={`${f.product_id}-${idx}`}
                data-testid={`v4-failure-${f.product_id}`}
                className="text-red-700"
              >
                {f.product_id.slice(0, 8)}: {f.message_ko}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* ── Audit trail list (CR 1.1 observability) ── */}
      {audit_trail && audit_trail.length > 0 && (
        <div
          data-testid="monthly-closing-report-audit-trail"
          className="rounded-md border bg-white p-3 text-sm"
        >
          <h3 className="font-medium">마감 보고서 검증 이력</h3>
          <ul className="mt-2 space-y-1">
            {audit_trail.map((entry) => (
              <li
                key={entry.id}
                data-testid={`audit-entry-${entry.id}`}
                className="flex gap-2"
              >
                <span>{entry.action}</span>
                <span className="text-muted-foreground">
                  {entry.created_at}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}