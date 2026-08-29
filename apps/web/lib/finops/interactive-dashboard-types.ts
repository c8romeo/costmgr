/**
 * interactive-dashboard-types — Phase 28 T2 TypeScript types for
 * FinOps Interactive Dashboard.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — Mirrors
 * Python TypedDicts in
 * `apps/api/modules/finops/interactive_dashboard/serializers.py`.
 *
 * CR 12-5 D-PARITY-01 inversion — Python TypedDict ↔ TypeScript
 * interface parity preserved.
 *
 * Provides:
 * - KPIRefreshCadence (6 values: realtime/hourly/daily/weekly/monthly/on_demand)
 * - ExportFormat (5 values: pdf/xlsx/csv/json/png)
 * - DashboardSharingScope (4 values: private/tenant/tenant_owner/cross_tenant)
 * - DashboardLayout (3 values: grid/masonry/tabs)
 * - DrillDownDimension (7 values: tenant/cost_center/department/business_unit/tag/cloud_provider/service)
 * - DrillDownGranularity (7 values: minute/hour/day/week/month/quarter/year)
 * - ExportJobStatus (5 values: pending/in_progress/completed/failed/cancelled)
 * - UnifiedKPI (24 fields, PRD §F43.1 verbatim)
 * - KPIBreakdown (8 fields, PRD §F43.1 verbatim)
 * - DrillDownContext (6 fields, PRD §F43.2 verbatim)
 * - SavedView (14 fields, PRD §F43.2 verbatim)
 * - ExportJob (12 fields, PRD §F43.3 verbatim)
 * - SharingGrant (8 fields, PRD §F43.7 verbatim)
 * - DASHBOARD_KPI_DIMENSION_WEIGHTS, DASHBOARD_CADENCE_HOURS_KST,
 *   DASHBOARD_RECIPIENT_TEMPLATES, INTERACTIVE_DASHBOARD_ENGINE_VERSION
 */

export type KPIRefreshCadence =
    | "realtime"
    | "hourly"
    | "daily"
    | "weekly"
    | "monthly"
    | "on_demand";

export type ExportFormat =
    | "pdf"
    | "xlsx"
    | "csv"
    | "json"
    | "png";

export type DashboardSharingScope =
    | "private"
    | "tenant"
    | "tenant_owner"
    | "cross_tenant";

export type DashboardLayout =
    | "grid"
    | "masonry"
    | "tabs";

export type DrillDownDimension =
    | "tenant"
    | "cost_center"
    | "department"
    | "business_unit"
    | "tag"
    | "cloud_provider"
    | "service";

export type DrillDownGranularity =
    | "minute"
    | "hour"
    | "day"
    | "week"
    | "month"
    | "quarter"
    | "year";

export type ExportJobStatus =
    | "pending"
    | "in_progress"
    | "completed"
    | "failed"
    | "cancelled";

/** 5-dim weighted aggregation (PRD §F43.2 + AD-56 (b) verbatim) */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const DASHBOARD_KPI_DIMENSION_WEIGHTS: Record<string, number> = {
    cost: 0.30,
    usage: 0.20,
    performance: 0.20,
    compliance: 0.15,
    sla: 0.15,
};

/** Cadence schedule KST pytz (PRD §F43.1 + AD-56 (a) verbatim) */
// eslint-disable-next-line @typescript-eslint/no-restricted-types
export const DASHBOARD_CADENCE_HOURS_KST: Record<string, readonly [number, number]> = {
    daily_unified_kpi_refresh: [4, 0],
    weekly_export_cleanup: [5, 0],
    monthly_sharing_expiry: [6, 0],
};

/** Recipient strategy templates (PRD §F43.3 verbatim) */
export const DASHBOARD_RECIPIENT_TEMPLATES: Record<
    string,
    {
        slack_channels: string[];
        email_recipients: string[];
        ms_teams_channels: string[];
        s3_archive_enabled: boolean;
    }
> = {
    owner_only: {
        slack_channels: ["#finops-interactive-dashboard"],
        email_recipients: ["tenant_owner"],
        ms_teams_channels: [],
        s3_archive_enabled: true,
    },
    executive: {
        slack_channels: [
            "#finops-interactive-dashboard",
            "#finops-executive",
        ],
        email_recipients: ["tenant_owner", "executive_viewer"],
        ms_teams_channels: ["FinOps Executive"],
        s3_archive_enabled: true,
    },
    all_viewers: {
        slack_channels: ["#finops-interactive-dashboard"],
        email_recipients: ["tenant_owner", "executive_viewer", "viewer"],
        ms_teams_channels: [],
        s3_archive_enabled: false,
    },
};

/** Interactive Dashboard engine version (Phase 28 wire verbatim) */
export const INTERACTIVE_DASHBOARD_ENGINE_VERSION = "1.0.0";

