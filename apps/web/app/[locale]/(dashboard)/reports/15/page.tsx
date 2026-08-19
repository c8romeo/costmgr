/**
 * apps/web/app/[locale]/(dashboard)/reports/15/page.tsx — Story 11.6
 *
 * RSC page for /reports/15 (Report #15 활동원가 내역서 — 활동별 원가·동인 단가).
 *
 * Per AC #1 (Story 11.6):
 *  - Server-side render: pass accessToken + initialReport (null) +
 *    initialError (null) to `<Report15Panel>` (Client Component).
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create file).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (COST_CALCULATION OR ABC_CALCULATION) is
 * enforced server-side at the backend.
 */

import { cookies } from "next/headers";

import { Report15Panel } from "@/components/m5-reports/Report15Panel";

export const dynamic = "force-dynamic";

interface Report15PageProps {
  params: Promise<{ locale: string }>;
}

export default async function Report15Page({
  params,
}: Report15PageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  return (
    <Report15Panel
      accessToken={accessToken}
      initialReport={null}
      initialError={null}
    />
  );
}