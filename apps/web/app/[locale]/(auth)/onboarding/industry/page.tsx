/**
 * apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx —
 * Server Component route for the 4지선다 onboarding screen.
 *
 * Story 1.1 — Task 3.1. Logic:
 *   1. Read `tenant_settings.onboarding.industry` from the server-side
 *      cookie session.
 *   2. If `null` → render `<IndustrySelector>` (Client Component).
 *   3. If non-null → redirect to `/[locale]/(dashboard)/`.
 *
 * F-4: the Server Component passes the accessToken STRING (not a function,
 * per F-1) to the IndustrySelector so its POST is authenticated. The
 * token is read from the `sb-access-token` cookie via `next/headers.cookies`.
 *
 * Cookie session: the `sb-access-token` cookie set by Supabase Auth.
 * Server Components can read it via `next/headers`. The full Supabase
 * SSR wiring is added in Story 0.5 (placeholder reads below).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { IndustrySelector } from "@/components/onboarding/IndustrySelector";

export const dynamic = "force-dynamic";

interface OnboardingIndustryPageProps {
  params: { locale: string };
}

export default async function OnboardingIndustryPage({
  params,
}: OnboardingIndustryPageProps) {
  const cookieStore = cookies();
  const hasSession = cookieStore.get("sb-access-token")?.value;
  // F-4: pass the accessToken STRING to the client component (was previously
  // undefined, which caused every POST to be unauthenticated).
  const accessToken = hasSession ?? undefined;

  if (!hasSession) {
    // Story 0.5 wires the real `supabase.auth.getUser()` check.
    redirect(`/${params.locale}/login`);
  }

  // Story 0.5 will replace this with a server-side `getTenantSettings()` call
  // that returns the persisted industry. For the Story 1.1 scaffold we let the
  // client fetch and branch — and redirect on success via IndustrySelector.
  return (
    <main>
      <IndustrySelector accessToken={accessToken} />
    </main>
  );
}