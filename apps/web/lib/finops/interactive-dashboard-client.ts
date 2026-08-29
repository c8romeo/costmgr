/**
 * interactive-dashboard-client — Phase 28 T2 TypeScript fetch client
 * for FinOps Interactive Dashboard.
 *
 * Epic 28 T2 frontend follow-up wire (cj-style 197번째) — Mirrors
 * FastAPI router endpoints in
 * `apps/api/modules/finops/interactive_dashboard/dashboard_router.py`.
 *
 * 11 endpoints:
 * 1. fetchHealthcheck — GET /api/v1/admin/finops/interactive-dashboard/healthcheck
 * 2. createSavedView — POST /saved-views
 * 3. readSavedView — GET /saved-views/{view_id}
 * 4. updateSavedView — PUT /saved-views/{view_id}
 * 5. deleteSavedView — DELETE /saved-views/{view_id}
 * 6. executeSavedView — POST /saved-views/{view_id}/execute
 * 7. computeUnifiedKPI — POST /unified-kpi
 * 8. startExportJob — POST /exports
 * 9. getExportJobStatus — GET /exports/{job_id}
 * 10. shareDashboard — POST /sharing
 * 11. listPredefinedTemplates — GET /templates
 *
 * CR 1-1 RSC boundary + CR 12-5 D-PARITY-01 + AD-22 owner-only RBAC.
 */

import type {
    DashboardHealthcheck,
    DrillDownDimension,
    DrillDownGranularity,
    ExportFormat,
    ExportJob,
    KPIRefreshCadence,
    SavedView,
    SharingGrant,
    UnifiedKPI,
} from "./interactive-dashboard-types";

const API_BASE = "/api/v1/admin/finops/interactive-dashboard";

async function get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        cache: "no-store",
    });
    if (!res.ok) {
        throw new Error(`GET ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

async function post<T, B>(path: string, body: B): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        cache: "no-store",
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`POST ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

async function put<T, B>(path: string, body: B): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        cache: "no-store",
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`PUT ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

async function del<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        cache: "no-store",
    });
    if (!res.ok) {
        throw new Error(`DELETE ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

export async function fetchHealthcheck(): Promise<DashboardHealthcheck> {
    return get<DashboardHealthcheck>("/healthcheck");
}

export interface CreateSavedViewInput {
    tenant_id: string;
    view_config: Record<string, unknown>;
    template_id?: string | null;
    view_name?: string;
    created_by_user_id?: string;
}

export async function createSavedView(
    input: CreateSavedViewInput
): Promise<SavedView> {
    return post<SavedView, CreateSavedViewInput>("/saved-views", input);
}

export async function readSavedView(
    viewId: string,
    tenantId: string
): Promise<SavedView> {
    const qs = new URLSearchParams({ tenant_id: tenantId }).toString();
    return get<SavedView>(`/saved-views/${encodeURIComponent(viewId)}?${qs}`);
}

export interface UpdateSavedViewInput {
    tenant_id: string;
    view_config?: Record<string, unknown>;
    view_name?: string;
    is_shared?: boolean;
}

export async function updateSavedView(
    viewId: string,
    input: UpdateSavedViewInput
): Promise<SavedView> {
    return put<SavedView, UpdateSavedViewInput>(
        `/saved-views/${encodeURIComponent(viewId)}`,
        input
    );
}

export async function deleteSavedView(
    viewId: string,
    tenantId: string
): Promise<{ deleted: boolean }> {
    const qs = new URLSearchParams({ tenant_id: tenantId }).toString();
    return del<{ deleted: boolean }>(
        `/saved-views/${encodeURIComponent(viewId)}?${qs}`
    );
}

export interface ExecuteSavedViewInput {
    tenant_id: string;
    period_key?: string;
}

export async function executeSavedView(
    viewId: string,
    input: ExecuteSavedViewInput
): Promise<UnifiedKPI[]> {
    return post<UnifiedKPI[], ExecuteSavedViewInput>(
        `/saved-views/${encodeURIComponent(viewId)}/execute`,
        input
    );
}

export interface ComputeUnifiedKPIInput {
    tenant_id: string;
    period_key?: string;
    modules?: string[];
    module_values?: Record<string, number>;
    dimension?: DrillDownDimension;
    dimension_value?: string;
}

export async function computeUnifiedKPI(
    input: ComputeUnifiedKPIInput
): Promise<UnifiedKPI> {
    return post<UnifiedKPI, ComputeUnifiedKPIInput>("/unified-kpi", input);
}

export interface StartExportJobInput {
    tenant_id: string;
    view_id: string;
    format?: ExportFormat;
    options?: Record<string, unknown>;
}

export async function startExportJob(
    input: StartExportJobInput
): Promise<ExportJob> {
    return post<ExportJob, StartExportJobInput>("/exports", input);
}

export async function getExportJobStatus(
    jobId: string
): Promise<ExportJob> {
    return get<ExportJob>(`/exports/${encodeURIComponent(jobId)}`);
}

export interface ShareDashboardInput {
    tenant_id: string;
    view_id: string;
    scope?: string;
    granted_to_user_id?: string;
}

export async function shareDashboard(
    input: ShareDashboardInput
): Promise<SavedView> {
    return post<SavedView, ShareDashboardInput>("/sharing", input);
}

export async function listPredefinedTemplates(): Promise<string[]> {
    return get<string[]>("/templates");
}

/** Re-export typed enum for caller convenience */
export type {
    DrillDownDimension,
    DrillDownGranularity,
    ExportFormat,
    KPIRefreshCadence,
    SharingGrant,
};