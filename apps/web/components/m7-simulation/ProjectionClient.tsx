"use client";

/**
 * apps/web/components/m7-simulation/ProjectionClient.tsx — Story 7.2 (Epic 7)
 *
 * Main client orchestrator for the M7 Next-Month Projection UI.
 *
 * Per AC #4:
 *  - Fetches baseline via GET /api/v1/simulation/projection/baseline.
 *  - 4 form inputs gate [예측 실행] button (disabled until all valid).
 *  - 4 result cards (projected_revenue / projected_fixed_cost /
 *    pre_tax_income / after_tax_income).
 *  - 1 ComposedChart (baseline vs projected).
 *  - 1 PDF download button.
 *  - Latency tracked for NFR9 P95 ≤ 1초.
 *
 * CR 11-4 D-001: this client is actually mounted by page.tsx.
 * CR 11-4 D-005: invalid baseline / input → reject (NOT silent fall-through).
 */

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

import {
  type NextMonthProjectionSerialized,
  type ProjectionBaselineSerialized,
  type ProjectionInputsSerialized,
  ERROR_CODE_PROJECTION_BASELINE_NOT_FOUND,
  ERROR_CODE_PROJECTION_INPUTS_INVALID,
  ERROR_CODE_INVALID_PROJECTION_MONTH,
  isProjectionMonthAfterPeriodKeyTS,
  isValidRealPeriodKeyTS,
} from "@/lib/m7-simulation-projection";
import { type ProjectionInputsSchema } from "@/lib/m7-simulation-projection-schema";
import {
  ProjectionForm,
} from "./ProjectionForm";
import {
  ProjectionResultCard,
} from "./ProjectionResultCard";
import {
  ProjectionComparisonChart,
} from "./ProjectionComparisonChart";
import {
  ProjectionPdfButton,
} from "./ProjectionPdfButton";

interface ProjectionClientProps {
  accessToken: string | undefined;
  initialPeriodKey: string;
  initialProjectionMonth?: string;
}

