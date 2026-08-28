"use client";

/**
 * DrillDownExplorer — Phase 28 T2 Drill-Down Explorer sub-component.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — PRD §F44.3
 * verbatim + AD-57 (a) verbatim. Provides 6-dim drill-down navigation
 * with breadcrumb navigation + period_key selector.
 *
 * Capability gate: require_finops_interactive_dashboard
 * (Phase 28 capability matrix v1.53 EXTENSION).
 */

import { useState } from "react";

import type {
    DrillDownContext,
    DrillDownDimension,
    DrillDownGranularity,
} from "@/lib/finops/interactive-dashboard-types";

interface DrillDownExplorerProps {
    dryRun: boolean;
    periodKey: string;
}

const DIMENSION_OPTIONS: ReadonlyArray<{
    value: DrillDownDimension;
    label: string;
}> = [
    { value: "tenant", label: "테넌트 (tenant)" },
    { value: "cost_center", label: "코스트센터 (cost_center)" },
    { value: "department", label: "부서 (department)" },
    { value: "business_unit", label: "사업부 (business_unit)" },
    { value: "tag", label: "태그 (tag)" },
    { value: "cloud_provider", label: "클라우드 (cloud_provider)" },
    { value: "service", label: "서비스 (service)" },
];

const GRANULARITY_OPTIONS: ReadonlyArray<DrillDownGranularity> = [
    "minute",
    "hour",
    "day",
    "week",
    "month",
    "quarter",
    "year",
];

export function DrillDownExplorer({
    dryRun,
    periodKey,
}: DrillDownExplorerProps) {
    const [breadcrumb, setBreadcrumb] = useState<
        ReadonlyArray<DrillDownContext>
    >([]);
    const [selectedDimension, setSelectedDimension] =
        useState<DrillDownDimension>("tenant");
    const [selectedGranularity, setSelectedGranularity] =
        useState<DrillDownGranularity>("month");

    function handleDrillDown(dimensionValue: string): void {
        const newContext: DrillDownContext = {
            tenant_id: "demo-tenant",
            dimension: selectedDimension,
            dimension_value: dimensionValue,
            granularity: selectedGranularity,
            period_key: periodKey,
            parent_dimension:
                breadcrumb.length > 0
                    ? breadcrumb[breadcrumb.length - 1].dimension
                    : null,
        };
        setBreadcrumb((prev) => [...prev, newContext]);
    }

    function handlePopBreadcrumb(): void {
        setBreadcrumb((prev) => prev.slice(0, -1));
    }

    return (
        <section
            className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
            aria-label="Drill-Down Explorer"
        >
            <header className="mb-4">
                <h2 className="text-xl font-bold text-slate-900">
                    Drill-Down Explorer
                </h2>
                <p className="mt-1 text-sm text-slate-600">
                    7-dim drill-down navigation · 7-dim granularity
                    {dryRun && (
                        <span className="ml-2 rounded bg-amber-100 px-2 py-0.5 text-xs font-medium text-amber-700">
                            DRY-RUN
                        </span>
                    )}
                </p>
            </header>

            <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                <div>
                    <label
                        htmlFor="dimension-select"
                        className="block text-sm font-medium text-slate-700"
                    >
                        Drill-down dimension
                    </label>
                    <select
                        id="dimension-select"
                        data-testid="dimension-select"
                        value={selectedDimension}
                        onChange={(e) =>
                            setSelectedDimension(
                                e.target.value as DrillDownDimension
                            )
                        }
                        className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
                    >
                        {DIMENSION_OPTIONS.map((d) => (
                            <option key={d.value} value={d.value}>
                                {d.label}
                            </option>
                        ))}
                    </select>
                </div>
                <div>
                    <label
                        htmlFor="drill-granularity-select"
                        className="block text-sm font-medium text-slate-700"
                    >
                        Granularity
                    </label>
                    <select
                        id="drill-granularity-select"
                        data-testid="drill-granularity-select"
                        value={selectedGranularity}
                        onChange={(e) =>
                            setSelectedGranularity(
                                e.target.value as DrillDownGranularity
                            )
                        }
                        className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
                    >
                        {GRANULARITY_OPTIONS.map((g) => (
                            <option key={g} value={g}>
                                {g}
                            </option>
                        ))}
                    </select>
                </div>
            </div>

            <nav
                className="mb-4 rounded bg-slate-50 px-3 py-2 text-sm"
                aria-label="Drill-down breadcrumb"
                data-testid="breadcrumb-nav"
            >
                <span className="font-medium text-slate-700">Breadcrumb:</span>
                <span className="ml-2 text-slate-600">
                    tenant / {selectedDimension} ({selectedGranularity})
                </span>
                {breadcrumb.length > 0 && (
                    <>
                        {" "}
                        <button
                            type="button"
                            onClick={handlePopBreadcrumb}
                            className="ml-2 rounded border border-slate-300 px-2 py-0.5 text-xs"
                            data-testid="pop-breadcrumb"
                        >
                            ← 뒤로
                        </button>
                    </>
                )}
            </nav>

            <div className="grid grid-cols-2 gap-2 md:grid-cols-4">
                {["alpha", "beta", "gamma", "delta"].map((value) => (
                    <button
                        key={value}
                        type="button"
                        onClick={() => handleDrillDown(value)}
                        className="rounded border border-slate-300 px-3 py-2 text-sm font-medium hover:bg-slate-50"
                        data-testid={`drill-${value}`}
                    >
                        {selectedDimension}: {value}
                    </button>
                ))}
            </div>

            {breadcrumb.length > 0 && (
                <ul
                    className="mt-4 text-xs text-slate-500"
                    data-testid="breadcrumb-list"
                >
                    {breadcrumb.map((ctx, idx) => (
                        <li
                            key={`${ctx.dimension}-${ctx.dimension_value}-${idx}`}
                        >
                            #{idx + 1} {ctx.dimension}={ctx.dimension_value} (
                            {ctx.granularity}, period={ctx.period_key})
                        </li>
                    ))}
                </ul>
            )}
        </section>
    );
}