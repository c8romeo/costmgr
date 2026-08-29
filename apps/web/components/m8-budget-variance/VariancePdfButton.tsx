/**
 * apps/web/components/m8-budget-variance/VariancePdfButton.tsx — Story 8.3 (8-2 wire activation)
 *
 * PDF 내보내기 button — §9 #20 (PRD §F8.2 + 8-3 wire activation).
 *
 * 8-3 atomic wire (resolved from 8-2 honestly DEFER #5):
 *  - Calls GET /api/v1/budget/variance/{period_key}/pdf
 *  - Returns real PDF bytes (8-3 wire activation; previously empty placeholder).
 *  - Button is enabled (no longer "8-3 follow-up" disabled).
 *  - 425 BUDGET_VARIANCE_PDF_NOT_READY surfaces in inline error.
 */

"use client";

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

interface VariancePdfButtonProps {
  accessToken: string | undefined;
  periodKey: string;
  envelope?: unknown;
}

export function VariancePdfButton({
  accessToken,
  periodKey,
  envelope: _envelope,
}: VariancePdfButtonProps): React.ReactElement {
  const t = useTranslations("budget_variance");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = useCallback(async (): Promise<void> => {
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
        setError(t("pdf_failed") + ` (HTTP ${res.status})`);
        return;
      }
      const data = (await res.json()) as {
        pdf_bytes_b64: string;
        filename?: string;
      };
      // Decode base64 → Blob → download.
      const bytes = Uint8Array.from(
        atob(data.pdf_bytes_b64),
        (c) => c.charCodeAt(0),
      );
      const blob = new Blob([bytes], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download =
        data.filename ?? `budget_variance_${periodKey}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSubmitting(false);
    }
  }, [accessToken, periodKey, t]);

  return (
    <div className="mt-3">
      <button
        type="button"
        disabled={submitting}
        title={t("pdf_button_tooltip_ready")}
        onClick={() => void handleDownload()}
        className="rounded bg-blue-600 px-3 py-1 text-white disabled:bg-gray-400"
        data-testid="variance-pdf-button"
      >
        {submitting ? t("pdf_exporting") : t("pdf_button")}
      </button>
      <p className="mt-1 text-xs text-gray-500">{t("pdf_active_note")}</p>
      {error ? (
        <p className="mt-2 text-sm text-red-600" data-testid="variance-pdf-error">
          {error}
        </p>
      ) : null}
    </div>
  );
}