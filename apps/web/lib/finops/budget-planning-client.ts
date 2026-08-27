/**
 * apps.web.lib.finops.budget-planning-client — Phase 24 TypeScript client.
 *
 * Phase 24 wire (cj-style 169번째) — FinOps Budget Planning pre-allocation
 * layer TypeScript client (PRD §F40.1~§F40.8 verbatim + AD-52 (a)~(g)
 * 7 sub-decisions).
 *
 * 8 NEW methods:
 * 1. createBudgetPlan
 * 2. allocateBudget
 * 3. submitForApproval
 * 4. approveStep
 * 5. computeBudgetVsActual
 * 6. triggerOverBudgetAlert
 * 7. fetchBudgetPlanningPlans
 * 8. fetchBudgetPlanningHealthcheck
 *
 * CR lessons applied:
 * - CR 12-5 D-PARITY-01 inversion — parity with backend budget_planning_routes.
 * - AD-52 (a)~(g) 7 sub-decisions.
 * - NFR18 ko-KR SSOT.
 */

import type {
    AllocateBudgetRequest,
    ApproveStepRequest,
    BudgetAllocationLine,
    BudgetApprovalStep,
    BudgetPlan,
    BudgetPlanningHealthcheck,
    BudgetVsActual,
    BudgetAlert,
    ComputeVsActualRequest,
    CreateBudgetPlanRequest,
    SubmitForApprovalRequest,
    TriggerAlertRequest,
} from "./budget-planning-types";

const BASE_URL = "/api/v1/finops/budget-planning";

async function request<T>(
    path: string,
    init?: RequestInit,
): Promise<T> {
    const res = await fetch(`${BASE_URL}${path}`, {
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...(init?.headers ?? {}),
        },
    });
    if (!res.ok) {
        throw new Error(`HTTP ${res.status} ${res.statusText}`);
    }
    return res.json() as Promise<T>;
}

export async function createBudgetPlan(
    req: CreateBudgetPlanRequest,
): Promise<BudgetPlan> {
    const params = new URLSearchParams();
    params.set("tenant_id", req.tenant_id);
    params.set("period_key", req.period_key);
    params.set("period_type", req.period_type);
    params.set("total_budget_amount", String(req.total_budget_amount));
    params.set("dry_run", String(req.dry_run ?? true));
    if (req.actor_id) params.set("actor_id", req.actor_id);

    const res = await request<{ status: string; plan: BudgetPlan }>(
        `/plans?${params.toString()}`,
        {
            method: "POST",
            body: JSON.stringify({
                scope: req.scope,
                approval_chain: req.approval_chain ?? [],
            }),
        },
    );
    return res.plan;
}

export async function allocateBudget(
    req: AllocateBudgetRequest,
): Promise<BudgetAllocationLine[]> {
    const res = await request<{ status: string; lines: BudgetAllocationLine[] }>(
        `/plans/${req.plan_id}/allocate?plan_id=${req.plan_id}&tenant_id=${req.tenant_id}&total_budget_amount=${req.total_budget_amount}`,
        {
            method: "POST",
            body: JSON.stringify({
                dim_rows: req.dim_rows,
                per_tenant_override: req.per_tenant_override,
                actor_id: req.actor_id,
                dry_run: req.dry_run,
            }),
        },
    );
    return res.lines;
}

export async function submitForApproval(
    req: SubmitForApprovalRequest,
): Promise<BudgetApprovalStep[]> {
    const res = await request<{ status: string; steps: BudgetApprovalStep[]; count: number }>(
        `/plans/${req.plan_id}/submit-approval?plan_id=${req.plan_id}&tenant_id=${req.tenant_id}&plan_total_budget_amount=${req.plan_total_budget_amount}`,
        {
            method: "POST",
            body: JSON.stringify({
                approval_chain: req.approval_chain,
                actor_id: req.actor_id,
            }),
        },
    );
    return res.steps;
}

export async function approveStep(
    req: ApproveStepRequest,
): Promise<BudgetApprovalStep> {
    const params = new URLSearchParams();
    params.set("step_id", req.step_id);
    params.set("decision", req.decision);
    params.set("actor_id", req.actor_id);
    params.set("two_fa_verified", String(req.two_fa_verified ?? false));
    if (req.comment) params.set("comment", req.comment);

    const res = await request<{ status: string; step: BudgetApprovalStep }>(
        `/plans/${req.plan_id}/approve-step?${params.toString()}`,
        { method: "POST" },
    );
    return res.step;
}

export async function computeBudgetVsActual(
    req: ComputeVsActualRequest,
): Promise<BudgetVsActual[]> {
    const res = await request<{ status: string; rows: BudgetVsActual[]; count: number }>(
        `/plans/${req.plan_id}/vs-actual?plan_id=${req.plan_id}&tenant_id=${req.tenant_id}&period_key=${req.period_key}`,
        {
            method: "POST",
            body: JSON.stringify({
                actual_amounts: req.actual_amounts,
                actor_id: req.actor_id,
            }),
        },
    );
    return res.rows;
}

export async function triggerOverBudgetAlert(
    req: TriggerAlertRequest,
): Promise<BudgetAlert> {
    const params = new URLSearchParams();
    params.set("plan_id", req.plan_id);
    params.set("tenant_id", req.tenant_id);
    params.set("variance_pct", String(req.variance_pct));
    params.set("plan_total_budget_amount", String(req.plan_total_budget_amount));
    params.set("dry_run", String(req.dry_run ?? true));
    if (req.actor_id) params.set("actor_id", req.actor_id);

    const res = await request<{ status: string; alert: BudgetAlert }>(
        `/plans/${req.plan_id}/alerts/trigger?${params.toString()}`,
        { method: "POST" },
    );
    return res.alert;
}

export async function fetchBudgetPlanningPlans(
    tenant_id?: string,
): Promise<{ plans: BudgetPlan[]; count: number }> {
    const params = new URLSearchParams();
    if (tenant_id) params.set("tenant_id", tenant_id);
    return request<{ plans: BudgetPlan[]; count: number }>(
        `/plans?${params.toString()}`,
    );
}

export async function fetchBudgetPlanningHealthcheck(): Promise<BudgetPlanningHealthcheck> {
    return request<BudgetPlanningHealthcheck>(`/healthcheck`);
}
