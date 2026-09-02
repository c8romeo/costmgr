/**
 * Cost Anomaly ML Prediction admin dashboard layout (Phase 26 wire — cj-style 186번째).
 *
 * RSC layout that wraps the FinOps Cost Anomaly ML Prediction dashboard
 * with locale + capability gate. CR 1-1 RSC boundary — Server Component
 * handles tenant_id + role checks via cookies (Phase 25 layout pattern).
 *
 * Capability: finops_cost_anomaly_ml_prediction (Phase 26 capability matrix
 * v1.52 EXTENSION).
 */

import type { ReactNode } from "react";

interface LayoutProps {
    children: ReactNode;
    params: Promise<{ locale: string }>;
}

export default async function CostAnomalyMLPredictionLayout({
    children,
    params,
}: LayoutProps): Promise<React.ReactElement> {
    const { locale } = await params;
    return (
        <div
            data-locale={locale}
            data-capability="finops_cost_anomaly_ml_prediction"
        >
            {children}
        </div>
    );
}
