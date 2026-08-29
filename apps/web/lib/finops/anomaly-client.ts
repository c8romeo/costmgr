/**
 * apps/web/lib/finops/anomaly-client.ts —
 * Phase 12 T7 (cj-style 111번째 wire) — FinOps Cost Anomaly Detection
 * & Budget Alerting client. Mirrors apps/web/lib/finops/finops-client.ts
 * pattern verbatim.
 *
 * TypedDict parity (CR 12-5 D-PARITY-01) — types here mirror the
 * backend Python TypedDicts in apps/api/modules/finops/anomaly_detection.py
 * + anomaly_detection_engine.py + budget_definition.py + budget_alert.py
 * + forecast_accuracy.py.
 */
import type {
  AnomalyDefinition,
  BudgetAlert,
  BudgetDefinition,
  DetectionResult,
  ForecastAccuracyMetrics,
} from "@/lib/finops/anomaly-types";

export type {
  AnomalyDefinition,
  BudgetAlert,
  BudgetDefinition,
  DetectionResult,
  ForecastAccuracyMetrics,
};

export interface AnomalyApiPage<T> {
  items: T[];
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  total: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  page: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  page_size: number;
}

export class AnomalyApiError extends Error {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  readonly status: number;
  readonly code: string;
  readonly trace_id: string;
  constructor(
    message: string,
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    status: number,
    code: string,
    trace_id: string,
  ) {
    super(message);
    this.name = "AnomalyApiError";
    this.status = status;
    this.code = code;
    this.trace_id = trace_id;
  }
}

const DEFAULT_TIMEOUT_MS = 15_000;

interface RequestOptions {
  accessToken: string;
  locale?: string;
  signal?: AbortSignal;
}

async function request<T>(
  path: string,
  init: RequestInit & { accessToken: string; locale?: string },
): Promise<T> {
  const { accessToken, locale, signal, ...rest } = init;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), DEFAULT_TIMEOUT_MS);
  const externalSignal = signal;
  try {
    const headers: Record<string, string> = {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      ...((rest.headers ?? {}) as Record<string, string>),
    };
    if (locale) headers["Accept-Language"] = locale;
    const res = await fetch(path, {
      ...rest,
      headers,
      signal: externalSignal ?? controller.signal,
    });
    if (!res.ok) {
      const body = (await res.json().catch(() => ({}))) as {
        code?: string;
        message?: string;
        trace_id?: string;
      };
      throw new AnomalyApiError(
        body.message ?? res.statusText,
        res.status,
        body.code ?? "ANOMALY_API_ERROR",
        body.trace_id ?? "",
      );
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timeout);
  }
}

export async function runAnomalyDetection(
  definition: AnomalyDefinition,
  opts: RequestOptions,
): Promise<DetectionResult> {
  return request<DetectionResult>(
    "/api/v1/admin/finops/anomaly/detect",
    {
      method: "POST",
      accessToken: opts.accessToken,
      locale: opts.locale,
      body: JSON.stringify(definition),
    },
  );
}

export async function listAnomalyDetections(
  period_key: string,
  opts: RequestOptions,
): Promise<AnomalyApiPage<DetectionResult>> {
  return request<AnomalyApiPage<DetectionResult>>(
    `/api/v1/admin/finops/anomaly/detections?period_key=${encodeURIComponent(period_key)}`,
    {
      method: "GET",
      accessToken: opts.accessToken,
      locale: opts.locale,
    },
  );
}

export async function createBudget(
  budget: BudgetDefinition,
  opts: RequestOptions,
): Promise<BudgetDefinition> {
  return request<BudgetDefinition>(
    "/api/v1/admin/finops/budget",
    {
      method: "POST",
      accessToken: opts.accessToken,
      locale: opts.locale,
      body: JSON.stringify(budget),
    },
  );
}

export async function listBudgets(
  period_key: string,
  opts: RequestOptions,
): Promise<AnomalyApiPage<BudgetDefinition>> {
  return request<AnomalyApiPage<BudgetDefinition>>(
    `/api/v1/admin/finops/budget?period_key=${encodeURIComponent(period_key)}`,
    {
      method: "GET",
      accessToken: opts.accessToken,
      locale: opts.locale,
    },
  );
}

export async function listBudgetAlerts(
  period_key: string,
  opts: RequestOptions,
): Promise<AnomalyApiPage<BudgetAlert>> {
  return request<AnomalyApiPage<BudgetAlert>>(
    `/api/v1/admin/finops/budget/alerts?period_key=${encodeURIComponent(period_key)}`,
    {
      method: "GET",
      accessToken: opts.accessToken,
      locale: opts.locale,
    },
  );
}

export async function evaluateForecastAccuracy(
  tenant_id: string,
  period_key: string,
  model_name: string,
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  predicted: number[],
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  actual: number[],
  opts: RequestOptions,
): Promise<ForecastAccuracyMetrics> {
  return request<ForecastAccuracyMetrics>(
    "/api/v1/admin/finops/forecast/accuracy",
    {
      method: "POST",
      accessToken: opts.accessToken,
      locale: opts.locale,
      body: JSON.stringify({
        tenant_id,
        period_key,
        model_name,
        predicted,
        actual,
      }),
    },
  );
}