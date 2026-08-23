"use client";

/**
 * apps/web/components/finops/FinopsDashboardPanel.tsx —
 * Phase 11 T7 (cj-style 107번째 wire) — Client orchestrator for the
 * FinOps Showback / Chargeback admin dashboard.
 *
 * 4 panels in one dashboard (PRD §F27.1 + §F27.2 + §F27.3 + §F27.5):
 *   - ShowbackBreakdown — department breakdown with period selector
 *   - ShowbackComparison — current vs previous comparison
 *   - ChargebackResults — calculated chargeback amounts
 *   - DepartmentMappings — department ↔ cost_center mapping
 *
 * All access is gated through `require_finops_showback` +
 * `require_finops_chargeback` capabilities (CR 12-5 D-GATE-01 inversion)
 * + owner-only RBAC at the backend (AD-22 verbatim for showback
 * generation + department mapping update + chargeback calculation +
 * CSV/PDF export).
 */
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  exportChargeback,
  listChargebackResults,
  listDepartmentMappings,
  listShowbackBreakdown,
  listShowbackComparison,
  type ChargebackResult,
  type ComparisonView,
  type DepartmentBreakdown,
  type DepartmentCostCenterMapping,
  type ExportFormat,
  type PeriodMode,
  type ShowbackDefinition,
} from "@/lib/finops/finops-client";

interface Props {
  accessToken: string;
  locale: string;
}

const PERIOD_MODES: PeriodMode[] = [
  "current_month",
  "previous_month",
  "last_3_months",
  "last_6_months",
  "ytd",
  "custom_range",
];

export function FinopsDashboardPanel({ accessToken, locale }: Props) {
  const router = useRouter();
  const [breakdown, setBreakdown] = useState<DepartmentBreakdown[]>([]);
  const [comparison, setComparison] = useState<ComparisonView[]>([]);
  const [chargeback, setChargeback] = useState<ChargebackResult[]>([]);
  const [mappings, setMappings] = useState<DepartmentCostCenterMapping[]>([]);
  const [periodMode, setPeriodMode] = useState<PeriodMode>("current_month");
  const [periodKey, setPeriodKey] = useState<string>("2026-08");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState<ExportFormat | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    const definition: ShowbackDefinition = {
      tenant_id: "",
      group_by: "department",
      period_mode: periodMode,
      currency_code: "KRW",
      comparison_period: "previous_month",
      governance_required: true,
    };
    void Promise.all([
      listShowbackBreakdown(definition, { accessToken, locale }),
      listShowbackComparison(definition, { accessToken, locale }),
      listChargebackResults(periodKey, { accessToken, locale }),
      listDepartmentMappings({ accessToken, locale }),
    ])
      .then(([bd, cmp, cb, mp]) => {
        if (cancelled) return;
        setBreakdown(bd.items);
        setComparison(cmp.items);
        setChargeback(cb.items);
        setMappings(mp.items);
        setLoading(false);
      })
      .catch(() => {
        if (cancelled) return;
        setError("finops.error_load_failed");
        setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [accessToken, locale, periodMode, periodKey]);

  const handleExport = async (format: ExportFormat) => {
    setExporting(format);
    try {
      const blob = await exportChargeback(periodKey, format, {
        accessToken,
        locale,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `chargeback-${periodKey}.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("finops.error_export_failed");
    } finally {
      setExporting(null);
    }
  };

  return (
    <div className="finops-dashboard" data-testid="finops-dashboard">
      <header>
        <h1 data-testid="finops-title">FinOps Showback / Chargeback</h1>
        <p data-testid="finops-subtitle">showback_report + chargeback dashboard</p>
      </header>

      <section data-testid="period-selector">
        <label htmlFor="period-mode">Period</label>
        <select
          id="period-mode"
          value={periodMode}
          onChange={(e) => setPeriodMode(e.target.value as PeriodMode)}
          data-testid="period-select"
        >
          {PERIOD_MODES.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
      </section>

      {loading && <p data-testid="loading-state">loading...</p>}
      {error && <p data-testid="error-state">{error}</p>}

      <section data-testid="department-breakdown">
        <h2>Department Breakdown</h2>
        {breakdown.length === 0 ? (
          <p>no breakdown</p>
        ) : (
          <ul>
            {breakdown.map((row) => (
              <li key={row.department_id} data-testid="breakdown-row">
                {row.department_name}: {row.total_amount} {row.currency_code}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section data-testid="comparison-view">
        <h2>Comparison</h2>
        {comparison.length === 0 ? (
          <p>no comparison</p>
        ) : (
          <ul>
            {comparison.map((row) => (
              <li
                key={row.department_id}
                data-testid="comparison-row"
              >
                {row.department_id}: delta {row.delta_pct}%
              </li>
            ))}
          </ul>
        )}
      </section>

      <section data-testid="chargeback-results">
        <h2>Chargeback</h2>
        {chargeback.length === 0 ? (
          <p>no chargeback</p>
        ) : (
          <ul>
            {chargeback.map((row) => (
              <li key={row.chargeback_id} data-testid="chargeback-row">
                {row.department_id}: {row.total_amount} {row.currency_code}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section data-testid="chargeback-export">
        <button
          type="button"
          onClick={() => void handleExport("csv")}
          disabled={exporting !== null}
          data-testid="export-csv"
        >
          Export CSV
        </button>
        <button
          type="button"
          onClick={() => void handleExport("pdf")}
          disabled={exporting !== null}
          data-testid="export-pdf"
        >
          Export PDF
        </button>
      </section>

      <section data-testid="department-mappings">
        <h2>Department Mappings</h2>
        {mappings.length === 0 ? (
          <p>no mappings</p>
        ) : (
          <ul>
            {mappings.map((row) => (
              <li
                key={row.department_id}
                data-testid="mapping-row"
              >
                {row.department_name} → {row.cost_center_id}
              </li>
            ))}
          </ul>
        )}
      </section>

      <footer>
        <button
          type="button"
          onClick={() => router.refresh()}
          data-testid="refresh"
        >
          refresh
        </button>
      </footer>
    </div>
  );
}
