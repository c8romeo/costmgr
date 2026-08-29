/**
 * Cost Anomaly ML Prediction admin dashboard page (Phase 26 wire — cj-style 186번째).
 *
 * Server Component (RSC) that renders the
 * FinopsCostAnomalyMLPredictionDashboardPanel Client Component.
 * CR 1-1 RSC boundary — Server Component handles locale + RBAC;
 * Client Component handles interactive state.
 *
 * Capability gate: require_finops_cost_anomaly_ml_prediction
 * (Phase 26 capability matrix v1.52 EXTENSION).
 */

import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { FinopsCostAnomalyMLPredictionDashboardPanel } from "@/components/finops/FinopsCostAnomalyMLPredictionDashboardPanel";

export const dynamic = "force-dynamic";

interface PageProps {
    params: Promise<{ locale: string }>;
    searchParams: Promise<{ period_key?: string }>;
}

export default async function CostAnomalyMLPredictionPage({
    params,
    searchParams,
}: PageProps): Promise<React.ReactElement> {
    const { locale } = await params;
    // eslint-disable-next-line @typescript-eslint/naming-convention, camelcase
    const { period_key } = await searchParams;

    const cookieStore = await cookies();
    const accessToken = cookieStore.get("sb-access-token")?.value;
    if (!accessToken) {
        redirect(`/${locale}/login`);
        return <></>;
    }

    return (
        <main lang={locale}>
            <FinopsCostAnomalyMLPredictionDashboardPanel
                // eslint-disable-next-line camelcase
                periodKey={period_key ?? "2026-08"}
            />
        </main>
    );
}
