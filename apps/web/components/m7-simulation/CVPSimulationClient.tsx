"use client";

/**
 * apps/web/components/m7-simulation/CVPSimulationClient.tsx — Story 7.1
 *
 * Client Component for the M7 CVP/BEP simulation UI.
 *
 * Per AC #4 (Story 7.1):
 *  - Fetches baseline via `GET /api/v1/simulation/cvp/baseline?period_key=YYYY-MM`.
 *  - 4 sliders trigger debounced simulation (POST /api/v1/simulation/cvp/compute).
 *  - 4 result cards (BEP 수량 / BEP 매출 / 목표 이익 / 공헌이익률) show baseline vs simulated.
 *  - 1 bar chart shows 4 variables (단가/단위변동비/고정비/조업도) baseline vs simulated.
 *  - Latency tracked for NFR9 P95 ≤ 1초.
 *
 * CR 11-4 D-005: invalid delta → reject (NOT silent fall-through).
 */

import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  type CVPBaselineSerialized,
  type CVPDeltaSerialized,
  type CVPResultSerialized,
  ERROR_CODE_CVP_BASELINE_NOT_FOUND,
  ERROR_CODE_CVP_INVALID_DELTA,
  FIXED_COST_DELTA_PCT_BOUNDS,
  OPERATING_RATE_DELTA_PCT_BOUNDS,
  PRICE_DELTA_PCT_BOUNDS,
  applyDeltaTS,
  isValidRealPeriodKeyTS,
  simulateCvpTS,
} from "@/lib/m7-simulation-cvp";

interface CVPSimulationClientProps {
  accessToken: string | undefined;
  initialPeriodKey: string;
}

