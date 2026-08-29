/**
 * finops-reporting-client — Phase 16 FinOps Reporting & Executive Dashboard TS mirror.
 *
 * Phase 16 (cj-style 127번째 wire) — CR 12-5 D-PARITY-01 Python
 * TypedDict ↔ TypeScript interface parity. Mirrors apps/api/modules/
 * finops/executive_dashboard_aggregator.py + cross_module_kpi.py +
 * executive_report_generator.py + scheduled_executive_dispatch.py
 * TypedDict definitions.
 */

// ── ExecutiveRollup ──
export interface ExecutiveRollup {
  rollup_id: string;
  tenant_id: string;
  scope_type: "tenant" | "department" | "cost_center" | "product_line";
  scope_id: string;
  period_key: string; // e.g. "2026-08" | "2026-Q3" | "2026"
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  showback_total_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  anomaly_count_30d: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  forecast_projection_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  optimization_savings_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  tag_compliance_pct: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  idle_cost_krw: number;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  department_breakdown: Record<string, number>;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  cost_center_breakdown: Record<string, number>;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  resource_type_breakdown: Record<string, number>;
  cache_key: string;
  generated_at: string;
  trace_id: string;
}

// ── KPIMetric ──
export type KPIName =
  | "total_monthly_cost_krw"
  | "monthly_cost_growth_pct"
  | "cost_per_employee_krw"
  | "cost_anomaly_count_30d"
  | "forecast_deviation_pct"
  | "idle_cost_monthly_krw"
  | "tag_compliance_pct"
  | "optimization_realized_savings_krw";

export interface KPIMetric {
  kpi_id: string;
  tenant_id: string;
  scope_type: "tenant" | "department" | "cost_center" | "product_line";
  scope_id: string;
  period_key: string;
  kpi_name: KPIName;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  kpi_value: number;
  kpi_unit: string; // "KRW" | "pct" | "count"
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  kpi_delta: number | null;
  kpi_trend: "up" | "down" | "flat";
  kpi_threshold_status: "on_track" | "warning" | "critical";
  computed_at: string;
  trace_id: string;
}

// ── ExecutiveReport ──
export interface ExecutiveReport {
  report_id: string;
  tenant_id: string;
  scope_type: "tenant" | "department" | "cost_center" | "product_line";
  scope_id: string;
  period_key: string;
  cadence: "monthly" | "quarterly" | "annual";
  export_format: "pdf" | "csv" | "excel";
  report_file_url: string;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  report_size_bytes: number;
  report_generated_at: string;
  generated_by: string;
  status: "generating" | "completed" | "failed" | "expired";
  expires_at: string | null;
  trace_id: string;
}

// ── ScheduledDispatch ──
export interface ScheduledDispatch {
  dispatch_id: string;
  tenant_id: string;
  dispatch_schedule: "weekly" | "monthly" | "quarterly" | "annual";
  cron_expression: string; // e.g. "0 9 1 * *"
  recipient_strategy:
    | "owner_only"
    | "executive_team"
    | "board_observers"
    | "custom_recipients";
  recipient_list: Record<string, unknown>;
  report_id: string | null;
  status:
    | "scheduled"
    | "running"
    | "completed"
    | "failed"
    | "cancelled";
  scheduled_at: string;
  last_run_at: string | null;
  next_run_at: string | null;
  trace_id: string;
}

// ── ComplianceTrendPoint ──
export interface ComplianceTrendPoint {
  period_key: string; // "YYYY-MM"
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  tag_compliance_pct: number;
}

// ── Error class (CR 12-5 D-GATE-01) ──
export class FinopsReportingApiError extends Error {
  constructor(
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "FinopsReportingApiError";
  }
}

// ── API client functions ──
export async function fetchExecutiveRollup(
  scopeType: string = "tenant",
  scopeId: string = "",
  periodKey: string = "",
): Promise<ExecutiveRollup> {
  const params = new URLSearchParams({
    scope_type: scopeType,
    scope_id: scopeId,
    period_key: periodKey,
  });
  const response = await fetch(
    `/api/v1/admin/finops/executive-dashboard/rollup?${params.toString()}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsReportingApiError(
      response.status,
      "EXECUTIVE_ROLLUP_FETCH_FAILED",
      `Executive rollup 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<ExecutiveRollup>;
}

export async function fetchCrossModuleKPIs(
  scopeType: string = "tenant",
  scopeId: string = "",
  periodKey: string = "",
  kpiSet?: KPIName[],
): Promise<{ kpis: KPIMetric[] }> {
  const params = new URLSearchParams({
    scope_type: scopeType,
    scope_id: scopeId,
    period_key: periodKey,
  });
  if (kpiSet && kpiSet.length > 0) {
    params.set("kpi_set", kpiSet.join(","));
  }
  const response = await fetch(
    `/api/v1/admin/finops/executive-dashboard/kpis?${params.toString()}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsReportingApiError(
      response.status,
      "CROSS_MODULE_KPI_FETCH_FAILED",
      `Cross-module KPI 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<{ kpis: KPIMetric[] }>;
}

export async function generateExecutiveReport(
  scopeType: string,
  scopeId: string,
  periodKey: string,
  cadence: "monthly" | "quarterly" | "annual",
  exportFormat: "pdf" | "csv" | "excel",
  dryRun: boolean = false,
): Promise<ExecutiveReport> {
  const response = await fetch(
    "/api/v1/admin/finops/executive-dashboard/reports",
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        scope_type: scopeType,
        scope_id: scopeId,
        period_key: periodKey,
        cadence,
        export_format: exportFormat,
      }),
      ...(dryRun ? { headers: { "X-Dry-Run": "true" } } : {}),
    },
  );
  if (!response.ok) {
    throw new FinopsReportingApiError(
      response.status,
      "EXECUTIVE_REPORT_GENERATE_FAILED",
      `Executive report 생성 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<ExecutiveReport>;
}

export async function scheduleExecutiveDispatch(
  dispatchSchedule: "weekly" | "monthly" | "quarterly" | "annual",
  recipientStrategy:
    | "owner_only"
    | "executive_team"
    | "board_observers"
    | "custom_recipients",
  recipientList: Record<string, unknown> = {},
): Promise<ScheduledDispatch> {
  const response = await fetch(
    "/api/v1/admin/finops/executive-dashboard/dispatches",
    {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        dispatch_schedule: dispatchSchedule,
        recipient_strategy: recipientStrategy,
        recipient_list: recipientList,
      }),
    },
  );
  if (!response.ok) {
    throw new FinopsReportingApiError(
      response.status,
      "SCHEDULED_DISPATCH_FAILED",
      `Scheduled dispatch 등록 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<ScheduledDispatch>;
}

export async function fetchComplianceTrend(
  scopeType: string = "tenant",
  scopeId: string = "",
): Promise<{ trend: ComplianceTrendPoint[] }> {
  const params = new URLSearchParams({
    scope_type: scopeType,
    scope_id: scopeId,
  });
  const response = await fetch(
    `/api/v1/admin/finops/executive-dashboard/compliance-trend?${params.toString()}`,
    { credentials: "include" },
  );
  if (!response.ok) {
    throw new FinopsReportingApiError(
      response.status,
      "COMPLIANCE_TREND_FETCH_FAILED",
      `Compliance trend 조회 실패: ${response.statusText}`,
    );
  }
  return response.json() as Promise<{ trend: ComplianceTrendPoint[] }>;
}