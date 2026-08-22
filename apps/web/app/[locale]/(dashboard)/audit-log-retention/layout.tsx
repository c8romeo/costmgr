/**
 * apps/web/app/[locale]/(dashboard)/audit-log-retention/layout.tsx —
 * Phase 6 (cj-style 87번째 wire) — auth gate.
 *
 * Mirror of `apps/web/app/[locale]/(dashboard)/audit-log/layout.tsx` —
 * ensure the sb-access-token cookie is present before rendering the
 * page; otherwise redirect to `/{locale}/login` (CR 11-4 D-001
 * verbatim). Capacity gate AUDIT_LOG_RETENTION is enforced at the
 * backend (CR 12-5 D-GATE-01).
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function AuditLogRetentionLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: Promise<{ locale: string }>;
}): Promise<React.ReactElement> {
  const { locale } = await params;
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    redirect(`/${locale}/login`);
  }
  return <>{children}</>;
}
