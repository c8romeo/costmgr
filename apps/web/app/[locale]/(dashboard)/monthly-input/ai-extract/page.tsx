/**
 * apps/web/app/[locale]/(dashboard)/monthly-input/ai-extract/page.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Story 10.1 (Monthly AI Document Extraction) RSC mount page.
 *
 * Per AC #1 (Sprint 10.5 T1):
 *  - Server-side render: pass accessToken + defaultPeriodKey to the
 *    `<AiExtractModal>` (Client Component) which handles AI extraction
 *    form + draft display.
 *  - CR 11-4 D-001: page MUST actually mount the JSX (not just create
 *    file or placeholder stub). Mount MUST be `<AiExtractModal .../>`.
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
 */

import { cookies } from "next/headers";

import { AiExtractModal } from "@/components/m10-ai";

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
    <AiExtractModal
      accessToken={accessToken}
      isOpen={true}
      onClose={(): void => {
        // RSC doesn't support client-side navigation here; this page is a
        // dedicated mount entry point. Closing returns the user to the
        // monthly-input shell via standard browser back.
        if (typeof window !== "undefined") window.history.back();
      }}
      defaultPeriodKey={new Date().toISOString().slice(0, 7)}
    />
  );
}
