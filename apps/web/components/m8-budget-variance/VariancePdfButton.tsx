/**
 * apps/web/components/m8-budget-variance/VariancePdfButton.tsx — Story 8.2
 *
 * PDF 내보내기 button — 8-3 honestly DEFER placeholder (PRD §F8.2).
 *
 * 8-2 atomic wire:
 *  - Calls GET /api/v1/budget/variance/{period_key}/pdf
 *  - Returns envelope shape with empty pdf_bytes_b64 (8-3 follow-up real PDF)
 *  - Button is disabled with tooltip "8-3 follow-up sprint"
 *  - 8-3 follow-up: delegate to packages.services.m6_reports.pdf_helpers
 *    (Epic 6 M5 PDF generator reuse, READ-ONLY pattern)
 */

"use client";

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

interface VariancePdfButtonProps {
  accessToken: string | undefined;
  periodKey: string;
  envelope: Record<string, unknown> | null;
}

export function VariancePdfButton({
  accessToken,
  periodKey,
  envelope,
}: VariancePdfButtonProps): React.ReactElement {
  const t = useTranslations("budget_variance");
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [envelopeResult, setEnvelopeResult] = useState<unknown>(envelope);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = useCallback(async (): Promise<void> => {
    setSubmitting(true);
    setError(null);

    try {
      // 8-2 atomic wire: hit the endpoint; the response is an envelope
      // with empty pdf_bytes_b64 (8-3 follow-up will produce real PDF bytes).
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
      if (!res.ok) {
        setError(t("pdf_failed") + ` (HTTP ${res.status})`);
        return;
      }
      const data = (await res.json()) as { envelope: unknown };
      setEnvelopeResult(data.envelope);
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
        title={t("pdf_disabled_message")}
        onClick={() => void handleDownload()}
        className="rounded bg-blue-600 px-3 py-1 text-white disabled:bg-gray-400"
        data-testid="variance-pdf-button"
      >
        {submitting ? t("pdf_exporting") : t("pdf_button")}
      </button>
      <p className="mt-1 text-xs text-gray-500">{t("pdf_envelope_only")}</p>
      {error ? (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      ) : null}
      {envelopeResult ? (
        <details className="mt-2 text-xs">
          <summary className="cursor-pointer text-gray-600">
            envelope SSOT (Epic 6 M5 reuse)
          </summary>
          <pre className="mt-1 overflow-auto rounded bg-gray-100 p-2 text-xs">
            {JSON.stringify(envelopeResult, null, 2)}
          </pre>
        </details>
      ) : null}
    </div>
  );
}
