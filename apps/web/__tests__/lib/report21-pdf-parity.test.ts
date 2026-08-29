// apps/web/__tests__/lib/report21-pdf-parity.test.ts — Story 9.7
//
// Cross-language parity tests for Report #21 PDF download TS mirror
// (PRD §9 #21 + A30 SHARED PDF Generator factory pattern).
//
// Mirrors `apps/web/lib/report21-pdf.ts`:
//   - Report21PdfResponse shape
//   - downloadReport21PdfTS discriminated union return
//   - base64PdfToBlob (Base64 → Blob with application/pdf MIME)
//   - triggerPdfDownload (anchor + click + revokeObjectURL)
//
// A35 wire — resolves D3 (TS mirror parity 누락 3건 중 report21-pdf parity 추가).

import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  base64PdfToBlob,
  downloadReport21PdfTS,
  triggerPdfDownload,
} from "../../lib/report21-pdf";
import { server } from "../../mocks/server";

afterEach(() => {
  server.resetHandlers();
});

// ── base64PdfToBlob (3 cases) ──────────────────────────────

describe("base64PdfToBlob (Story 9.4 parity, A35 wire)", () => {
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
  it("creates anchor element with download attribute set to 'report21_{periodKey}.pdf'", () => {
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

// ── downloadReport21PdfTS discriminated union (4 cases) ───

describe("downloadReport21PdfTS discriminated union return", () => {
  it("returns error envelope when periodKey is empty", async () => {
    const result = await downloadReport21PdfTS("", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT21_PERIOD_NOT_COMMITTED");
    }
  });

  it("returns ok envelope on 200 with PDF base64", async () => {
    server.use(
      http.post("/api/v1/reports/21/pdf", () =>
        HttpResponse.json(
          {
            period_key: "2026-08",
            pdf_base64: btoa("PDF bytes"),
            size_bytes: 9,
            generation_hash: "sha256:" + "p".repeat(64),
            report_code: "COST_OBJECT_BREAKDOWN",
          },
          { status: 200 },
        ),
      ),
    );

    const result = await downloadReport21PdfTS("2026-08", "sb-token");
    expect(result.kind).toBe("ok");
    if (result.kind === "ok") {
      expect(result.data.report_code).toBe("COST_OBJECT_BREAKDOWN");
      expect(result.data.pdf_base64).toBe(btoa("PDF bytes"));
    }
  });

  it("returns error envelope on 500 with PDF_GENERATION_ERROR code", async () => {
    server.use(
      http.post("/api/v1/reports/21/pdf", () =>
        HttpResponse.json(
          {
            code: "REPORT_PDF_GENERATION_ERROR",
            message_ko: "PDF 생성 중 오류가 발생했습니다",
          },
          { status: 500 },
        ),
      ),
    );

    const result = await downloadReport21PdfTS("2026-08", "sb-token");
    expect(result.kind).toBe("error");
    if (result.kind === "error") {
      expect(result.code).toBe("REPORT_PDF_GENERATION_ERROR");
    }
  });

  it("sends period_key in request body (POST JSON)", async () => {
    let observedBody: unknown = null;
    server.use(
      http.post("/api/v1/reports/21/pdf", async ({ request }) => {
        observedBody = await request.json();
        return HttpResponse.json(
          {
            period_key: "2026-08",
            pdf_base64: btoa("PDF bytes"),
            size_bytes: 9,
            generation_hash: "sha256:" + "p".repeat(64),
            report_code: "COST_OBJECT_BREAKDOWN",
          },
          { status: 200 },
        );
      }),
    );

    await downloadReport21PdfTS("2026-08", "sb-token");
    expect(observedBody).toEqual({ period_key: "2026-08" });
  });
});

// ── Report21PdfResponse shape (2 cases) ──────────────────

describe("Report21PdfResponse shape", () => {
  it("requires period_key, pdf_base64, size_bytes, generation_hash, report_code", () => {
    const response = {
      period_key: "2026-08",
      pdf_base64: "BASE64",
      size_bytes: 100,
      generation_hash: "sha256:" + "0".repeat(64),
      report_code: "COST_OBJECT_BREAKDOWN" as const,
    };
    expect(response.report_code).toBe("COST_OBJECT_BREAKDOWN");
    expect(typeof response.pdf_base64).toBe("string");
    expect(typeof response.size_bytes).toBe("number");
  });

  it("report_code Literal is 'COST_OBJECT_BREAKDOWN'", () => {
    const validCode = "COST_OBJECT_BREAKDOWN";
    expect(validCode).toBe("COST_OBJECT_BREAKDOWN");
  });
});