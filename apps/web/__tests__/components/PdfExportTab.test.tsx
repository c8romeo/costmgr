/**
 * apps/web/__tests__/components/PdfExportTab.test.tsx — cj-293 follow-up #1 (cj-style 295번째)
 *
 * Vitest tests for PdfExportTab (Story 30.2 PDF export tab UI, FR-30-2).
 *
 * Coverage (4 tests):
 *   1. ko-KR NFR18 SSOT labels verbatim
 *   2. data-testid: pdf-export-tab-panel + pdf-export-tab + pdf-period-selector-* + pdf-download-button
 *   3. period dropdown generates 12 monthly options (last 12 months)
 *   4. type selector defaults to cost-records + has bom option
 *
 * Pattern verbatim from CsvExportTab.test.tsx (cj-282a wire sprint 결정 wire).
 *
 * CR 11-3 honest-DEFER 235번째:
 *   - tenant_id 결정 wire 보류 (backend tenant context 가 canonical)
 *   - ko-KR.json EXTENSION 결정 wire 보류 (cj-style 296+ 적용)
 *   - DB integration / e2e 결정 wire 보류 (cj-style 296+ 적용)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PdfExportTab } from "@/components/reports/PdfExportTab";

const DEFAULT_PROPS = {
  accessToken: "test-token-abc",
  // cj-287 wire 결정 wire 보존 — tenantId prop EXTENSION pattern.
  // The PdfExportTab fetches /api/v1/exports/pdf with tenant_id as a query
  // param; tests render the component with a deterministic UUIDv5 placeholder
  // matching the cj-286 EXTENSION report_fixtures tenant namespace.
  tenantId: "00000000-0000-0000-0000-000000000000",
  initialPeriod: "2026-08",
  initialType: "cost-records" as const,
};

describe("PdfExportTab — cj-293 follow-up #1 (cj-style 295번째)", () => {
  it("renders ko-KR labels verbatim per NFR18 SSOT", () => {
    render(<PdfExportTab {...DEFAULT_PROPS} />);

    // ko-KR NFR18 SSOT 결정 wire.
    expect(screen.getByText("PDF 내보내기")).toBeInTheDocument();
    expect(screen.getByText("내보내기 종류")).toBeInTheDocument();
    expect(screen.getByText(/기간 선택/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /PDF 다운로드/ })).toBeInTheDocument();
  });

  it("mounts 4 data-testids: pdf-export-tab-panel, pdf-export-tab, pdf-period-selector-{YYYY-MM}, pdf-download-button", () => {
    render(<PdfExportTab {...DEFAULT_PROPS} />);

    // 4 mandatory data-testids — cj-293 wire 결정 wire 보존.
    expect(screen.getByTestId("pdf-export-tab-panel")).toBeInTheDocument();
    expect(screen.getByTestId("pdf-export-tab")).toBeInTheDocument();
    expect(
      screen.getByTestId("pdf-period-selector-2026-08"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("pdf-download-button")).toBeInTheDocument();
  });

  it("period dropdown generates last 12 monthly options in YYYY-MM format", () => {
    render(<PdfExportTab {...DEFAULT_PROPS} />);

    const periodSelect = screen.getByTestId(
      "pdf-period-selector-2026-08",
    ) as HTMLSelectElement;
    expect(periodSelect.tagName).toBe("SELECT");

    // 12 options (current month + 11 previous) 결정 wire.
    const options = periodSelect.querySelectorAll("option");
    expect(options).toHaveLength(12);

    // initialPeriod ("2026-08") is in the option list 결정 wire.
    const optionValues = Array.from(options).map((opt) => opt.value);
    expect(optionValues).toContain("2026-08");

    // First option = current month (most recent first, UX convention) 결정 wire.
    const today = new Date();
    const currentYyyyMm = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
    expect(options[0]?.value).toBe(currentYyyyMm);

    // All options match YYYY-MM format 결정 wire.
    const yyyyMmPattern = /^\d{4}-(0[1-9]|1[0-2])$/;
    options.forEach((opt) => {
      expect(opt.value).toMatch(yyyyMmPattern);
    });
  });

  it("type selector defaults to cost-records with bom as alternative option", () => {
    render(<PdfExportTab {...DEFAULT_PROPS} />);

    const typeSelect = screen.getByTestId(
      "pdf-export-type-selector",
    ) as HTMLSelectElement;
    expect(typeSelect.tagName).toBe("SELECT");
    expect(typeSelect.value).toBe("cost-records"); // initialType 결정 wire.

    // 2 options: cost-records + bom 결정 wire (verbatim from cj-282 PRD entry spec line 110).
    const options = typeSelect.querySelectorAll("option");
    expect(options).toHaveLength(2);
    expect(options[0]?.value).toBe("cost-records");
    expect(options[1]?.value).toBe("bom");
  });
});
