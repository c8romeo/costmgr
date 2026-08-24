"use client";

/**
 * FinopsExecutiveDashboardPanel — Phase 16 FinOps Reporting & Executive Dashboard Client panel.
 *
 * Phase 16 (cj-style 127번째 wire) — FinOps Reporting & Executive Dashboard
 * territory (PRD §F32.6). 5 sub-components:
 * 1. ExecutiveDashboardAggregator — 4 scope_type (tenant/department/
 *    cost_center/product_line) + period selector (monthly/quarterly/
 *    annual) + 8 KPI metrics summary + 5-module breakdown.
 * 2. CrossModuleKPISelector — 8 KPI toggle selectbox (total_monthly_
 *    cost_krw + monthly_cost_growth_pct + cost_per_employee_krw +
 *    cost_anomaly_count_30d + forecast_deviation_pct + idle_cost_monthly_
 *    krw + tag_compliance_pct + optimization_realized_savings_krw) +
 *    KPI delta arrow + trend chart mini.
 * 3. ExecutiveReportGeneratorPanel — 3 cadence (monthly/quarterly/
 *    annual) + 3 export_format (PDF/CSV/Excel) + generate button +
 *    recent reports list table.
 * 4. ScheduledDispatchConfigPanel — 4 cron schedules (weekly/monthly/
 *    quarterly/annual) + 4 recipient strategies (owner_only/
 *    executive_team/board_observers/custom_recipients) + enable/disable
 *    + test_dispatch dry-run.
 * 5. ComplianceTrendMiniChart — tag_compliance_pct 12-month trend
 *    (Phase 15 ComplianceReportPanel EXTENSION 정합).
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops-reporting/finops-reporting-client.ts`.
 */

import { useState } from "react";
import {
  fetchExecutiveRollup,
  fetchCrossModuleKPIs,
  generateExecutiveReport,
  scheduleExecutiveDispatch,
  fetchComplianceTrend,
  type ExecutiveRollup,
  type KPIMetric,
  type KPIName,
  type ExecutiveReport,
  type ScheduledDispatch,
  type ComplianceTrendPoint,
} from "@/lib/finops-reporting/finops-reporting-client";

const ALL_KPI_NAMES: KPIName[] = [
  "total_monthly_cost_krw",
  "monthly_cost_growth_pct",
  "cost_per_employee_krw",
  "cost_anomaly_count_30d",
  "forecast_deviation_pct",
  "idle_cost_monthly_krw",
  "tag_compliance_pct",
  "optimization_realized_savings_krw",
];

