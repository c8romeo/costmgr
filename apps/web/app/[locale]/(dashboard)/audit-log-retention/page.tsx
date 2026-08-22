/**
 * apps/web/app/[locale]/(dashboard)/audit-log-retention/page.tsx —
 * Phase 6 T7a (AC #7.1~#7.8) — audit log retention configuration page.
 *
 * Per PRD §F22.1 + §F22.2 + §F22.4 verbatim + AD-33 (a)~(g):
 *   - RSC + server-side fetch (F-20 race-free initial fetch).
 *   - Hands off to `<AuditLogRetentionPanel>` client orchestrator.
 *   - fail-closed null on backend failure → Client Component retry
 *     via `useEffect` on mount.
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { AuditLogRetentionPanel } from "@/components/audit/AuditLogRetentionPanel";

export const dynamic = "force-dynamic";

interface AuditLogRetentionPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AuditLogRetentionPage({
  params,
}: AuditLogRetentionPageProps): Promise<React.ReactElement> {
  const { locale } = await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    redirect(`/${locale}/login`);
  }
  return <AuditLogRetentionPanel accessToken={accessToken} locale={locale} />;
}
