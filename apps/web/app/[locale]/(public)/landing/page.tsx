/**
 * apps/web/app/[locale]/(public)/landing/page.tsx — 1st release public landing page.
 *
 * 1st release launch (cj-style 64번째 진입점) — T1.1 (AC #1.1) — F18.1 Marketing landing page.
 * - (public) route group 신규 — `/landing` public route 결정 wire (vercel.json EXTENSION).
 * - no auth required — public marketing surface.
 * - capability gate `LAUNCH_LANDING` (v1.27) — industry-agnostic 4-industry grants.
 * - D-001 actual mount: page.tsx MUST render <LandingHero /> + <LandingFeatures /> +
 *   <LandingPricing /> + <LandingCTA /> (CR 11-4 D-001 lesson carry, no <TODO> stubs).
 * - ko-KR SSOT only (CR 11-4 D-002) — uses `landing.*` namespace from messages/ko-KR.json.
 */
import { LandingCTA } from "@/components/landing/LandingCTA";
import { LandingFeatures } from "@/components/landing/LandingFeatures";
import { LandingHero } from "@/components/landing/LandingHero";
import { LandingPricing } from "@/components/landing/LandingPricing";

export const dynamic = "force-dynamic";

interface LandingPageProps {
  params: Promise<{ locale: string }>;
}

export default async function LandingPage({ params: _params }: LandingPageProps) {
  await _params; // satisfy Next 15+ Promise<params>
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        background: "var(--bg, #0a0a0a)",
        color: "var(--fg, #f5f5f5)",
      }}
    >
      <LandingHero />
      <LandingFeatures />
      <LandingPricing />
      <LandingCTA />
    </main>
  );
}
