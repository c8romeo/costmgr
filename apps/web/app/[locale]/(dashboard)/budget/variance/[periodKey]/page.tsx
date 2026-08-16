/**
 * apps/web/app/[locale]/(dashboard)/budget/variance/[periodKey]/page.tsx — Story 8.2
 *
 * RSC page for /budget/variance/{periodKey} (M8 budget-actual variance UI).
 *
 * Per AC #6 (Story 8.2):
 *  - Server-side fetch tenant variance via `fetchBudgetVarianceServerSide`.
 *  - Hand the response to `<BudgetVarianceTable>` (Client Component)
 *    which composes ABCDGrayBadge + VarianceRow + VarianceSummary + VariancePdfButton.
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (BUDGET_SCENARIO reuse) is enforced server-side at the
 * backend (`require_capability(Capability.BUDGET_SCENARIO)`).
 */

import { cookies } from "next/headers";

import { BudgetVarianceTable } from "@/components/m8-budget-variance/BudgetVarianceTable";
import { fetchBudgetVarianceServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface BudgetVariancePageProps {
  params: Promise<{ locale: string; periodKey: string }>;
}

export default async function BudgetVariancePage({
  params,
}: BudgetVariancePageProps): Promise<React.ReactElement> {
  const { periodKey } = await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  const initial = await fetchBudgetVarianceServerSide(
    accessToken,
    decodeURIComponent(periodKey),
    traceId,
  );

  return (
    <BudgetVarianceTable
      initialTable={initial}
      accessToken={accessToken}
      initialError={initial === null ? "fetch_failed" : null}
    />
  );
}