// ── 1. ExecutiveDashboardAggregator ──
function ExecutiveDashboardAggregator({
  rollup,
  onRefresh,
}: {
  rollup: ExecutiveRollup | null;
  onRefresh: () => void;
}) {
  return (
    <div className="executive-dashboard-aggregator mb-6 rounded bg-slate-900 p-4">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-slate-100">
          Executive Dashboard Aggregator
        </h2>
        <button
          type="button"
          aria-label="executive_dashboard_refresh"
          className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
          onClick={onRefresh}
        >
          새로고침
        </button>
      </div>
      {rollup ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm text-slate-200">
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Showback Total (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.showback_total_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Anomaly Count (30d)</div>
            <div className="text-lg font-semibold">{rollup.anomaly_count_30d}</div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">
              Forecast Projection (KRW)
            </div>
            <div className="text-lg font-semibold">
              {rollup.forecast_projection_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">
              Optimization Savings (KRW)
            </div>
            <div className="text-lg font-semibold">
              {rollup.optimization_savings_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Tag Compliance %</div>
            <div className="text-lg font-semibold">
              {rollup.tag_compliance_pct.toFixed(2)}%
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Idle Cost (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.idle_cost_krw.toLocaleString()}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-slate-400">대시보드 데이터 없음</div>
      )}
    </div>
  );
}

// ── 2. CrossModuleKPISelector ──
function CrossModuleKPISelector({
  kpis,
  enabledKpis,
  onToggle,
}: {
  kpis: KPIMetric[];
  enabledKpis: Set<KPIName>;
  onToggle: (kpi: KPIName) => void;
}) {
  return (
    <div className="cross-module-kpi-selector mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Cross-Module KPI Selector
      </h2>
      <div className="flex flex-wrap gap-2 mb-3">
        {ALL_KPI_NAMES.map((name) => (
          <button
            type="button"
            key={name}
            aria-label={`kpi_toggle_${name}`}
            className={`rounded px-2 py-1 text-xs ${
              enabledKpis.has(name)
                ? "bg-emerald-600 text-white"
                : "bg-slate-700 text-slate-300"
            }`}
            onClick={() => onToggle(name)}
          >
            {name}
          </button>
        ))}
      </div>
      <table className="w-full text-sm text-slate-200">
        <thead>
          <tr className="text-left">
            <th className="p-2">KPI</th>
            <th className="p-2">값</th>
            <th className="p-2">단위</th>
            <th className="p-2">변화</th>
            <th className="p-2">추세</th>
            <th className="p-2">상태</th>
          </tr>
        </thead>
        <tbody>
          {kpis
            .filter((k) => enabledKpis.has(k.kpi_name))
            .map((k) => (
              <tr key={k.kpi_id} className="border-t border-slate-700">
                <td className="p-2">{k.kpi_name}</td>
                <td className="p-2">{k.kpi_value.toLocaleString()}</td>
                <td className="p-2">{k.kpi_unit}</td>
                <td className="p-2">
                  {k.kpi_delta !== null ? k.kpi_delta.toFixed(2) : "—"}
                </td>
                <td className="p-2">
                  {k.kpi_trend === "up"
                    ? "▲"
                    : k.kpi_trend === "down"
                      ? "▼"
                      : "—"}
                </td>
                <td className="p-2">{k.kpi_threshold_status}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 3. ExecutiveReportGeneratorPanel ──
function ExecutiveReportGeneratorPanel({
  reports,
  onGenerate,
}: {
  reports: ExecutiveReport[];
  onGenerate: (
    cadence: "monthly" | "quarterly" | "annual",
    exportFormat: "pdf" | "csv" | "excel",
  ) => void;
}) {
  const [cadence, setCadence] = useState<"monthly" | "quarterly" | "annual">(
    "monthly",
  );
  const [exportFormat, setExportFormat] = useState<"pdf" | "csv" | "excel">(
    "pdf",
  );

  return (
    <div className="executive-report-generator-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Executive Report Generator
      </h2>
      <div className="flex flex-wrap gap-2 mb-3">
        {(["monthly", "quarterly", "annual"] as const).map((c) => (
          <label
            key={c}
            className="flex items-center gap-1 text-sm text-slate-200"
          >
            <input
              type="radio"
              name="cadence"
              aria-label={`cadence_${c}`}
              checked={cadence === c}
              onChange={() => setCadence(c)}
            />
            {c}
          </label>
        ))}
      </div>
      <div className="flex flex-wrap gap-2 mb-3">
        {(["pdf", "csv", "excel"] as const).map((f) => (
          <label
            key={f}
            className="flex items-center gap-1 text-sm text-slate-200"
          >
            <input
              type="radio"
              name="format"
              aria-label={`format_${f}`}
              checked={exportFormat === f}
              onChange={() => setExportFormat(f)}
            />
            {f.toUpperCase()}
          </label>
        ))}
      </div>
      <button
        type="button"
        aria-label="generate_executive_report"
        className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
        onClick={() => onGenerate(cadence, exportFormat)}
      >
        리포트 생성
      </button>
      <table className="w-full text-sm text-slate-200 mt-3">
        <thead>
          <tr className="text-left">
            <th className="p-2">report_id</th>
            <th className="p-2">cadence</th>
            <th className="p-2">format</th>
            <th className="p-2">size</th>
            <th className="p-2">status</th>
          </tr>
        </thead>
        <tbody>
          {reports.map((r) => (
            <tr key={r.report_id} className="border-t border-slate-700">
              <td className="p-2">{r.report_id.slice(0, 8)}</td>
              <td className="p-2">{r.cadence}</td>
              <td className="p-2">{r.export_format}</td>
              <td className="p-2">{r.report_size_bytes}</td>
              <td className="p-2">{r.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 4. ScheduledDispatchConfigPanel ──
function ScheduledDispatchConfigPanel({
  dispatches,
  onSchedule,
}: {
  dispatches: ScheduledDispatch[];
  onSchedule: (
    schedule: "weekly" | "monthly" | "quarterly" | "annual",
    strategy:
      | "owner_only"
      | "executive_team"
      | "board_observers"
      | "custom_recipients",
  ) => void;
}) {
  return (
    <div className="scheduled-dispatch-config-panel mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Scheduled Dispatch Config
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        <div>
          <label className="block text-xs text-slate-400 mb-1">Schedule</label>
          <select
            aria-label="dispatch_schedule_select"
            className="w-full rounded bg-slate-800 text-slate-200 p-2"
            defaultValue="monthly"
          >
            <option value="weekly">weekly (월요일 09:00 KST)</option>
            <option value="monthly">monthly (1일 09:00 KST)</option>
            <option value="quarterly">quarterly (1일 09:00 KST)</option>
            <option value="annual">annual (1월 1일 09:00 KST)</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-slate-400 mb-1">Recipient</label>
          <select
            aria-label="dispatch_recipient_select"
            className="w-full rounded bg-slate-800 text-slate-200 p-2"
            defaultValue="owner_only"
          >
            <option value="owner_only">owner_only</option>
            <option value="executive_team">executive_team</option>
            <option value="board_observers">board_observers</option>
            <option value="custom_recipients">custom_recipients</option>
          </select>
        </div>
      </div>
      <button
        type="button"
        aria-label="schedule_test_dispatch"
        className="rounded bg-emerald-600 px-3 py-1 text-white hover:bg-emerald-700"
        onClick={() => onSchedule("monthly", "owner_only")}
      >
        테스트 발송 (Dry-run)
      </button>
      <table className="w-full text-sm text-slate-200 mt-3">
        <thead>
          <tr className="text-left">
            <th className="p-2">dispatch_id</th>
            <th className="p-2">schedule</th>
            <th className="p-2">strategy</th>
            <th className="p-2">status</th>
          </tr>
        </thead>
        <tbody>
          {dispatches.map((d) => (
            <tr key={d.dispatch_id} className="border-t border-slate-700">
              <td className="p-2">{d.dispatch_id.slice(0, 8)}</td>
              <td className="p-2">{d.dispatch_schedule}</td>
              <td className="p-2">{d.recipient_strategy}</td>
              <td className="p-2">{d.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ── 5. ComplianceTrendMiniChart ──
function ComplianceTrendMiniChart({
  trend,
}: {
  trend: ComplianceTrendPoint[];
}) {
  if (trend.length === 0) {
    return (
      <div className="compliance-trend-mini-chart mb-6 rounded bg-slate-900 p-4">
        <h2 className="text-lg font-semibold text-slate-100 mb-3">
          Compliance Trend (12개월)
        </h2>
        <div className="text-slate-400">트렌드 데이터 없음</div>
      </div>
    );
  }

  const maxPct = Math.max(...trend.map((t) => t.tag_compliance_pct), 100);
  const minPct = Math.min(...trend.map((t) => t.tag_compliance_pct), 0);

  return (
    <div className="compliance-trend-mini-chart mb-6 rounded bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Compliance Trend (12개월)
      </h2>
      <div className="flex items-end gap-1 h-32" aria-label="compliance_trend_chart">
        {trend.map((t) => {
          const heightPct =
            maxPct === minPct
              ? 100
              : ((t.tag_compliance_pct - minPct) / (maxPct - minPct)) * 100;
          return (
            <div
              key={t.period_key}
              className="flex-1 flex flex-col items-center"
              title={`${t.period_key}: ${t.tag_compliance_pct.toFixed(2)}%`}
            >
              <div
                className="w-full bg-emerald-600 rounded-t"
                style={{ height: `${heightPct}%` }}
              />
              <div className="text-[10px] text-slate-400 mt-1">
                {t.period_key.slice(-5)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main panel ──
export function FinopsExecutiveDashboardPanel() {
  const [rollup, setRollup] = useState<ExecutiveRollup | null>(null);
  const [kpis, setKpis] = useState<KPIMetric[]>([]);
  const [reports, setReports] = useState<ExecutiveReport[]>([]);
  const [dispatches, setDispatches] = useState<ScheduledDispatch[]>([]);
  const [trend, setTrend] = useState<ComplianceTrendPoint[]>([]);
  const [enabledKpis, setEnabledKpis] = useState<Set<KPIName>>(
    new Set(ALL_KPI_NAMES),
  );

  async function handleRefresh() {
    try {
      const r = await fetchExecutiveRollup("tenant", "", "");
      setRollup(r);
      const k = await fetchCrossModuleKPIs("tenant", "", "");
      setKpis(k.kpis);
      const t = await fetchComplianceTrend("tenant", "");
      setTrend(t.trend);
    } catch (err) {
      console.error("executive_dashboard_refresh_failed", err);
    }
  }

  async function handleGenerate(
    cadence: "monthly" | "quarterly" | "annual",
    exportFormat: "pdf" | "csv" | "excel",
  ) {
    try {
      const report = await generateExecutiveReport(
        "tenant",
        "",
        "",
        cadence,
        exportFormat,
      );
      setReports((prev) => [report, ...prev]);
    } catch (err) {
      console.error("executive_report_generate_failed", err);
    }
  }

  async function handleSchedule(
    schedule: "weekly" | "monthly" | "quarterly" | "annual",
    strategy:
      | "owner_only"
      | "executive_team"
      | "board_observers"
      | "custom_recipients",
  ) {
    try {
      const dispatch = await scheduleExecutiveDispatch(schedule, strategy);
      setDispatches((prev) => [dispatch, ...prev]);
    } catch (err) {
      console.error("scheduled_dispatch_failed", err);
    }
  }

  function handleToggleKpi(kpi: KPIName) {
    setEnabledKpis((prev) => {
      const next = new Set(prev);
      if (next.has(kpi)) {
        next.delete(kpi);
      } else {
        next.add(kpi);
      }
      return next;
    });
  }

  return (
    <section
      aria-label="finops_executive_dashboard_panel"
      className="finops-executive-dashboard-panel"
    >
      <h1 className="text-2xl font-bold text-slate-100 mb-4">
        FinOps Reporting & Executive Dashboard
      </h1>
      <p className="text-sm text-slate-400 mb-4">
        소유자 전용 — Epic 12 2FA 챌린지 필요
      </p>
      <ExecutiveDashboardAggregator rollup={rollup} onRefresh={handleRefresh} />
      <CrossModuleKPISelector
        kpis={kpis}
        enabledKpis={enabledKpis}
        onToggle={handleToggleKpi}
      />
      <ExecutiveReportGeneratorPanel
        reports={reports}
        onGenerate={handleGenerate}
      />
      <ScheduledDispatchConfigPanel
        dispatches={dispatches}
        onSchedule={handleSchedule}
      />
      <ComplianceTrendMiniChart trend={trend} />
    </section>
  );
}

export default FinopsExecutiveDashboardPanel;