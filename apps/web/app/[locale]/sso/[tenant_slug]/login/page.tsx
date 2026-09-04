/**
 * apps/web/app/[locale]/sso/[tenant_slug]/login/page.tsx — SSO entry per tenant.
 *
 * Epic 15 — T5.2 (AC #3.6) — F17.3 SSO enterprise UI.
 * - /sso/<tenant_slug>/login → trigger SAML AuthnRequest to IdP.
 * - Tenant slug routed to the per-tenant IdP metadata.
 * - D-001 actual mount: page.tsx renders real JSX (CR 11-4 D-001).
 * - Epic 12 2FA gate preserved (D-GATE-01 inversion).
 */
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

interface SSOLoginPageProps {
  // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
  // cj-258 패턴. `next build` 강제 type check surface.
  params: Promise<{ locale: string; tenant_slug: string }>;
  searchParams: Promise<{ relay_state?: string }>;
}

export default async function SSOLoginPage({ params, searchParams }: SSOLoginPageProps) {
  // Encode the original path (searchParams.relay_state or /dashboard default)
  // as URL-safe base64 and forward to the backend SSO login route.
  // cj-272 (D-CI-FUNC-4): URL contract (path [tenant_slug], query ?relay_state)
  // 강결합 identifier → camelcase disable. cj-264 proven pattern.
  const { locale, tenant_slug } = await params; // eslint-disable-line camelcase, @typescript-eslint/naming-convention
  const { relay_state } = await searchParams; // eslint-disable-line camelcase, @typescript-eslint/naming-convention
  const original = relay_state ?? `/${locale}/dashboard`; // eslint-disable-line camelcase
  const relayB64 = Buffer.from(original, "utf-8")
    .toString("base64")
    .replace(/=+$/, "")
    .replace(/\+/g, "-")
    .replace(/\//g, "_");

  const ssoUrl = `/api/v1/auth/sso/login?tenant_slug=${encodeURIComponent(
    tenant_slug,
  )}&relay_state=${encodeURIComponent(relayB64)}`;

  // The backend redirects to the IdP. We forward the browser via Next
  // redirect (HTTP 307 preserves the method).
  redirect(ssoUrl);
}
