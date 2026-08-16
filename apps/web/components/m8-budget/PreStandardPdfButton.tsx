"use client";

/**
 * apps/web/components/m8-budget/PreStandardPdfButton.tsx — Story 8.3
 *
 * §9 #20 PDF download button — wires to /variance/{period_key}/pdf endpoint
 * (8-3 wire activation, 8-2 placeholder 해소).
 *
 * 8-3 wire:
 *  - Calls GET /api/v1/budget/variance/{period_key}/pdf (8-2 pdf endpoint
 *    now wired to real PDF generation via pre-standard snapshot).
 *  - 425 BUDGET_VARIANCE_PDF_NOT_READY if pre-standard snapshot not yet inserted.
 *  - Button is disabled with tooltip "예측을 먼저 실행하세요" when snapshotReady=false.
 *  - Button is enabled with tooltip "§9 #20 예산-실적 차이 명세서 PDF 다운로드" when ready.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

interface PreStandardPdfButtonProps {
  accessToken: string | undefined;
  periodKey: string;
  snapshotReady: boolean;
}

export function PreStandardPdfButton({
  accessToken,
  periodKey,
  snapshotReady,
}: PreStandardPdfButtonProps): React.ReactElement {
  const t = useTranslations("budget_pre_standard");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = useCallback(async (): Promise<void> => {
    if (!snapshotReady) return;
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(
        `/api/v1/budget/variance/${encodeURIComponent(periodKey)}/pdf`,
        {
          method: "GET",
          headers: {
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          cache: "no-store",
        },
      );
      if (res.status === 425) {
        setError(t("pdf_not_ready"));
        return;
      }
      if (!res.ok) {
        setError(`HTTP ${res.status}`);
        return;
      }
      const data = (await res.json()) as { pdf_bytes_b64: string; filename?: string };
      // Decode base64 → Blob → download.
      const bytes = Uint8Array.from(atob(data.pdf_bytes_b64), (c) => c.charCodeAt(0));
      const blob = new Blob([bytes], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `budget_variance_${periodKey}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }, [accessToken, periodKey, snapshotReady, t]);

  return (
    <div className="mt-3">
      <button
        type="button"
        disabled={submitting || !snapshotReady}
        title={snapshotReady ? t("pdf_button_tooltip_ready") : t("pdf_button_tooltip_disabled")}
        onClick={() => void handleDownload()}
        className="rounded bg-blue-600 px-3 py-1 text-white disabled:bg-gray-400"
        data-testid="pre-standard-pdf-button"
      >
        {submitting ? t("pdf_exporting") : t("pdf_button_label")}
      </button>
      {error ? (
        <p className="mt-2 text-sm text-red-600" data-testid="pdf-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}
