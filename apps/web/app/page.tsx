// apps/web/app/page.tsx — root route resolver.
//
// Background: cj-style 64번째 (commit be0cf97) wire-up of the 1st release
// launch polished landing at `app/[locale]/(public)/landing/page.tsx`
// (LandingHero + LandingFeatures + LandingPricing + LandingCTA + ko-KR
// SSOT copy). However the root `app/page.tsx` remained the Story 0.1
// architecture-summary stub, so visiting `http://localhost:3000/`
// exposed only the dev-facing text — users never reached the polished
// landing without manually prefixing `/ko-KR/landing`.
//
// Fix: redirect root `/` → `/ko-KR/landing`. Locale prefix is explicit
// (not `as-needed`) so the user lands directly on the polished landing
// regardless of the next-intl `localePrefix` middleware config.
//
// Auth-aware routing intentionally deferred: authenticated users can
// navigate to the dashboard via LandingHero CTA buttons (login →
// dashboard handoff) which already exist in the landing component.

import { redirect } from "next/navigation";

export default function RootPage(): never {
  redirect("/ko-KR/landing");
}