export function CVPSimulationClient({
  accessToken,
  initialPeriodKey,
}: CVPSimulationClientProps): React.ReactElement {
  const t = useTranslations("cvp_simulation");

  const [periodKey] = useState<string>(initialPeriodKey);
  const [baseline, setBaseline] = useState<CVPBaselineSerialized | null>(null);
  const [delta, setDelta] = useState<CVPDeltaSerialized>({
    unit_price_delta_pct: "0",
    unit_variable_cost_delta_pct: "0",
    fixed_cost_delta_pct: "0",
    operating_rate_delta_pct: "0",
  });
  const [result, setResult] = useState<CVPResultSerialized | null>(null);
  const [isComputing, setIsComputing] = useState<boolean>(false);
  const [latencyMs, setLatencyMs] = useState<number>(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ── Fetch baseline on mount ────────────────────────────────
  useEffect(() => {
    if (!isValidRealPeriodKeyTS(periodKey)) {
      setLoadError(t("invalid_period_key_message"));
      return;
    }
    const fetchBaseline = async (): Promise<void> => {
      try {
        const res = await fetch(
          `/api/v1/simulation/cvp/baseline?period_key=${encodeURIComponent(periodKey)}`,
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
          const body = (await res.json().catch(() => ({}))) as {
            code?: string;
            message_ko?: string;
          };
          if (body.code === ERROR_CODE_CVP_BASELINE_NOT_FOUND) {
            setLoadError(t("baseline_not_found_message"));
          } else {
            setLoadError(body.message_ko ?? `HTTP ${res.status}`);
          }
          return;
        }
        const data = (await res.json()) as { baseline: CVPBaselineSerialized };
        setBaseline(data.baseline);
        setLoadError(null);
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : String(e));
      }
    };
    void fetchBaseline();
  }, [periodKey, accessToken, t]);

  // ── Debounced simulation (150ms per AC #4) ───────────────────
  const runSimulation = useCallback(
    async (currentDelta: CVPDeltaSerialized): Promise<void> => {
      if (!baseline) return;
      setIsComputing(true);
      const started = performance.now();
      try {
        const res = await fetch("/api/v1/simulation/cvp/compute", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: accessToken ? `Bearer ${accessToken}` : "",
            "X-Trace-Id": crypto.randomUUID(),
          },
          body: JSON.stringify({ period_key: periodKey, delta: currentDelta }),
          cache: "no-store",
        });
        if (!res.ok) {
          const body = (await res.json().catch(() => ({}))) as {
            code?: string;
            message_ko?: string;
          };
          if (body.code === ERROR_CODE_CVP_INVALID_DELTA) {
            setLoadError(t("invalid_delta_message"));
          } else {
            setLoadError(body.message_ko ?? `HTTP ${res.status}`);
          }
          return;
        }
        const data = (await res.json()) as { result: CVPResultSerialized; latency_ms: number };
        setResult(data.result);
        setLatencyMs(data.latency_ms);
      } catch (e) {
        setLoadError(e instanceof Error ? e.message : String(e));
      } finally {
        const elapsed = Math.round(performance.now() - started);
        setLatencyMs(elapsed);
        setIsComputing(false);
      }
    },
    [baseline, periodKey, accessToken, t],
  );

  useEffect(() => {
    if (!baseline) return;
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      void runSimulation(delta);
    }, 150);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [delta, baseline, runSimulation]);

  // ── Slider change handlers ─────────────────────────────────
  const handleSliderChange = useCallback(
    (field: keyof CVPDeltaSerialized, valuePct: number): void => {
      setDelta((prev) => ({ ...prev, [field]: valuePct.toString() }));
    },
    [],
  );

  const handleReset = useCallback((): void => {
    setDelta({
      unit_price_delta_pct: "0",
      unit_variable_cost_delta_pct: "0",
      fixed_cost_delta_pct: "0",
      operating_rate_delta_pct: "0",
    });
  }, []);

  // ── Local fallback simulation (TS mirror) for offline UX ────
  const localResult = useMemo<CVPResultSerialized | null>(() => {
    if (!baseline) return null;
    try {
      return simulateCvpTS(baseline, delta);
    } catch {
      return null;
    }
  }, [baseline, delta]);

  const displayResult = result ?? localResult;

  return (
    <main className="p-6">
      <h1 className="text-2xl font-semibold">{t("page_title")}</h1>
      <p className="mt-1 text-sm text-gray-600">{t("page_subtitle")}</p>

      <div className="mt-4 flex items-center gap-4 text-sm">
        <span className="text-gray-500">
          {t("period_key_label")}: <span className="font-mono">{periodKey}</span>
        </span>
        <span className="text-gray-500">
          {t("latency_label")}: <span className="font-mono">{latencyMs} ms</span>
        </span>
        {isComputing ? (
          <span className="text-blue-600">{t("computing_message")}</span>
        ) : null}
      </div>

      {loadError ? (
        <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-600">
          {loadError}
        </p>
      ) : null}

      <section className="mt-6 rounded border p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">{t("sliders_title")}</h2>
          <button
            type="button"
            className="rounded border px-3 py-1 text-sm"
            onClick={handleReset}
          >
            {t("reset_button")}
          </button>
        </div>

        <SliderRow
          label={t("slider_unit_price")}
          field="unit_price_delta_pct"
          min={PRICE_DELTA_PCT_BOUNDS[0]}
          max={PRICE_DELTA_PCT_BOUNDS[1]}
          step={0.01}
          value={parseFloat(delta.unit_price_delta_pct)}
          onChange={handleSliderChange}
          suffix="%"
        />
        <SliderRow
          label={t("slider_unit_variable_cost")}
          field="unit_variable_cost_delta_pct"
          min={PRICE_DELTA_PCT_BOUNDS[0]}
          max={PRICE_DELTA_PCT_BOUNDS[1]}
          step={0.01}
          value={parseFloat(delta.unit_variable_cost_delta_pct)}
          onChange={handleSliderChange}
          suffix="%"
        />
        <SliderRow
          label={t("slider_fixed_cost")}
          field="fixed_cost_delta_pct"
          min={FIXED_COST_DELTA_PCT_BOUNDS[0]}
          max={FIXED_COST_DELTA_PCT_BOUNDS[1]}
          step={0.01}
          value={parseFloat(delta.fixed_cost_delta_pct)}
          onChange={handleSliderChange}
          suffix="%"
        />
        <SliderRow
          label={t("slider_operating_rate")}
          field="operating_rate_delta_pct"
          min={OPERATING_RATE_DELTA_PCT_BOUNDS[0]}
          max={OPERATING_RATE_DELTA_PCT_BOUNDS[1]}
          step={0.01}
          value={parseFloat(delta.operating_rate_delta_pct)}
          onChange={handleSliderChange}
          suffix="%"
        />
      </section>

      <section className="mt-6 rounded border p-4">
        <h2 className="text-lg font-medium">{t("results_title")}</h2>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <ResultCard
            title={t("card_bep_quantity")}
            beforeValue={displayResult?.baseline_bep.bep_quantity ?? "—"}
            afterValue={displayResult?.simulated_bep.bep_quantity ?? "—"}
          />
          <ResultCard
            title={t("card_bep_revenue")}
            beforeValue={displayResult?.baseline_bep.bep_revenue ?? "—"}
            afterValue={displayResult?.simulated_bep.bep_revenue ?? "—"}
          />
          <ResultCard
            title={t("card_target_profit")}
            beforeValue={displayResult?.baseline_target_profit.target_quantity ?? "—"}
            afterValue={displayResult?.simulated_target_profit.target_quantity ?? "—"}
          />
          <ResultCard
            title={t("card_contribution_margin_ratio")}
            beforeValue={displayResult?.baseline_bep.contribution_margin_ratio ?? "—"}
            afterValue={displayResult?.simulated_bep.contribution_margin_ratio ?? "—"}
            ratio
          />
        </div>
      </section>

      {baseline ? (
        <section className="mt-6 rounded border p-4">
          <h2 className="text-lg font-medium">{t("comparison_title")}</h2>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="py-2 text-left">{t("comparison_variable")}</th>
                <th className="py-2 text-right">{t("comparison_baseline")}</th>
                <th className="py-2 text-right">{t("comparison_simulated")}</th>
              </tr>
            </thead>
            <tbody>
              <ComparisonRow
                label={t("slider_unit_price")}
                baseline={baseline.unit_price}
                simulated={applyDeltaTS(baseline, delta).unit_price}
              />
              <ComparisonRow
                label={t("slider_unit_variable_cost")}
                baseline={baseline.unit_variable_cost}
                simulated={applyDeltaTS(baseline, delta).unit_variable_cost}
              />
              <ComparisonRow
                label={t("slider_fixed_cost")}
                baseline={baseline.fixed_cost}
                simulated={applyDeltaTS(baseline, delta).fixed_cost}
              />
              <ComparisonRow
                label={t("slider_operating_rate")}
                baseline={baseline.operating_rate}
                simulated={applyDeltaTS(baseline, delta).operating_rate}
                ratio
              />
            </tbody>
          </table>
        </section>
      ) : null}
    </main>
  );
}

