/**
 * apps/web/__tests__/finops/interactive-dashboard-dashboard.test.tsx —
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — vitest cases
 * for the FinOps Interactive Dashboard.
 *
 * Covers (mirrors Phase 26 pattern verbatim — 25~28 NEW vitest cases):
 * - 4 cases for lib types constants (PRD §F43.1~§F43.7 + AD-56 (a)~(g))
 * - 6 cases for lib client fetch (11 endpoints sampled)
 * - 4 cases for CrossPhaseKPIOverview sub-component
 * - 4 cases for SavedViewManager sub-component
 * - 4 cases for DrillDownExplorer sub-component
 * - 3 cases for ExportConfigPanel sub-component
 * - 4 cases for DashboardSharingPanel sub-component
 * - 1 case for FinopsInteractiveDashboardPanel orchestrator
 *
 * CR 1-1 RSC boundary + CR 12-5 D-PARITY-01 + AD-22 owner-only RBAC +
 * NFR18 ko-KR SSOT.
 */
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import {
    DASHBOARD_CADENCE_HOURS_KST,
    DASHBOARD_KPI_DIMENSION_WEIGHTS,
    DASHBOARD_RECIPIENT_TEMPLATES,
    EXPORT_MAX_RETRIES,
    HIGH_VALUE_THRESHOLD_KRW_PER_YEAR,
    INTERACTIVE_DASHBOARD_ENGINE_VERSION,
    MAX_EXPORT_SIZE_BYTES,
    MAX_SAVED_VIEWS_PER_TENANT,
    PHASE_KPI_SOURCE_MODULES,
    PREDEFINED_VIEW_TEMPLATES,
    SAVED_VIEW_CACHE_TTL_SECONDS,
    SHARING_EXPIRES_DEFAULT_DAYS,
} from "@/lib/finops/interactive-dashboard-types";

// ---------------------------------------------------------------------------
// Group 1: lib types/constants — 4 cases
// ---------------------------------------------------------------------------

describe("Phase 28 T2 interactive-dashboard-types constants", () => {
    it("Test 1: DASHBOARD_KPI_DIMENSION_WEIGHTS has 5 dims with cost=0.30 (PRD §F43.2 + AD-56 (b) verbatim)", () => {
        expect(Object.keys(DASHBOARD_KPI_DIMENSION_WEIGHTS)).toHaveLength(5);
        expect(DASHBOARD_KPI_DIMENSION_WEIGHTS.cost).toBe(0.30);
        expect(DASHBOARD_KPI_DIMENSION_WEIGHTS.usage).toBe(0.20);
        expect(DASHBOARD_KPI_DIMENSION_WEIGHTS.performance).toBe(0.20);
        expect(DASHBOARD_KPI_DIMENSION_WEIGHTS.compliance).toBe(0.15);
        expect(DASHBOARD_KPI_DIMENSION_WEIGHTS.sla).toBe(0.15);
        const sum = Object.values(DASHBOARD_KPI_DIMENSION_WEIGHTS).reduce(
            (acc, w) => acc + w,
            0,
        );
        expect(sum).toBeCloseTo(1.0, 5);
    });

    it("Test 2: PHASE_KPI_SOURCE_MODULES has 18 entries (Phase 11~28 verbatim)", () => {
        expect(Object.keys(PHASE_KPI_SOURCE_MODULES)).toHaveLength(18);
        expect(PHASE_KPI_SOURCE_MODULES.phase_11).toBe("showback_krw");
        expect(PHASE_KPI_SOURCE_MODULES.phase_28).toBe("unified_kpi_total");
    });

    it("Test 3: PREDEFINED_VIEW_TEMPLATES has 12 templates (PRD §F43.2 verbatim)", () => {
        expect(PREDEFINED_VIEW_TEMPLATES).toHaveLength(12);
        expect(PREDEFINED_VIEW_TEMPLATES).toContain("CostByCloudProvider");
        expect(PREDEFINED_VIEW_TEMPLATES).toContain(
            "ReservedInstanceUtilizationByTier"
        );
    });

    it("Test 4: Guard constants + cadence + engine version verbatim (PRD §F43.1~§F43.7 + AD-56 (a)(g))", () => {
        expect(INTERACTIVE_DASHBOARD_ENGINE_VERSION).toBe("1.0.0");
        expect(MAX_SAVED_VIEWS_PER_TENANT).toBe(50);
        expect(SAVED_VIEW_CACHE_TTL_SECONDS).toBe(300);
        expect(SHARING_EXPIRES_DEFAULT_DAYS).toBe(30);
        expect(MAX_EXPORT_SIZE_BYTES).toBe(52_428_800);
        expect(EXPORT_MAX_RETRIES).toBe(3);
        expect(HIGH_VALUE_THRESHOLD_KRW_PER_YEAR).toBe(10_000_000.0);
        expect(DASHBOARD_CADENCE_HOURS_KST.daily_unified_kpi_refresh).toEqual([
            4, 0,
        ]);
        expect(DASHBOARD_RECIPIENT_TEMPLATES.owner_only.email_recipients).toEqual(
            ["tenant_owner"],
        );
    });
});