/** Phase 11~28 unified KPI source modules (PRD §F43.1 verbatim — 18 KPIs) */
export const PHASE_KPI_SOURCE_MODULES: Record<string, string> = {
    phase_11: "showback_krw",
    phase_12: "anomaly_count",
    phase_13: "forecast_krw",
    phase_14: "optimization_savings_krw",
    phase_15: "tag_compliance_pct",
    phase_16: "report_krw",
    phase_17: "sustainability_co2_kg",
    phase_18: "commitment_utilization_pct",
    phase_19: "pricing_savings_krw",
    phase_20: "multi_cloud_reconciliation_krw",
    phase_21: "reserved_capacity_utilization_pct",
    phase_22: "chargeback_settlement_krw",
    phase_23: "unit_economics_cost_per_unit",
    phase_24: "budget_consumption_pct",
    phase_25: "vendor_spend_krw",
    phase_26: "anomaly_ml_score",
    phase_27: "carry_over_metric",
    phase_28: "unified_kpi_total",
};

/** 12 pre-defined saved-view templates (PRD §F43.2 verbatim) */
export const PREDEFINED_VIEW_TEMPLATES: readonly string[] = [
    "CostByCloudProvider",
    "CostByService",
    "CostByCostCenter",
    "CostByDepartment",
    "CostByBusinessUnit",
    "CostByTag",
    "SavingsByOptimizationType",
    "CommitmentUtilizationByCloud",
    "BudgetVarianceByPeriod",
    "SustainabilityByCloudProvider",
    "VendorSpendByCategory",
    "ReservedInstanceUtilizationByTier",
] as const;

/** High-value threshold for owner approval / 2FA challenge (AD-56 (g)) */
export const HIGH_VALUE_THRESHOLD_KRW_PER_YEAR = 10_000_000.0;

/** Max saved views per tenant (PRD §F43.2 verbatim) */
export const MAX_SAVED_VIEWS_PER_TENANT = 50;

/** Max export size in bytes (PRD §F43.3 verbatim — 50MB) */
export const MAX_EXPORT_SIZE_BYTES = 52_428_800;

/** Export auto-retries (PRD §F43.3 verbatim) */
export const EXPORT_MAX_RETRIES = 3;

/** Saved view cache TTL seconds (PRD §F43.2 verbatim) */
export const SAVED_VIEW_CACHE_TTL_SECONDS = 300;

/** Sharing expiry default days (PRD §F43.7 verbatim) */
export const SHARING_EXPIRES_DEFAULT_DAYS = 30;

/** Cross-phase unified KPI record (PRD §F43.1 — 24 fields) */
export interface UnifiedKPI {
    unified_kpi_id: string;
    tenant_id: string;
    period_key: string;
    dimension: string;
    dimension_value: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    kpi_value_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    showback_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    anomaly_count: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    forecast_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    optimization_savings_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    tag_compliance_pct: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    report_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    sustainability_co2_kg: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    commitment_utilization_pct: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    pricing_savings_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    multi_cloud_reconciliation_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    reserved_capacity_utilization_pct: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    chargeback_settlement_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    unit_economics_cost_per_unit: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    budget_consumption_pct: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    vendor_spend_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    anomaly_ml_score: number;
    refresh_cadence: KPIRefreshCadence;
    computed_at: string;
    trace_id: string;
}

/** Weighted 5-dim KPI breakdown (PRD §F43.1 — 8 fields) */
export interface KPIBreakdown {
    tenant_id: string;
    period_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    usage_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    performance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    compliance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    sla_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    weighted_total: number;
}

/** Drill-down navigation context (PRD §F43.2 — 6 fields) */
export interface DrillDownContext {
    tenant_id: string;
    dimension: DrillDownDimension;
    dimension_value: string;
    granularity: DrillDownGranularity;
    period_key: string;
    parent_dimension: DrillDownDimension | null;
}

/** Per-tenant saved dashboard view (PRD §F43.2 — 14 fields) */
export interface SavedView {
    saved_view_id: string;
    tenant_id: string;
    view_name: string;
    template_id: string | null;
    filter_by: Record<string, unknown>;
    group_by: string[];
    sort_by: string;
    chart_type: string;
    time_range: string;
    layout: DashboardLayout;
    is_shared: boolean;
    created_by_user_id: string;
    created_at: string;
    updated_at: string;
}

/** Export job tracking record (PRD §F43.3 — 12 fields) */
export interface ExportJob {
    export_job_id: string;
    tenant_id: string;
    saved_view_id: string;
    export_format: ExportFormat;
    status: ExportJobStatus;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    progress_pct: number;
    file_path: string | null;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    file_size_bytes: number;
    checksum_sha256: string | null;
    expires_at: string | null;
    started_at: string;
    completed_at: string | null;
}

/** Dashboard sharing grant (PRD §F43.7 — 8 fields) */
export interface SharingGrant {
    sharing_grant_id: string;
    tenant_id: string;
    saved_view_id: string;
    scope: DashboardSharingScope;
    granted_to_user_id: string;
    granted_by_user_id: string;
    granted_at: string;
    expires_at: string;
}

/** Healthcheck response (Phase 28 wire T1.6 verbatim) */
export interface DashboardHealthcheck {
    status: string;
    module_tag: string;
    engine_version: string;
    router_version: string;
}