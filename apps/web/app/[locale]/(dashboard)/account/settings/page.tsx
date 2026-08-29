/**
 * apps/web/app/[locale]/(dashboard)/account/settings/page.tsx — Story 12.3
 *
 * RSC page for /account/settings (M12 account settings + deletion UI).
 *
 * Per AC #5 (Story 12.3):
 *  - Server-side fetch `GET /api/v1/account/deletion/status` via
 *    `fetchDeletionStatusServerSide` to seed the initial FSM snapshot.
 *  - Hand the response to `<DeletionStatusPanel>` (Client Component) which
 *    orchestrates the destructive flow (TOTP challenge → consent → submit).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The `account/settings/layout.tsx` parent layer enforces authentication.
 * Owner-only role gate is enforced server-side at the FastAPI route handler
 * (`require_role("owner")`).
 *
 * CR 11-4 D-001 fix: page.tsx actually mounts the panel (vitest assertion).
 */

import { cookies } from "next/headers";

import { DeletionStatusPanel } from "@/components/m12-account/DeletionStatusPanel";
import type { DeletionStatusResponse } from "@/lib/m12-account-deletion";
import { fetchDeletionStatusServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface AccountSettingsPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AccountSettingsPage({
  params,
}: AccountSettingsPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  const initial = await fetchDeletionStatusServerSide(accessToken);

  // Fail-closed: when fetch fails (network / auth / 410 deleted), render
  // the panel with null initial state so the client component can attempt
  // its own refresh or render the terminal "deleted" state.
  const initialStatus: DeletionStatusResponse | null = initial;

  return (
    <main className="mx-auto max-w-2xl space-y-6 p-6">
      <header>
        <h1 className="text-2xl font-semibold">계정 설정</h1>
      </header>
      <DeletionStatusPanel
        initialStatus={initialStatus}
        accessToken={accessToken}
      />
    </main>
  );
}
