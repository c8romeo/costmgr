/**
 * apps/web/app/[locale]/(auth)/magic-link/page.tsx — Magic link request page.
 *
 * Epic 15 — T2.2 (AC #1.3) — F17.1 Magic link entry point.
 * - (auth) route group public — already in middleware.ts auth paths.
 * - Capability gate `MAGIC_LINK` (v1.26) — all 4 industries have it
 *   (industry-agnostic, CR 12-1 L4 precedent). The client-side
 *   `LoginForm` already fetches from the tenant context.
 * - D-001 actual mount: page.tsx MUST render <MagicLinkForm /> JSX
 *   (CR 11-4 D-001 lesson carry).
 */
import { MagicLinkForm } from "@/components/auth/MagicLinkForm";

export const dynamic = "force-dynamic";

interface MagicLinkPageProps {
  // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
  // cj-258 패턴. `next build` 강제 type check surface.
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ redirect?: string }>;
}

export default async function MagicLinkPage({ params, searchParams }: MagicLinkPageProps) {
  const { locale } = await params;
  const { redirect: redirectParam } = await searchParams;
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem 1rem",
      }}
    >
      <MagicLinkForm locale={locale} redirectTo={redirectParam} />
    </main>
  );
}
