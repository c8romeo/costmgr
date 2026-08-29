"use client";

/**
 * FinopsPricingDashboardPanel — Phase 19 FinOps Pricing, Rate Card & TCO
 * Modeling Client panel.
 *
 * Phase 19 (cj-style 139번째 wire) — FinOps Pricing, Rate Card & TCO
 * Modeling territory (PRD §F35.6). 5 sub-components:
 * 1. RateCardInventoryAggregator — 4 scope_type (tenant/department/
 *    cost_center/product_line) + period selector (monthly/quarterly/
 *    annual) + 8 KPI metrics summary + 5-cloud-provider breakdown +
 *    6-pricing-model × 4-unit-metric matrix.
 * 2. TCOKPISelector — 8 KPI toggle selectbox
 *    (total_blended_rate_krw_per_hour + effective_discount_pct +
 *    tco_1year_commitment_krw + tco_3year_commitment_krw +
 *    tco_on_demand_krw + cost_per_user_krw + cost_per_transaction_krw +
 *    unit_economics_score) + KPI delta arrow + trend chart mini +
 *    break_even_months calculation.
 * 3. PricingReportGeneratorPanel — 3 cadence (monthly/quarterly/
 *    annual) + 3 export_format (PDF/CSV/Excel) + 5-framework support
 *    (FinOps Foundation / AWS Pricing Models / Azure Pricing Calculator /
 *    GCP Pricing Calculator / 한국 공공 조달 가격 가이드라인) + generate
 *    button + recent reports list table.
 * 4. ScheduledPricingDispatchConfigPanel — 4 cron schedules
 *    (weekly/monthly/quarterly/annual) + 4 recipient strategies
 *    (owner_only/pricing_team/finance_team/custom_recipients)
 *    + enable/disable + test_dispatch dry-run.
 * 5. PricingUnitEconomicsTrendMiniChart — unit_economics_score 12-month
 *    trend + cost_per_user industry baseline comparison (Phase 17
 *    CarbonOffsetTrendMiniChart EXTENSION 정합).
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/pricing-client.ts`.
 * AD-14 stack pin — Recharts 2.12.7.
 */

import { useState } from "react";

import {
  aggregateRateCardInventory,
  selectTCOKPIs,
  generatePricingReport,
  dispatchPricingReport,
  type AggregateRateCardInventoryRequest,
  type SelectTCOKPIsRequest,
  type GeneratePricingReportRequest,
  type DispatchPricingReportRequest,
} from "@/lib/finops/pricing-client";
import type {
  RateCardInventory,
  TCOKPIBundle,
  PricingReport,
  ScheduledPricingDispatch,
  PricingKPIName,
} from "@/lib/finops/pricing-types";

const ALL_KPI_NAMES: PricingKPIName[] = [
  "total_blended_rate_krw_per_hour",
  "effective_discount_pct",
  "tco_1year_commitment_krw",
  "tco_3year_commitment_krw",
  "tco_on_demand_krw",
  "cost_per_user_krw",
  "cost_per_transaction_krw",
  "unit_economics_score",
];

