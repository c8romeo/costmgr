/**
 * apps/web/app/[locale]/(dashboard)/settings/sso/page.tsx — Epic 16 T4 (AC #7.1)
 *
 * RSC page for /settings/sso (Tenant IdP admin management UI).
 *
 * Per PRD §F19.4 + AD-30 (d):
 *   - Server-side fetch initial IdP config list via
 *     `fetchIdPConfigServerSide` (F-20 race-free initial fetch).
 *   - Hand the response (or fail-closed null) to `<IdPAdminPanel>`
 *     which orchestrates IdPList / IdPCreateForm / IdPEditForm /
 *     IdPTestPanel.
 *
 * Fail-closed pattern: when the backend fetch fails (network, 401,
 * 403, 5xx) we pass `null` through and the Client Component renders
 * a "설정 정보를 가져올 수 없습니다" empty state. The Client Component
 * retries via `useEffect` on mount and surfaces typed CR 12-5 D-14
 * error envelopes to the user.
 *
 * The path resolves under `/[locale]/(dashboard)/settings/sso`. It
 * is the ONLY AC §F19.4 deliverable left after Epic 16 atomic wire
 * `e117e09` (which delivered the backend 5 CRUD routes + 4 audit
 * actions + capability gate).
 */
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { IdPAdminPanel } from "@/components/settings/sso/IdPAdminPanel";
import { fetchIdPConfigServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface SettingsSsoPageProps {
  params: Promise<{ locale: string }>;
}

export default async function SettingsSsoPage({
  params,
}: SettingsSsoPageProps): Promise<React.ReactElement> {
  await params; // satisfy Next 15+ Promise<params>

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  if (!accessToken) {
    // Layout-level gate should have caught this, but defense in depth.
    redirect("/ko-KR/login");
  }

  const traceId = crypto.randomUUID();

  // Tenant slug is required for the admin IdP endpoint. For the
  // initial render we attempt to read it from the cookie set by the
  // MenuProvider (`current-tenant-slug`); if missing, the Client
  // Component surfaces an empty state.
  const tenantSlug = cookieStore.get("current-tenant-slug")?.value ?? "";

  const initialConfigs = tenantSlug
    ? await fetchIdPConfigServerSide(accessToken, tenantSlug, traceId)
    : null;

  return (
    <main className="p-6">
      <IdPAdminPanel
        tenantSlug={tenantSlug}
        initialConfigs={initialConfigs ?? []}
        accessToken={accessToken}
      />
    </main>
  );
}
