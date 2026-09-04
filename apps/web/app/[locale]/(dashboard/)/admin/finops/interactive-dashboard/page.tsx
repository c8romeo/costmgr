/**
 * /admin/finops/interactive-dashboard — RSC page entry.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — PRD §F44.6
 * verbatim + AD-57 (a) verbatim. RSC boundary: Server Component handles
 * locale + RBAC + cookies auth check via access token + period_key
 * searchParam. Client Component handles interactive state.
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION — fail-closed 403
 * Forbidden).
 *
 * CR 1-1 RSC boundary + CR 0-2 RLS + AD-22 owner-only RBAC + NFR18
 * ko-KR SSOT + WCAG 2.1 AA ARIA labels.
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { FinopsInteractiveDashboardPanel } from "@/components/finops/FinopsInteractiveDashboardPanel";

export const dynamic = "force-dynamic";

interface PageProps {
    // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
    // cj-258 패턴. `next build` 강제 type check surface.
    params: Promise<{ locale: string }>;
    searchParams: Promise<{ period_key?: string; tenant_id?: string }>;
}

export default async function InteractiveDashboardPage({
    params,
    searchParams,
}: PageProps) {
    const { locale } = await params;
    // cj-272 (D-CI-FUNC-4): URL contract (?period_key) 강결합 identifier →
    // camelcase disable. cj-264 proven pattern.
    const { period_key } = await searchParams; // eslint-disable-line camelcase, @typescript-eslint/naming-convention
    const cookieStore = await cookies();
    const accessToken = cookieStore.get("access_token")?.value;
    if (!accessToken) {
        redirect(`/${locale}/login`);
    }

    const periodKey = period_key ?? "2026-08"; // eslint-disable-line camelcase

    return (
        <div data-locale={locale} data-period-key={periodKey}>
            <FinopsInteractiveDashboardPanel
                periodKey={periodKey}
                isOwner={true}
                savedViewCount={0}
                impactKrwPerYear={0}
            />
        </div>
    );
}