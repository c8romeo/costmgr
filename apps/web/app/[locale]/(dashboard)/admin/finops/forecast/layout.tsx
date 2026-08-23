import type { ReactNode } from "react";

/**
 * /[locale]/(dashboard)/admin/finops/forecast layout — Phase 13 wire.
 *
 * Phase 13 (cj-style 115번째 wire) — RTL section wrapper for forecast
 * dashboard. No state — purely structural.
 */
export default function FinopsForecastLayout({ children }: { children: ReactNode }) {
  return <section className="finops-forecast-section">{children}</section>;
}