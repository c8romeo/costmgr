/**
 * apps/web/app/[locale]/(dashboard)/budget/pre-standard/layout.tsx — Story 8.3
 *
 * RSC layout for /budget/pre-standard (M8 budget pre-standard cost preview UI).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (BUDGET_SCENARIO reuse) is enforced server-side at the
 * backend (`require_capability(Capability.BUDGET_SCENARIO)`).
 */

import { ReactNode } from "react";

interface BudgetPreStandardLayoutProps {
  children: ReactNode;
}

export default function BudgetPreStandardLayout({
  children,
}: BudgetPreStandardLayoutProps): React.ReactElement {
  return <div className="budget-pre-standard-layout">{children}</div>;
}
