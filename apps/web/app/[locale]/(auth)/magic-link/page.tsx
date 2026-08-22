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
  params: { locale: string };
  searchParams: { redirect?: string };
}

export default function MagicLinkPage({ params, searchParams }: MagicLinkPageProps) {
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
      <MagicLinkForm locale={params.locale} redirectTo={searchParams.redirect} />
    </main>
  );
}
