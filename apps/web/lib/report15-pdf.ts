/**
 * apps/web/lib/report15-pdf.ts — Story 11.6
 *
 * TS mirror for Report #15 PDF download (POST /api/v1/reports/15/pdf).
 *
 * A30 forward-lock SHARED PDF generator 결정 wire (9-3 handoff lock):
 * Report #21 (Cost Object Breakdown) 본 진입점 + Report #15 (활동원가 내역서) =
 * SHARED factory pattern via Discriminated union
 * report_id: Literal[15..21]. A32 forward-lock (SHARED factory reuse 1st case) wire 진입점.
 */

import { REPORT15_ERROR_CODES, type Report15ErrorCode } from "./report15";

// Re-export Report15ErrorCode so callers (PdfExportButton) can use it as a
// React state type without importing from ./report15 directly (SSOT).
export type { Report15ErrorCode };

export interface Report15PdfResponse {
  period_key: string;
  /** Base64-encoded PDF bytes (AD-15 cross-language parity) */
  pdf_base64: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  size_bytes: number;
  /** V8 byte-equality sha256 hexdigest */
  generation_hash: string;
  report_code: "ACTIVITY_COST_DETAIL";
}

/**
 * Generate Report #15 PDF via POST /api/v1/reports/15/pdf.
 *
 * Returns discriminated union: PDF envelope (success) | Error envelope.
 */
export async function downloadReport15PdfTS(
  periodKey: string,
  accessToken: string | undefined,
): Promise<
  | { kind: "ok"; data: Report15PdfResponse }
  | { kind: "error"; code: Report15ErrorCode | "NETWORK_ERROR"; message: string }
> {
  if (!periodKey) {
    return { kind: "error", code: "REPORT15_PERIOD_NOT_COMMITTED", message: "기간 키가 필요합니다" };
  }
  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (accessToken) headers["Authorization"] = `Bearer ${accessToken}`;

    const response = await fetch("/api/v1/reports/15/pdf", {
      method: "POST",
      headers,
      body: JSON.stringify({ period_key: periodKey }),
    });
    if (!response.ok) {
      const errBody = (await response.json().catch(() => ({}))) as {
        code?: string;
        message_ko?: string;
      };
      return {
        kind: "error",
        code: (errBody.code as Report15ErrorCode) ||
          REPORT15_ERROR_CODES.PDF_GENERATION_ERROR,
        message: errBody.message_ko || `HTTP ${response.status}`,
      };
    }
    const data = (await response.json()) as Report15PdfResponse;
    return { kind: "ok", data };
  } catch (e) {
    return { kind: "error", code: "NETWORK_ERROR", message: String(e) };
  }
}

/**
 * Convert Base64-encoded PDF to Blob for browser download.
 */
export function base64PdfToBlob(base64: string): Blob {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: "application/pdf" });
}

/**
 * Trigger browser PDF download with filename `report15_{periodKey}.pdf`.
 */
export function triggerPdfDownload(pdfBlob: Blob, periodKey: string): void {
  const url = URL.createObjectURL(pdfBlob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `report15_${periodKey}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}