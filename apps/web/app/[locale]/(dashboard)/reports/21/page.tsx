/**
 * apps/web/app/[locale]/(dashboard)/reports/21/page.tsx — Story 9.4
 *
 * RSC page for /reports/21 (Report #21 Cost Object Breakdown).
 *
 * Per AC #1 (Story 9.4):
 *  - Server-side render: pass accessToken + initialReport (null) +
 *    initialError (null) to `<Report21Panel>` (Client Component).
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create file).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (COST_CALCULATION OR ABC_CALCULATION) is
 * enforced server-side at the backend.
 */

import { cookies } from "next/headers";

import { Report21Panel } from "@/components/m5-reports/Report21Panel";

export const dynamic = "force-dynamic";

interface Report21PageProps {
  params: Promise<{ locale: string }>;
}

export default async function Report21Page({
  params,
}: Report21PageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  return (
    <Report21Panel
      accessToken={accessToken}
      initialReport={null}
      initialError={null}
    />
  );
}
