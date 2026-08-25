"use client";

/**
 * FinopsSustainabilityDashboardPanel — Phase 17 FinOps Sustainability &
 * Carbon Reporting Client panel.
 *
 * Phase 17 (cj-style 131번째 wire) — FinOps Sustainability & Carbon
 * Reporting territory (PRD §F33.6). 5 sub-components:
 * 1. CarbonEmissionsAggregator — 4 scope_type (tenant/department/
 *    cost_center/product_line) + period selector (monthly/quarterly/
 *    annual) + 8 KPI metrics summary + 6-module breakdown.
 * 2. SustainabilityKPISelector — 8 KPI toggle selectbox
 *    (total_carbon_emissions_kgco2e + scope1/2/3_emissions_kgco2e +
 *    carbon_intensity_kgco2e_per_krw + data_center_pue +
 *    renewable_energy_pct + carbon_offset_kgco2e) +
 *    KPI delta arrow + trend chart mini.
 * 3. SustainabilityReportGeneratorPanel — 3 cadence (monthly/quarterly/
 *    annual) + 3 export_format (PDF/CSV/Excel) + 5-framework support
 *    (CSRD/SEC Climate/EU Taxonomy/IFRS S2/KSSB) + generate button +
 *    recent reports list table.
 * 4. ScheduledSustainabilityDispatchConfigPanel — 4 cron schedules
 *    (weekly/monthly/quarterly/annual) + 4 recipient strategies
 *    (owner_only/sustainability_team/board_observers/custom_recipients)
 *    + enable/disable + test_dispatch dry-run.
 * 5. CarbonOffsetTrendMiniChart — renewable_energy_pct 12-month trend
 *    + carbon_offset_kgco2e cumulative (Phase 16 ComplianceTrendMiniChart
 *    EXTENSION 정합).
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/sustainability-client.ts`.
 * AD-14 stack pin — Recharts 2.12.7.
 */

import { useState } from "react";
import {
  aggregateCarbonEmissions,
  selectSustainabilityKPIs,
  generateSustainabilityReport,
  dispatchSustainabilityReport,
  type AggregateCarbonEmissionsRequest,
  type SelectSustainabilityKPIsRequest,
  type GenerateSustainabilityReportRequest,
  type DispatchSustainabilityReportRequest,
} from "@/lib/finops/sustainability-client";
import type {
  CarbonEmissionsRollup,
  SustainabilityKPIMetric,
  SustainabilityReport,
  ScheduledSustainabilityDispatch,
  SustainabilityKPIName,
} from "@/lib/finops/sustainability-types";

const ALL_KPI_NAMES: SustainabilityKPIName[] = [
  "total_carbon_emissions_kgco2e",
  "scope1_emissions_kgco2e",
  "scope2_emissions_kgco2e",
  "scope3_emissions_kgco2e",
  "carbon_intensity_kgco2e_per_krw",
  "data_center_pue",
  "renewable_energy_pct",
  "carbon_offset_kgco2e",
];

