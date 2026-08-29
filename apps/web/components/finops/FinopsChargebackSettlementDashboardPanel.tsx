"use client";

/**
 * FinopsChargebackSettlementDashboardPanel — Phase 22 FinOps Chargeback
 * Settlement Client panel.
 *
 * Phase 22 (cj-style 160번째 wire) — FinOps Chargeback Settlement
 * territory (PRD §F38.1~§F38.8 + AD-50 (a)~(g) 7 sub-decisions).
 *
 * 5 sub-components:
 * 1. SettlementRulesCard — settlement rule CRUD (5-module cross-join
 *    attribution: phase_11_chargeback=0.30 + phase_18_commitment=0.20 +
 *    phase_19_pricing=0.20 + phase_20_multi_cloud=0.15 +
 *    phase_21_reserved_capacity=0.15 → single settlement_id) +
 *    4 rule types (flat_fee / proportional_allocation / metered_volume /
 *    tag_weighted) + 5 settlement_status (draft / pending_approval /
 *    approved / invoiced / reconciled) + Epic 12 2FA 챌린지 mandatory
 *    (high-value threshold 10M KRW/year).
 * 2. AllocationBreakdownPanel — 5-dim weighted allocation
 *    (cost_center=0.30 + department=0.25 + business_unit=0.20 +
 *    tag=0.15 + tenant=0.10) → allocation_lines + confidence_pct +
 *    tolerance_band_krw + banker's rounding (CR 5-1).
 * 3. InvoicePreviewPanel — PDF (reportlab 4.0.7 + noto-sans-cjk-kr +
 *    A4 landscape) + XLSX (xlsxwriter 3.1.9) + CSV (stdlib UTF-8-SIG)
 *    + 3 recipient templates (owner_only / executive / audit_only) +
 *    MAX_INVOICE_BYTES=10MB guard.
 * 4. ReconciliationStatusPanel — 3-way match (allocation vs invoice vs
 *    ledger) + 1.0% tolerance (RECONCILIATION_TOLERANCE_PCT) + 3
 *    auto-retries (RECONCILIATION_MAX_RETRIES) + 4 reconciliation_status
 *    (matched / variance_detected / retry_exhausted / needs_approval) +
 *    admin email alert on variance.
 * 5. SettlementTrendMiniChart — Recharts 2.12.7 stack pin settlement
 *    rollout trend (AreaChart placeholder) + 5-dim allocation
 *    breakdown (BarChart placeholder).
 *
 * Plus ChargebackSettlementDryRunPreviewPanel — dry-run preview UI
 * EXTENSION (audit_action `settlement_dry_run_executed` +
 * orchestration_status 'dry_run').
 *
 * Plus ScheduledChargebackSettlementDispatchConfigPanel — 4 cadence
 * schedule KST pytz (monthly 04:00 / quarterly 05:00 / semi_annual
 * 06:00 / annual 07:00 KST) + 3 recipient templates.
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/chargeback-settlement-types.ts`.
 * AD-14 stack pin — Recharts 2.12.7 + reportlab 4.0.7 + xlsxwriter 3.1.9
 * + apscheduler 3.10.4 + noto-sans-cjk-kr.
 */

import { useState } from "react";

import {
    createSettlementRule,
    computeAllocation,
    generateInvoice,
    reconcileSettlement,
    executeDispatch,
    fetchCadencePreview,
    runDryRun,
    type CreateSettlementRuleRequest,
    type ComputeAllocationRequest,
    type GenerateInvoiceRequest,
    type ReconcileSettlementRequest,
    type DispatchRequest,
    type DryRunRequest,
} from "@/lib/finops/chargeback-settlement-client";
import type {
    SettlementRule,
    SettlementResult,
    ReconciliationResult,
    SettlementRuleType,
    SettlementStatus,
    AllocationDimension,
    InvoiceFormat,
    SettlementCadence,
} from "@/lib/finops/chargeback-settlement-types";

