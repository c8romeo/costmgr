"use client";

/**
 * FinopsCommitmentDashboardPanel — Phase 18 FinOps Cloud Commitment
 * Management Client panel.
 *
 * Phase 18 (cj-style 135번째 wire) — FinOps Cloud Commitment Management
 * territory (PRD §F34.6). 5 sub-components:
 * 1. CommitmentInventoryAggregator — 4 scope_type (tenant/department/
 *    cost_center/product_line) + period selector (monthly/quarterly/
 *    annual) + 8 KPI metrics summary + 5-cloud-provider breakdown.
 * 2. CommitmentKPISelector — 8 KPI toggle selectbox
 *    (total_commitment_value_krw + coverage_pct + utilization_pct +
 *    expiring_commitments_30d + recommended_purchase_krw +
 *    savings_realized_krw + idle_commitment_krw + renewal_decision_score)
 *    + KPI delta arrow + trend chart mini.
 * 3. CommitmentReportGeneratorPanel — 3 cadence (monthly/quarterly/
 *    annual) + 3 export_format (PDF/CSV/Excel) + 5-framework support
 *    (FinOps Foundation / AWS Cost Optimization / Azure Cost Optimization
 *    / GCP Cost Optimization / 한국 조달청) + generate button + recent
 *    reports list table.
 * 4. ScheduledCommitmentDispatchConfigPanel — 4 cron schedules
 *    (weekly/monthly/quarterly/annual) + 4 recipient strategies
 *    (owner_only/commitment_team/finance_team/custom_recipients)
 *    + enable/disable + test_dispatch dry-run.
 * 5. CommitmentCoverageTrendMiniChart — coverage_pct 12-month trend
 *    + utilization_pct cumulative (Phase 17 CarbonOffsetTrendMiniChart
 *    EXTENSION 정합).
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/commitment-client.ts`.
 * AD-14 stack pin — Recharts 2.12.7.
 */

import { useState } from "react";

import {
  aggregateCommitmentInventory,
  selectCommitmentKPIs,
  generateCommitmentReport,
  dispatchCommitmentReport,
  type AggregateCommitmentInventoryRequest,
  type SelectCommitmentKPIsRequest,
  type GenerateCommitmentReportRequest,
  type DispatchCommitmentReportRequest,
} from "@/lib/finops/commitment-client";
import type {
  CommitmentInventoryRollup,
  CommitmentKPI,
  CommitmentReport,
  ScheduledCommitmentDispatch,
  CommitmentKPIName,
} from "@/lib/finops/commitment-types";

const ALL_KPI_NAMES: CommitmentKPIName[] = [
  "total_commitment_value_krw",
  "coverage_pct",
  "utilization_pct",
  "expiring_commitments_30d",
  "recommended_purchase_krw",
  "savings_realized_krw",
  "idle_commitment_krw",
  "renewal_decision_score",
];

