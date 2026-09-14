/**
 * apps/web/app/[locale]/(dashboard)/monthly-input/ai-extract/page.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Story 10.1 (Monthly AI Document Extraction) RSC mount page.
 *
 * Per AC #1 (Sprint 10.5 T1):
 *  - Server-side render: pass accessToken + defaultPeriodKey to a Client
 *    Component wrapper, which in turn mounts `<AiExtractModal>` with the
 *    close handler (RSC cannot serialize event-handler functions).
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create
 *    file or placeholder stub). Mount MUST be `<AiExtractPageClient .../>`
 *    which renders `<AiExtractModal .../>`.
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The capability gate (AI_INSIGHT) is enforced server-side at the
 * backend via `require_capability(Capability.AI_INSIGHT)` (10-2 wire).
 *
 * AD-7 verbatim: this page is DISPLAY ONLY. M10 NEVER writes to
 * confirmed_inputs/monthly_input_rows. The promote-to-confirmed flow
 * lives in `/ai/promote` (Sprint 10.4 AD-17 verbatim promotion port).
 *
 * AD-15 parity SSOT: POST /api/v1/ai/extract-monthly endpoint mirrors
 * `apps/api/modules/m10_ai/schemas.py` `MonthlyExtractRequest` body shape.
 *
 * cj-style N+15 (D-Day MVP demo, 2026-09-14 KST): prior implementation
 * passed `onClose={() => window.history.back()}` directly from RSC to
 * `<AiExtractModal>` — this violated the RSC boundary
 * ("Event handlers cannot be passed to Client Component props") and
 * yielded HTTP 500 on the sidebar route. Moved the close handler into
 * a thin Client Component wrapper (`AiExtractPageClient`) so all
 * serialized props cross the boundary cleanly.
 */

import { cookies } from "next/headers";

import { AiExtractPageClient } from "./AiExtractPageClient";

export const dynamic = "force-dynamic";

interface AiExtractPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AiExtractPage({
  params,
}: AiExtractPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;

  return (
    <AiExtractPageClient
      accessToken={accessToken}
      defaultPeriodKey={new Date().toISOString().slice(0, 7)}
    />
  );
}
