/**
 * apps/web/app/[locale]/(dashboard)/budget/abc-validation/page.tsx — Story 9.1
 *
 * RSC page for /budget/abc-validation (M9 ABC 100% validation UI).
 *
 * Per AC #4 (Story 9.1):
 *  - Server-side render: pass accessToken + initialResponse (null) to
 *    `<AbcValidationPanel>` (Client Component).
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create file).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (ABC_CALCULATION) is enforced server-side at the
 * backend (`require_capability(Capability.ABC_CALCULATION)`).
 */

import { cookies } from "next/headers";

import { AbcValidationPanel } from "@/components/m9-abc";

export const dynamic = "force-dynamic";

interface AbcValidationPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AbcValidationPage({
  params,
}: AbcValidationPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  return (
    <AbcValidationPanel
      accessToken={accessToken}
      initialResponse={null}
      initialError={null}
    />
  );
}