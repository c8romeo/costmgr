/**
 * apps/web/app/[locale]/(dashboard)/budget/scenarios/page.tsx — Story 8.1
 *
 * RSC page for /budget/scenarios (M8 budget scenario management UI).
 *
 * Per AC #4 (Story 8.1):
 *  - Server-side fetch tenant scenarios via `fetchBudgetScenariosServerSide`.
 *  - Hand the response to `<BudgetScenarioPanel>` (Client Component) which
 *    orchestrates list refresh + scenario creation.
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The `budget/scenarios/layout.tsx` parent layer enforces authentication.
 * Owner/member write gate is enforced server-side at the route handler
 * (`require_any_role("owner", "member")`).
 */

import { cookies } from "next/headers";

import { BudgetScenarioPanel } from "@/components/m8-budget/BudgetScenarioPanel";
import { fetchBudgetScenariosServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface BudgetScenariosPageProps {
  params: Promise<{ locale: string }>;
}

export default async function BudgetScenariosPage({
  params,
}: BudgetScenariosPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  const initial = await fetchBudgetScenariosServerSide(accessToken, traceId);

  return (
    <BudgetScenarioPanel
      initialList={initial}
      accessToken={accessToken}
      initialError={initial === null ? "fetch_failed" : null}
    />
  );
}