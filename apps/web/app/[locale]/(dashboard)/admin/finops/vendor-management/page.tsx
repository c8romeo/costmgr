/**
 * Vendor Management admin dashboard page (Phase 25 wire — cj-style 173번째).
 *
 * Server Component (RSC) that renders the FinopsVendorManagementDashboardPanel
 * Client Component. CR 1-1 RSC boundary — Server Component handles
 * locale + RBAC; Client Component handles interactive state.
 */

import { FinopsVendorManagementDashboardPanel } from "@/components/finops/FinopsVendorManagementDashboardPanel";

interface PageProps {
    params: { locale: string };
}

export default function VendorManagementPage({ params }: PageProps) {
    return (
        <main lang={params.locale}>
            <FinopsVendorManagementDashboardPanel />
        </main>
    );
}