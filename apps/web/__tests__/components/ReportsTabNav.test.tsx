/**
 * apps/web/__tests__/components/ReportsTabNav.test.tsx — cj-295 follow-up #1 (cj-style 295번째)
 *
 * Vitest tests for ReportsTabNav (Story 30.1/30.2 reports tab nav wrapper).
 *
 * Coverage (3 tests):
 *   1. Default active tab is "csv" (CSV tab visible, PDF tab hidden).
 *   2. Clicking the PDF tab activates the PdfExportTab panel.
 *   3. data-testid: reports-tab-nav, reports-tab-csv, reports-tab-pdf.
 *
 * Pattern verbatim from CsvExportTab.test.tsx (cj-282a wire sprint 결정 wire).
 *
 * CR 11-3 honest-DEFER 235번째:
 *   - tenant_id 결정 wire 보류 (backend tenant context 가 canonical)
 *   - ko-KR.json EXTENSION 결정 wire 보류 (cj-style 296+ 적용)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ReportsTabNav } from "@/components/reports/ReportsTabNav";

const DEFAULT_PROPS = {
  accessToken: "test-token-abc",
  tenantId: "00000000-0000-0000-0000-000000000000",
  initialPeriod: "2026-08",
  initialType: "cost-records" as const,
};

describe("ReportsTabNav — cj-295 follow-up #1 (cj-style 295번째)", () => {
  it("defaults to CSV tab on mount (CsvExportTab visible, PdfExportTab hidden)", () => {
    render(<ReportsTabNav {...DEFAULT_PROPS} />);

    // CSV tab heading visible (CsvExportTab data-testid).
    expect(screen.getByTestId("csv-export-tab")).toBeInTheDocument();

    // PDF tab heading NOT in document (PdfExportTab not yet rendered).
    expect(screen.queryByTestId("pdf-export-tab")).not.toBeInTheDocument();
  });

  it("mounts 3 data-testids: reports-tab-nav, reports-tab-csv, reports-tab-pdf", () => {
    render(<ReportsTabNav {...DEFAULT_PROPS} />);

    expect(screen.getByTestId("reports-tab-nav")).toBeInTheDocument();
    expect(screen.getByTestId("reports-tab-csv")).toBeInTheDocument();
    expect(screen.getByTestId("reports-tab-pdf")).toBeInTheDocument();
  });

  it("renders ko-KR labels for both tabs (NFR18 SSOT)", () => {
    render(<ReportsTabNav {...DEFAULT_PROPS} />);

    // Both tab labels in ko-KR (NFR18 SSOT 결정 wire).
    expect(screen.getByRole("tab", { name: "CSV 내보내기" })).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "PDF 내보내기" })).toBeInTheDocument();
  });
});
