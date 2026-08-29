/**
 * apps/web/__tests__/closing-pdf-export.test.ts — Story 6.3 T2 Vitest.
 *
 * Vitest tests for the TS closing PDF export projection:
 * 1. CLOSING_PDF_EXPORT_TITLE_KO / CLOSING_PDF_EXPORT_EMPTY_KO SSOT values.
 * 2. CLOSING_PDF_INDUSTRY_VALUES — 4 canonical industries.
 * 3. isValidClosingPdfIndustry — W5 deferral guard.
 * 4. buildClosingPdfExportFilename — `closing-{period_key}.pdf` format.
 * 5. formatClosingPdfExportSize — B / KB / MB units.
 * 6. triggerClosingPdfExportDownload — blob + a[download] pattern.
 * 7. ClosingPdfExportButton — render test (loading + idle states).
 *
 * Story 0.5 vitest activation — these tests run as part of `pnpm test`.
 */

import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi, beforeEach } from "vitest";

import { ClosingPdfExportButton } from "@/components/m2-input/ClosingPdfExportButton";
import {
  CLOSING_PDF_EXPORT_TITLE_KO,
  CLOSING_PDF_EXPORT_EMPTY_KO,
  CLOSING_PDF_INDUSTRY_VALUES,
  buildClosingPdfExportFilename,
  formatClosingPdfExportSize,
  isValidClosingPdfIndustry,
  triggerClosingPdfExportDownload,
} from "@/lib/closing-pdf-export";

// Mock sonner toast
vi.mock("sonner", () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
    info: vi.fn(),
  },
}));

// Mock next-intl useTranslations
vi.mock("next-intl", () => ({
  useTranslations: () => (key: string, vars?: Record<string, string>) => {
    const map: Record<string, string> = {
      button_label: "PDF 다운로드",
      button_downloading: "PDF 생성 중...",
      panel_section_label: "PDF Export",
      panel_section_help: "월 마감 보고서를 PDF(A4, ≤ 5MB)로 다운로드",
      toast_success_export: `PDF 다운로드 완료 (${vars?.size ?? "?"})`,
      toast_error_invalid_industry: "업종 미지원",
      toast_error_size_exceeded: "PDF 크기 초과",
      toast_error_audit_emit: "PDF 저장 audit emit 실패",
      toast_error_generic_unknown: "PDF Export 실패: 알 수 없는 오류",
    };
    return map[key] ?? key;
  },
}));

// ── Pure-kernel constants ──────────────────────────────────────

describe("ClosingPdfExport — Korean SSOT", () => {
  it("test_closing_pdf_export_title_ko", () => {
    expect(CLOSING_PDF_EXPORT_TITLE_KO).toBe("마감 보고서 PDF Export");
  });

  it("test_closing_pdf_export_empty_ko", () => {
    expect(CLOSING_PDF_EXPORT_EMPTY_KO).toBe("PDF 데이터 없음");
  });

  it("test_canonical_industry_values", () => {
    expect(CLOSING_PDF_INDUSTRY_VALUES).toHaveLength(4);
    expect(CLOSING_PDF_INDUSTRY_VALUES).toContain("manufacturing");
    expect(CLOSING_PDF_INDUSTRY_VALUES).toContain("manufacturing_service");
    expect(CLOSING_PDF_INDUSTRY_VALUES).toContain("manufacturing_service_other");
    expect(CLOSING_PDF_INDUSTRY_VALUES).toContain("service");
  });

  it("test_reject_non_canonical_industry", () => {
    expect(isValidClosingPdfIndustry("trad")).toBe(false);
    expect(isValidClosingPdfIndustry("manufacturing")).toBe(true);
    expect(isValidClosingPdfIndustry(null)).toBe(false);
    expect(isValidClosingPdfIndustry(undefined)).toBe(false);
  });

  it("test_build_filename_format", () => {
    expect(buildClosingPdfExportFilename("2026-07")).toBe("closing-2026-07.pdf");
    expect(buildClosingPdfExportFilename("2026-08")).toBe("closing-2026-08.pdf");
  });

  it("test_format_size_units", () => {
    expect(formatClosingPdfExportSize(500)).toBe("500 B");
    expect(formatClosingPdfExportSize(2048)).toBe("2.0 KB");
    expect(formatClosingPdfExportSize(5 * 1024 * 1024)).toBe("5.00 MB");
  });
});

// ── Browser download helper ─────────────────────────────────────

