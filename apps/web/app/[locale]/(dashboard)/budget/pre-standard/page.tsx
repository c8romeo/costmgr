/**
 * apps/web/app/[locale]/(dashboard)/budget/pre-standard/page.tsx — Story 8.3
 *
 * RSC page for /budget/pre-standard (M8 budget pre-standard cost preview UI).
 *
 * Per AC #4 (Story 8.3):
 *  - Server-side fetch tenant pre-standard snapshot via `fetchBudgetPreStandardServerSide`.
 *  - Hand the response to `<BudgetPreStandardPreview>` (Client Component).
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create file).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (BUDGET_SCENARIO reuse) is enforced server-side at the
 * backend (`require_capability(Capability.BUDGET_SCENARIO)`).
 */

import { cookies } from "next/headers";

import { BudgetPreStandardPreview } from "@/components/m8-budget/BudgetPreStandardPreview";
import { fetchBudgetPreStandardServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface BudgetPreStandardPageProps {
  params: Promise<{ locale: string }>;
}

export default async function BudgetPreStandardPage({
  params,
}: BudgetPreStandardPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  const initial = await fetchBudgetPreStandardServerSide(
    accessToken,
    "2026-07#B1", // Default virtual period key (8-1 wire)
    traceId,
  );

  return (
    <BudgetPreStandardPreview
      initialSnapshot={initial}
      accessToken={accessToken}
      initialError={initial === null ? "fetch_failed" : null}
    />
  );
}
