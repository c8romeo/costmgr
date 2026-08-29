"use client";

/**
 * apps/web/components/finops/AnomalyDashboardPanel.tsx —
 * Phase 12 T7 (cj-style 111번째 wire) — Client orchestrator for the
 * FinOps Cost Anomaly Detection & Budget Alerting admin dashboard.
 *
 * 4 panels in one dashboard (PRD §F28.1 + §F28.2 + §F28.3 + §F28.4 +
 * §F28.5):
 *   - AnomalyDetections — multi-method voting consensus results
 *   - BudgetDefinitions — active budget per scope/period
 *   - BudgetAlerts — 3-level alert routing history
 *   - ForecastAccuracy — MAE / MAPE / RMSE metrics + retraining trigger
 *
 * All access is gated through `require_finops_anomaly_detection` +
 * `require_finops_budget_alert` capabilities (CR 12-5 D-GATE-01 inversion)
 * + owner-only RBAC at the backend (AD-22 verbatim for anomaly detection
 * + budget definition + budget alert + forecast accuracy).
 */
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import {
  createBudget,
  evaluateForecastAccuracy,
  listAnomalyDetections,
  listBudgetAlerts,
  listBudgets,
  type AnomalyDefinition,
  type BudgetAlert,
  type BudgetDefinition,
  type DetectionResult,
  type ForecastAccuracyMetrics,
} from "@/lib/finops/finops-client";

interface Props {
  accessToken: string;
  locale: string;
  periodKey: string;
}

const DETECTION_METHODS: AnomalyDefinition["threshold_method"][] = [
  "z_score",
  "iqr",
  "ewma",
  "isolation_forest",
];

const DIMENSIONS: AnomalyDefinition["dimension"][] = [
  "department",
  "cost_center",
  "product_line",
  "service",
  "tenant_total",
];

const BASELINE_WINDOWS: AnomalyDefinition["baseline_window"][] = [
  "last_30d",
  "last_90d",
  "ytd",
];