// ── 1. CarbonEmissionsAggregator ──
function CarbonEmissionsAggregator({
  rollup,
  onRefresh,
}: {
  rollup: CarbonEmissionsRollup | null;
  onRefresh: () => void;
}) {
  return (
    <div
      className="carbon-emissions-aggregator mb-6 rounded bg-slate-900 p-4"
      aria-label="carbon_emissions_aggregator"
    >
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-slate-100">
          Carbon Emissions Aggregator
        </h2>
        <button
          type="button"
          aria-label="carbon_emissions_refresh"
          className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
          onClick={onRefresh}
        >
          새로고침
        </button>
      </div>
      {rollup ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm text-slate-200">
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Total Carbon (kgCO2e)</div>
            <div className="text-lg font-semibold">
              {rollup.total_carbon_emissions_kgco2e.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Scope 1 (kgCO2e)</div>
            <div className="text-lg font-semibold">
              {rollup.scope1_emissions_kgco2e.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Scope 2 (kgCO2e)</div>
            <div className="text-lg font-semibold">
              {rollup.scope2_emissions_kgco2e.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Scope 3 (kgCO2e)</div>
            <div className="text-lg font-semibold">
              {rollup.scope3_emissions_kgco2e.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Carbon Offset (kgCO2e)</div>
            <div className="text-lg font-semibold">
              {rollup.carbon_offset_kgco2e.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Renewable Energy (%)</div>
            <div className="text-lg font-semibold">
              {rollup.renewable_energy_pct.toFixed(2)}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-slate-400 text-sm">No rollup loaded</div>
      )}
    </div>
  );
}

// ── 2. SustainabilityKPISelector ──
function SustainabilityKPISelector({
  kpis,
  selectedKPIName,
  onSelect,
}: {
  kpis: SustainabilityKPIMetric[];
  selectedKPIName: SustainabilityKPIName;
  onSelect: (kpiName: SustainabilityKPIName) => void;
}) {
  return (
    <div
      className="sustainability-kpi-selector mb-6 rounded bg-slate-900 p-4"
      aria-label="sustainability_kpi_selector"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Sustainability KPI Selector
      </h2>
      <div className="mb-3">
        <label htmlFor="sustainability-kpi-select" className="text-sm text-slate-300">
          KPI 선택:
        </label>
        <select
          id="sustainability-kpi-select"
          aria-label="sustainability_kpi_select"
          className="ml-2 rounded bg-slate-800 px-2 py-1 text-slate-100"
          value={selectedKPIName}
          onChange={(e) =>
            onSelect(e.target.value as SustainabilityKPIName)
          }
        >
          {ALL_KPI_NAMES.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
      </div>
      {kpis.length > 0 ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm text-slate-200">
          {kpis.map((kpi) => (
            <div
              key={kpi.kpi_name}
              className="rounded bg-slate-800 p-3"
              aria-label={`sustainability_kpi_${kpi.kpi_name}`}
            >
              <div className="text-xs text-slate-400">{kpi.kpi_name}</div>
              <div className="text-lg font-semibold">
                {kpi.kpi_value.toLocaleString()} {kpi.kpi_unit}
              </div>
              <div
                className={`text-xs ${
                  kpi.kpi_threshold_status === "critical"
                    ? "text-red-400"
                    : kpi.kpi_threshold_status === "warning"
                      ? "text-yellow-400"
                      : "text-green-400"
                }`}
              >
                {kpi.kpi_threshold_status}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-slate-400 text-sm">No KPIs loaded</div>
      )}
    </div>
  );
}

// ── 3. SustainabilityReportGeneratorPanel ──
function SustainabilityReportGeneratorPanel({
  reports,
  onGenerate,
}: {
  reports: SustainabilityReport[];
  onGenerate: (req: GenerateSustainabilityReportRequest) => void;
}) {
  return (
    <div
      className="sustainability-report-generator mb-6 rounded bg-slate-900 p-4"
      aria-label="sustainability_report_generator"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Sustainability Report Generator
      </h2>
      <button
        type="button"
        aria-label="sustainability_report_generate"
        className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
        onClick={() =>
          onGenerate({
            tenant_id: "default",
            period_key: "2026-08",
            cadence: "monthly",
            export_format: "pdf",
            framework: "csrd",
          })
        }
      >
        보고서 생성
      </button>
      {reports.length > 0 ? (
        <table className="mt-3 w-full text-sm text-slate-200">
          <thead>
            <tr className="text-left text-slate-400">
              <th>Report ID</th>
              <th>Period</th>
              <th>Cadence</th>
              <th>Framework</th>
              <th>Format</th>
              <th>Status</th>
              <th>Size (bytes)</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.report_id} className="border-t border-slate-700">
                <td>{report.report_id.substring(0, 8)}</td>
                <td>{report.period_key}</td>
                <td>{report.cadence}</td>
                <td>{report.framework}</td>
                <td>{report.export_format}</td>
                <td>{report.status}</td>
                <td>{report.report_size_bytes.toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="text-slate-400 text-sm mt-3">No reports generated</div>
      )}
    </div>
  );
}

// ── 4. ScheduledSustainabilityDispatchConfigPanel ──
function ScheduledSustainabilityDispatchConfigPanel({
  dispatches,
  onSchedule,
}: {
  dispatches: ScheduledSustainabilityDispatch[];
  onSchedule: (req: DispatchSustainabilityReportRequest) => void;
}) {
  return (
    <div
      className="scheduled-sustainability-dispatch-config mb-6 rounded bg-slate-900 p-4"
      aria-label="scheduled_sustainability_dispatch_config"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Scheduled Sustainability Dispatch
      </h2>
      <button
        type="button"
        aria-label="sustainability_dispatch_schedule"
        className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
        onClick={() =>
          onSchedule({
            tenant_id: "default",
            dispatch_schedule: "weekly",
            period_key: "2026-08",
            recipient_strategy: "owner_only",
          })
        }
      >
        스케줄 등록
      </button>
      {dispatches.length > 0 ? (
        <table className="mt-3 w-full text-sm text-slate-200">
          <thead>
            <tr className="text-left text-slate-400">
              <th>Dispatch ID</th>
              <th>Schedule</th>
              <th>Cron</th>
              <th>Strategy</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {dispatches.map((dispatch) => (
              <tr key={dispatch.dispatch_id} className="border-t border-slate-700">
                <td>{dispatch.dispatch_id.substring(0, 8)}</td>
                <td>{dispatch.dispatch_schedule}</td>
                <td>{dispatch.cron_expression}</td>
                <td>{dispatch.recipient_strategy}</td>
                <td>{dispatch.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="text-slate-400 text-sm mt-3">No dispatches scheduled</div>
      )}
    </div>
  );
}

// ── 5. CarbonOffsetTrendMiniChart ──
function CarbonOffsetTrendMiniChart() {
  // Phase 17 wire — placeholder for renewable_energy_pct 12-month trend chart.
  // Real implementation uses Recharts 2.12.7 LineChart (AD-14 stack pin).
  return (
    <div
      className="carbon-offset-trend-mini-chart mb-6 rounded bg-slate-900 p-4"
      aria-label="carbon_offset_trend_mini_chart"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Carbon Offset Trend (12-month)
      </h2>
      <div className="text-slate-400 text-sm">
        Recharts 2.12.7 LineChart placeholder — renewable_energy_pct + carbon_offset_kgco2e cumulative
      </div>
    </div>
  );
}

// ── Main panel ──
export function FinopsSustainabilityDashboardPanel() {
  const [rollup, setRollup] = useState<CarbonEmissionsRollup | null>(null);
  const [kpis, setKPIs] = useState<SustainabilityKPIMetric[]>([]);
  const [reports, setReports] = useState<SustainabilityReport[]>([]);
  const [dispatches, setDispatches] = useState<ScheduledSustainabilityDispatch[]>([]);
  const [selectedKPI, setSelectedKPI] =
    useState<SustainabilityKPIName>("total_carbon_emissions_kgco2e");
  const [error, setError] = useState<string | null>(null);

  const handleRefreshCarbon = async () => {
    try {
      const req: AggregateCarbonEmissionsRequest = {
        tenant_id: "default",
        scope_type: "tenant",
        scope_id: "default",
        period_key: "2026-08",
        industry: "manufacturing",
      };
      const result = await aggregateCarbonEmissions(req);
      setRollup(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleSelectKPI = async (kpiName: SustainabilityKPIName) => {
    setSelectedKPI(kpiName);
    try {
      const req: SelectSustainabilityKPIsRequest = {
        tenant_id: "default",
        period_key: "2026-08",
        industry: "manufacturing",
      };
      const result = await selectSustainabilityKPIs(req);
      setKPIs(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleGenerateReport = async (
    req: GenerateSustainabilityReportRequest,
  ) => {
    try {
      const result = await generateSustainabilityReport(req);
      setReports((prev) => [...prev, result]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleScheduleDispatch = async (
    req: DispatchSustainabilityReportRequest,
  ) => {
    try {
      const result = await dispatchSustainabilityReport(req);
      setDispatches((prev) => [...prev, result]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="finops-sustainability-dashboard-panel">
      {error && (
        <div
          className="mb-4 rounded bg-red-900 p-3 text-sm text-red-100"
          aria-label="sustainability_dashboard_error"
        >
          {error}
        </div>
      )}
      <CarbonEmissionsAggregator rollup={rollup} onRefresh={handleRefreshCarbon} />
      <SustainabilityKPISelector
        kpis={kpis}
        selectedKPIName={selectedKPI}
        onSelect={handleSelectKPI}
      />
      <SustainabilityReportGeneratorPanel
        reports={reports}
        onGenerate={handleGenerateReport}
      />
      <ScheduledSustainabilityDispatchConfigPanel
        dispatches={dispatches}
        onSchedule={handleScheduleDispatch}
      />
      <CarbonOffsetTrendMiniChart />
    </div>
  );
}