export function ProjectionClient({
  accessToken,
  initialPeriodKey,
  initialProjectionMonth,
}: ProjectionClientProps): React.ReactElement {
  const t = useTranslations("projection_simulation");

  const [periodKey] = useState<string>(initialPeriodKey);
  const [projectionMonth] = useState<string>(
    initialProjectionMonth ?? defaultNextMonth(initialPeriodKey),
  );
  const [baseline, setBaseline] = useState<ProjectionBaselineSerialized | null>(
    null,
  );
  const [result, setResult] = useState<NextMonthProjectionSerialized | null>(
    null,
  );
  const [lastSubmittedInputs, setLastSubmittedInputs] =
    useState<ProjectionInputsSerialized | null>(null);
  const [isComputing, setIsComputing] = useState<boolean>(false);
  const [latencyMs, setLatencyMs] = useState<number>(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [formValid, setFormValid] = useState<boolean>(false);

  // ── Fetch baseline on mount ────────────────────────────────
  useEffect(() => {
    if (!isValidRealPeriodKeyTS(periodKey)) {
      setLoadError(t("invalid_period_key_message"));
      return;
    }
    if (!isValidRealPeriodKeyTS(projectionMonth)) {
      setLoadError(t("invalid_projection_month_message"));
      return;
    }
    if (!isProjectionMonthAfterPeriodKeyTS(periodKey, projectionMonth)) {
      setLoadError(t("projection_month_must_be_after_period_key"));
      return;
    }
    const fetchBaseline = async (): Promise<void> => {
      try {
        const url = `/api/v1/simulation/projection/baseline?period_key=${encodeURIComponent(
          periodKey,
        )}&projection_month=${encodeURIComponent(projectionMonth)}`;
        const res = await fetch(url, {
          method: "GET",
          headers: {
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          cache: "no-store",
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as {
            code?: string;
            message_ko?: string;
          };
          if (body.code === ERROR_CODE_PROJECTION_BASELINE_NOT_FOUND) {
            setLoadError(t("baseline_not_found_message"));
          } else if (body.code === ERROR_CODE_INVALID_PROJECTION_MONTH) {
            setLoadError(t("invalid_projection_month_message"));
          } else {
            setLoadError(body.message_ko ?? `HTTP ${res.status}`);
          }
          return;
        }
        const data = (await res.json()) as { baseline: ProjectionBaselineSerialized };
        setBaseline(data.baseline);
        setLoadError(null);
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : String(e));
      }
    };
    void fetchBaseline();
  }, [periodKey, projectionMonth, accessToken, t]);

  // ── Submit (예측 실행) ─────────────────────────────────────
  const handleSubmit = useCallback(
    async (values: ProjectionInputsSchema): Promise<void> => {
      if (!baseline) {
        setLoadError(t("baseline_not_found_message"));
        return;
      }
      setIsComputing(true);
      const started = performance.now();
      const inputs: ProjectionInputsSerialized = {
        loan_amount: String(values.loan_amount),
        interest_rate: String(values.interest_rate),
        cost_inflation_rate: String(values.cost_inflation_rate),
        corporate_tax_rate: String(values.corporate_tax_rate),
      };
      try {
        const res = await fetch("/api/v1/simulation/projection/compute", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          body: JSON.stringify({
            period_key: periodKey,
            projection_month: projectionMonth,
            projection_inputs: inputs,
          }),
          cache: "no-store",
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as {
            code?: string;
            message_ko?: string;
          };
          if (body.code === ERROR_CODE_PROJECTION_INPUTS_INVALID) {
            setLoadError(t("invalid_inputs_message"));
          } else if (body.code === ERROR_CODE_PROJECTION_BASELINE_NOT_FOUND) {
            setLoadError(t("baseline_not_found_message"));
          } else if (body.code === ERROR_CODE_INVALID_PROJECTION_MONTH) {
            setLoadError(t("invalid_projection_month_message"));
          } else {
            setLoadError(body.message_ko ?? `HTTP ${res.status}`);
          }
          return;
        }
        const data = (await res.json()) as {
          result: NextMonthProjectionSerialized;
          latency_ms: number;
        };
        setResult(data.result);
        setLatencyMs(data.latency_ms);
        setLastSubmittedInputs(inputs);
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : String(e));
      } finally {
        const elapsed = Math.round(performance.now() - started);
        setLatencyMs(elapsed);
        setIsComputing(false);
      }
    },
    [baseline, periodKey, projectionMonth, accessToken, t],
  );

  const handleValidityChange = useCallback((isValid: boolean) => {
    setFormValid(isValid);
  }, []);

  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">{t("page_title")}</h1>
      <p className="mt-1 text-sm text-gray-600">{t("page_subtitle")}</p>

      <div className="mt-4 flex flex-wrap items-center gap-4 text-sm">
        <span className="text-gray-500">
          {t("period_key_label")}:{" "}
          <span className="font-mono">{periodKey}</span>
        </span>
        <span className="text-gray-500">
          {t("projection_month_label")}:{" "}
          <span className="font-mono">{projectionMonth}</span>
        </span>
        <span className="text-gray-500">
          {t("latency_label")}: <span className="font-mono">{latencyMs} ms</span>
        </span>
        {isComputing ? (
          <span className="text-blue-600">{t("computing_message")}</span>
        ) : null}
      </div>

      {loadError ? (
        <p
          className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-600"
          role="alert"
          data-testid="projection-load-error"
        >
          {loadError}
        </p>
      ) : null}

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ProjectionForm
          onSubmit={(values) =>
            void handleSubmit(values as unknown as ProjectionInputsSchema)
          }
          onValidityChange={handleValidityChange}
          isSubmitting={isComputing}
        />

        {baseline && result ? (
          <section
            className="rounded border p-4"
            data-testid="projection-results-section"
          >
            <h2 className="text-lg font-medium">{t("results_title")}</h2>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
              <ProjectionResultCard
                title={t("card_projected_revenue")}
                value={result.projected_revenue}
                baseline_value={baseline.monthly_revenue}
                higherIsBetter={true}
                testId="projection-result-card-revenue"
              />
              <ProjectionResultCard
                title={t("card_projected_fixed_cost")}
                value={result.projected_fixed_cost}
                baseline_value={baseline.monthly_fixed_cost}
                higherIsBetter={false}
                testId="projection-result-card-fixed-cost"
              />
              <ProjectionResultCard
                title={t("card_pre_tax_income")}
                value={result.pre_tax_income}
                baseline_value={baseline.monthly_revenue}
                higherIsBetter={true}
                testId="projection-result-card-pre-tax"
              />
              <ProjectionResultCard
                title={t("card_after_tax_income")}
                value={result.after_tax_income}
                baseline_value={baseline.monthly_revenue}
                higherIsBetter={true}
                testId="projection-result-card-after-tax"
              />
            </div>
          </section>
        ) : null}
      </div>

      {baseline && result ? (
        <section className="mt-6 rounded border p-4">
          <h2 className="text-lg font-medium">{t("comparison_chart_title")}</h2>
          <ProjectionComparisonChart
            baseline={result}
            sourceBaseline={{
              monthly_revenue: baseline.monthly_revenue,
              monthly_variable_cost: baseline.monthly_variable_cost,
              monthly_fixed_cost: baseline.monthly_fixed_cost,
              after_tax_income: baseline.monthly_revenue,
            }}
          />
        </section>
      ) : null}

      {baseline && result && lastSubmittedInputs ? (
        <section className="mt-6 rounded border p-4">
          <h2 className="text-lg font-medium">{t("pdf_section_title")}</h2>
          <ProjectionPdfButton
            periodKey={periodKey}
            projectionMonth={projectionMonth}
            inputs={lastSubmittedInputs}
            accessToken={accessToken}
          />
        </section>
      ) : null}

      {!formValid && baseline ? (
        <p className="mt-2 text-xs text-gray-500">
          {t("form_submit_button_tooltip")}
        </p>
      ) : null}
    </main>
  );
}

/**
 * Compute default next-month string for a given period key (YYYY-MM).
 * e.g. "2026-08" → "2026-09". Used as fallback when user does not
 * specify projection_month in URL.
 */
function defaultNextMonth(periodKey: string): string {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(periodKey)) return "2026-01";
  const [yearStr, monthStr] = periodKey.split("-");
  let year = parseInt(yearStr, 10);
  let month = parseInt(monthStr, 10);
  month += 1;
  if (month > 12) {
    month = 1;
    year += 1;
  }
  return `${year}-${String(month).padStart(2, "0")}`;
}
