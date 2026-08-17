/**
 * apps/web/app/[locale]/(dashboard)/budget/abc-calculation/page.tsx — Story 9.3
 *
 * RSC page for /budget/abc-calculation (M9 ABC Dispatch dual-route UI).
 *
 * Per AC #1 (Story 9.3) — POST /api/v1/calc is the SINGLE public endpoint
 * (M3 owns the route). The orchestrator's `_resolve_engine_type(industry)`
 * dispatches to M9 ABC path if `tenant.industry == 'service'`.
 *
 * The RSC:
 *   - Reads `sb-access-token` cookie for capability gate.
 *   - Resolves `tenant.industry` from session/profile (default: "manufacturing"
 *     for demo; production wire fetches from /api/v1/tenant/profile).
 *   - Passes `accessToken` + `tenantIndustry` + null initial state to
 *     `<AbcDispatchPanel>` (Client Component).
 *
 * CR 11-4 D-001: page MUST actually mount the JSX (not just create file).
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * Capability gate dual-route (COST_CALCULATION | ABC_CALCULATION) is
 * enforced server-side at handlers.py (T2.2 wire).
 */

import { cookies } from "next/headers";

import { AbcDispatchPanel } from "@/components/m9-abc";

export const dynamic = "force-dynamic";

interface AbcCalculationPageProps {
  params: Promise<{ locale: string }>;
}

/**
 * Read tenant.industry from cookie (demo). Production wire fetches from
 * /api/v1/tenant/profile with TenantContext (CR 12-1 L3 ORM→kernel boundary).
 *
 * Defaults to "manufacturing" so the trad path is the default dispatch
 * decision (PRD §F9.3 — service industry → ABC path).
 */
function resolveTenantIndustryFromCookie(
  cookieValue: string | undefined,
): string {
  if (cookieValue === undefined || cookieValue === "") {
    return "manufacturing";
  }
  // Sanity-check: only accept known industry Literal values.
  if (cookieValue === "service" || cookieValue === "manufacturing") {
    return cookieValue;
  }
  return "manufacturing";
}

export default async function AbcCalculationPage({
  params,
}: AbcCalculationPageProps): Promise<React.ReactElement> {
  await params;

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const tenantIndustryCookie = cookieStore.get("tenant-industry")?.value;
  const tenantIndustry = resolveTenantIndustryFromCookie(tenantIndustryCookie);

  return (
    <AbcDispatchPanel
      accessToken={accessToken}
      tenantIndustry={tenantIndustry}
      initialOutcome={null}
      initialError={null}
    />
  );
}
