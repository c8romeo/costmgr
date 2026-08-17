"use client";

/**
 * apps/web/components/m5-reports/PdfExportButton.tsx — Story 9.4
 *
 * Report #21 PDF export button. POST /api/v1/reports/21/pdf → Base64-decoded
 * PDF blob → browser download trigger.
 *
 * A30 SHARED PDF generator factory (Discriminated union
 * report_id: Literal[15..21]).
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import {
  base64PdfToBlob,
  downloadReport21PdfTS,
  triggerPdfDownload,
  type Report21ErrorCode,
} from "@/lib/report21-pdf";

interface PdfExportButtonProps {
  periodKey: string;
  accessToken: string | undefined;
  disabled?: boolean;
}

export function PdfExportButton({
  periodKey,
  accessToken,
  disabled,
}: PdfExportButtonProps): React.ReactElement {
  const t = useTranslations("pdf_common");

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<Report21ErrorCode | "NETWORK_ERROR" | null>(
    null,
  );

  const handleDownload = useCallback(async () => {
    if (!periodKey) {
      setError("REPORT21_PERIOD_NOT_COMMITTED");
      return;
    }
    setLoading(true);
    setError(null);
    const result = await downloadReport21PdfTS(periodKey, accessToken);
    setLoading(false);
    if (result.kind === "ok") {
      const blob = base64PdfToBlob(result.data.pdf_base64);
      triggerPdfDownload(blob, periodKey);
    } else {
      setError(result.code);
    }
  }, [periodKey, accessToken]);

  return (
    <div data-testid="report21-pdf-button-container">
      <button
        onClick={handleDownload}
        disabled={loading || disabled || !periodKey}
        data-testid="report21-pdf-button"
        aria-busy={loading}
      >
        {loading ? t("downloading_label") : t("download_label")}
      </button>
      {error && (
        <div role="alert" data-error-code={error}>
          {t("download_error")}: {error}
        </div>
      )}
    </div>
  );
}
