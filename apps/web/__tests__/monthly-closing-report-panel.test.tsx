/**
 * apps/web/__tests__/monthly-closing-report-panel.test.tsx — Story 6.2 T8.1
 *
 * Vitest + React Testing Library scenarios for `<MonthlyClosingReportPanel />`:
 * 1. test_panel_renders_ready_view_mode — view_mode=READY → green Alert + 4 KPI cards + table.
 * 2. test_panel_renders_partial_view_mode — view_mode=PARTIAL → amber Alert + toast.info.
 * 3. test_panel_renders_empty_view_mode — view_mode=EMPTY → muted Alert + toast.warning.
 * 4. test_panel_hidden_when_capability_denied — capability_granted=false → null.
 * 5. test_panel_renders_v4_fail_verdict — v4_verdict FAIL → KPI red + failures list.
 * 6. test_panel_renders_krw_usd_dual_display — closing_qty_krw + closing_qty_usd cell.
 *
 * Story 0.5 vitest activation — these tests run as part of `pnpm test`.
 */

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MonthlyClosingReportPanel } from "@/components/m2-input/MonthlyClosingReportPanel";
import type { MonthlyClosingReportAggregate } from "@/lib/monthly-closing-report";

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    warning: vi.fn(),
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

// Mock next-intl useTranslations (return key as-is for SSOT assertion)
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => {
    const map: Record<string, string> = {
      panel_title_ko: "월 마감 보고서",
      panel_subtitle_ko: "PRD §F5 — 마감 보고서 + §F5.2 KRW/USD dual display + §V4 closing snapshot 일관성",
      kpi_closing_snapshot_count: "closing_snapshot 수",
      kpi_ledger_event_count: "ledger event 수",
      kpi_fiscal_period_snapshot_count: "fiscal_period_snapshot 수",
      kpi_v4_verdict: "V4 verdict",
      table_opening_qty: "기초 수량",
      table_closing_qty: "기말 수량",
      table_closing_qty_usd: "기말 금액 (KRW/USD)",
      table_delta: "변동 수량",
      table_delta_usd: "변동 금액 (USD)",
      toast_view_partial: "마감 데이터 일부만 표시됩니다 — 잠시 후 갱신됩니다",
      toast_view_empty: "마감 데이터 없음",
      toast_error_krw_usd_rate_missing: "KRW/USD 환율 누락: tenant_settings.baseline.currency_pair 미설정",
      toast_error_industry_not_supported: "업종 미지원: MONTHLY_CLOSING_REPORT capability 미보유 (A10)",
    };
    return map[key] ?? key;
  },
}));

const PERIOD_KEY = "2026-08";

function makeAggregate(
  view_mode: "READY" | "PARTIAL" | "EMPTY",
  closingSnapshotCount = 4,
  ledgerEventCount = 12,
  fiscalPeriodSnapshotCount = 4,
): MonthlyClosingReportAggregate {
  return {
    period_key: PERIOD_KEY,
    view_mode,
    closing_snapshot_count: closingSnapshotCount,
    ledger_event_count: ledgerEventCount,
    fiscal_period_snapshot_count: fiscalPeriodSnapshotCount,
    opening_inventory_count: 4,
    closing_per_product:
      view_mode === "READY"
        ? [
            {
              product_id: "019200a0-0000-7000-8000-0000000000a1",
              opening_qty: "100.0000",
              closing_qty: "90.0000",
              delta_qty: "-10.0000",
              closing_qty_krw: "1200000",
              closing_qty_usd: "909.09",
              delta_usd: "-101.01",
            },
            {
              product_id: "019200a0-0000-7000-8000-0000000000a2",
              opening_qty: "50.0000",
              closing_qty: "55.5000",
              delta_qty: "5.5000",
              closing_qty_krw: "800000",
              closing_qty_usd: "606.06",
              delta_usd: "83.33",
            },
          ]
        : [],
    audit_emitted: false,
    currency_pair:
      view_mode === "READY"
        ? {
            base: "KRW",
            quote: "USD",
            rate: "1320.50",
            source: "한국은행 2026-08-08",
          }
        : null,
    trace_id: "trace-001",
    report_generated_at: "2026-08-08T00:00:00Z",
  };
}

