/**
 * apps/web/app/[locale]/(dashboard)/simulation/cvp/page.tsx — Story 7.1
 *
 * RSC page for /simulation/cvp (M7 CVP/BEP simulation UI).
 *
 * Per AC #4 (Story 7.1):
 *  - Mounts `<CVPSimulationClient>` (CR 11-4 D-001 actual mount MUST).
 *  - Hands session token + initial period_key to the client component.
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The `simulation/cvp/layout.tsx` parent layer enforces authentication.
 */

import { cookies } from "next/headers";

import { CVPSimulationClient } from "@/components/m7-simulation";

export const dynamic = "force-dynamic";

interface CVPPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ period_key?: string }>;
}

export default async function CVPPage({
  params,
  searchParams,
}: CVPPageProps): Promise<React.ReactElement> {
  await params;
  // eslint-disable-next-line camelcase
  const { period_key } = await searchParams;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  // Default period_key to current YYYY-MM (story 7-1 baseline extraction).
  const fallbackPeriodKey = (() => {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, "0");
    return `${year}-${month}`;
  })();

  // eslint-disable-next-line camelcase
  const initialPeriodKey = period_key ?? fallbackPeriodKey;

  return (
    <CVPSimulationClient
      accessToken={accessToken}
      initialPeriodKey={initialPeriodKey}
    />
  );
}
