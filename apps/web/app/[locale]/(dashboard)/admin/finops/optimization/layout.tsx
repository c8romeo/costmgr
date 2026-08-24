/**
 * /[locale]/(dashboard)/admin/finops/optimization layout — Phase 14 FinOps Optimization dashboard.
 *
 * Phase 14 (cj-style 119번째 wire) — RTL section wrapper for
 * optimization dashboard. Mirrors Phase 13 forecast/layout.tsx pattern
 * verbatim. Provides shared layout (header + nav) for optimization
 * dashboard pages.
 */
export default function FinopsOptimizationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <section dir="ltr" className="optimization-dashboard-layout">
      {children}
    </section>
  );
}
