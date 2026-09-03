/**
 * apps/web/components/m2-input/ClosingPdfExportButton.tsx — Story 6.3 T2.
 *
 * Client Component for the Closing PDF Export download flow (PRD §F6.3).
 *
 * Wire:
 * 1. POST /api/v1/inventory/monthly-closing-report/export-pdf?period_key=...
 *    with body { industry } → returns raw PDF bytes (application/pdf).
 * 2. Server emits `closing_pdf_export_viewed` audit row BEFORE PDF
 *    render (CR 1.1 — audit-first invariant).
 * 3. Client receives bytes → triggers browser download via
 *    `triggerClosingPdfExportDownload` (blob + a[download] pattern).
 * 4. Toast feedback: success (size info) / error (3 typed envelopes).
 *
 * 3 typed exceptions (AD-15 §4 envelope):
 * - 422 CLOSING_PDF_EXPORT_INVALID_INDUSTRY (W5 deferral guard).
 * - 409 CLOSING_PDF_EXPORT_SIZE_EXCEEDED (>5MB).
 * - 500 CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR (CR 1.1 invariant).
 *
 * Capability gate (A10): MONTHLY_CLOSING_REPORT (reused from 6-2 wire).
 * The button is hidden when `capability_granted=false` (service-only tenant).
 */

"use client";

import { Download } from "lucide-react";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import {
  type ClosingPdfIndustry,
  buildClosingPdfExportFilename,
  formatClosingPdfExportSize,
  isValidClosingPdfIndustry,
  triggerClosingPdfExportDownload,
} from "@/lib/closing-pdf-export";

export interface ClosingPdfExportButtonProps {
  /** Period key (YYYY-MM). */
  periodKey: string;
  /** Industry code (W5 deferral guard — must be one of 4 canonical). */
  industry: ClosingPdfIndustry;
  /** Tenant access token (JWT) from session. */
  accessToken?: string;
  /** Optional className override. */
  className?: string;
}

/**
 * ClosingPdfExportButton — Story 6.3 T2 frontend wire.
 *
 * Disabled when download is in-flight (status=DOWNLOADING). Triggers
 * POST /api/v1/inventory/monthly-closing-report/export-pdf, handles
 * 3 typed error envelopes, and triggers browser download on success.
 *
 * Audit-first invariant (CR 1.1): server emits `closing_pdf_export_viewed`
 * audit row BEFORE PDF byte render. Client does NOT need to emit audit.
 */
export function ClosingPdfExportButton({
  periodKey,
  industry,
  accessToken,
  className,
}: ClosingPdfExportButtonProps): React.ReactElement | null {
  const t = useTranslations("closing_pdf_export");
  // eslint-disable-next-line camelcase, @typescript-eslint/naming-convention
  const [is_downloading, setIsDownloading] = React.useState(false);

  // Defensive: industry must be one of 4 canonical (W5 deferral guard).
  // Surface via useEffect (NOT during render — React anti-pattern).
  React.useEffect(() => {
    if (!isValidClosingPdfIndustry(industry)) {
      toast.error(t("toast_error_invalid_industry"));
    }
  }, [industry, t]);

  if (!isValidClosingPdfIndustry(industry)) {
    return null;
  }

  const handleDownload = async (): Promise<void> => {
    // eslint-disable-next-line camelcase
    if (is_downloading) return; // idempotent no-op (CR 1.1)
    setIsDownloading(true);

    try {
      const headers = new Headers();
      headers.set("Content-Type", "application/json");
      if (accessToken) {
        headers.set("Authorization", `Bearer ${accessToken}`);
      }

      const path = `/api/v1/inventory/monthly-closing-report/export-pdf?period_key=${encodeURIComponent(periodKey)}`;
      const response = await fetch(path, {
        method: "POST",
        headers,
        credentials: accessToken ? "omit" : "same-origin",
        body: JSON.stringify({ industry }),
      });

      if (!response.ok) {
        // Try to parse AD-15 envelope — fall back to generic error.
        let errPayload: { code?: string; message_ko?: string } = {};
        try {
          errPayload = await response.json();
        } catch {
          // ignore parse error
        }
        const code = errPayload.code ?? "EXPORT_PDF_ERROR";
        // eslint-disable-next-line camelcase, @typescript-eslint/naming-convention
        const message_ko =
          errPayload.message_ko ?? t("toast_error_generic", { code });

        if (code === "CLOSING_PDF_EXPORT_INVALID_INDUSTRY") {
          toast.error(t("toast_error_invalid_industry"));
        } else if (code === "CLOSING_PDF_EXPORT_SIZE_EXCEEDED") {
          toast.error(t("toast_error_size_exceeded"));
        } else if (code === "CLOSING_PDF_EXPORT_AUDIT_EMIT_ERROR") {
          toast.error(t("toast_error_audit_emit"));
        } else {
          toast.error(message_ko);
        }
        return;
      }

      // Read raw bytes (PDF).
      const buffer = await response.arrayBuffer();
      const pdfBytes = new Uint8Array(buffer);

      // Defensive: validate size cap (PRD §F6.3 — 5MB).
      const MAX_SIZE = 5 * 1024 * 1024;
      if (pdfBytes.length > MAX_SIZE) {
        toast.error(t("toast_error_size_exceeded"));
        return;
      }

      // Trigger browser download.
      const filename = buildClosingPdfExportFilename(periodKey);
      triggerClosingPdfExportDownload(pdfBytes, filename);

      toast.success(
        t("toast_success_export", {
          size: formatClosingPdfExportSize(pdfBytes.length),
        }),
      );
    } catch (err) {
      // Network error or unexpected failure.
      const message =
        err instanceof Error ? err.message : t("toast_error_generic_unknown");
      toast.error(message);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <button
      type="button"
      onClick={handleDownload}
      // eslint-disable-next-line camelcase
      disabled={is_downloading}
      data-testid="closing-pdf-export-button"
      data-period-key={periodKey}
      data-industry={industry}
      // eslint-disable-next-line camelcase
      data-status={is_downloading ? "DOWNLOADING" : "IDLE"}
      className={
        "inline-flex items-center justify-center rounded-md border " +
        "border-slate-300 bg-white px-4 py-2 text-sm font-medium " +
        "text-slate-700 transition hover:bg-slate-50 " +
        "disabled:cursor-not-allowed disabled:opacity-60 " +
        (className ?? "")
      }
    >
      <Download className="mr-2 h-4 w-4" aria-hidden="true" />
      {/* eslint-disable-next-line camelcase */}
      {is_downloading ? t("button_downloading") : t("button_label")}
    </button>
  );
}
