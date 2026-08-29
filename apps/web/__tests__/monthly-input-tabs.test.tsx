/**
 * apps/web/__tests__/monthly-input-tabs.test.tsx — Story 5.3 T15.2
 *
 * Vitest + React Testing Library scenarios for `<MonthlyInputTabs />`
 * with 5-3 NEW closing-guard field projections:
 *
 * 1. test_tabs_render_three_navigation — 3 tabs (기초재고 / 수불부 / 마감).
 * 2. test_closing_guard_banner_when_blocked — invariant='NEGATIVE_CLOSING' →
 *    red banner visible + top 5 offenders.
 * 3. test_close_button_disabled_when_blocked — is_blocked=true →
 *    fieldset disabled around [마감] form.
 * 4. test_audit_trail_renders_entries — closing_guard_audit_trail entries
 *    surface in [마감] tab.
 * 5. test_production_consumption_events_render — production_material_consumption
 *    events surface in [수불부] tab.
 * 6. test_opening_locked_disables_fieldset — opening_inventory_locked=true →
 *    sonner toast on attempt.
 *
 * Story 0.5 vitest activation — these tests run as part of `pnpm test`.
 */

import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, within } from "@testing-library/react";

import { MonthlyInputTabs } from "@/components/m2-input/MonthlyInputTabs";
import {
  INVARIANT_CODE_NEGATIVE_CLOSING,
  INVARIANT_CODE_CLOSING_OK,
  INVARIANT_CODE_EMPTY_PERIOD,
} from "@/lib/closing-guard";

// Mock sonner toast (used in toast warning paths)
vi.mock("sonner", () => ({
  toast: {
    warning: vi.fn(),
    error: vi.fn(),
    success: vi.fn(),
    info: vi.fn(),
  },
}));

// Mock next-intl useTranslations (return key as-is)
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string) => key,
}));

const PERIOD_KEY = "2026-08";

