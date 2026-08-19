"use client";

/**
 * apps/web/components/m5-reports/Report15Panel.tsx — Story 11.6
 *
 * Main Client Component for the Report #15 (활동원가 내역서) UI.
 * PRD §9 #15 + §7.1 (활동·동인 매트릭스) verbatim.
 *
 * Per AC #1 + AC #2 (Story 11.6):
 *  - Period input form (period_key validation)
 *  - Activity Cost Breakdown table (7 columns)
 *  - V7 ABC 무결성 verdict (1원 단위 검증)
 *  - PDF export via A30 SHARED factory (POST /api/v1/reports/15/pdf)
 *
 * Capability gate (COST_CALCULATION OR ABC_CALCULATION) enforced server-side.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { ActivityCostBreakdownTable } from "./ActivityCostBreakdownTable";
import { ActivityCostPdfExportButton } from "./ActivityCostPdfExportButton";
import {
  type Report15ErrorCode,
  type Report15ResponseEnvelope,
  fetchReport15TS,
} from "@/lib/report15";

interface Report15PanelProps {
  accessToken: string | undefined;
  initialReport: Report15ResponseEnvelope | null;
  initialError: Report15ErrorCode | null;
}

export function Report15Panel({
  accessToken,
  initialReport,
  initialError,
}: Report15PanelProps): React.ReactElement {
  const t = useTranslations("report15");
  const tCommon = useTranslations("pdf_common");

  const [periodKey, setPeriodKey] = useState<string>("");
  const [report, setReport] = useState<Report15ResponseEnvelope | null>(
    initialReport,
  );
  const [error, setError] = useState<Report15ErrorCode | "NETWORK_ERROR" | null>(
    initialError,
  );
  const [loading, setLoading] = useState<boolean>(false);

  const handleFetch = useCallback(async () => {
    if (!periodKey) {
      setError("REPORT15_PERIOD_NOT_COMMITTED");
      return;
    }
    setLoading(true);
    setError(null);
    const result = await fetchReport15TS(periodKey, accessToken);
    if (result.kind === "ok") {
      setReport(result.data);
      setError(null);
    } else {
      setReport(null);
      setError(result.code);
    }
    setLoading(false);
  }, [periodKey, accessToken]);

  return (
    <div data-testid="report15-panel" style={{ padding: 24 }}>
      <h1>{t("page_title")}</h1>
      <p>{t("page_subtitle")}</p>

      <div style={{ marginTop: 16 }}>
        <label htmlFor="period-key-input">{t("form_label_period_key")}</label>
        <input
          id="period-key-input"
          type="text"
          value={periodKey}
          onChange={(e) => setPeriodKey(e.target.value)}
          placeholder={t("form_label_period_key_placeholder")}
          disabled={loading}
        />
        <button
          onClick={handleFetch}
          disabled={loading || !periodKey}
          aria-label={t("form_submit_label")}
        >
          {loading ? t("submitting") : t("form_submit_label")}
        </button>
      </div>

      {error && (
        <div role="alert" data-error-code={error}>
          {tCommon("download_error")}: {error}
        </div>
      )}

      {!report && !error && (
        <p data-testid="report15-empty-result">{t("empty_result")}</p>
      )}

      {report && (
        <>
          <div data-testid="report15-meta">
            <span>{tCommon("report_code_label")}: {report.report_code}</span>
            <span data-testid="report15-hash">
              {tCommon("title_prefix").replace("[", "").replace("]", "").trim()} {t("generation_hash_label")}: {report.generation_hash}
            </span>
            <span data-testid="report15-v7-verdict">
              {report.v7_verdict_is_balanced
                ? t("v7_verdict_balanced")
                : t("v7_verdict_unbalanced")}
            </span>
            <span data-testid="report15-activity-count">
              {t("activity_count_label")}: {report.activity_count}
            </span>
            <span data-testid="report15-driver-count">
              {t("driver_count_label")}: {report.total_driver_count}
            </span>
          </div>

          <section data-testid="report15-activity-section">
            <h2>{t("activity_breakdown_title")}</h2>
            <ActivityCostBreakdownTable rows={report.activity_breakdown} />
          </section>

          <section data-testid="report15-pdf-section">
            <ActivityCostPdfExportButton
              periodKey={periodKey}
              accessToken={accessToken}
              disabled={loading}
            />
          </section>
        </>
      )}
    </div>
  );
}