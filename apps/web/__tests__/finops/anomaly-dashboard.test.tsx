/**
 * apps/web/__tests__/finops/anomaly-dashboard.test.tsx —
 * Phase 12 T6.5 (cj-style 111번째 wire) — Anomaly dashboard frontend
 * tests. Mirrors apps/web/__tests__/finops/finops-dashboard.test.tsx
 * pattern verbatim.
 */
import { describe, expect, it, vi } from "vitest";

import {
  AnomalyApiError,
  createBudget,
  evaluateForecastAccuracy,
  listAnomalyDetections,
  listBudgetAlerts,
  listBudgets,
  runAnomalyDetection,
} from "@/lib/finops/anomaly-client";
import type {
  AnomalyDefinition,
  BudgetAlert,
  BudgetDefinition,
  DetectionResult,
  ForecastAccuracyMetrics,
} from "@/lib/finops/anomaly-types";

const ACCESS_TOKEN = "test-access-token";

const SAMPLE_DETECTION: DetectionResult = {
  result_id: "result-1",
  tenant_id: "11111111-1111-1111-1111-111111111111",
  period_key: "2026-08",
  dimension: "department",
  dimension_value: "DEPT-001",
  observed_cost: "150000.00",
  baseline_cost: "100000.00",
  deviation_pct: 0.5,
  severity: "high",
  methods_voted: ["z_score", "iqr", "ewma"],
  status: "confirmed",
  detected_at: "2026-08-15T00:00:00Z",
  trace_id: "trace-1",
};

const SAMPLE_BUDGET: BudgetDefinition = {
  budget_id: "budget-1",
  tenant_id: "11111111-1111-1111-1111-111111111111",
  period_key: "2026-08",
  budget_period: "monthly",
  scope: "tenant",
  scope_id: "TENANT",
  amount: "1000000.00",
  currency_code: "KRW",
  alert_thresholds: { warning: 80.0, critical: 90.0, exceeded: 100.0 },
  status: "active",
  created_at: "2026-08-01T00:00:00Z",
  updated_at: "2026-08-15T00:00:00Z",
};

const SAMPLE_ALERT: BudgetAlert = {
  alert_id: "alert-1",
  tenant_id: "11111111-1111-1111-1111-111111111111",
  budget_id: "budget-1",
  period_key: "2026-08",
  alert_level: "warning",
  consumption_pct: 0.85,
  consumption_amount: "850000.00",
  budget_amount: "1000000.00",
  routing: {
    channels: ["slack"],
    recipients: ["default-owner"],
    retry_policy: "exponential_backoff_3x",
  },
  status: "sent",
  created_at: "2026-08-15T00:00:00Z",
  trace_id: "trace-1",
};

describe("anomaly-client API surface", () => {
  it("listAnomalyDetections returns detection page", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            items: [SAMPLE_DETECTION],
            total: 1,
            page: 1,
            page_size: 20,
          }),
          { status: 200 },
        ),
      ),
    ) as unknown as typeof fetch;
    const result = await listAnomalyDetections("2026-08", { accessToken: ACCESS_TOKEN });
    expect(result.items).toHaveLength(1);
    expect(result.items[0].severity).toBe("high");
  });

  it("runAnomalyDetection returns DetectionResult", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify(SAMPLE_DETECTION), { status: 200 })),
    ) as unknown as typeof fetch;
    const def: AnomalyDefinition = {
      tenant_id: SAMPLE_DETECTION.tenant_id,
      period_key: "2026-08",
      dimension: "department",
      dimension_value: "DEPT-001",
      threshold_method: "z_score",
      threshold_value: 3.0,
      baseline_window: "last_30d",
      consecutive_periods_required: 3,
    };
    const result = await runAnomalyDetection(def, { accessToken: ACCESS_TOKEN });
    expect(result.deviation_pct).toBe(0.5);
    expect(result.methods_voted).toEqual(["z_score", "iqr", "ewma"]);
  });

  it("createBudget returns BudgetDefinition", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify(SAMPLE_BUDGET), { status: 200 })),
    ) as unknown as typeof fetch;
    const result = await createBudget(SAMPLE_BUDGET, { accessToken: ACCESS_TOKEN });
    expect(result.budget_id).toBe("budget-1");
    expect(result.alert_thresholds.warning).toBe(80.0);
  });

  it("listBudgets returns budget page", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            items: [SAMPLE_BUDGET],
            total: 1,
            page: 1,
            page_size: 20,
          }),
          { status: 200 },
        ),
      ),
    ) as unknown as typeof fetch;
    const result = await listBudgets("2026-08", { accessToken: ACCESS_TOKEN });
    expect(result.items).toHaveLength(1);
  });

  it("listBudgetAlerts returns alert page", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve(
        new Response(
          JSON.stringify({
            items: [SAMPLE_ALERT],
            total: 1,
            page: 1,
            page_size: 20,
          }),
          { status: 200 },
        ),
      ),
    ) as unknown as typeof fetch;
    const result = await listBudgetAlerts("2026-08", { accessToken: ACCESS_TOKEN });
    expect(result.items).toHaveLength(1);
    expect(result.items[0].alert_level).toBe("warning");
  });

  it("evaluateForecastAccuracy returns accuracy metrics", async () => {
    const accuracy: ForecastAccuracyMetrics = {
      tenant_id: SAMPLE_DETECTION.tenant_id,
      period_key: "2026-08",
      model_name: "moving_average_30d",
      mae: 0.05,
      mape: 0.05,
      rmse: 0.06,
      status: "high",
      retraining_recommended: false,
      trace_id: "trace-1",
    };
    global.fetch = vi.fn(() =>
      Promise.resolve(new Response(JSON.stringify(accuracy), { status: 200 })),
    ) as unknown as typeof fetch;
    const result = await evaluateForecastAccuracy(
      accuracy.tenant_id,
      "2026-08",
      "moving_average_30d",
      [100.0, 200.0, 300.0],
      [105.0, 195.0, 305.0],
      { accessToken: ACCESS_TOKEN },
    );
    expect(result.mape).toBe(0.05);
    expect(result.retraining_recommended).toBe(false);
  });

  it("AnomalyApiError carries status + code + trace_id", () => {
    const err = new AnomalyApiError("bad", 400, "ANOMALY_DEFINITION_INVALID", "trace-1");
    expect(err.status).toBe(400);
    expect(err.code).toBe("ANOMALY_DEFINITION_INVALID");
    expect(err.trace_id).toBe("trace-1");
    expect(err.name).toBe("AnomalyApiError");
  });
});