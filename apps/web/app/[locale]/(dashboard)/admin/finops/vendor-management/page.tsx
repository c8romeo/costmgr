/**
 * Vendor Management admin dashboard page (Phase 25 wire — cj-style 173번째).
 *
 * Server Component (RSC) that renders the FinopsVendorManagementDashboardPanel
 * Client Component. CR 1-1 RSC boundary — Server Component handles
 * locale + RBAC; Client Component handles interactive state.
 */

import { FinopsVendorManagementDashboardPanel } from "@/components/finops/FinopsVendorManagementDashboardPanel";

interface PageProps {
    // cj-271 (D-CI-FUNC-5 typedRoutes): Next.js 15 typedRoutes 호환.
    // cj-258 패턴. `next build` 강제 type check surface.
    params: Promise<{ locale: string }>;
}

export default async function VendorManagementPage({ params }: PageProps) {
    const { locale } = await params;
    return (
        <main lang={locale}>
            <FinopsVendorManagementDashboardPanel />
        </main>
    );
}