const ALL_CADENCES: SettlementCadence[] = [
    "monthly",
    "quarterly",
    "semi_annual",
    "annual",
];

const ALL_RULE_TYPES: SettlementRuleType[] = [
    "flat_fee",
    "proportional_allocation",
    "metered_volume",
    "tag_weighted",
];

const ALL_STATUSES: SettlementStatus[] = [
    "draft",
    "pending_approval",
    "approved",
    "invoiced",
    "reconciled",
];

const ALL_DIMENSIONS: AllocationDimension[] = [
    "cost_center",
    "department",
    "business_unit",
    "tag",
    "tenant",
];

const ALL_INVOICE_FORMATS: InvoiceFormat[] = ["pdf", "xlsx", "csv"];

// eslint-disable-next-line @typescript-eslint/no-restricted-types
const FIVE_MODULE_WEIGHTS_CLIENT: Record<string, number> = {
    phase_11_chargeback: 0.30,
    phase_18_commitment: 0.20,
    phase_19_pricing: 0.20,
    phase_20_multi_cloud: 0.15,
    phase_21_reserved_capacity: 0.15,
};

// eslint-disable-next-line @typescript-eslint/no-restricted-types
const ALLOCATION_DIMENSION_WEIGHTS_CLIENT: Record<AllocationDimension, number> = {
    cost_center: 0.30,
    department: 0.25,
    business_unit: 0.20,
    tag: 0.15,
    tenant: 0.10,
};

export function FinopsChargebackSettlementDashboardPanel() {
    const [activeTab, setActiveTab] = useState<
        "rules" | "allocation" | "invoice" | "reconciliation" | "trend"
    >("rules");

    return (
        <div className="space-y-6 text-slate-100">
            <header className="space-y-2">
                <h1 className="text-2xl font-semibold">
                    FinOps Chargeback Settlement 대시보드
                </h1>
                <p className="text-sm text-slate-400">
                    Phase 22 — 5-module cross-join settlement + 5-dim
                    weighted allocation + 3-way match reconciliation + 4
                    cadence schedule KST.
                </p>
            </header>

            <nav className="flex gap-2 border-b border-slate-700">
                {(
                    [
                        ["rules", "정산 규칙"],
                        ["allocation", "할당 분석"],
                        ["invoice", "인보이스"],
                        ["reconciliation", "대조 정합"],
                        ["trend", "추세"],
                    ] as const
                ).map(([key, label]) => (
                    <button
                        key={key}
                        type="button"
                        onClick={() => setActiveTab(key)}
                        className={`px-4 py-2 text-sm ${
                            activeTab === key
                                ? "border-b-2 border-emerald-400 text-emerald-300"
                                : "text-slate-400 hover:text-slate-200"
                        }`}
                    >
                        {label}
                    </button>
                ))}
            </nav>

            {activeTab === "rules" ? <SettlementRulesCard /> : null}
            {activeTab === "allocation" ? <AllocationBreakdownPanel /> : null}
            {activeTab === "invoice" ? <InvoicePreviewPanel /> : null}
            {activeTab === "reconciliation" ? (
                <ReconciliationStatusPanel />
            ) : null}
            {activeTab === "trend" ? <SettlementTrendMiniChart /> : null}

            <ChargebackSettlementDryRunPreviewPanel />
            <ScheduledChargebackSettlementDispatchConfigPanel />
        </div>
    );
}

