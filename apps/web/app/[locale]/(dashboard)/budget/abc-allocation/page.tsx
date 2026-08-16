/**
 * apps/web/app/[locale]/(dashboard)/budget/abc-allocation/page.tsx — Story 9.2
 *
 * RSC page for /budget/abc-allocation (M9 ABC Allocation Engine UI).
 *
 * Per AC #1 (Story 9.2):
 *  - Server-side render: pass accessToken + initialAllocation (null) to
 *    `<AbcAllocationPanel>` (Client Component).
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create file).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (ABC_CALCULATION) is enforced server-side at the
 * backend (`require_capability(Capability.ABC_CALCULATION)`).
 */

import { cookies } from "next/headers";

import { AbcAllocationPanel } from "@/components/m9-abc";

export const dynamic = "force-dynamic";

interface AbcAllocationPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AbcAllocationPage({
  params,
}: AbcAllocationPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  return (
    <AbcAllocationPanel
      accessToken={accessToken}
      initialAllocation={null}
      initialError={null}
    />
  );
}