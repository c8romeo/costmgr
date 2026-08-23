/**
 * apps/web/app/[locale]/(dashboard)/admin/slo/page.tsx —
 * Phase 10 T7 (cj-style 103번째 wire) — SLO Engineering / Error Budget
 * Management admin dashboard.
 *
 * Per PRD §F26.1 + §F26.3 + §F26.4 + §F26.5 verbatim + AD-37 (a)~(g):
 *   - RSC + server-side fetch (F-20 race-free initial fetch, CR 1-1 verbatim).
 *   - Hands off to `<SloDashboardPanel>` client orchestrator.
 *   - fail-closed null on backend failure → Client Component retry
 *     via `useEffect` on mount.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { SloDashboardPanel } from "@/components/slo/SloDashboardPanel";

export const dynamic = "force-dynamic";

interface SloDashboardPageProps {
  params: Promise<{ locale: string }>;
}

export default async function SloDashboardPage({
  params,
}: SloDashboardPageProps): Promise<React.ReactElement> {
  const { locale } = await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    redirect(`/${locale}/login`);
    return <></>;
  }

  return <SloDashboardPanel accessToken={accessToken} locale={locale} />;
}