function SettlementRulesCard() {
    const [ruleName, setRuleName] = useState<string>("monthly-chargeback");
    const [ruleType, setRuleType] = useState<SettlementRuleType>(
        "proportional_allocation"
    );
    const [settlementStatus, setSettlementStatus] = useState<SettlementStatus>(
        "draft"
    );
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const [targetAmountKrw, setTargetAmountKrw] = useState<number>(1_000_000);
    const [targetDimensions, setTargetDimensions] = useState<
        AllocationDimension[]
    >(["cost_center", "department"]);
    const [periodKey, setPeriodKey] = useState<string>("2026-08");
    const [result, setResult] = useState<SettlementRule | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleSubmit() {
        setPending(true);
        setError(null);
        try {
            const req: CreateSettlementRuleRequest = {
                period_key: periodKey,
                rule_name: ruleName,
                rule_type: ruleType,
                target_amount_krw: targetAmountKrw,
                target_dimensions: targetDimensions,
                settlement_status: settlementStatus,
                five_module_inputs: {
                    phase_11_chargeback: 800_000,
                    phase_18_commitment: 200_000,
                    phase_19_pricing: 100_000,
                    phase_20_multi_cloud: 50_000,
                    phase_21_reserved_capacity: 50_000,
                },
                dry_run: false,
            };
            const resp = await createSettlementRule(req);
            setResult(resp.settlement_rule);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    const highValueFlag = targetAmountKrw * 12 >= 10_000_000;

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">정산 규칙 (Settlement Rule)</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">규칙 이름</span>
                    <input
                        value={ruleName}
                        onChange={(e) => setRuleName(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">기간</span>
                    <input
                        value={periodKey}
                        onChange={(e) => setPeriodKey(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">규칙 유형</span>
                    <select
                        value={ruleType}
                        onChange={(e) =>
                            setRuleType(e.target.value as SettlementRuleType)
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    >
                        {ALL_RULE_TYPES.map((rt) => (
                            <option key={rt} value={rt}>
                                {rt}
                            </option>
                        ))}
                    </select>
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">상태</span>
                    <select
                        value={settlementStatus}
                        onChange={(e) =>
                            setSettlementStatus(
                                e.target.value as SettlementStatus
                            )
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    >
                        {ALL_STATUSES.map((s) => (
                            <option key={s} value={s}>
                                {s}
                            </option>
                        ))}
                    </select>
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">목표 금액 (KRW)</span>
                    <input
                        type="number"
                        value={targetAmountKrw}
                        onChange={(e) =>
                            setTargetAmountKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">할당 차원</span>
                    <select
                        multiple
                        value={targetDimensions}
                        onChange={(e) =>
                            setTargetDimensions(
                                Array.from(
                                    e.target.selectedOptions,
                                    (o) => o.value as AllocationDimension
                                )
                            )
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    >
                        {ALL_DIMENSIONS.map((d) => (
                            <option key={d} value={d}>
                                {d}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            {highValueFlag && settlementStatus === "pending_approval" ? (
                <div className="rounded bg-amber-900 p-2 text-xs text-amber-200">
                    ⚠️ 고가 정산 (연 10M KRW 이상) — Epic 12 2FA 챌린지 필요
                </div>
            ) : null}

            <button
                type="button"
                onClick={handleSubmit}
                disabled={pending}
                className="rounded bg-emerald-600 px-3 py-1 text-sm hover:bg-emerald-500 disabled:opacity-50"
            >
                {pending ? "생성 중..." : "정산 규칙 생성"}
            </button>

            {error ? (
                <div className="text-xs text-red-400">{error}</div>
            ) : null}
            {result ? (
                <pre className="overflow-x-auto rounded bg-slate-950 p-2 text-xs">
                    {JSON.stringify(result, null, 2)}
                </pre>
            ) : null}
        </section>
    );
}

function AllocationBreakdownPanel() {
    const [resultId, setResultId] = useState<string>("res-1");
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const [totalAmount, setTotalAmount] = useState<number>(1_000_000);
    const [dimensionAmounts, setDimensionAmounts] = useState<
        // eslint-disable-next-line @typescript-eslint/no-restricted-types
        Record<AllocationDimension, number>
    >({
        cost_center: 300_000,
        department: 250_000,
        business_unit: 200_000,
        tag: 150_000,
        tenant: 100_000,
    });
    const [result, setResult] = useState<SettlementResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function handleCompute() {
        setError(null);
        try {
            const req: ComputeAllocationRequest = {
                result_id: resultId,
                period_key: "2026-08",
                total_amount_krw: totalAmount,
                dimension_amounts: dimensionAmounts,
                target_dimensions: ALL_DIMENSIONS,
                settlement_status: "draft",
                dry_run: false,
            };
            const resp = await computeAllocation(req);
            setResult(resp.settlement_result);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                5차원 가중치 할당 (Allocation Breakdown)
            </h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">결과 ID</span>
                    <input
                        value={resultId}
                        onChange={(e) => setResultId(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">총 금액 (KRW)</span>
                    <input
                        type="number"
                        value={totalAmount}
                        onChange={(e) => setTotalAmount(Number(e.target.value))}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                {ALL_DIMENSIONS.map((dim) => (
                    <label key={dim} className="space-y-1">
                        <span className="text-slate-300">
                            {dim} (weight: {ALLOCATION_DIMENSION_WEIGHTS_CLIENT[dim]})
                        </span>
                        <input
                            type="number"
                            value={dimensionAmounts[dim]}
                            onChange={(e) =>
                                setDimensionAmounts({
                                    ...dimensionAmounts,
                                    [dim]: Number(e.target.value),
                                })
                            }
                            className="w-full rounded bg-slate-800 px-2 py-1"
                        />
                    </label>
                ))}
            </div>
            <button
                type="button"
                onClick={handleCompute}
                className="rounded bg-emerald-600 px-3 py-1 text-sm hover:bg-emerald-500"
            >
                할당 계산
            </button>
            {error ? (
                <div className="text-xs text-red-400">{error}</div>
            ) : null}
            {result ? (
                <div className="space-y-2">
                    <div className="text-xs text-slate-400">
                        신뢰도: {result.confidence_pct}% / 허용 오차:{" "}
                        {result.tolerance_band_krw.toLocaleString()} KRW
                    </div>
                    <pre className="overflow-x-auto rounded bg-slate-950 p-2 text-xs">
                        {JSON.stringify(result, null, 2)}
                    </pre>
                </div>
            ) : null}
        </section>
    );
}

function InvoicePreviewPanel() {
    const [invoiceFormat, setInvoiceFormat] =
        useState<InvoiceFormat>("pdf");
    const [recipientTemplate, setRecipientTemplate] =
        useState<string>("owner_only");
    const [result, setResult] = useState<Record<string, unknown> | null>(
        null
    );
    const [error, setError] = useState<string | null>(null);

    async function handleGenerate() {
        setError(null);
        try {
            const req: GenerateInvoiceRequest = {
                result_id: "res-1",
                period_key: "2026-08",
                invoice_format: invoiceFormat,
                settlement_result: {
                    total_amount_krw: 1_000_000,
                    allocation_count: 5,
                    confidence_pct: 100.0,
                    tolerance_band_krw: 10_000,
                    settlement_status: "draft",
                    model_version: "1.0.0",
                },
                allocation_lines: [
                    {
                        dimension: "cost_center",
                        dimension_value: "cost_center",
                        weight: 0.3,
                        allocated_amount_krw: 300_000,
                    },
                    {
                        dimension: "department",
                        dimension_value: "department",
                        weight: 0.25,
                        allocated_amount_krw: 250_000,
                    },
                ],
                recipient_template: recipientTemplate,
                dry_run: false,
            };
            const resp = await generateInvoice(req);
            setResult(resp.artifact);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">인보이스 미리보기 (Invoice)</h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">형식</span>
                    <select
                        value={invoiceFormat}
                        onChange={(e) =>
                            setInvoiceFormat(
                                e.target.value as InvoiceFormat
                            )
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    >
                        {ALL_INVOICE_FORMATS.map((f) => (
                            <option key={f} value={f}>
                                {f}
                            </option>
                        ))}
                    </select>
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">수신자 템플릿</span>
                    <select
                        value={recipientTemplate}
                        onChange={(e) => setRecipientTemplate(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    >
                        <option value="owner_only">owner_only</option>
                        <option value="executive">executive</option>
                        <option value="audit_only">audit_only</option>
                    </select>
                </label>
            </div>
            <button
                type="button"
                onClick={handleGenerate}
                className="rounded bg-emerald-600 px-3 py-1 text-sm hover:bg-emerald-500"
            >
                인보이스 생성
            </button>
            {error ? (
                <div className="text-xs text-red-400">{error}</div>
            ) : null}
            {result ? (
                <pre className="overflow-x-auto rounded bg-slate-950 p-2 text-xs">
                    {JSON.stringify(result, null, 2)}
                </pre>
            ) : null}
        </section>
    );
}

function ReconciliationStatusPanel() {
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const [allocationAmount, setAllocationAmount] = useState<number>(1_000_000);
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const [invoiceAmount, setInvoiceAmount] = useState<number>(1_000_000);
    // eslint-disable-next-line @typescript-eslint/no-restricted-types
    const [ledgerAmount, setLedgerAmount] = useState<number>(1_000_000);
    const [result, setResult] = useState<ReconciliationResult | null>(null);
    const [error, setError] = useState<string | null>(null);

    async function handleReconcile() {
        setError(null);
        try {
            const req: ReconcileSettlementRequest = {
                result_id: "res-1",
                period_key: "2026-08",
                allocation_amount_krw: allocationAmount,
                invoice_amount_krw: invoiceAmount,
                ledger_amount_krw: ledgerAmount,
                target_amount_krw: allocationAmount,
                tolerance_pct: 1.0,
                max_retries: 3,
                dry_run: false,
            };
            const resp = await reconcileSettlement(req);
            setResult(resp.reconciliation);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        }
    }

    const variancePct =
        allocationAmount > 0
            ? ((invoiceAmount - allocationAmount) / allocationAmount) * 100
            : 0;

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">3-way 매치 대조 정합</h2>
            <div className="grid grid-cols-3 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">할당 금액 (KRW)</span>
                    <input
                        type="number"
                        value={allocationAmount}
                        onChange={(e) =>
                            setAllocationAmount(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">인보이스 금액 (KRW)</span>
                    <input
                        type="number"
                        value={invoiceAmount}
                        onChange={(e) =>
                            setInvoiceAmount(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">원장 금액 (KRW)</span>
                    <input
                        type="number"
                        value={ledgerAmount}
                        onChange={(e) =>
                            setLedgerAmount(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
            </div>
            <div className="text-xs text-slate-400">
                예상 오차율: {variancePct.toFixed(4)}% (허용: 1.0%)
            </div>
            <button
                type="button"
                onClick={handleReconcile}
                className="rounded bg-emerald-600 px-3 py-1 text-sm hover:bg-emerald-500"
            >
                대조 정합 실행
            </button>
            {error ? (
                <div className="text-xs text-red-400">{error}</div>
            ) : null}
            {result ? (
                <pre className="overflow-x-auto rounded bg-slate-950 p-2 text-xs">
                    {JSON.stringify(result, null, 2)}
                </pre>
            ) : null}
        </section>
    );
}

function SettlementTrendMiniChart() {
    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">정산 추세 (Trend Mini Chart)</h2>
            <div className="rounded bg-slate-800 p-4 text-center text-sm text-slate-400">
                Recharts 2.12.7 AreaChart + BarChart placeholder — settlement
                rollout trend (실제 데이터는 API 응답 시 동적 렌더링)
            </div>
            <div className="grid grid-cols-5 gap-2 text-xs">
                {ALL_DIMENSIONS.map((dim) => (
                    <div
                        key={dim}
                        className="rounded bg-slate-800 p-2 text-center"
                    >
                        <div className="font-medium">{dim}</div>
                        <div className="text-emerald-400">
                            weight: {ALLOCATION_DIMENSION_WEIGHTS_CLIENT[dim]}
                        </div>
                    </div>
                ))}
            </div>
        </section>
    );
}

function ChargebackSettlementDryRunPreviewPanel() {
    const [dryRunResult, setDryRunResult] = useState<Record<
        string,
        unknown
    > | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleDryRun() {
        setPending(true);
        setError(null);
        try {
            const req: DryRunRequest = {
                cadence: "monthly",
                tenant_id: "tenant-1",
                five_module_inputs: {
                    phase_11_chargeback: 1.0,
                    phase_18_commitment: 1.0,
                    phase_19_pricing: 1.0,
                    phase_20_multi_cloud: 1.0,
                    phase_21_reserved_capacity: 1.0,
                },
                target_amount_krw: 10_000_000,
                target_dimensions: ["cost_center"],
            };
            const resp = await runDryRun(req);
            setDryRunResult(resp);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                Dry-run 미리보기 (Dry-Run Preview)
            </h2>
            <p className="text-xs text-slate-400">
                실제 정산 실행 없이 미리보기 — audit_action{" "}
                <code className="rounded bg-slate-800 px-1">
                    settlement_dry_run_executed
                </code>
            </p>
            <button
                type="button"
                onClick={handleDryRun}
                disabled={pending}
                className="rounded bg-amber-600 px-3 py-1 text-sm hover:bg-amber-500 disabled:opacity-50"
            >
                {pending ? "미리보기 중..." : "Dry-Run 실행"}
            </button>
            {error ? (
                <div className="text-xs text-red-400">{error}</div>
            ) : null}
            {dryRunResult ? (
                <pre className="overflow-x-auto rounded bg-slate-950 p-2 text-xs">
                    {JSON.stringify(dryRunResult, null, 2)}
                </pre>
            ) : null}
        </section>
    );
}

function ScheduledChargebackSettlementDispatchConfigPanel() {
    const [cadence, setCadence] = useState<SettlementCadence>("monthly");
    const [preview, setPreview] = useState<Record<string, unknown> | null>(
        null
    );
    const [error, setError] = useState<string | null>(null);

    async function handleFetchPreview() {
        setError(null);
        try {
            const resp = await fetchCadencePreview(cadence);
            setPreview(resp);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        }
    }

    async function handleDispatch() {
        setError(null);
        try {
            const req: DispatchRequest = {
                cadence,
                five_module_inputs: {
                    phase_11_chargeback: 1_000_000,
                    phase_18_commitment: 500_000,
                    phase_19_pricing: 500_000,
                    phase_20_multi_cloud: 250_000,
                    phase_21_reserved_capacity: 250_000,
                },
                target_amount_krw: 10_000_000,
                target_dimensions: ["cost_center", "department"],
                dry_run: false,
            };
            const resp = await executeDispatch(req);
            setPreview(resp.dispatch as Record<string, unknown>);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                정기 디스패치 (Scheduled Dispatch)
            </h2>
            <div className="flex gap-3">
                <label className="space-y-1">
                    <span className="text-sm text-slate-300">주기</span>
                    <select
                        value={cadence}
                        onChange={(e) =>
                            setCadence(e.target.value as SettlementCadence)
                        }
                        className="rounded bg-slate-800 px-2 py-1 text-sm"
                    >
                        {ALL_CADENCES.map((c) => (
                            <option key={c} value={c}>
                                {c}
                            </option>
                        ))}
                    </select>
                </label>
                <button
                    type="button"
                    onClick={handleFetchPreview}
                    className="self-end rounded bg-slate-700 px-3 py-1 text-sm hover:bg-slate-600"
                >
                    미리보기 조회
                </button>
                <button
                    type="button"
                    onClick={handleDispatch}
                    className="self-end rounded bg-emerald-600 px-3 py-1 text-sm hover:bg-emerald-500"
                >
                    디스패치 실행
                </button>
            </div>
            {error ? (
                <div className="text-xs text-red-400">{error}</div>
            ) : null}
            {preview ? (
                <pre className="overflow-x-auto rounded bg-slate-950 p-2 text-xs">
                    {JSON.stringify(preview, null, 2)}
                </pre>
            ) : null}
        </section>
    );
}

// Re-export weights for testing
export {
    FIVE_MODULE_WEIGHTS_CLIENT,
    ALLOCATION_DIMENSION_WEIGHTS_CLIENT,
};