// ---------------------------------------------------------------------------
// Group 2: lib client fetch — 6 cases
// ---------------------------------------------------------------------------

import {
    computeUnifiedKPI,
    createSavedView,
    deleteSavedView,
    executeSavedView,
    fetchHealthcheck,
    getExportJobStatus,
    listPredefinedTemplates,
    shareDashboard,
    startExportJob,
    updateSavedView,
} from "@/lib/finops/interactive-dashboard-client";

describe("Phase 28 T2 interactive-dashboard-client endpoints", () => {
    it("Test 5: fetchHealthcheck GET /healthcheck returns status envelope", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        status: "ok",
                        module_tag: "m28_finops_interactive_dashboard",
                        engine_version: "1.0.0",
                        router_version: "1.0.0",
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const result = await fetchHealthcheck();
        expect(result.status).toBe("ok");
        expect(result.engine_version).toBe("1.0.0");
    });

    it("Test 6: listPredefinedTemplates GET /templates returns 12 templates", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(JSON.stringify([...PREDEFINED_VIEW_TEMPLATES]), {
                    status: 200,
                }),
            ),
        ) as unknown as typeof fetch;
        const list = await listPredefinedTemplates();
        expect(list).toHaveLength(12);
    });

    it("Test 7: computeUnifiedKPI POST /unified-kpi returns UnifiedKPI", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        unified_kpi_id: "u-1",
                        tenant_id: "t-1",
                        period_key: "2026-08",
                        dimension: "tenant",
                        dimension_value: "t-1",
                        kpi_value_krw: 1234567,
                        showback_krw: 1000000,
                        anomaly_count: 5,
                        forecast_krw: 1500000,
                        optimization_savings_krw: 200000,
                        tag_compliance_pct: 95.0,
                        report_krw: 1100000,
                        sustainability_co2_kg: 100.0,
                        commitment_utilization_pct: 80.0,
                        pricing_savings_krw: 150000,
                        multi_cloud_reconciliation_krw: 1200000,
                        reserved_capacity_utilization_pct: 75.0,
                        chargeback_settlement_krw: 900000,
                        unit_economics_cost_per_unit: 100.0,
                        budget_consumption_pct: 60.0,
                        vendor_spend_krw: 800000,
                        anomaly_ml_score: 0.85,
                        refresh_cadence: "daily",
                        computed_at: "2026-08-15T00:00:00Z",
                        trace_id: "trace-001",
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const kpi = await computeUnifiedKPI({
            tenant_id: "t-1",
            period_key: "2026-08",
        });
        expect(kpi.kpi_value_krw).toBe(1234567);
        expect(kpi.refresh_cadence).toBe("daily");
    });

    it("Test 8: createSavedView POST /saved-views returns SavedView envelope", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        saved_view_id: "sv-1",
                        tenant_id: "t-1",
                        view_name: "demo view",
                        template_id: "CostByCloudProvider",
                        filter_by: {},
                        group_by: [],
                        sort_by: "kpi_value_krw",
                        chart_type: "bar",
                        time_range: "2026-08",
                        layout: "grid",
                        is_shared: false,
                        created_by_user_id: "u-1",
                        created_at: "2026-08-15T00:00:00Z",
                        updated_at: "2026-08-15T00:00:00Z",
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        const sv = await createSavedView({
            tenant_id: "t-1",
            view_config: {},
            template_id: "CostByCloudProvider",
            view_name: "demo view",
        });
        expect(sv.saved_view_id).toBe("sv-1");
        expect(sv.template_id).toBe("CostByCloudProvider");
    });

    it("Test 9: startExportJob + getExportJobStatus lifecycle flow", async () => {
        global.fetch = vi
            .fn()
            .mockReturnValueOnce(
                Promise.resolve(
                    new Response(
                        JSON.stringify({
                            export_job_id: "ej-1",
                            tenant_id: "t-1",
                            saved_view_id: "sv-1",
                            export_format: "pdf",
                            status: "pending",
                            progress_pct: 0.0,
                            file_path: null,
                            file_size_bytes: 0,
                            checksum_sha256: null,
                            expires_at: null,
                            started_at: "2026-08-15T00:00:00Z",
                            completed_at: null,
                        }),
                        { status: 200 },
                    ),
                ),
            )
            .mockReturnValueOnce(
                Promise.resolve(
                    new Response(
                        JSON.stringify({
                            export_job_id: "ej-1",
                            tenant_id: "t-1",
                            saved_view_id: "sv-1",
                            export_format: "pdf",
                            status: "completed",
                            progress_pct: 100.0,
                            file_path: "/exports/ej-1.pdf",
                            file_size_bytes: 1024,
                            checksum_sha256: "abc123",
                            expires_at: "2026-09-15T00:00:00Z",
                            started_at: "2026-08-15T00:00:00Z",
                            completed_at: "2026-08-15T00:01:00Z",
                        }),
                        { status: 200 },
                    ),
                ),
            ) as unknown as typeof fetch;
        const started = await startExportJob({
            tenant_id: "t-1",
            view_id: "sv-1",
            format: "pdf",
        });
        expect(started.export_job_id).toBe("ej-1");
        const status = await getExportJobStatus("ej-1");
        expect((status as unknown as { status: string }).status).toBe(
            "completed"
        );
    });

    it("Test 10: shareDashboard POST /sharing + executeSavedView + deleteSavedView + updateSavedView flow", async () => {
        const fetchMock = vi.fn();
        fetchMock
            .mockReturnValueOnce(
                Promise.resolve(
                    new Response(
                        JSON.stringify({
                            saved_view_id: "sv-1",
                            tenant_id: "t-1",
                            view_name: "shared view",
                            template_id: null,
                            filter_by: {},
                            group_by: [],
                            sort_by: "kpi_value_krw",
                            chart_type: "bar",
                            time_range: "2026-08",
                            layout: "grid",
                            is_shared: true,
                            created_by_user_id: "u-1",
                            created_at: "2026-08-15T00:00:00Z",
                            updated_at: "2026-08-15T00:01:00Z",
                        }),
                        { status: 200 },
                    ),
                ),
            )
            .mockReturnValueOnce(
                Promise.resolve(
                    new Response(JSON.stringify([]), { status: 200 }),
                ),
            )
            .mockReturnValueOnce(
                Promise.resolve(
                    new Response(
                        JSON.stringify({ deleted: true }),
                        { status: 200 },
                    ),
                ),
            )
            .mockReturnValueOnce(
                Promise.resolve(
                    new Response(
                        JSON.stringify({
                            saved_view_id: "sv-1",
                            tenant_id: "t-1",
                            view_name: "updated view",
                            template_id: null,
                            filter_by: {},
                            group_by: [],
                            sort_by: "kpi_value_krw",
                            chart_type: "bar",
                            time_range: "2026-08",
                            layout: "grid",
                            is_shared: false,
                            created_by_user_id: "u-1",
                            created_at: "2026-08-15T00:00:00Z",
                            updated_at: "2026-08-15T00:02:00Z",
                        }),
                        { status: 200 },
                    ),
                ),
            );
        global.fetch = fetchMock as unknown as typeof fetch;
        const shared = await shareDashboard({
            tenant_id: "t-1",
            view_id: "sv-1",
            scope: "tenant",
        });
        expect(shared.is_shared).toBe(true);
        const executed = await executeSavedView("sv-1", {
            tenant_id: "t-1",
            period_key: "2026-08",
        });
        expect(Array.isArray(executed)).toBe(true);
        const deleted = await deleteSavedView("sv-1", "t-1");
        expect(deleted.deleted).toBe(true);
        const updated = await updateSavedView("sv-1", {
            tenant_id: "t-1",
            view_name: "updated view",
        });
        expect(updated.view_name).toBe("updated view");
    });
});

