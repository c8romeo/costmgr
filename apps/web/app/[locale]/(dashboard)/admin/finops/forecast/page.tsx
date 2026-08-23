import { FinopsForecastDashboardPanel } from "@/components/finops/FinopsForecastDashboardPanel";

/**
 * /[locale]/(dashboard)/admin/finops/forecast — Phase 13 forecast dashboard RSC.
 *
 * Phase 13 (cj-style 115번째 wire) — FinOps Forecasting & Capacity
 * Planning territory (PRD §F29.6). Owner-only RBAC gate (AD-22) +
 * Epic 12 2FA 챌린지 mandatory when governance_required=True.
 *
 * CR 1-1 RSC boundary — this page is a React Server Component
 * (no client interactivity). All dashboard state + interactivity lives
 * in <FinopsForecastDashboardPanel /> (Client).
 */
export default function FinopsForecastPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">
          FinOps Forecasting & Capacity Planning
        </h1>
        <p className="text-sm text-slate-400">
          4-model ensemble forecast (ARIMA + Prophet + LSTM + ensemble) +
          90일 capacity headroom + budget burn-rate projection.
        </p>
      </header>
      <FinopsForecastDashboardPanel />
    </main>
  );
}