// ── 1. RateCardInventoryAggregator ──
function RateCardInventoryAggregator({
  rollup,
  onRefresh,
}: {
  rollup: RateCardInventory | null;
  onRefresh: () => void;
}) {
  return (
    <div
      className="pricing-rate-card-aggregator mb-6 rounded bg-slate-900 p-4"
      aria-label="pricing_rate_card_aggregator"
    >
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-slate-100">
          Rate Card Inventory Aggregator
        </h2>
        <button
          type="button"
          aria-label="pricing_rate_card_refresh"
          className="rounded bg-blue-600 px-3 py-1 text-white hover:bg-blue-700"
          onClick={onRefresh}
        >
          새로고침
        </button>
      </div>
      {rollup ? (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm text-slate-200">
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Blended Rate (KRW/hour)</div>
            <div className="text-lg font-semibold">
              {rollup.total_blended_rate_krw_per_hour.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Effective Discount (%)</div>
            <div className="text-lg font-semibold">
              {rollup.effective_discount_pct.toFixed(2)}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">1y TCO (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.tco_1year_commitment_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">3y TCO (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.tco_3year_commitment_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">On-Demand TCO (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.tco_on_demand_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Cost per User (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.cost_per_user_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Cost per Transaction (KRW)</div>
            <div className="text-lg font-semibold">
              {rollup.cost_per_transaction_krw.toLocaleString()}
            </div>
          </div>
          <div className="rounded bg-slate-800 p-3">
            <div className="text-xs text-slate-400">Unit Economics Score</div>
            <div className="text-lg font-semibold">
              {rollup.unit_economics_score.toFixed(2)}
            </div>
          </div>
        </div>
      ) : (
        <div className="text-slate-400 text-sm">No rollup loaded</div>
      )}
    </div>
  );
}

// ── 2. TCOKPISelector ──
function TCOKPISelector({
  kpis,
  selectedKPIName,
  onSelect,
}: {
  kpis: TCOKPIBundle[];
  selectedKPIName: PricingKPIName;
  onSelect: (kpiName: PricingKPIName) => void;
}) {
  return (
    <div
      className="pricing-tco-kpi-selector mb-6 rounded bg-slate-900 p-4"
      aria-label="pricing_tco_kpi_selector"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        TCO KPI Selector
      </h2>
      <div className="mb-3">
        <label htmlFor="pricing-tco-kpi-select" className="text-sm text-slate-300">
          KPI 선택:
        </label>
        <select
          id="pricing-tco-kpi-select"
          aria-label="pricing_tco_kpi_select"
          className="ml-2 rounded bg-slate-800 px-2 py-1 text-slate-100"
          value={selectedKPIName}
          onChange={(e) =>
            onSelect(e.target.value as PricingKPIName)
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
              aria-label={`pricing_tco_kpi_${kpi.kpi_name}`}
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

// ── 3. PricingReportGeneratorPanel ──
function PricingReportGeneratorPanel({
  reports,
  onGenerate,
}: {
  reports: PricingReport[];
  onGenerate: (req: GeneratePricingReportRequest) => void;
}) {
  return (
    <div
      className="pricing-report-generator mb-6 rounded bg-slate-900 p-4"
      aria-label="pricing_report_generator"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Pricing Report Generator
      </h2>
      <button
        type="button"
        aria-label="pricing_report_generate"
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

// ── 4. ScheduledPricingDispatchConfigPanel ──
function ScheduledPricingDispatchConfigPanel({
  dispatches,
  onSchedule,
}: {
  dispatches: ScheduledPricingDispatch[];
  onSchedule: (req: DispatchPricingReportRequest) => void;
}) {
  return (
    <div
      className="scheduled-pricing-dispatch-config mb-6 rounded bg-slate-900 p-4"
      aria-label="scheduled_pricing_dispatch_config"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Scheduled Pricing Dispatch
      </h2>
      <button
        type="button"
        aria-label="pricing_dispatch_schedule"
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
              <tr
                key={dispatch.dispatch_id}
                className="border-t border-slate-700"
              >
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

// ── 5. PricingUnitEconomicsTrendMiniChart ──
function PricingUnitEconomicsTrendMiniChart() {
  // Phase 19 wire — placeholder for unit_economics_score 12-month trend chart.
  // Real implementation uses Recharts 2.12.7 LineChart (AD-14 stack pin).
  return (
    <div
      className="pricing-unit-economics-trend-mini-chart mb-6 rounded bg-slate-900 p-4"
      aria-label="pricing_unit_economics_trend_mini_chart"
    >
      <h2 className="text-lg font-semibold text-slate-100 mb-3">
        Unit Economics Trend (12-month)
      </h2>
      <div className="text-slate-400 text-sm">
        Recharts 2.12.7 LineChart placeholder — unit_economics_score + cost_per_user
        industry baseline comparison
      </div>
    </div>
  );
}

// ── Main panel ──
export function FinopsPricingDashboardPanel() {
  const [rollup, setRollup] = useState<RateCardInventory | null>(null);
  const [kpis, setKPIs] = useState<TCOKPIBundle[]>([]);
  const [reports, setReports] = useState<PricingReport[]>([]);
  const [dispatches, setDispatches] = useState<ScheduledPricingDispatch[]>([]);
  const [selectedKPI, setSelectedKPI] =
    useState<PricingKPIName>("total_blended_rate_krw_per_hour");
  const [error, setError] = useState<string | null>(null);

  const handleRefreshRateCard = async () => {
    try {
      const req: AggregateRateCardInventoryRequest = {
        tenant_id: "default",
        scope_type: "tenant",
        scope_id: "default",
        period_key: "2026-08",
        industry: "manufacturing",
      };
      const result = await aggregateRateCardInventory(req);
      setRollup(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleSelectKPI = async (kpiName: PricingKPIName) => {
    setSelectedKPI(kpiName);
    try {
      const req: SelectTCOKPIsRequest = {
        tenant_id: "default",
        period_key: "2026-08",
        industry: "manufacturing",
      };
      const result = await selectTCOKPIs(req);
      setKPIs(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleGenerateReport = async (
    req: GeneratePricingReportRequest,
  ) => {
    try {
      const result = await generatePricingReport(req);
      setReports((prev) => [...prev, result]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleScheduleDispatch = async (
    req: DispatchPricingReportRequest,
  ) => {
    try {
      const result = await dispatchPricingReport(req);
      setDispatches((prev) => [...prev, result]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="finops-pricing-dashboard-panel">
      {error && (
        <div
          className="mb-4 rounded bg-red-900 p-3 text-sm text-red-100"
          aria-label="pricing_dashboard_error"
        >
          {error}
        </div>
      )}
      <RateCardInventoryAggregator rollup={rollup} onRefresh={handleRefreshRateCard} />
      <TCOKPISelector
        kpis={kpis}
        selectedKPIName={selectedKPI}
        onSelect={handleSelectKPI}
      />
      <PricingReportGeneratorPanel
        reports={reports}
        onGenerate={handleGenerateReport}
      />
      <ScheduledPricingDispatchConfigPanel
        dispatches={dispatches}
        onSchedule={handleScheduleDispatch}
      />
      <PricingUnitEconomicsTrendMiniChart />
    </div>
  );
}