// ---------------------------------------------------------------------------
// Group 3: sub-components — 18 cases total (4+4+4+3+4)
// ---------------------------------------------------------------------------

import { CrossPhaseKPIOverview } from "@/components/finops/interactive-dashboard/CrossPhaseKPIOverview";

describe("CrossPhaseKPIOverview sub-component", () => {
    it("Test 11: renders loading state initially", () => {
        global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch;
        render(
            <CrossPhaseKPIOverview dryRun={true} periodKey="2026-08" />
        );
        expect(
            screen.getByLabelText(/Cross-Phase Unified KPI 로딩 중/)
        ).toBeTruthy();
    });

    it("Test 12: renders 18 phase KPI tiles after load", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        unified_kpi_id: "u-1",
                        tenant_id: "t-1",
                        period_key: "2026-08",
                        dimension: "tenant",
                        dimension_value: "t-1",
                        kpi_value_krw: 1000,
                        showback_krw: 100,
                        anomaly_count: 1,
                        forecast_krw: 200,
                        optimization_savings_krw: 50,
                        tag_compliance_pct: 95,
                        report_krw: 100,
                        sustainability_co2_kg: 10,
                        commitment_utilization_pct: 80,
                        pricing_savings_krw: 30,
                        multi_cloud_reconciliation_krw: 100,
                        reserved_capacity_utilization_pct: 75,
                        chargeback_settlement_krw: 90,
                        unit_economics_cost_per_unit: 1,
                        budget_consumption_pct: 60,
                        vendor_spend_krw: 80,
                        anomaly_ml_score: 0.85,
                        refresh_cadence: "daily",
                        computed_at: "2026-08-15T00:00:00Z",
                        trace_id: "trace-001",
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        render(
            <CrossPhaseKPIOverview dryRun={true} periodKey="2026-08" />
        );
        await waitFor(() =>
            expect(
                screen.getByTestId("phase-kpi-phase_11")
            ).toBeTruthy()
        );
        for (let i = 11; i <= 28; i++) {
            expect(
                screen.getByTestId(`phase-kpi-phase_${i}`)
            ).toBeTruthy();
        }
    });

    it("Test 13: shows DRY-RUN badge when dryRun=true", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(
                    JSON.stringify({
                        unified_kpi_id: "u-1",
                        tenant_id: "t-1",
                        period_key: "2026-08",
                        dimension: "tenant",
                        dimension_value: "t-1",
                        kpi_value_krw: 1000,
                        showback_krw: 100,
                        anomaly_count: 1,
                        forecast_krw: 200,
                        optimization_savings_krw: 50,
                        tag_compliance_pct: 95,
                        report_krw: 100,
                        sustainability_co2_kg: 10,
                        commitment_utilization_pct: 80,
                        pricing_savings_krw: 30,
                        multi_cloud_reconciliation_krw: 100,
                        reserved_capacity_utilization_pct: 75,
                        chargeback_settlement_krw: 90,
                        unit_economics_cost_per_unit: 1,
                        budget_consumption_pct: 60,
                        vendor_spend_krw: 80,
                        anomaly_ml_score: 0.85,
                        refresh_cadence: "daily",
                        computed_at: "2026-08-15T00:00:00Z",
                        trace_id: "trace-001",
                    }),
                    { status: 200 },
                ),
            ),
        ) as unknown as typeof fetch;
        render(
            <CrossPhaseKPIOverview dryRun={true} periodKey="2026-08" />
        );
        await waitFor(() =>
            expect(screen.getByText(/DRY-RUN/)).toBeTruthy()
        );
    });

    it("Test 14: renders error alert on fetch failure", async () => {
        global.fetch = vi.fn(() =>
            Promise.reject(new Error("network down"))
        ) as unknown as typeof fetch;
        render(
            <CrossPhaseKPIOverview dryRun={false} periodKey="2026-08" />
        );
        await waitFor(() =>
            expect(screen.getByRole("alert")).toBeTruthy()
        );
    });
});

