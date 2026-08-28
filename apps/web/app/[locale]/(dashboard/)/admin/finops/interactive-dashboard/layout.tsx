/**
 * /admin/finops/interactive-dashboard — RSC layout entry.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — PRD §F44.6
 * verbatim + AD-57 (a) verbatim. data-locale + data-capability wrapper
 * with ARIA labels WCAG 2.1 AA + (dashboard) route group 보호.
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION — fail-closed 403
 * Forbidden).
 */

import type { ReactNode } from "react";

export default function InteractiveDashboardLayout({
    children,
}: {
    children: ReactNode;
}) {
    return (
        <div
            data-capability="finops_interactive_dashboard"
            data-layout="phase-28-t2-frontend-follow-up"
            role="region"
            aria-label="FinOps Interactive Dashboard — Phase 28 T2 frontend follow-up"
        >
            {children}
        </div>
    );
}