describe("MonthlyClosingReportPanel", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  // ── Case 1: READY view mode renders full panel ────────────────
  it("test_panel_renders_ready_view_mode", () => {
    render(
      <MonthlyClosingReportPanel
        aggregate={makeAggregate("READY")}
        capability_granted={true}
      />,
    );

    const panel = screen.getByTestId("monthly-closing-report-panel");
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveAttribute("data-view-mode", "READY");

    // 4 KPI cards
    expect(screen.getByTestId("kpi-closing-snapshot-count")).toHaveTextContent("4");
    expect(screen.getByTestId("kpi-ledger-event-count")).toHaveTextContent("12");
    expect(screen.getByTestId("kpi-fiscal-period-snapshot-count")).toHaveTextContent("4");
    expect(screen.getByTestId("kpi-v4-verdict")).toBeInTheDocument();

    // Closing per product table with 2 rows
    const table = screen.getByTestId("closing-per-product-table");
    expect(table).toBeInTheDocument();
    const rows = table.querySelectorAll("tbody tr");
    expect(rows).toHaveLength(2);

    // Currency pair display
    expect(screen.getByTestId("currency-pair-display")).toHaveTextContent(
      "한국은행",
    );
  });

  // ── Case 2: PARTIAL view mode + sonner toast.info ────────────
  it("test_panel_renders_partial_view_mode", async () => {
    const { toast } = await import("sonner");
    render(
      <MonthlyClosingReportPanel
        aggregate={makeAggregate("PARTIAL", 4, 0, 0)}
        capability_granted={true}
      />,
    );

    const panel = screen.getByTestId("monthly-closing-report-panel");
    expect(panel).toHaveAttribute("data-view-mode", "PARTIAL");

    // toast.info called for partial-path
    expect(toast.info).toHaveBeenCalledWith(
      expect.stringContaining("마감 데이터 일부"),
    );
  });

  // ── Case 3: EMPTY view mode + sonner toast.warning ──────────
  it("test_panel_renders_empty_view_mode", async () => {
    const { toast } = await import("sonner");
    render(
      <MonthlyClosingReportPanel
        aggregate={makeAggregate("EMPTY", 0, 0, 0)}
        capability_granted={true}
      />,
    );

    const panel = screen.getByTestId("monthly-closing-report-panel");
    expect(panel).toHaveAttribute("data-view-mode", "EMPTY");

    // toast.warning called for empty
    expect(toast.warning).toHaveBeenCalledWith(
      expect.stringContaining("마감 데이터 없음"),
    );
  });

  // ── Case 4: capability_granted=false → panel hidden ─────────
  it("test_panel_hidden_when_capability_denied", () => {
    const { container } = render(
      <MonthlyClosingReportPanel
        aggregate={makeAggregate("READY")}
        capability_granted={false}
      />,
    );

    expect(
      container.querySelector('[data-testid="monthly-closing-report-panel"]'),
    ).toBeNull();
  });

  // ── Case 5: V4 FAIL verdict → KPI 빨강 + failures list ──────
  it("test_panel_renders_v4_fail_verdict", () => {
    // NOTE (bmad-code-review D1 결정, 2026-08-08): 3-source contract —
    // fiscal_period_snapshot_qty / industry 필드 제거, source_count 2.
    const v4_verdict = {
      status: "FAIL" as const,
      code: "V4",
      failures: [
        {
          product_id: "019200a0-0000-7000-8000-0000000000a1",
          ledger_qty: "10.0000",
          closing_snapshot_qty: "11.0000",
          message_ko: "마감 snapshot 불일치: 기말재고 ledger vs closing_snapshot 갱신 필요",
        },
      ],
      verified_at: "2026-08-08T00:00:00Z",
      product_whitelist_size: 3,
      skip_reason_ko: null,
      source_count: 2 as const,
    };

    render(
      <MonthlyClosingReportPanel
        aggregate={makeAggregate("READY")}
        v4_verdict={v4_verdict}
        capability_granted={true}
      />,
    );

    const kpi = screen.getByTestId("kpi-v4-verdict");
    expect(kpi).toHaveAttribute("data-status", "FAIL");

    // Failure list visible
    const failuresList = screen.getByTestId("v4-failures-list");
    expect(failuresList).toBeInTheDocument();

    // Failure count badge
    expect(screen.getByTestId("v4-failure-count")).toHaveTextContent("(1)");

    // Specific failure message rendered
    expect(
      screen.getByTestId("v4-failure-019200a0-0000-7000-8000-0000000000a1"),
    ).toHaveTextContent(/마감 snapshot 불일치/);
  });

  // ── Case 6: KRW/USD dual display cell ────────────────────────
  it("test_panel_renders_krw_usd_dual_display", () => {
    render(
      <MonthlyClosingReportPanel
        aggregate={makeAggregate("READY")}
        capability_granted={true}
      />,
    );

    // First row USD cell — KRW 1,200,000 / USD 909.09
    const usdCell = screen.getByTestId(
      "closing-row-usd-019200a0-0000-7000-8000-0000000000a1",
    );
    expect(usdCell).toHaveTextContent("1,200,000원");
    expect(usdCell).toHaveTextContent("$909.09");
  });
});