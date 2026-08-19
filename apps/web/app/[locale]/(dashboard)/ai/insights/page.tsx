/**
 * apps/web/app/[locale]/(dashboard)/ai/insights/page.tsx — Sprint 10.5 T2 wire (D-10-2-DEFER-4 해소)
 *
 * Story 10.2 (Three-Insight Cache Policy) RSC mount page.
 *
 * Per AC #2 (Sprint 10.5 T2):
 *  - Server-side render: pass accessToken to `<InsightCachePanel>`
 *    (Client Component) which handles the cache key form + insights
 *    grid display.
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create
 *    file or placeholder stub).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (AI_INSIGHT) is enforced server-side at the
 * backend via `require_capability(Capability.AI_INSIGHT)`.
 *
 * AD-7 verbatim: this page is DISPLAY ONLY on the cache output.
 * 10-2 wire 진입 시점에 all 3 default insights are `source_kind='auto_analysis'`.
 */

import { cookies } from "next/headers";

import { InsightCachePanel } from "@/components/m10-ai";

export const dynamic = "force-dynamic";

interface AiInsightsPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AiInsightsPage({
  params,
}: AiInsightsPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  return (
    <InsightCachePanel
      accessToken={accessToken}
      initialPeriodKey={new Date().toISOString().slice(0, 7)}
    />
  );
}
