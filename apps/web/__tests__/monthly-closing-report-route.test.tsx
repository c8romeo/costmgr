/**
 * apps/web/__tests__/monthly-closing-report-route.test.tsx — Story 6.2 T8.3
 *
 * Vitest + React Testing Library scenarios for the monthly closing report
 * route page (RSC). 12 scenarios total.
 *
 * Categories:
 * 1. SSOT parity (Python ↔ TS constants)
 * 2. View mode classification
 * 3. KRW/USD parity helper
 * 4. Wire envelope projection
 *
 * Story 0.5 vitest activation — these tests run as part of `pnpm test`.
 */

import "@testing-library/jest-dom/vitest";
import { describe, expect, it } from "vitest";

import {
  MONTHLY_CLOSING_REPORT_TITLE_KO,
  REPORT_VIEW_MODE_READY,
  REPORT_VIEW_MODE_PARTIAL,
  REPORT_VIEW_MODE_EMPTY,
  REPORT_VIEW_MODES,
  classifyReportViewMode,
  isMonthlyClosingReportAllowed,
  formatCurrencyPairDisplayKo,
  buildMonthlyClosingReportAggregate,
  type MonthlyClosingReportResponse,
} from "@/lib/monthly-closing-report";
import {
  QTY_QUANTUM,
  USD_QUANTUM,
  parityQuantizeQty,
  parityQuantizeUSD,
  parityComputeUsdFromKrw,
  parityFormatPeriodClosingKrwUsd,
  parityFormatCurrencyPairDisplayKo,
  assertParityConstants,
} from "@/lib/monthly-closing-report-parity";

// ── SSOT parity (Python ↔ TS constants) ────────────────────────────

describe("monthly-closing-report SSOT parity", () => {
  // Case 1: Korean title matches Python SSOT
  it("test_monthly_closing_report_title_ko_ssot", () => {
    expect(MONTHLY_CLOSING_REPORT_TITLE_KO).toBe("월 마감 보고서");
  });

  // Case 2: 3 view modes + frozen tuple of constants
  it("test_report_view_modes_three_codes", () => {
    expect(REPORT_VIEW_MODES).toHaveLength(3);
    expect(REPORT_VIEW_MODES).toContain(REPORT_VIEW_MODE_READY);
    expect(REPORT_VIEW_MODES).toContain(REPORT_VIEW_MODE_PARTIAL);
    expect(REPORT_VIEW_MODES).toContain(REPORT_VIEW_MODE_EMPTY);
  });

  // Case 3: QTY_QUANTUM SSOT (Python = "0.0001")
  it("test_qty_quantum_parity_constant", () => {
    expect(QTY_QUANTUM).toBe("0.0001");
  });

  // Case 4: USD_QUANTUM SSOT (Python = "0.01")
  it("test_usd_quantum_parity_constant", () => {
    expect(USD_QUANTUM).toBe("0.01");
  });

  // Case 5: assertParityConstants passes
  it("test_assert_parity_constants_does_not_throw", () => {
    expect(() => assertParityConstants()).not.toThrow();
  });
});

// ── View mode classification ────────────────────────────────────────

describe("classifyReportViewMode", () => {
  // Case 6: all 3 sources populated → READY
  it("test_classify_ready_when_all_three_populated", () => {
    expect(classifyReportViewMode(5, 4, 4)).toBe(REPORT_VIEW_MODE_READY);
  });

  // Case 7: 0 sources → EMPTY
  it("test_classify_empty_when_zero_sources", () => {
    expect(classifyReportViewMode(0, 0, 0)).toBe(REPORT_VIEW_MODE_EMPTY);
  });

  // Case 8: 1 source → PARTIAL
  it("test_classify_partial_when_one_source", () => {
    expect(classifyReportViewMode(5, 0, 0)).toBe(REPORT_VIEW_MODE_PARTIAL);
  });

  // Case 9: 2 sources → PARTIAL
  it("test_classify_partial_when_two_sources", () => {
    expect(classifyReportViewMode(5, 4, 0)).toBe(REPORT_VIEW_MODE_PARTIAL);
  });

  // Case 10: gate helper — only READY is allowed
  it("test_is_monthly_closing_report_allowed_only_ready", () => {
    expect(isMonthlyClosingReportAllowed(REPORT_VIEW_MODE_READY)).toBe(true);
    expect(isMonthlyClosingReportAllowed(REPORT_VIEW_MODE_PARTIAL)).toBe(false);
    expect(isMonthlyClosingReportAllowed(REPORT_VIEW_MODE_EMPTY)).toBe(false);
  });
});

