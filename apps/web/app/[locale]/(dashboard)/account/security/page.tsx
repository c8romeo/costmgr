/**
 * apps/web/app/[locale]/(dashboard)/account/security/page.tsx — Story 12.5
 *
 * RSC page for /account/security (M12 2FA self-service).
 *
 * Per AC #4 (Story 12.5):
 *  - Server-side fetch TOTP status + role via `fetchTotpStatusServerSide`.
 *  - Hand the response to `<AccountSecurityPanel>` (Client Component) which
 *    orchestrates the setup / disable / recovery displays.
 *
 * Inherits the `(dashboard)` layout → Sidebar + MenuProvider.
 * The `account/security/layout.tsx` parent layer enforces authentication.
 */

import { cookies } from "next/headers";

import { AccountSecurityPanel } from "@/components/m12-account/AccountSecurityPanel";
import { fetchTotpStatusServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

interface AccountSecurityPageProps {
  params: Promise<{ locale: string }>;
}

export default async function AccountSecurityPage({
  params,
}: AccountSecurityPageProps): Promise<React.ReactElement> {
  await params; // satisfy Next 15+ Promise<params>

  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  const totp = await fetchTotpStatusServerSide(accessToken, traceId);

  // Fail-closed: when fetch fails, treat as viewer + disabled so the panel
  // shows a [설정하기] CTA rather than crashing.
  const fallback = {
    totp_enabled: false,
    totp_enabled_at: null,
    recovery_codes_remaining: null,
    failed_attempts: 0,
    locked_out: false,
    lockout_until: null,
    last_login_at: null,
    role: "viewer",
  };

  const state = totp
    ? {
        totp_enabled: totp.totp_enabled,
        totp_enabled_at: totp.totp_enabled_at,
        recovery_codes_remaining: totp.recovery_codes_remaining,
        failed_attempts: totp.failed_attempts,
        locked_out: totp.locked_out,
        lockout_until: totp.lockout_until,
        last_login_at: totp.last_login_at,
        role: totp.role,
      }
    : fallback;

  return (
    <main className="p-6">
      <AccountSecurityPanel
        totp_enabled={state.totp_enabled}
        totp_enabled_at={state.totp_enabled_at}
        recovery_codes_remaining={state.recovery_codes_remaining}
        locked_out={state.locked_out}
        lockout_until={state.lockout_until}
        role={state.role}
        accessToken={accessToken}
      />
    </main>
  );
}
