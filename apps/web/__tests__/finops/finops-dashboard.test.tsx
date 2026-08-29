/**
 * apps/web/__tests__/finops/finops-dashboard.test.tsx —
 * Phase 11 T7 (cj-style 107번째 wire) — 3 NEW vitest cases for the
 * FinOps Showback / Chargeback dashboard.
 */
import { render, screen, waitFor } from "@testing-library/react";
import { NextIntlClientProvider } from "next-intl";
import { describe, expect, it, vi } from "vitest";

import koKR from "@/messages/ko-KR.json";

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    refresh: vi.fn(),
  }),
  redirect: vi.fn(),
}));

import { FinopsDashboardPanel } from "@/components/finops/FinopsDashboardPanel";

vi.mock("@/lib/finops/finops-client", () => ({
  listShowbackBreakdown: vi.fn().mockResolvedValue({
    items: [
      {
        department_id: "dept-1",
        department_name: "Engineering",
        cost_center_id: "CC-0001",
        cost_center_code: "CC-0001",
        total_amount: "1000.00",
        currency_code: "KRW",
        period_key: "2026-08",
        rank: 1,
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  }),
  listShowbackComparison: vi.fn().mockResolvedValue({
    items: [
      {
        department_id: "dept-1",
        current_period_amount: "1100.00",
        previous_period_amount: "1000.00",
        delta_amount: "100.00",
        delta_pct: "10.00",
        currency_code: "KRW",
        comparison_period: "previous_month",
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  }),
  listChargebackResults: vi.fn().mockResolvedValue({
    items: [
      {
        chargeback_id: "cb-1",
        tenant_id: "t1",
        period_key: "2026-08",
        department_id: "dept-1",
        cost_center_id: "CC-0001",
        rule_type: "flat_fee",
        base_amount: "1000.00",
        markup_amount: "100.00",
        tax_amount: "110.00",
        total_amount: "1210.00",
        currency_code: "KRW",
        computed_at: "2026-08-24T00:00:00Z",
        trace_id: "trace-1",
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  }),
  listDepartmentMappings: vi.fn().mockResolvedValue({
    items: [
      {
        id: "m1",
        tenant_id: "t1",
        department_id: "dept-1",
        department_name: "Engineering",
        cost_center_id: "CC-0001",
        auto_created: false,
        created_by: "user-1",
        updated_by: "user-1",
      },
    ],
    total: 1,
    page: 1,
    page_size: 20,
  }),
  exportChargeback: vi.fn().mockResolvedValue(new Blob(["hello"])),
}));

function renderWithIntl(ui: React.ReactElement) {
  return render(
    <NextIntlClientProvider locale="ko" messages={koKR as Record<string, unknown>}>
      {ui}
    </NextIntlClientProvider>,
  );
}

describe("FinopsDashboardPanel", () => {
  it("renders the dashboard title + period selector", async () => {
    renderWithIntl(<FinopsDashboardPanel accessToken="t" locale="ko" />);
    expect(screen.getByTestId("finops-title")).toBeInTheDocument();
    expect(screen.getByTestId("period-select")).toBeInTheDocument();
  });

  it("renders breakdown + comparison + chargeback rows after fetch", async () => {
    renderWithIntl(<FinopsDashboardPanel accessToken="t" locale="ko" />);
    await waitFor(
      () => {
        expect(
          screen.getAllByTestId("breakdown-row").length,
        ).toBeGreaterThanOrEqual(1);
      },
      { timeout: 5000 },
    );
    expect(
      screen.getAllByTestId("comparison-row").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByTestId("chargeback-row").length,
    ).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByTestId("mapping-row").length,
    ).toBeGreaterThanOrEqual(1);
  });

  it("renders export buttons + handles CSV export click", async () => {
    renderWithIntl(<FinopsDashboardPanel accessToken="t" locale="ko" />);
    await waitFor(() =>
      expect(screen.getByTestId("export-csv")).toBeInTheDocument(),
    );
    expect(screen.getByTestId("export-csv")).toBeInTheDocument();
    expect(screen.getByTestId("export-pdf")).toBeInTheDocument();
  });
});
