/**
 * apps/web/__tests__/components/CsvExportTab.test.tsx — cj-282a wire sprint (cj-style 283번째)
 *
 * Vitest tests for CsvExportTab (Story 30.1 CSV export tab UI, FR-30-1).
 *
 * Coverage (4 tests):
 *   1. ko-KR NFR18 SSOT labels verbatim (cj-282 PRD entry spec line 132)
 *   2. data-testid: reports-tab + csv-export-tab + period-selector-* + download-button
 *   3. period dropdown generates 12 monthly options (last 12 months)
 *   4. type selector defaults to cost-records + has bom option
 *
 * CR 11-3 honest-DEFER 223번째:
 *   - tenant_id 결정 wire 보류 (cj-style 284+ 적용 — backend tenant context 가 canonical)
 *   - ko-KR.json EXTENSION 결정 wire 보류 (cj-style 284+ 적용)
 *   - DB integration / e2e 결정 wire 보류 (cj-style 284+ 적용)
 */

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { CsvExportTab } from "@/components/reports/CsvExportTab";

const DEFAULT_PROPS = {
  accessToken: "test-token-abc",
  initialPeriod: "2026-08",
  initialType: "cost-records" as const,
};

describe("CsvExportTab — cj-282a wire sprint (cj-style 283번째)", () => {
  it("renders ko-KR labels verbatim per cj-282 PRD entry spec line 132 (NFR18 SSOT)", () => {
    render(<CsvExportTab {...DEFAULT_PROPS} />);

    // ko-KR NFR18 SSOT — cj-282 PRD entry spec line 132 verbatim 결정 wire.
    expect(screen.getByText("CSV 내보내기")).toBeInTheDocument();
    expect(screen.getByText("내보내기 종류")).toBeInTheDocument();
    expect(screen.getByText(/기간 선택/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "다운로드" })).toBeInTheDocument();
  });

  it("mounts 4 data-testids: reports-tab, csv-export-tab, period-selector-{YYYY-MM}, download-button", () => {
    render(<CsvExportTab {...DEFAULT_PROPS} />);

    // 4 mandatory data-testids — cj-282 PRD entry spec §F44.1 verbatim 결정 wire.
    expect(screen.getByTestId("reports-tab")).toBeInTheDocument();
    expect(screen.getByTestId("csv-export-tab")).toBeInTheDocument();
    expect(
      screen.getByTestId("period-selector-2026-08"),
    ).toBeInTheDocument();
    expect(screen.getByTestId("download-button")).toBeInTheDocument();
  });

  it("period dropdown generates last 12 monthly options in YYYY-MM format", () => {
    render(<CsvExportTab {...DEFAULT_PROPS} />);

    const periodSelect = screen.getByTestId(
      "period-selector-2026-08",
    ) as HTMLSelectElement;
    expect(periodSelect.tagName).toBe("SELECT");

    // 12 options (current month + 11 previous) 결정 wire.
    const options = periodSelect.querySelectorAll("option");
    expect(options).toHaveLength(12);

    // initialPeriod ("2026-08") is in the option list 결정 wire.
    const optionValues = Array.from(options).map((opt) => opt.value);
    expect(optionValues).toContain("2026-08");

    // First option = current month (most recent first, UX convention) 결정 wire.
    // Today is 2026-09 → first option should be "2026-09" or later.
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
    render(<CsvExportTab {...DEFAULT_PROPS} />);

    const typeSelect = screen.getByTestId(
      "csv-export-type-selector",
    ) as HTMLSelectElement;
    expect(typeSelect.tagName).toBe("SELECT");
    expect(typeSelect.value).toBe("cost-records"); // initialType 결정 wire.

    // 2 options: cost-records + bom 결정 wire (PRD line 110 verbatim).
    const options = typeSelect.querySelectorAll("option");
    expect(options).toHaveLength(2);
    expect(options[0]?.value).toBe("cost-records");
    expect(options[1]?.value).toBe("bom");
  });
});