interface SliderRowProps {
  label: string;
  field: keyof CVPDeltaSerialized;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (field: keyof CVPDeltaSerialized, value: number) => void;
  suffix: string;
}

function SliderRow({
  label,
  field,
  min,
  max,
  step,
  value,
  onChange,
  suffix,
}: SliderRowProps): React.ReactElement {
  return (
    <div className="mt-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-medium">{label}</label>
        <span className="font-mono text-sm">
          {(value * 100).toFixed(0)}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(field, parseFloat(e.target.value))}
        className="mt-1 w-full"
      />
    </div>
  );
}

interface ResultCardProps {
  title: string;
  beforeValue: string;
  afterValue: string;
  ratio?: boolean;
}

function ResultCard({ title, beforeValue, afterValue, ratio }: ResultCardProps): React.ReactElement {
  const before = parseFloat(beforeValue);
  const after = parseFloat(afterValue);
  const isImproved = Number.isFinite(before) && Number.isFinite(after) && after < before;
  const isWorse = Number.isFinite(before) && Number.isFinite(after) && after > before;
  const arrow = isImproved ? "↑" : isWorse ? "↓" : "=";
  const color = isImproved
    ? "text-green-600"
    : isWorse
      ? "text-red-600"
      : "text-gray-500";
  return (
    <div className="rounded border p-3">
      <p className="text-sm text-gray-500">{title}</p>
      <p className="mt-1 font-mono text-lg">
        {beforeValue} → {afterValue}
        {ratio ? "" : " 개"}
      </p>
      <p className={`mt-1 text-sm ${color}`}>{arrow}</p>
    </div>
  );
}

interface ComparisonRowProps {
  label: string;
  baseline: string;
  simulated: string;
  ratio?: boolean;
}

function ComparisonRow({
  label,
  baseline,
  simulated,
  ratio,
}: ComparisonRowProps): React.ReactElement {
  return (
    <tr className="border-b">
      <td className="py-2">{label}</td>
      <td className="py-2 text-right font-mono">
        {baseline}
        {ratio ? "" : " 원"}
      </td>
      <td className="py-2 text-right font-mono">
        {simulated}
        {ratio ? "" : " 원"}
      </td>
    </tr>
  );
}