export default function AnomalyDashboardPanel({
  accessToken,
  locale,
  periodKey,
}: Props) {
  const router = useRouter();
  const [detections, setDetections] = useState<DetectionResult[]>([]);
  const [budgets, setBudgets] = useState<BudgetDefinition[]>([]);
  const [alerts, setAlerts] = useState<BudgetAlert[]>([]);
  const [accuracy, setAccuracy] = useState<ForecastAccuracyMetrics | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMethod, setSelectedMethod] =
    useState<AnomalyDefinition["threshold_method"]>("z_score");
  const [selectedDimension, setSelectedDimension] =
    useState<AnomalyDefinition["dimension"]>("department");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [detRes, budgetRes, alertRes] = await Promise.all([
          listAnomalyDetections(periodKey, { accessToken, locale }),
          listBudgets(periodKey, { accessToken, locale }),
          listBudgetAlerts(periodKey, { accessToken, locale }),
        ]);
        if (cancelled) return;
        setDetections(detRes.items);
        setBudgets(budgetRes.items);
        setAlerts(alertRes.items);
        // Sample forecast accuracy — actuals drawn from detection baseline
        if (detRes.items.length > 0) {
          const baselineValues = detRes.items
            .slice(0, 3)
            .map((d) => Number(d.baseline_cost));
          const observedValues = detRes.items
            .slice(0, 3)
            .map((d) => Number(d.observed_cost));
          if (baselineValues.length >= 3) {
            const acc = await evaluateForecastAccuracy(
              detRes.items[0].tenant_id,
              periodKey,
              "moving_average_30d",
              baselineValues,
              observedValues,
              { accessToken, locale },
            );
            if (!cancelled) setAccuracy(acc);
          }
        }
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "anomaly_load_failed",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [accessToken, locale, periodKey]);

  async function handleDetect() {
    setError(null);
    try {
      await runAnomalyDetectionWithDefinition(
        accessToken,
        locale,
        periodKey,
        selectedMethod,
        selectedDimension,
      );
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "detect_failed");
    }
  }

  async function handleCreateBudget() {
    setError(null);
    try {
      await createBudget(
        {
          budget_id: crypto.randomUUID(),
          tenant_id: "",
          period_key: periodKey,
          budget_period: "monthly",
          scope: "tenant",
          scope_id: "default",
          amount: "1000000.00",
          currency_code: "KRW",
          alert_thresholds: { warning: 80.0, critical: 90.0, exceeded: 100.0 },
          status: "active",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        { accessToken, locale },
      );
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "budget_create_failed");
    }
  }

  if (loading) {
    return (
      <div role="status" aria-live="polite">
        Anomaly 데이터를 불러오는 중...
      </div>
    );
  }

  return (
    <section aria-label="FinOps Anomaly Detection & Budget Alerting">
      {error && (
        <div role="alert" className="finops-anomaly-error">
          {error}
        </div>
      )}

      <div className="finops-anomaly-controls">
        <label htmlFor="detection-method">검출 방식</label>
        <select
          id="detection-method"
          value={selectedMethod}
          onChange={(e) =>
            setSelectedMethod(
              e.target.value as AnomalyDefinition["threshold_method"],
            )
          }
        >
          {DETECTION_METHODS.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>

        <label htmlFor="detection-dimension">차원</label>
        <select
          id="detection-dimension"
          value={selectedDimension}
          onChange={(e) =>
            setSelectedDimension(
              e.target.value as AnomalyDefinition["dimension"],
            )
          }
        >
          {DIMENSIONS.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>

        <button type="button" onClick={handleDetect}>
          이상 탐지 실행
        </button>
        <button type="button" onClick={handleCreateBudget}>
          예산 생성
        </button>
      </div>

      <h2>이상 탐지 결과</h2>
      {detections.length === 0 ? (
        <p>이상 탐지 결과가 없습니다.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>기간</th>
              <th>차원</th>
              <th>관측값</th>
              <th>기준값</th>
              <th>편차(%)</th>
              <th>심각도</th>
              <th>상태</th>
              <th>투표 방식</th>
            </tr>
          </thead>
          <tbody>
            {detections.map((d) => (
              <tr key={d.result_id}>
                <td>{d.period_key}</td>
                <td>
                  {d.dimension}: {d.dimension_value}
                </td>
                <td>{d.observed_cost}</td>
                <td>{d.baseline_cost}</td>
                <td>{(d.deviation_pct * 100).toFixed(2)}%</td>
                <td>{d.severity}</td>
                <td>{d.status}</td>
                <td>{d.methods_voted.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>예산 정의</h2>
      {budgets.length === 0 ? (
        <p>정의된 예산이 없습니다.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>기간</th>
              <th>범위</th>
              <th>금액</th>
              <th>경보 임계값</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {budgets.map((b) => (
              <tr key={b.budget_id}>
                <td>{b.period_key}</td>
                <td>
                  {b.scope}: {b.scope_id}
                </td>
                <td>
                  {b.amount} {b.currency_code}
                </td>
                <td>
                  {b.alert_thresholds.warning}% / {b.alert_thresholds.critical}
                  % / {b.alert_thresholds.exceeded}%
                </td>
                <td>{b.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>예산 경보 이력</h2>
      {alerts.length === 0 ? (
        <p>발송된 경보가 없습니다.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>기간</th>
              <th>레벨</th>
              <th>소비율</th>
              <th>채널</th>
              <th>상태</th>
              <th>발송 시각</th>
            </tr>
          </thead>
          <tbody>
            {alerts.map((a) => (
              <tr key={a.alert_id}>
                <td>{a.period_key}</td>
                <td>{a.alert_level}</td>
                <td>{(a.consumption_pct * 100).toFixed(2)}%</td>
                <td>{a.routing.channels.join(", ")}</td>
                <td>{a.status}</td>
                <td>{a.created_at}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h2>예측 정확도</h2>
      {accuracy === null ? (
        <p>예측 정확도 데이터가 없습니다 (최소 3개 기간 필요).</p>
      ) : (
        <div>
          <p>모델: {accuracy.model_name}</p>
          <p>MAE: {accuracy.mae.toFixed(4)}</p>
          <p>MAPE: {(accuracy.mape * 100).toFixed(2)}%</p>
          <p>RMSE: {accuracy.rmse.toFixed(4)}</p>
          <p>상태: {accuracy.status}</p>
          {accuracy.retraining_recommended && (
            <p role="alert">⚠️ MAPE 20% 초과 — 모델 재학습 권장</p>
          )}
        </div>
      )}
    </section>
  );
}

async function runAnomalyDetectionWithDefinition(
  accessToken: string,
  locale: string,
  periodKey: string,
  thresholdMethod: AnomalyDefinition["threshold_method"],
  dimension: AnomalyDefinition["dimension"],
): Promise<DetectionResult> {
  const { runAnomalyDetection } = await import("@/lib/finops/finops-client");
  return runAnomalyDetection(
    {
      tenant_id: "",
      period_key: periodKey,
      dimension,
      dimension_value: "*",
      threshold_method: thresholdMethod,
      threshold_value: 3.0,
      baseline_window: "last_30d",
      consecutive_periods_required: 3,
    },
    { accessToken, locale },
  );
}