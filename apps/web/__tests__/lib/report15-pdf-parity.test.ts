// apps/web/__tests__/lib/report15-pdf-parity.test.ts — Story 11.6
//
// Cross-language parity tests for Report #15 PDF download TS mirror
// (PRD §9 #15 + A30 SHARED PDF Generator factory pattern, A32 forward-lock 결정 wire 진입점).
//
// Mirrors `apps/web/lib/report15-pdf.ts`:
//   - Report15PdfResponse shape
//   - downloadReport15PdfTS discriminated union return
//   - base64PdfToBlob (Base64 → Blob with application/pdf MIME)
//   - triggerPdfDownload (anchor + click + revokeObjectURL — filename 'report15_{periodKey}.pdf')

import { afterEach, describe, expect, it, vi } from "vitest";

import {
  base64PdfToBlob,
  downloadReport15PdfTS,
  triggerPdfDownload,
} from "../../lib/report15-pdf";
import { server } from "../../mocks/server";
import { http, HttpResponse } from "msw";

afterEach(() => {
  server.resetHandlers();
});

// ── base64PdfToBlob (3 cases) ──────────────────────────────

describe("base64PdfToBlob (Story 11.6 parity)", () => {
  it("returns Blob with MIME type 'application/pdf'", () => {
    const base64 = btoa("PDF content bytes");
    const blob = base64PdfToBlob(base64);
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe("application/pdf");
  });

  it("Blob size matches decoded byte length", () => {
    const content = "PDF binary content";
    const base64 = btoa(content);
    const blob = base64PdfToBlob(base64);
    expect(blob.size).toBe(content.length);
  });

  it("handles empty base64 input as 0-byte Blob", () => {
    const blob = base64PdfToBlob("");
    expect(blob).toBeInstanceOf(Blob);
    expect(blob.size).toBe(0);
  });
});

// ── triggerPdfDownload (3 cases) ─────────────────────────

describe("triggerPdfDownload (browser anchor pattern)", () => {
  it("creates anchor element with download attribute for Report #15", () => {
    const blob = new Blob(["pdf"], { type: "application/pdf" });
    const createElementSpy = vi.spyOn(document, "createElement");
    triggerPdfDownload(blob, "2026-08");
    const anchorCall = createElementSpy.mock.calls.find(
      (call) => call[0] === "a",
    );
    expect(anchorCall).toBeDefined();
    createElementSpy.mockRestore();
  });

  it("calls revokeObjectURL after click", () => {
    const blob = new Blob(["pdf"], { type: "application/pdf" });
    const revokeSpy = vi.spyOn(URL, "revokeObjectURL");
    triggerPdfDownload(blob, "2026-08");
    expect(revokeSpy).toHaveBeenCalled();
    revokeSpy.mockRestore();
  });

  it("uses createObjectURL with the blob", () => {
    const blob = new Blob(["pdf content"], { type: "application/pdf" });
    const createObjectURLSpy = vi.spyOn(URL, "createObjectURL");
    triggerPdfDownload(blob, "2026-08");
    expect(createObjectURLSpy).toHaveBeenCalledWith(blob);
    createObjectURLSpy.mockRestore();
  });
});

// ── downloadReport15PdfTS discriminated union (4 cases) ───

describe("downloadReport15PdfTS discriminated union return", () => {
  it("returns error envelope when periodKey is empty", async () => {
    const result = await downloadReport15PdfTS("", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT15_PERIOD_NOT_COMMITTED");
    }
  });

  it("returns ok envelope on 200 with PDF base64", async () => {
    server.use(
      http.post("/api/v1/reports/15/pdf", () =>
        HttpResponse.json(
          {
            period_key: "2026-08",
            pdf_base64: btoa("PDF bytes"),
            size_bytes: 9,
            generation_hash: "sha256:" + "1".repeat(64),
            report_code: "ACTIVITY_COST_DETAIL",
          },
          { status: 200 },
        ),
      ),
    );

    const result = await downloadReport15PdfTS("2026-08", "sb-token");
    expect(result.kind).toBe("ok");
    if (result.kind === "ok") {
      expect(result.data.report_code).toBe("ACTIVITY_COST_DETAIL");
    }
  });

  it("returns error envelope on 500", async () => {
    server.use(
      http.post("/api/v1/reports/15/pdf", () =>
        HttpResponse.json(
          { code: "REPORT_PDF_GENERATION_ERROR", message_ko: "PDF 생성 실패" },
          { status: 500 },
        ),
      ),
    );

    const result = await downloadReport15PdfTS("2026-08", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT_PDF_GENERATION_ERROR");
    }
  });

  it("includes Bearer Authorization header when accessToken is provided", async () => {
    let observedAuthHeader = "";
    server.use(
      http.post("/api/v1/reports/15/pdf", ({ request }) => {
        observedAuthHeader = request.headers.get("Authorization") ?? "";
        return HttpResponse.json(
          {
            period_key: "2026-08",
            pdf_base64: btoa("PDF"),
            size_bytes: 3,
            generation_hash: "sha256:" + "1".repeat(64),
            report_code: "ACTIVITY_COST_DETAIL",
          },
          { status: 200 },
        );
      }),
    );

    await downloadReport15PdfTS("2026-08", "sb-token-xyz");
    expect(observedAuthHeader).toBe("Bearer sb-token-xyz");
  });
});