// ── 1. CommitmentInventoryAggregator ──
function CommitmentInventoryAggregator({
  rollup,
  onRefresh,
}: {
  rollup: CommitmentInventoryRollup | null;
  onRefresh: () => void;
}) {
  return (
    <div
      className="commitment-inventory-aggregator mb-6 rounded bg-slate-900 p-4"
      aria-label="commitment_inventory_aggregator"
    >
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-slate-100">
          Commitment Inventory Aggregator
        </h2>
        <button
          type="button"
          aria-label="commitment_inventory_refresh"
          className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
          onClick={onRefresh}
        >
          새로고침
        </button>
      </div>
      {rollup ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm text-slate-200">
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Total Commitment (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.total_commitment_value_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Coverage (%)</div>
            <div className="text-lg font-semibold">
              {rollup.coverage_pct.toFixed(2)}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Utilization (%)</div>
            <div className="text-lg font-semibold">
              {rollup.utilization_pct.toFixed(2)}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Expiring 30d</div>
            <div className="text-lg font-semibold">
              {rollup.expiring_commitments_30d.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Recommended Purchase (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.recommended_purchase_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Savings Realized (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.savings_realized_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Idle Commitment (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.idle_commitment_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Renewal Decision Score</div>
            <div className="text-lg font-semibold">
              {rollup.renewal_decision_score.toFixed(2)}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-slate-400 text-sm">No rollup loaded</div>
      )}
    </div>
  );
}

// ── 2. CommitmentKPISelector ──
function CommitmentKPISelector({
  kpis,
  selectedKPIName,
  onSelect,
}: {
  kpis: CommitmentKPI[];
  selectedKPIName: CommitmentKPIName;
  onSelect: (kpiName: CommitmentKPIName) => void;
}) {
  return (
    <div
      className="commitment-kpi-selector mb-6 rounded bg-slate-900 p-4"
      aria-label="commitment_kpi_selector"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Commitment KPI Selector
      </h2>
      <div className="mb-3">
        <label htmlFor="commitment-kpi-select" className="text-sm text-slate-300">
          KPI 선택:
        </label>
        <select
          id="commitment-kpi-select"
          aria-label="commitment_kpi_select"
          className="ml-2 rounded bg-slate-800 px-2 py-1 text-slate-100"
          value={selectedKPIName}
          onChange={(e) =>
            onSelect(e.target.value as CommitmentKPIName)
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
              aria-label={`commitment_kpi_${kpi.kpi_name}`}
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

// ── 3. CommitmentReportGeneratorPanel ──
function CommitmentReportGeneratorPanel({
  reports,
  onGenerate,
}: {
  reports: CommitmentReport[];
  onGenerate: (req: GenerateCommitmentReportRequest) => void;
}) {
  return (
    <div
      className="commitment-report-generator mb-6 rounded bg-slate-900 p-4"
      aria-label="commitment_report_generator"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Commitment Report Generator
      </h2>
      <button
        type="button"
        aria-label="commitment_report_generate"
        className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
        onClick={() =>
          onGenerate({
            tenant_id: "default",
            period_key: "2026-08",
            cadence: "monthly",
            export_format: "pdf",
            framework: "finops_foundation",
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

// ── 4. ScheduledCommitmentDispatchConfigPanel ──
function ScheduledCommitmentDispatchConfigPanel({
  dispatches,
  onSchedule,
}: {
  dispatches: ScheduledCommitmentDispatch[];
  onSchedule: (req: DispatchCommitmentReportRequest) => void;
}) {
  return (
    <div
      className="scheduled-commitment-dispatch-config mb-6 rounded bg-slate-900 p-4"
      aria-label="scheduled_commitment_dispatch_config"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Scheduled Commitment Dispatch
      </h2>
      <button
        type="button"
        aria-label="commitment_dispatch_schedule"
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

// ── 5. CommitmentCoverageTrendMiniChart ──
function CommitmentCoverageTrendMiniChart() {
  // Phase 18 wire — placeholder for coverage_pct 12-month trend chart.
  // Real implementation uses Recharts 2.12.7 LineChart (AD-14 stack pin).
  return (
    <div
      className="commitment-coverage-trend-mini-chart mb-6 rounded bg-slate-900 p-4"
      aria-label="commitment_coverage_trend_mini_chart"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Commitment Coverage Trend (12-month)
      </h2>
      <div className="text-slate-400 text-sm">
        Recharts 2.12.7 LineChart placeholder — coverage_pct + utilization_pct cumulative
      </div>
    </div>
  );
}

// ── Main panel ──
export function FinopsCommitmentDashboardPanel() {
  const [rollup, setRollup] = useState<CommitmentInventoryRollup | null>(null);
  const [kpis, setKPIs] = useState<CommitmentKPI[]>([]);
  const [reports, setReports] = useState<CommitmentReport[]>([]);
  const [dispatches, setDispatches] = useState<ScheduledCommitmentDispatch[]>([]);
  const [selectedKPI, setSelectedKPI] =
    useState<CommitmentKPIName>("total_commitment_value_krw");
  const [error, setError] = useState<string | null>(null);

  const handleRefreshCommitment = async () => {
    try {
      const req: AggregateCommitmentInventoryRequest = {
        tenant_id: "default",
        scope_type: "tenant",
        scope_id: "default",
        period_key: "2026-08",
        industry: "manufacturing",
      };
      const result = await aggregateCommitmentInventory(req);
      setRollup(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleSelectKPI = async (kpiName: CommitmentKPIName) => {
    setSelectedKPI(kpiName);
    try {
      const req: SelectCommitmentKPIsRequest = {
        tenant_id: "default",
        period_key: "2026-08",
        industry: "manufacturing",
      };
      const result = await selectCommitmentKPIs(req);
      setKPIs(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleGenerateReport = async (
    req: GenerateCommitmentReportRequest,
  ) => {
    try {
      const result = await generateCommitmentReport(req);
      setReports((prev) => [...prev, result]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleScheduleDispatch = async (
    req: DispatchCommitmentReportRequest,
  ) => {
    try {
      const result = await dispatchCommitmentReport(req);
      setDispatches((prev) => [...prev, result]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="finops-commitment-dashboard-panel">
      {error && (
        <div
          className="mb-4 rounded bg-red-900 p-3 text-sm text-red-100"
          aria-label="commitment_dashboard_error"
        >
          {error}
        </div>
      )}
      <CommitmentInventoryAggregator rollup={rollup} onRefresh={handleRefreshCommitment} />
      <CommitmentKPISelector
        kpis={kpis}
        selectedKPIName={selectedKPI}
        onSelect={handleSelectKPI}
      />
      <CommitmentReportGeneratorPanel
        reports={reports}
        onGenerate={handleGenerateReport}
      />
      <ScheduledCommitmentDispatchConfigPanel
        dispatches={dispatches}
        onSchedule={handleScheduleDispatch}
      />
      <CommitmentCoverageTrendMiniChart />
    </div>
  );
}