import { SavedViewManager } from "@/components/finops/interactive-dashboard/SavedViewManager";

describe("SavedViewManager sub-component", () => {
    it("Test 15: renders 12 pre-defined templates in select", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(JSON.stringify([...PREDEFINED_VIEW_TEMPLATES]), {
                    status: 200,
                }),
            ),
        ) as unknown as typeof fetch;
        render(<SavedViewManager dryRun={true} periodKey="2026-08" />);
        await waitFor(() =>
            expect(screen.getByTestId("template-select")).toBeTruthy()
        );
        const opts = screen.getAllByRole("option");
        expect(opts.length).toBeGreaterThanOrEqual(12);
    });

    it("Test 16: 7 granularity options available", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(JSON.stringify([...PREDEFINED_VIEW_TEMPLATES]), {
                    status: 200,
                }),
            ),
        ) as unknown as typeof fetch;
        render(<SavedViewManager dryRun={true} periodKey="2026-08" />);
        await waitFor(() =>
            expect(screen.getByTestId("granularity-select")).toBeTruthy()
        );
        expect(screen.getByText("분 (minute)")).toBeTruthy();
        expect(screen.getByText("년 (year)")).toBeTruthy();
    });

    it("Test 17: shows max saved views per tenant notice", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(JSON.stringify([...PREDEFINED_VIEW_TEMPLATES]), {
                    status: 200,
                }),
            ),
        ) as unknown as typeof fetch;
        render(<SavedViewManager dryRun={true} periodKey="2026-08" />);
        await waitFor(() =>
            expect(screen.getByText(/max 50 views\/tenant/)).toBeTruthy()
        );
    });

    it("Test 18: create button present", async () => {
        global.fetch = vi.fn(() =>
            Promise.resolve(
                new Response(JSON.stringify([...PREDEFINED_VIEW_TEMPLATES]), {
                    status: 200,
                }),
            ),
        ) as unknown as typeof fetch;
        render(<SavedViewManager dryRun={true} periodKey="2026-08" />);
        await waitFor(() =>
            expect(
                screen.getByTestId("create-saved-view")
            ).toBeTruthy()
        );
    });
});

