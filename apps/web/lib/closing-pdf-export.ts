/**
 * apps/web/lib/closing-pdf-export.ts — Story 6.3 TS mirror.
 *
 * Closing PDF Export TS projection (AD-15 §11 SSOT parity with
 * `packages/services/m4_inventory/closing_pdf_export.py`).
 *
 * Drift caught by `tests/integration/test_closing_pdf_export_label_consistency.py`.
 *
 * Korean message SSOT (single source of truth for ko-KR.json parity):
 * - CLOSING_PDF_EXPORT_TITLE_KO mirrors Python
 *   `CLOSING_PDF_EXPORT_TITLE_KO`.
 * - CLOSING_PDF_EXPORT_EMPTY_KO mirrors Python
 *   `CLOSING_PDF_EXPORT_EMPTY_KO`.
 *
 * PRD §F6.3 (Closing PDF Export):
 * - A4 page (595×842pt) + Korean subset (UTF-8 hex encoding in metadata).
 * - PDF size ≤ 5MB per period (PRD §F6.3 cap).
 * - 1 product per page + summary cover page.
 * - industry extension follow-up (Epic 12+ 결정 — W5 deferral).
 *
 * A8 inline projection deprecation timeline (carry from 6-2):
 * - 6-3 wire 시점: inline projection 보존 (1 epic maintenance window).
 * - Epic 6 close-out 시점에 fold-in vs deprecate 결정 (A8).
 */

// ── Constants (Korean SSOT) ──────────────────────────────────────
export const CLOSING_PDF_EXPORT_TITLE_KO = "마감 보고서 PDF Export" as const;
export const CLOSING_PDF_EXPORT_EMPTY_KO = "PDF 데이터 없음" as const;

// Canonical industry codes (PRD §6.1 + 6-2 carry-over de-scope).
// W5 deferral: industry='trad' hard-code in 6-2 → Epic 12+ 결정.
export const CLOSING_PDF_INDUSTRY_VALUES = [
  "manufacturing",
  "manufacturing_service",
  "manufacturing_service_other",
  "service",
] as const;

// eslint-disable-next-line @typescript-eslint/no-restricted-types
export type ClosingPdfIndustry = (typeof CLOSING_PDF_INDUSTRY_VALUES)[number];

// ── Export status (3 codes — AD-15 §11 SSOT) ─────────────────────
export const CLOSING_PDF_EXPORT_STATUS_DOWNLOADING = "DOWNLOADING" as const;
export const CLOSING_PDF_EXPORT_STATUS_SUCCESS = "SUCCESS" as const;
export const CLOSING_PDF_EXPORT_STATUS_ERROR = "ERROR" as const;

export const CLOSING_PDF_EXPORT_STATUSES = [
  CLOSING_PDF_EXPORT_STATUS_DOWNLOADING,
  CLOSING_PDF_EXPORT_STATUS_SUCCESS,
  CLOSING_PDF_EXPORT_STATUS_ERROR,
] as const;

export type ClosingPdfExportStatus =
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  (typeof CLOSING_PDF_EXPORT_STATUSES)[number];

// ── Export response wire envelope (matches backend Pydantic) ──────
//
// `pdf_bytes` is provided pre-rendered by the backend — the TS client
// only triggers the download via blob + a[download]. Wire format:
//   {
//     period_key: string,
//     industry: ClosingPdfIndustry,
//     pdf_size_bytes: number,
//     is_empty: boolean,
//     closing_snapshot_count: number,
//     ledger_event_count: number,
//     finalized_at: string (ISO-8601 UTC),
//     pdf_bytes: Uint8Array (raw PDF bytes; size ≤ 5MB per PRD §F6.3),
//   }
export interface ClosingPdfExportResponse {
  period_key: string;
  industry: ClosingPdfIndustry;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  pdf_size_bytes: number;
  is_empty: boolean;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  closing_snapshot_count: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  ledger_event_count: number;
  finalized_at: string;
  pdf_bytes: Uint8Array;
}

// ── Helper: validate industry (W5 deferral guard) ─────────────
export function isValidClosingPdfIndustry(
  industry: string | null | undefined,
): industry is ClosingPdfIndustry {
  if (typeof industry !== "string") return false;
  return (CLOSING_PDF_INDUSTRY_VALUES as readonly string[]).includes(industry);
}

// ── Helper: build filename for Content-Disposition ──────────────
export function buildClosingPdfExportFilename(periodKey: string): string {
  // PRD §F6.3: filename = `closing-{period_key}.pdf`
  return `closing-${periodKey}.pdf`;
}

// ── Helper: trigger browser download via blob + a[download] ──────
//
// Pure helper — takes the raw bytes + filename and dispatches the
// download. Caller is responsible for handling error states (e.g.
// file size > 5MB, audit emit failure, etc.) via the toast.
export function triggerClosingPdfExportDownload(
  pdfBytes: Uint8Array,
  filename: string,
): void {
  // Defensive — copy into a fresh Uint8Array to avoid Blob SharedArrayBuffer
  // transfer issues in some browsers.
  const safeBytes = new Uint8Array(pdfBytes);
  const blob = new Blob([safeBytes], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.style.display = "none";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Free the blob URL after a small delay to allow the browser to
  // start the download (per common pattern in V8/Blink).
  setTimeout(() => URL.revokeObjectURL(url), 1_000);
}

// ── Helper: format PDF size for toast display ──────────────────
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export function formatClosingPdfExportSize(sizeBytes: number): string {
  if (sizeBytes < 1024) return `${sizeBytes} B`;
  if (sizeBytes < 1024 * 1024) return `${(sizeBytes / 1024).toFixed(1)} KB`;
  return `${(sizeBytes / 1024 / 1024).toFixed(2)} MB`;
}
