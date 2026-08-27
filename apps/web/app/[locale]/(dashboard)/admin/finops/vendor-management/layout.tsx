/**
 * Vendor Management admin dashboard layout (Phase 25 wire — cj-style 173번째).
 *
 * RSC layout that wraps the FinOps Vendor Management dashboard with
 * locale + capability gate. CR 1-1 RSC boundary — Server Component
 * handles tenant_id + role checks via cookies (Phase 24 layout pattern).
 */

import type { ReactNode } from "react";

interface LayoutProps {
    children: ReactNode;
    params: { locale: string };
}

export default function VendorManagementLayout({
    children,
    params,
}: LayoutProps) {
    return (
        <div data-locale={params.locale} data-capability="finops_vendor_management">
            {children}
        </div>
    );
}