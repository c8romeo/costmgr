/**
 * apps/web/app/[locale]/(dashboard)/account/backups/page.tsx — Story 12.2
 *
 * RSC page for /account/backups (M12 backup download UI).
 *
 * Per AC #4 (Story 12.2):
 *  - Server-side fetch recent backups via `fetchBackupsRecentServerSide`.
 *  - Hand the response to `<BackupDownloadPanel>` (Client Component) which
 *    orchestrates list refresh, manual trigger, and JSON downloads.
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The `account/backups/layout.tsx` parent layer enforces authentication.
 * Owner-only role gate is enforced server-side at the route handler
 * (`require_role("owner")`).
 */

import { cookies } from "next/headers";

import { BackupDownloadPanel } from "@/components/m12-account/BackupDownloadPanel";
import type { BackupListResponse } from "@/lib/m12-account-backup";
import { fetchBackupsRecentServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface AccountBackupsPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AccountBackupsPage({
  params,
}: AccountBackupsPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  const initial = await fetchBackupsRecentServerSide(
    accessToken,
    traceId,
    7, // default days
  );

  // Fail-closed: when fetch fails (network / auth), render an empty
  // panel so the client component can attempt its own refresh.
  const initialList: BackupListResponse | null = initial
    ? {
        items: initial.items,
        total_count: initial.total_count,
        days: initial.days,
        trace_id: initial.trace_id,
      }
    : null;

  return (
    <BackupDownloadPanel
      initialList={initialList}
      accessToken={accessToken}
      initialError={initial === null ? "fetch_failed" : null}
    />
  );
}