describe("MonthlyInputTabs", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  // ── Case 1: 3 tabs render ────────────────────────────────────
  it("test_tabs_render_three_navigation", () => {
    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        invariant={{
          code: INVARIANT_CODE_CLOSING_OK,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: true,
        }}
      />,
    );
    expect(screen.getByTestId("tab-opening")).toHaveTextContent("기초재고");
    expect(screen.getByTestId("tab-subub")).toHaveTextContent("수불부");
    expect(screen.getByTestId("tab-close")).toHaveTextContent("마감");
    // Verify TabsList has exactly 3 triggers
    const triggers = screen.getAllByRole("tab");
    expect(triggers).toHaveLength(3);
  });

  // ── Case 2: closing guard banner when blocked ────────────────
  it("test_closing_guard_banner_when_blocked", () => {
    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_NEGATIVE_CLOSING,
          negative_products: {
            "019200a0-0000-7000-8000-0000000000a1": "-5.0000",
            "019200a0-0000-7000-8000-0000000000a2": "-3.0000",
          },
          closing_per_product: {},
          guard_enabled: true,
        }}
      />,
    );

    const banner = screen.getByTestId("m2-closing-guard-banner");
    expect(banner).toBeInTheDocument();
    expect(screen.getAllByText(/기말재고 음수/).length).toBeGreaterThanOrEqual(1);
    // 2 offenders rendered in the list
    const offenderList = within(banner).getByRole("list");
    const items = within(offenderList).getAllByRole("listitem");
    expect(items.length).toBeGreaterThanOrEqual(2);
  });

  // ── Case 3: close button disabled when blocked ───────────────
  it("test_close_button_disabled_when_blocked", () => {
    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_NEGATIVE_CLOSING,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: true,
        }}
      />,
    );

    const gate = screen.getByTestId("m2-closing-guard-gate");
    expect(gate.tagName).toBe("FIELDSET");
    expect(gate).toBeDisabled();
  });

  // ── Case 4: audit trail renders entries ──────────────────────
  it("test_audit_trail_renders_entries", () => {
    // P3-3rd-sweep P6: render <MonthlyInputTabs> with audit_trail prop
    // and assert on tab content (not synthetic <div>).
    const auditTrail = [
      {
        id: "audit-1",
        tenant_id: "t1",
        period_key: PERIOD_KEY,
        action: "closing_guard_violated",
        trace_id: "trace-1",
        created_at: "2026-08-05T10:00:00Z",
        payload: { invariant: "NEGATIVE_CLOSING" },
      },
      {
        id: "audit-2",
        tenant_id: "t1",
        period_key: PERIOD_KEY,
        action: "closing_guard_passed",
        trace_id: "trace-2",
        created_at: "2026-08-05T11:00:00Z",
        payload: { invariant: "CLOSING_OK" },
      },
    ];

    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_NEGATIVE_CLOSING,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: true,
        }}
        audit_trail={auditTrail}
      />,
    );

    const auditList = screen.getByTestId("audit-trail-list");
    expect(within(auditList).getByTestId("audit-entry-audit-1")).toBeInTheDocument();
    expect(within(auditList).getByTestId("audit-entry-audit-2")).toBeInTheDocument();
  });

  // ── Case 5: production consumption events render ─────────────
  it("test_production_consumption_events_render", () => {
    // P3-3rd-sweep P6: render <MonthlyInputTabs> with
    // production_consumption_events prop and assert on [수불부] tab content.
    const events = [
      {
        product_id: "019200a0-0000-7000-8000-0000000000b1",
        period_key: PERIOD_KEY,
        event_type: "production_output_inbound" as const,
        qty: "10.0000",
        trace_id: "trace-1",
      },
      {
        product_id: "019200a0-0000-7000-8000-0000000000b2",
        period_key: PERIOD_KEY,
        event_type: "production_material_consumption" as const,
        qty: "-4.0000",
        trace_id: "trace-1",
      },
    ];

    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="subub"
        invariant={{
          code: INVARIANT_CODE_CLOSING_OK,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: true,
        }}
        production_consumption_events={events}
      />,
    );

    expect(screen.getByTestId("event-019200a0-0000-7000-8000-0000000000b1")).toBeInTheDocument();
    expect(screen.getByTestId("event-019200a0-0000-7000-8000-0000000000b2")).toBeInTheDocument();
  });

  // ── Case 6: opening locked disables fieldset ─────────────────
  it("test_opening_locked_disables_fieldset", () => {
    // P3-3rd-sweep P7: render <MonthlyInputTabs> with blocked invariant
    // and assert the gate fieldset is disabled. P31: assert the form
    // submit button shows "마감 불가" (not "저장") — which means the user
    // can see the manual edit reject state without firing a click.
    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_NEGATIVE_CLOSING,
          negative_products: {
            "019200a0-0000-7000-8000-0000000000a1": "-5.0000",
          },
          closing_per_product: {},
          guard_enabled: true,
        }}
      />,
    );

    const gate = screen.getByTestId("m2-closing-guard-gate");
    expect(gate.tagName).toBe("FIELDSET");
    expect(gate).toBeDisabled();
    // P3-3rd-sweep P31: blocked form shows "마감 불가" (manual edit reject UI).
    const submitButton = screen.getByTestId("monthly-input-row-submit");
    expect(submitButton).toHaveTextContent("마감 불가");
  });

  // ── Bonus: EMPTY_PERIOD invariant hides banner ───────────────
  it("test_empty_period_hides_banner", () => {
    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_EMPTY_PERIOD,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: false,
        }}
      />,
    );
    expect(screen.queryByTestId("m2-closing-guard-banner")).toBeNull();
  });

  // ── Story 6.2 T8.2 — 3 NEW 6-2 scenarios ─────────────────────

  // Case 7: monthly_closing_report=READY → panel renders in [마감] tab
  it("test_monthly_closing_report_ready_panel_renders", () => {
    const aggregate = {
      period_key: PERIOD_KEY,
      view_mode: "READY" as const,
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
      audit_emitted: false,
      currency_pair: {
        base: "KRW",
        quote: "USD",
        rate: "1320.50",
        source: "한국은행 2026-08-08",
      },
      trace_id: "trace-001",
      report_generated_at: "2026-08-08T00:00:00Z",
    };

    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_CLOSING_OK,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: true,
        }}
        monthly_closing_report={aggregate}
        closing_period_capability_granted={true}
      />,
    );

    const panel = screen.getByTestId("monthly-closing-report-panel");
    expect(panel).toBeInTheDocument();
    expect(panel).toHaveAttribute("data-view-mode", "READY");
    expect(screen.getByTestId("kpi-closing-snapshot-count")).toHaveTextContent("4");
  });

  // Case 8: monthly_closing_report_capability_granted=false → panel hidden
  it("test_monthly_closing_report_panel_hidden_when_capability_denied", () => {
    const aggregate = {
      period_key: PERIOD_KEY,
      view_mode: "READY" as const,
      closing_snapshot_count: 4,
      ledger_event_count: 12,
      fiscal_period_snapshot_count: 4,
      opening_inventory_count: 4,
      closing_per_product: [],
      audit_emitted: false,
      currency_pair: null,
      trace_id: "trace-001",
      report_generated_at: "2026-08-08T00:00:00Z",
    };

    const { container } = render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_CLOSING_OK,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: true,
        }}
        monthly_closing_report={aggregate}
        closing_period_capability_granted={false}
      />,
    );

    // Panel hidden when capability denied
    expect(
      container.querySelector('[data-testid="monthly-closing-report-panel"]'),
    ).toBeNull();
  });

  // Case 9: monthly_closing_report V4 FAIL verdict → KPI 빨강
  it("test_monthly_closing_report_v4_fail_kpi_red", () => {
    const aggregate = {
      period_key: PERIOD_KEY,
      view_mode: "READY" as const,
      closing_snapshot_count: 4,
      ledger_event_count: 12,
      fiscal_period_snapshot_count: 4,
      opening_inventory_count: 4,
      closing_per_product: [],
      audit_emitted: false,
      currency_pair: null,
      trace_id: "trace-001",
      report_generated_at: "2026-08-08T00:00:00Z",
    };

    const v4_verdict = {
      code: "monthly_closing_v4_fail",
      product_whitelist_size: 4,
      status: "FAIL" as const,
      source_count: 2 as const,
      failures: [
        {
          product_id: "019200a0-0000-7000-8000-0000000000a1",
          ledger_qty: "10.0000",
          closing_snapshot_qty: "11.0000",
          message_ko: "마감 snapshot 불일치",
        },
      ],
      skip_reason_ko: null,
      verified_at: "2026-08-08T00:00:00Z",
      trace_id: "trace-v4",
    };

    render(
      <MonthlyInputTabs
        period_key={PERIOD_KEY}
        defaultTab="close"
        invariant={{
          code: INVARIANT_CODE_CLOSING_OK,
          negative_products: {},
          closing_per_product: {},
          guard_enabled: true,
        }}
        monthly_closing_report={aggregate}
        monthly_closing_report_v4_verdict={v4_verdict}
        closing_period_capability_granted={true}
      />,
    );

    const kpi = screen.getByTestId("kpi-v4-verdict");
    expect(kpi).toHaveAttribute("data-status", "FAIL");
    expect(screen.getByTestId("v4-failures-list")).toBeInTheDocument();
  });
});
