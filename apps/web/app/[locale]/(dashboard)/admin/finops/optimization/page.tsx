import { FinopsOptimizationDashboardPanel } from "@/components/finops/FinopsOptimizationDashboardPanel";

/**
 * /[locale]/(dashboard)/admin/finops/optimization — Phase 14 FinOps Optimization dashboard RSC.
 *
 * Phase 14 (cj-style 119번째 wire) — FinOps Optimization & Rightsizing
 * territory (PRD §F30.6). Owner-only RBAC gate (AD-22) + Epic 12 2FA
 * 챌린지 mandatory when governance_required=True.
 *
 * CR 1-1 RSC boundary — this page is a React Server Component
 * (no client interactivity). All dashboard state + interactivity lives
 * in <FinopsOptimizationDashboardPanel /> (Client).
 */
export default function FinopsOptimizationPage() {
  return (
    <main className="min-h-screen bg-slate-950 p-6">
      <header className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">
          FinOps Optimization & Rightsizing
        </h1>
        <p className="text-sm text-slate-400">
          5 resource types (compute + storage + database + network + container)
          + 80+ AWS EC2 instance type mapping + z-score &lt; -2.0 idle detection +
          6 commitment_type + 1y/3y RI/SP + precision/recall/realized_savings.
        </p>
      </header>
      <FinopsOptimizationDashboardPanel />
    </main>
  );
}