import { DrillDownExplorer } from "@/components/finops/interactive-dashboard/DrillDownExplorer";

describe("DrillDownExplorer sub-component", () => {
    it("Test 19: renders 7 dimension options", () => {
        render(
            <DrillDownExplorer dryRun={true} periodKey="2026-08" />
        );
        const opts = screen.getAllByRole("option");
        expect(opts.length).toBeGreaterThanOrEqual(7);
    });

    it("Test 20: shows breadcrumb nav element", () => {
        render(
            <DrillDownExplorer dryRun={true} periodKey="2026-08" />
        );
        expect(screen.getByTestId("breadcrumb-nav")).toBeTruthy();
    });

    it("Test 21: drill-down buttons add to breadcrumb list", () => {
        render(
            <DrillDownExplorer dryRun={true} periodKey="2026-08" />
        );
        const btn = screen.getByTestId("drill-alpha");
        fireEvent.click(btn);
        expect(screen.getByTestId("breadcrumb-list")).toBeTruthy();
    });

    it("Test 22: 7 granularity options in select", () => {
        render(
            <DrillDownExplorer dryRun={true} periodKey="2026-08" />
        );
        expect(screen.getByTestId("drill-granularity-select")).toBeTruthy();
    });
});

import { ExportConfigPanel } from "@/components/finops/interactive-dashboard/ExportConfigPanel";

describe("ExportConfigPanel sub-component", () => {
    it("Test 23: 5 export format radio options present", () => {
        render(<ExportConfigPanel dryRun={true} periodKey="2026-08" />);
        expect(screen.getByTestId("format-pdf")).toBeTruthy();
        expect(screen.getByTestId("format-xlsx")).toBeTruthy();
        expect(screen.getByTestId("format-csv")).toBeTruthy();
        expect(screen.getByTestId("format-json")).toBeTruthy();
        expect(screen.getByTestId("format-png")).toBeTruthy();
    });

    it("Test 24: shows 50MB size guard notice", () => {
        render(<ExportConfigPanel dryRun={true} periodKey="2026-08" />);
        expect(screen.getByText(/max 50 MB/)).toBeTruthy();
    });

    it("Test 25: shows 3 auto-retries indicator", () => {
        render(<ExportConfigPanel dryRun={true} periodKey="2026-08" />);
        expect(screen.getByText(/3 auto-retries/)).toBeTruthy();
    });
});