// ── KRW/USD parity helpers (TS↔Python SSOT) ───────────────────────

describe("monthly-closing-report-parity KRW/USD helpers", () => {
  // Case 11: USD quantum (2 decimal banker's rounding)
  it("test_parity_quantize_usd_two_decimals", () => {
    expect(parityQuantizeUSD("1.005")).toBe("1.00"); // ROUND_HALF_EVEN
    expect(parityQuantizeUSD("1.015")).toBe("1.02"); // ROUND_HALF_EVEN
    expect(parityQuantizeUSD(1.5)).toBe("1.50");
  });

  // Case 12: QTY quantum (4 decimals)
  it("test_parity_quantize_qty_four_decimals", () => {
    expect(parityQuantizeQty("1.23456")).toBe("1.2346");
    expect(parityQuantizeQty("0.00015")).toBe("0.0002"); // ROUND_HALF_EVEN
  });

  // Case 13: KRW → USD conversion (PRD §F5.2 — 환율 injection)
  it("test_parity_compute_usd_from_krw", () => {
    // KRW 1,320,000 / rate 1,320 = USD 1,000.00
    expect(parityComputeUsdFromKrw("1320000", "1320")).toBe("1000.00");
    // KRW 1,320,000 / rate 1,320.5 = USD 999.62 (banker's rounding)
    expect(parityComputeUsdFromKrw("1320000", "1320.5")).toBe("999.62");
  });

  // Case 14: format KRW/USD display
  it("test_parity_format_period_closing_krw_usd", () => {
    const formatted = parityFormatPeriodClosingKrwUsd(
      "1320000",
      "1320",
      "한국은행 2026-07-25",
    );
    expect(formatted).toContain("1,320,000 KRW");
    expect(formatted).toContain("USD 1000.00");
    expect(formatted).toContain("한국은행 2026-07-25");
  });

  // Case 15: format currency pair display ko
  it("test_parity_format_currency_pair_display_ko", () => {
    const formatted = parityFormatCurrencyPairDisplayKo(
      "KRW",
      "USD",
      "1320.50",
      "한국은행 2026-07-25",
    );
    expect(formatted).toBe("1 USD = 1320.50 KRW (한국은행 2026-07-25)");
  });

  // Case 16: TS formatCurrencyPairDisplayKo parity
  it("test_format_currency_pair_display_ko_match_python", () => {
    expect(
      formatCurrencyPairDisplayKo({
        base: "KRW",
        quote: "USD",
        rate: "1320.50",
        source: "한국은행 2026-07-25",
      }),
    ).toBe("1 USD = 1320.50 KRW (한국은행 2026-07-25)");
  });
});

// ── Wire envelope projection ───────────────────────────────────────

describe("buildMonthlyClosingReportAggregate", () => {
  // Case 17: wire envelope → projection (AD-15 §11 parity)
  it("test_build_monthly_closing_report_aggregate_projection", () => {
    const wire: MonthlyClosingReportResponse = {
      period_key: "2026-08",
      view_mode: REPORT_VIEW_MODE_READY,
      closing_snapshot_count: 4,
      ledger_event_count: 12,
      fiscal_period_snapshot_count: 4,
      opening_inventory_count: 4,
      closing_per_product: [
        {
          product_id: "019200a0-0000-7000-8000-0000000000a1",
          opening_qty: "100.0000",
          closing_qty: "90.0000",
          delta_qty: "-10.0000",
          closing_qty_krw: "1200000",
          closing_qty_usd: "909.09",
          delta_usd: "-101.01",
        },
      ],
      currency_pair: {
        base: "KRW",
        quote: "USD",
        rate: "1320.50",
        source: "한국은행 2026-08-08",
      },
      trace_id: "trace-001",
      report_generated_at: "2026-08-08T00:00:00Z",
    };

    const projection = buildMonthlyClosingReportAggregate(wire);
    expect(projection.period_key).toBe("2026-08");
    expect(projection.view_mode).toBe(REPORT_VIEW_MODE_READY);
    expect(projection.closing_per_product).toHaveLength(1);
    expect(projection.closing_per_product[0].closing_qty_usd).toBe("909.09");
    expect(projection.audit_emitted).toBe(false);
  });
});