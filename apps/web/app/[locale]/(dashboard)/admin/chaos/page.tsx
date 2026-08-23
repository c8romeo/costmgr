/**
 * apps/web/app/[locale]/(dashboard)/admin/chaos/page.tsx —
 * Phase 9 T7 (cj-style 99번째 wire) — chaos engineering admin dashboard.
 *
 * Per PRD §F25.1 + §F25.3 + §F25.6 verbatim + AD-36 (a)~(g):
 *   - RSC + server-side fetch (F-20 race-free initial fetch, CR 1-1 verbatim).
 *   - Hands off to `<ChaosDashboardPanel>` client orchestrator.
 *   - fail-closed null on backend failure → Client Component retry
 *     via `useEffect` on mount.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { ChaosDashboardPanel } from "@/components/chaos/ChaosDashboardPanel";

export const dynamic = "force-dynamic";

interface ChaosDashboardPageProps {
  params: Promise<{ locale: string }>;
}

export default async function ChaosDashboardPage({
  params,
}: ChaosDashboardPageProps): Promise<React.ReactElement> {
  const { locale } = await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    redirect(`/${locale}/login`);
  }
  return <ChaosDashboardPanel accessToken={accessToken} locale={locale} />;
}
