/**
 * apps/web/app/[locale]/(dashboard)/simulation/projection/page.tsx — Story 7.2
 *
 * RSC page for /simulation/projection (M7 Next-Month Projection UI).
 *
 * Per AC #4 (Story 7.2):
 *  - Mounts `<ProjectionClient>` (CR 11-4 D-001 actual mount MUST).
 *  - Hands session token + initial period_key + initial projection_month
 *    to the client component.
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The `simulation/projection/layout.tsx` parent layer enforces authentication.
 */

import { cookies } from "next/headers";

import { ProjectionClient } from "@/components/m7-simulation";

export const dynamic = "force-dynamic";

interface ProjectionPageProps {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{
    period_key?: string;
    projection_month?: string;
  }>;
}

export default async function ProjectionPage({
  params,
  searchParams,
}: ProjectionPageProps): Promise<React.ReactElement> {
  await params;
  // eslint-disable-next-line camelcase
  const { period_key, projection_month } = await searchParams;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  // Default period_key to current YYYY-MM (story 7-2 baseline extraction).
  const fallbackPeriodKey = (() => {
    const now = new Date();
    const year = now.getUTCFullYear();
    const month = String(now.getUTCMonth() + 1).padStart(2, "0");
    return `${year}-${month}`;
  })();

  // Default projection_month = next calendar month.
  const fallbackProjectionMonth = (() => {
    const now = new Date();
    let year = now.getUTCFullYear();
    let month = now.getUTCMonth() + 2; // +2 because getUTCMonth() is 0-indexed and we want next month
    if (month > 12) {
      month = 1;
      year += 1;
    }
    return `${year}-${String(month).padStart(2, "0")}`;
  })();

  // eslint-disable-next-line camelcase
  const initialPeriodKey = period_key ?? fallbackPeriodKey;
  // eslint-disable-next-line camelcase
  const initialProjectionMonth = projection_month ?? fallbackProjectionMonth;

  return (
    <ProjectionClient
      accessToken={accessToken}
      initialPeriodKey={initialPeriodKey}
      initialProjectionMonth={initialProjectionMonth}
    />
  );
}
