"use client";

/**
 * apps/web/components/m5-reports/Report21Panel.tsx — Story 9.4
 *
 * Main Client Component for the Report #21 (Cost Object Breakdown) UI.
 * PRD §9 #21 + §7.3 (법인세법 시행규칙 제76조 2기준) verbatim.
 *
 * Per AC #1 + AC #2 (Story 9.4):
 *  - Period input form (period_key validation)
 *  - Cost Object Breakdown table (4 columns)
 *  - Unused Capacity breakdown section
 *  - V7 ABC 무결성 verdict (1원 단위 검증)
 *  - PDF export via A30 SHARED factory (POST /api/v1/reports/21/pdf)
 *
 * Capability gate (COST_CALCULATION OR ABC_CALCULATION) enforced server-side.
 */

import { useTranslations } from "next-intl";
import { useCallback, useState } from "react";

import { CostObjectBreakdownTable } from "./CostObjectBreakdownTable";
import { PdfExportButton } from "./PdfExportButton";
import { UnusedCapacityAccordion } from "./UnusedCapacityAccordion";
import {
  type Report21ErrorCode,
  type Report21ResponseEnvelope,
  fetchReport21TS,
} from "@/lib/report21";

interface Report21PanelProps {
  accessToken: string | undefined;
  initialReport: Report21ResponseEnvelope | null;
  initialError: Report21ErrorCode | null;
}

export function Report21Panel({
  accessToken,
  initialReport,
  initialError,
}: Report21PanelProps): React.ReactElement {
  const t = useTranslations("report21");
  const tCommon = useTranslations("pdf_common");

  const [periodKey, setPeriodKey] = useState<string>("");
  const [report, setReport] = useState<Report21ResponseEnvelope | null>(
    initialReport,
  );
  const [error, setError] = useState<Report21ErrorCode | "NETWORK_ERROR" | null>(
    initialError,
  );
  const [loading, setLoading] = useState<boolean>(false);

  const handleFetch = useCallback(async () => {
    if (!periodKey) {
      setError("REPORT21_PERIOD_NOT_COMMITTED");
      return;
    }
    setLoading(true);
    setError(null);
    const result = await fetchReport21TS(periodKey, accessToken);
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
    <div data-testid="report21-panel" style={{ padding: 24 }}>
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
        <p data-testid="report21-empty-result">{t("empty_result")}</p>
      )}

      {report && (
        <>
          <div data-testid="report21-meta">
            <span>{tCommon("report_code_label")}: {report.report_code}</span>
            <span data-testid="report21-hash">
              {tCommon("title_prefix").replace("[", "").replace("]", "").trim()} {t("generation_hash_label")}: {report.generation_hash}
            </span>
            <span data-testid="report21-v7-verdict">
              {report.v7_verdict_is_balanced
                ? t("v7_verdict_balanced")
                : t("v7_verdict_unbalanced")}
            </span>
          </div>

          <section data-testid="report21-cost-object-section">
            <h2>{t("cost_object_breakdown_title")}</h2>
            <CostObjectBreakdownTable rows={report.cost_object_breakdown} />
          </section>

          <section data-testid="report21-unused-section">
            <h2>{t("unused_capacity_title")}</h2>
            <UnusedCapacityAccordion rows={report.unused_capacity_breakdown} />
          </section>

          <section data-testid="report21-pdf-section">
            <PdfExportButton
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
