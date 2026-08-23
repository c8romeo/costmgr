/**
 * apps/web/app/[locale]/(dashboard)/admin/finops/page.tsx —
 * Phase 11 T7 (cj-style 107번째 wire) — FinOps Showback / Chargeback
 * admin dashboard.
 *
 * Per PRD §F27.1 + §F27.2 + §F27.3 + §F27.5 verbatim + AD-38 (a)~(g):
 *   - RSC + server-side fetch (F-20 race-free initial fetch, CR 1-1 verbatim).
 *   - Hands off to `<FinopsDashboardPanel>` client orchestrator.
 *   - fail-closed null on backend failure → Client Component retry
 *     via `useEffect` on mount.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { FinopsDashboardPanel } from "@/components/finops/FinopsDashboardPanel";

export const dynamic = "force-dynamic";

interface FinopsDashboardPageProps {
  params: Promise<{ locale: string }>;
}

export default async function FinopsDashboardPage({
  params,
}: FinopsDashboardPageProps): Promise<React.ReactElement> {
  const { locale } = await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    redirect(`/${locale}/login`);
    return <></>;
  }

  return <FinopsDashboardPanel accessToken={accessToken} locale={locale} />;
}