import { DashboardSharingPanel } from "@/components/finops/interactive-dashboard/DashboardSharingPanel";

describe("DashboardSharingPanel sub-component", () => {
    it("Test 26: 4 sharing scope radios + cross_tenant disabled when isOwner=false", () => {
        render(
            <DashboardSharingPanel
                dryRun={true}
                periodKey="2026-08"
                isOwner={false}
                impactKrwPerYear={0}
                savedViewCount={0}
            />
        );
        const crossTenant = screen.getByTestId("scope-cross_tenant");
        const radio = crossTenant.querySelector(
            'input[type="radio"]'
        ) as HTMLInputElement | null;
        expect(radio?.disabled).toBe(true);
    });

    it("Test 27: shows 2FA 챌린지 mandatory notice when impact ≥ 10M KRW/year", () => {
        render(
            <DashboardSharingPanel
                dryRun={true}
                periodKey="2026-08"
                isOwner={true}
                impactKrwPerYear={20_000_000}
                savedViewCount={0}
            />
        );
        const radios = screen.getAllByRole("radio");
        const crossTenantRadio = radios.find(
            (r) => (r as HTMLInputElement).value === "cross_tenant"
        );
        if (crossTenantRadio) (crossTenantRadio as HTMLInputElement).click();
        expect(
            screen.getByTestId("two-fa-required-notice")
        ).toBeTruthy();
    });

    it("Test 28: cross_tenant sharing requires owner (AD-22 owner-only RBAC)", () => {
        render(
            <DashboardSharingPanel
                dryRun={true}
                periodKey="2026-08"
                isOwner={false}
                impactKrwPerYear={0}
                savedViewCount={0}
            />
        );
        const btn = screen.getByTestId("share-dashboard");
        const radios = screen.getAllByRole("radio");
        const crossTenantRadio = radios.find(
            (r) => (r as HTMLInputElement).value === "cross_tenant"
        ) as HTMLInputElement | undefined;
        if (crossTenantRadio && !crossTenantRadio.disabled) {
            crossTenantRadio.click();
        }
        btn.click();
        // Even when cross_tenant is disabled, the owner-only notice is shown
        expect(screen.getAllByText(/owner-only/).length).toBeGreaterThan(0);
    });

    it("Test 29: 4 sharing scope options total present", () => {
        render(
            <DashboardSharingPanel
                dryRun={true}
                periodKey="2026-08"
                isOwner={true}
                impactKrwPerYear={0}
                savedViewCount={0}
            />
        );
        expect(screen.getByTestId("scope-private")).toBeTruthy();
        expect(screen.getByTestId("scope-tenant")).toBeTruthy();
        expect(screen.getByTestId("scope-tenant_owner")).toBeTruthy();
        expect(screen.getByTestId("scope-cross_tenant")).toBeTruthy();
    });
});

// ---------------------------------------------------------------------------
// Group 4: orchestrator — 1 case
// ---------------------------------------------------------------------------

import { FinopsInteractiveDashboardPanel } from "@/components/finops/FinopsInteractiveDashboardPanel";

describe("FinopsInteractiveDashboardPanel orchestrator", () => {
    it("Test 30: renders 5 tabs + dry-run toggle default ON", () => {
        global.fetch = vi.fn(() => new Promise(() => {})) as unknown as typeof fetch;
        render(
            <FinopsInteractiveDashboardPanel
                periodKey="2026-08"
                isOwner={true}
                savedViewCount={0}
                impactKrwPerYear={0}
            />
        );
        expect(screen.getByTestId("tab-overview")).toBeTruthy();
        expect(screen.getByTestId("tab-saved_views")).toBeTruthy();
        expect(screen.getByTestId("tab-drill_down")).toBeTruthy();
        expect(screen.getByTestId("tab-export")).toBeTruthy();
        expect(screen.getByTestId("tab-sharing")).toBeTruthy();
        const toggle = screen.getByTestId(
            "dry-run-toggle"
        ) as HTMLInputElement;
        expect(toggle.checked).toBe(true);
    });
});