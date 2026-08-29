/**
 * vendor-management-client — Phase 25 TypeScript fetch client for FinOps Vendor Management.
 *
 * Phase 25 wire (cj-style 173번째) — Mirrors FastAPI router endpoints
 * in `apps/api/modules/finops/vendor_management/vendor_management_routes.py`.
 *
 * 9 endpoints:
 * 1. fetchVendorCatalog — GET /api/finops/vendor-management/vendors
 * 2. createVendor — POST /api/finops/vendor-management/vendors
 * 3. blacklistVendor — POST /api/finops/vendor-management/vendors/{id}/blacklist
 * 4. runVendorSelection — POST /api/finops/vendor-management/selection
 * 5. fetchVendorSelection — GET /api/finops/vendor-management/selection
 * 6. fetchVendorContracts — GET /api/finops/vendor-management/contracts
 * 7. advanceContractLifecycle — POST /api/finops/vendor-management/contracts/{id}/advance
 * 8. fetchVendorPerformance — GET /api/finops/vendor-management/performance
 * 9. fetchVendorSpendAttribution — GET /api/finops/vendor-management/spend
 */

import type {
    Vendor,
    VendorSelectionScore,
    VendorContract,
    VendorPerformanceScorecard,
    VendorSpendAttribution,
    VendorCategory,
    VendorContractLifecycle,
} from "./vendor-management-types";

const API_BASE = "/api/finops/vendor-management";

async function get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "GET",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
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
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`POST ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

async function patch<T, B>(path: string, body: B): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`PATCH ${path} failed: ${res.statusText}`);
    }
    return res.json();
}

export async function fetchVendorCatalog(
    category?: VendorCategory,
    status?: string
): Promise<{ vendors: Vendor[] }> {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (status) params.set("status_filter", status);
    const qs = params.toString();
    return get(`/vendors${qs ? `?${qs}` : ""}`);
}

export interface CreateVendorInput {
    tenant_id: string;
    vendor_name: string;
    vendor_category: VendorCategory;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    performance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    reliability_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    compliance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    strategic_fit_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    contract_count?: number;
}

export async function createVendor(
    input: CreateVendorInput
): Promise<Vendor> {
    return post("/vendors", input);
}

export async function updateVendor(
    vendorId: string,
    input: Partial<CreateVendorInput>
): Promise<Vendor> {
    return patch(`/vendors/${vendorId}`, input);
}

export async function blacklistVendor(
    vendorId: string,
    reason: string,
    severity: string = "high"
): Promise<{ vendor_id: string; blacklisted: true; reason: string }> {
    return post(`/vendors/${vendorId}/blacklist`, { reason, severity });
}

export interface VendorSelectionInput {
    vendor_ids: string[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    threshold?: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    candidate_limit?: number;
}

export async function runVendorSelection(
    input: VendorSelectionInput
): Promise<{
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    threshold: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    candidate_limit: number;
    selected_vendors: VendorSelectionScore[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    selected_count: number;
}> {
    return post("/selection", input);
}

export async function fetchVendorSelection(): Promise<{
    selected_vendors: VendorSelectionScore[];
}> {
    return get("/selection");
}

export async function fetchVendorContracts(): Promise<{
    contracts: VendorContract[];
}> {
    return get("/contracts");
}

export async function advanceContractLifecycle(
    contractId: string,
    targetLifecycle: VendorContractLifecycle
): Promise<VendorContract> {
    return post(`/contracts/${contractId}/advance`, {
        target_lifecycle: targetLifecycle,
    });
}

export async function fetchVendorPerformance(): Promise<{
    scorecards: VendorPerformanceScorecard[];
}> {
    return get("/performance");
}

export async function fetchVendorSpendAttribution(): Promise<{
    attributions: VendorSpendAttribution[];
}> {
    return get("/spend");
}

export async function dryRun(input: {
    vendor_name: string;
    vendor_category: VendorCategory;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    cost_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    performance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    reliability_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    compliance_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    strategic_fit_score: number;
}): Promise<{
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    weighted_score: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    selection_threshold: number;
    passes_threshold: boolean;
}> {
    return post("/dry-run", input);
}