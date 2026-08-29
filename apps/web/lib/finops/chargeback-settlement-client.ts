/**
 * Phase 22 wire (cj-style 160번째) — FinOps Chargeback Settlement Client.
 *
 * Mirrors Python
 * `apps/api/modules/finops/chargeback_settlement/chargeback_settlement_routes.py`
 * verbatim (CR 12-5 D-PARITY-01 inversion).
 *
 * 8 endpoints:
 * 1. createSettlementRule — POST /api/v1/finops/chargeback-settlement/settlement-rules
 * 2. computeAllocation — POST /api/v1/finops/chargeback-settlement/allocation
 * 3. generateInvoice — POST /api/v1/finops/chargeback-settlement/invoice
 * 4. reconcileSettlement — POST /api/v1/finops/chargeback-settlement/reconciliation
 * 5. executeDispatch — POST /api/v1/finops/chargeback-settlement/dispatch
 * 6. fetchCadencePreview — GET /api/v1/finops/chargeback-settlement/cadence-preview
 * 7. runDryRun — POST /api/v1/finops/chargeback-settlement/dispatch (dry_run=true)
 * 8. healthcheck — GET /api/v1/finops/chargeback-settlement/healthcheck
 */

import type {
    AllocationDimension,
    InvoiceFormat,
    SettlementCadence,
    SettlementRule,
    SettlementResult,
    ReconciliationResult,
} from "@/lib/finops/chargeback-settlement-types";

const API_BASE_URL = "/api/v1/finops/chargeback-settlement";

export interface CreateSettlementRuleRequest {
    period_key: string;
    rule_name: string;
    rule_type: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    target_amount_krw: number;
    target_dimensions: AllocationDimension[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    five_module_inputs: Record<string, number>;
    settlement_status?: string;
    requires_2fa_challenge?: boolean;
    dry_run?: boolean;
}

export interface ComputeAllocationRequest {
    result_id: string;
    period_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    total_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    dimension_amounts: Record<string, number>;
    target_dimensions: AllocationDimension[];
    settlement_status?: string;
    dry_run?: boolean;
}

export interface GenerateInvoiceRequest {
    result_id: string;
    period_key: string;
    invoice_format: InvoiceFormat;
    settlement_result: Record<string, unknown>;
    allocation_lines: Array<{
        dimension: string;
        dimension_value: string;
        // eslint-disable-next-line @typescript-eslint/no-restricted-types
        weight: number;
        // eslint-disable-next-line @typescript-eslint/no-restricted-types
        allocated_amount_krw: number;
    }>;
    recipient_template?: string;
    dry_run?: boolean;
}

export interface ReconcileSettlementRequest {
    result_id: string;
    period_key: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    allocation_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    invoice_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    ledger_amount_krw: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    target_amount_krw?: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    tolerance_pct?: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    max_retries?: number;
    dry_run?: boolean;
}

export interface DispatchRequest {
    cadence: SettlementCadence;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    five_module_inputs: Record<string, number>;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    target_amount_krw: number;
    target_dimensions: AllocationDimension[];
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    invoice_amount_krw?: number;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    ledger_amount_krw?: number;
    dry_run?: boolean;
}

export interface DryRunRequest {
    cadence: SettlementCadence;
    tenant_id: string;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    five_module_inputs: Record<string, number>;
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    target_amount_krw: number;
    target_dimensions: AllocationDimension[];
}

async function postJson<T>(path: string, body: object): Promise<T> {
    const res = await fetch(path, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) {
        throw new Error(`POST ${path} failed: ${res.status}`);
    }
    return res.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
    const res = await fetch(path, { method: "GET" });
    if (!res.ok) {
        throw new Error(`GET ${path} failed: ${res.status}`);
    }
    return res.json() as Promise<T>;
}

export async function createSettlementRule(
    req: CreateSettlementRuleRequest
): Promise<{ settlement_rule: SettlementRule; dry_run: boolean }> {
    return postJson(`${API_BASE_URL}/settlement-rules`, req);
}

export async function computeAllocation(
    req: ComputeAllocationRequest
): Promise<{ settlement_result: SettlementResult; dry_run: boolean }> {
    return postJson(`${API_BASE_URL}/allocation`, req);
}

export async function generateInvoice(
    req: GenerateInvoiceRequest
): Promise<{ artifact: Record<string, unknown>; dry_run: boolean }> {
    return postJson(`${API_BASE_URL}/invoice`, req);
}

export async function reconcileSettlement(
    req: ReconcileSettlementRequest
): Promise<{ reconciliation: ReconciliationResult; dry_run: boolean }> {
    return postJson(`${API_BASE_URL}/reconciliation`, req);
}

export async function executeDispatch(
    req: DispatchRequest
): Promise<{ dispatch: Record<string, unknown>; dry_run: boolean }> {
    return postJson(`${API_BASE_URL}/dispatch`, req);
}

export async function fetchCadencePreview(
    cadence: SettlementCadence
): Promise<Record<string, unknown>> {
    const params = new URLSearchParams({ cadence });
    return getJson(`${API_BASE_URL}/cadence-preview?${params.toString()}`);
}

export async function runDryRun(
    req: DryRunRequest
): Promise<Record<string, unknown>> {
    return postJson(`${API_BASE_URL}/dispatch`, { ...req, dry_run: true });
}

export async function healthcheck(): Promise<Record<string, unknown>> {
    return getJson(`${API_BASE_URL}/healthcheck`);
}
