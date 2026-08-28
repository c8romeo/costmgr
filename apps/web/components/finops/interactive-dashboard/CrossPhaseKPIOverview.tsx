"use client";

/**
 * CrossPhaseKPIOverview — Phase 28 T2 Cross-Phase Unified KPI Overview.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — PRD §F44.1
 * verbatim + AD-57 (a) verbatim + Epic 28 wire cj-193 의 4 NEW backend
 * modules (cross_phase_aggregator + saved_view_engine + export_pipeline
 * + dashboard_router) 의 frontend UI surface 신규 진입.
 *
 * Composes Phase 11~28 unified KPI tile grid + 5-dim weighted
 * aggregation gauge + `INTERACTIVE_DASHBOARD_ENGINE_VERSION` engine
 * version display.
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION).
 */

import { useEffect, useState } from "react";

import { computeUnifiedKPI } from "@/lib/finops/interactive-dashboard-client";
import {
    DASHBOARD_KPI_DIMENSION_WEIGHTS,
    INTERACTIVE_DASHBOARD_ENGINE_VERSION,
    PHASE_KPI_SOURCE_MODULES,
} from "@/lib/finops/interactive-dashboard-types";
import type { UnifiedKPI } from "@/lib/finops/interactive-dashboard-types";

interface CrossPhaseKPIOverviewProps {
    dryRun: boolean;
    periodKey: string;
}

const PHASE_KEYS: ReadonlyArray<keyof typeof PHASE_KPI_SOURCE_MODULES> = [
    "phase_11",
    "phase_12",
    "phase_13",
    "phase_14",
    "phase_15",
    "phase_16",
    "phase_17",
    "phase_18",
    "phase_19",
    "phase_20",
    "phase_21",
    "phase_22",
    "phase_23",
    "phase_24",
    "phase_25",
    "phase_26",
    "phase_27",
    "phase_28",
];

const DIMENSION_LABELS: Record<string, string> = {
    cost: "비용 (Cost)",
    usage: "사용량 (Usage)",
    performance: "성능 (Performance)",
    compliance: "컴플라이언스 (Compliance)",
    sla: "SLA",
};

export function CrossPhaseKPIOverview({
    dryRun,
    periodKey,
}: CrossPhaseKPIOverviewProps) {
    const [kpi, setKpi] = useState<UnifiedKPI | null>(null);
    const [loading, setLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function load() {
            setLoading(true);
            setError(null);
            try {
                const result = await computeUnifiedKPI({
                    tenant_id: "demo-tenant",
                    period_key: periodKey,
                    dimension: "tenant",
                    dimension_value: "demo-tenant",
                });
                if (cancelled) return;
                setKpi(result);
            } catch (err) {
                if (cancelled) return;
                setError(
                    err instanceof Error
                        ? err.message
                        : "cross_phase_kpi_load_failed"
                );
            } finally {
                if (!cancelled) setLoading(false);
            }
        }
        void load();
        return () => {
            cancelled = true;
        };
    }, [periodKey]);

    if (loading) {
        return (
            <section
                className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
                aria-label="Cross-Phase Unified KPI 로딩 중"
            >
                <div className="text-slate-400">
                    Cross-Phase Unified KPI 데이터를 불러오는 중...
                </div>
            </section>
        );
    }

    if (error) {
        return (
            <section
                className="rounded-lg border border-rose-200 bg-rose-50 p-6 shadow-sm"
                role="alert"
                aria-label="Cross-Phase Unified KPI 오류"
            >
                <div className="text-rose-700">Error: {error}</div>
            </section>
        );
    }

    if (!kpi) {
        return (
            <section
                className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
                aria-label="Cross-Phase Unified KPI 데이터 없음"
            >
                <div className="text-slate-500">
                    표시할 Cross-Phase KPI 데이터가 없습니다.
                </div>
            </section>
        );
    }

    const weightedTotal =
        DASHBOARD_KPI_DIMENSION_WEIGHTS.cost * kpi.kpi_value_krw +
        DASHBOARD_KPI_DIMENSION_WEIGHTS.usage * kpi.showback_krw +
        DASHBOARD_KPI_DIMENSION_WEIGHTS.performance *
            (kpi.optimization_savings_krw / 1_000_000) +
        DASHBOARD_KPI_DIMENSION_WEIGHTS.compliance * kpi.tag_compliance_pct +
        DASHBOARD_KPI_DIMENSION_WEIGHTS.sla *
            kpi.commitment_utilization_pct;

    return (
        <section
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
            aria-label="Cross-Phase Unified KPI Overview"
        >
            <header className="mb-4 flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-bold text-slate-900">
                        Cross-Phase 통합 KPI ({INTERACTIVE_DASHBOARD_ENGINE_VERSION})
                    </h2>
                    <p className="mt-1 text-sm text-slate-600">
                        Phase 11~28 unified_kpi_total 기반 5-dim 가중
                        집계 (cost 0.30 + usage 0.20 + performance 0.20 +
                        compliance 0.15 + sla 0.15)
                        {dryRun && (
                            <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                                DRY-RUN
                            </span>
                        )}
                    </p>
                </div>
            </header>

            <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
                {PHASE_KEYS.map((phaseKey) => {
                    const fieldName = PHASE_KPI_SOURCE_MODULES[phaseKey];
                    const value = (kpi as unknown as Record<string, unknown>)[
                        fieldName
                    ];
                    return (
                        <div
                            key={phaseKey}
                            className="rounded border border-slate-100 bg-slate-50 p-3"
                            data-testid={`phase-kpi-${phaseKey}`}
                        >
                            <div className="text-xs font-medium text-slate-500">
                                {phaseKey.toUpperCase()}
                            </div>
                            <div className="mt-1 text-sm font-semibold text-slate-900">
                                {typeof value === "number"
                                    ? value.toLocaleString("ko-KR")
                                    : String(value ?? "—")}
                            </div>
                            <div className="mt-0.5 text-xs text-slate-400">
                                {fieldName}
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-5">
                {Object.entries(DASHBOARD_KPI_DIMENSION_WEIGHTS).map(
                    ([dim, weight]) => (
                        <div
                            key={dim}
                            className="rounded border border-slate-200 bg-slate-50 p-4"
                            data-testid={`dimension-${dim}`}
                        >
                            <div className="text-xs font-medium text-slate-500">
                                {DIMENSION_LABELS[dim] ?? dim}
                            </div>
                            <div className="mt-1 text-lg font-semibold text-slate-900">
                                weight {weight.toFixed(2)}
                            </div>
                        </div>
                    )
                )}
            </div>

            <footer className="mt-4 text-right text-xs text-slate-400">
                weighted_total ≈ {weightedTotal.toLocaleString("ko-KR")} |{" "}
                period_key={kpi.period_key}
            </footer>
        </section>
    );
}