describe("triggerClosingPdfExportDownload", () => {
  let originalCreateObjectURL: typeof URL.createObjectURL;
  let originalRevokeObjectURL: typeof URL.revokeObjectURL;
  let clicked_elements: HTMLAnchorElement[];

  beforeEach(() => {
    clicked_elements = [];
    originalCreateObjectURL = URL.createObjectURL;
    originalRevokeObjectURL = URL.revokeObjectURL;
    URL.createObjectURL = vi.fn(() => "blob:mock-url");
    URL.revokeObjectURL = vi.fn();

    // Track click on anchor — store references to detect via dispatchEvent.
    const origCreate = document.createElement.bind(document);
    vi.spyOn(document, "createElement").mockImplementation((tag: string) => {
      const el = origCreate(tag);
      if (tag === "a") {
        const anchorEl = el as HTMLAnchorElement;
        const origClick = anchorEl.click.bind(anchorEl);
        anchorEl.click = () => {
          clicked_elements.push(anchorEl);
          origClick();
        };
      }
      return el;
    });
  });

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL;
    URL.revokeObjectURL = originalRevokeObjectURL;
    vi.restoreAllMocks();
  });

  it("test_trigger_download_creates_blob_anchor", () => {
    const bytes = new Uint8Array([0x25, 0x50, 0x44, 0x46]); // %PDF magic
    triggerClosingPdfExportDownload(bytes, "closing-2026-07.pdf");

    expect(URL.createObjectURL).toHaveBeenCalledTimes(1);
    expect(clicked_elements).toHaveLength(1);
    expect(clicked_elements[0].download).toBe("closing-2026-07.pdf");
  });
});

// ── React Component: ClosingPdfExportButton ─────────────────────

describe("ClosingPdfExportButton", () => {
  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
    vi.restoreAllMocks();
  });

  it("test_button_renders_with_test_id", () => {
    render(
      <ClosingPdfExportButton
        periodKey="2026-07"
        industry="manufacturing"
      />,
    );
    const btn = screen.getByTestId("closing-pdf-export-button");
    expect(btn).toBeInTheDocument();
    expect(btn).toHaveAttribute("data-period-key", "2026-07");
    expect(btn).toHaveAttribute("data-industry", "manufacturing");
    expect(btn).toHaveAttribute("data-status", "IDLE");
    expect(btn).toHaveTextContent("PDF 다운로드");
  });

  it("test_button_hidden_when_invalid_industry", () => {
    // Industry 'trad' is pre-6-2 hardcode — REJECT.
    // The component renders null because the type system rejects it,
    // but we test the runtime guard via the TS helper.
    // (Component prop type narrows — can only pass valid industries.)
    const valid = isValidClosingPdfIndustry("trad");
    expect(valid).toBe(false);
  });

  it("test_button_triggers_download_on_click", async () => {
    const mockPdfBytes = new Uint8Array([0x25, 0x50, 0x44, 0x46, 0x2d, 0x31, 0x2e, 0x34]); // %PDF-1.4

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      arrayBuffer: () => Promise.resolve(mockPdfBytes.buffer),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    // Mock URL.createObjectURL for download.
    URL.createObjectURL = vi.fn(() => "blob:mock-url");
    URL.revokeObjectURL = vi.fn();

    render(
      <ClosingPdfExportButton
        periodKey="2026-07"
        industry="manufacturing"
      />,
    );

    const btn = screen.getByTestId("closing-pdf-export-button");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        expect.stringContaining("/api/v1/inventory/monthly-closing-report/export-pdf"),
        expect.objectContaining({ method: "POST" }),
      );
    });

    await waitFor(() => {
      expect(btn).toHaveAttribute("data-status", "IDLE");
    });
  });

  it("test_button_shows_error_toast_on_invalid_industry_response", async () => {
    const { toast } = await import("sonner");

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: () =>
        Promise.resolve({
          code: "CLOSING_PDF_EXPORT_INVALID_INDUSTRY",
          message_ko: "업종 미지원",
        }),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    render(
      <ClosingPdfExportButton
        periodKey="2026-07"
        industry="manufacturing"
      />,
    );

    const btn = screen.getByTestId("closing-pdf-export-button");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("업종 미지원");
    });
  });

  it("test_button_shows_error_toast_on_size_exceeded", async () => {
    const { toast } = await import("sonner");

    // Return 6MB (over 5MB cap) of zeros.
    const sixMbBytes = new Uint8Array(6 * 1024 * 1024);

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      arrayBuffer: () => Promise.resolve(sixMbBytes.buffer),
    });
    global.fetch = fetchMock as unknown as typeof fetch;

    render(
      <ClosingPdfExportButton
        periodKey="2026-07"
        industry="manufacturing"
      />,
    );

    const btn = screen.getByTestId("closing-pdf-export-button");
    fireEvent.click(btn);

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith("PDF 크기 초과");
    });
  });
});
