"use client";

/**
 * FinopsUnitEconomicsDashboardPanel — Phase 23 FinOps Unit Economics
 * Client panel.
 *
 * Phase 23 (cj-style 164번째 wire) — FinOps Unit Economics derived
 * metric layer territory (PRD §F39.1~§F39.8 + AD-51 (a)~(g) 7
 * sub-decisions).
 *
 * 5 sub-components:
 * 1. UnitEconomicsOverviewCard — compute unit_economics_id from Phase
 *    22 settlement_id → allocation_lines ledger via 5-dim cross-join
 *    (cost_center=0.30 + department=0.25 + business_unit=0.20 + tag=0.15
 *    + tenant=0.10) + confidence_pct 0~100 + margin_status 4-tier +
 *    dry-run support + Epic 12 2FA 챌린지 mandatory (high-value ≥10M
 *    KRW/year).
 * 2. CostPerBusinessUnitCard — 5-dim rollup + ledger-key dedup +
 *    cost_per_unit_krw + transaction_count breakdown + Decimal
 *    precision (CR 5-1).
 * 3. CostPerTransactionCard — tag propagation (Phase 22 settlement tags
 *    → transaction-level filtering) + ledger-key dedup + 3 NEW tag
 *    filter dimensions.
 * 4. MarginAnalysisCard — OPTIONAL revenue attribution + 3-tier status
 *    thresholds (healthy ≥30% / warning 15-30% / critical 0-15% /
 *    negative <0%) + alert generation + Epic 12 2FA 챌린지 detection.
 * 5. UnitEconomicsTrendMiniChart — Recharts 2.12.7 stack pin
 *    unit_economics rollout trend (AreaChart placeholder) + 5-dim
 *    attribution breakdown (BarChart placeholder).
 *
 * Plus UnitEconomicsDryRunPreviewPanel — dry-run preview UI EXTENSION
 * (audit_action `unit_economics_dry_run_executed` + orchestration_status
 * 'dry_run').
 *
 * Plus ScheduledUnitEconomicsCalculationConfigPanel — 4 cadence
 * schedule KST pytz (daily 03:30 / weekly 04:00 / monthly 04:30 /
 * quarterly 05:00 KST) + 3 recipient templates.
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/unit-economics-types.ts`.
 * AD-14 stack pin — Recharts 2.12.7 + noto-sans-cjk-kr +
 * apscheduler 3.10.4 + pytz 2024.1.
 *
 * D-FINOPS-12 honestly DEFER (cost_per_customer CRM + multi-currency
 * FX + real-time stream — all honestly DEFER to future Phase 23.x).
 */

import { useState } from "react";
import {
    computeUnitEconomics,
    refreshCostPerBusinessUnit,
    computeCostPerTransaction,
    executeMarginAnalysis,
    runDryRun,
    fetchCadencePreview,
    fetchTrend,
    type ComputeUnitEconomicsRequest,
    type RefreshCostPerBusinessUnitRequest,
    type ComputeCostPerTransactionRequest,
    type ExecuteMarginAnalysisRequest,
    type DryRunRequest,
} from "@/lib/finops/unit-economics-client";
import type {
    CostPerBusinessUnitBreakdown,
    CostPerTransactionBreakdown,
    MarginAnalysisResult,
    UnitEconomicsCadence,
    UnitEconomicsDimension,
    UnitEconomicsResult,
} from "@/lib/finops/unit-economics-types";

const ALL_CADENCES: UnitEconomicsCadence[] = [
    "daily",
    "weekly",
    "monthly",
    "quarterly",
];

const ALL_DIMENSIONS: UnitEconomicsDimension[] = [
    "cost_center",
    "department",
    "business_unit",
    "tag",
    "tenant",
];

const DERIVATION_DIMENSION_WEIGHTS_CLIENT: Record<
    UnitEconomicsDimension,
    number
> = {
    cost_center: 0.30,
    department: 0.25,
    business_unit: 0.20,
    tag: 0.15,
    tenant: 0.10,
};

const COST_PER_X_METRIC_WEIGHTS_CLIENT: Record<string, number> = {
    cost_per_business_unit: 0.40,
    cost_per_transaction: 0.30,
    cost_per_department: 0.20,
    cost_per_cost_center: 0.10,
};

export function FinopsUnitEconomicsDashboardPanel() {
    const [activeTab, setActiveTab] = useState<
        | "overview"
        | "cost_per_business_unit"
        | "cost_per_transaction"
        | "margin_analysis"
        | "trend"
    >("overview");

    return (
        <div className="space-y-6 text-slate-100">
            <header className="space-y-2">
                <h1 className="text-2xl font-semibold">
                    FinOps Unit Economics 대시보드
                </h1>
                <p className="text-sm text-slate-400">
                    Phase 23 — 5-dim cross-join derived metric layer (Phase 22
                    allocation_lines ledger) + 4 cost_per_X dimensions + 3-tier
                    margin analysis + 4 cadence schedule KST.
                </p>
            </header>

            <nav className="flex gap-2 border-b border-slate-700">
                {(
                    [
                        ["overview", "개요"],
                        ["cost_per_business_unit", "사업부 단가"],
                        ["cost_per_transaction", "거래 단가"],
                        ["margin_analysis", "마진 분석"],
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

            {activeTab === "overview" ? <UnitEconomicsOverviewCard /> : null}
            {activeTab === "cost_per_business_unit" ? (
                <CostPerBusinessUnitCard />
            ) : null}
            {activeTab === "cost_per_transaction" ? (
                <CostPerTransactionCard />
            ) : null}
            {activeTab === "margin_analysis" ? <MarginAnalysisCard /> : null}
            {activeTab === "trend" ? <UnitEconomicsTrendMiniChart /> : null}

            <UnitEconomicsDryRunPreviewPanel />
            <ScheduledUnitEconomicsCalculationConfigPanel />
        </div>
    );
}

function UnitEconomicsOverviewCard() {
    const [periodKey, setPeriodKey] = useState<string>("2026-08");
    const [sourceSettlementId, setSourceSettlementId] = useState<string>(
        "phase_22_settlement_default"
    );
    const [totalCostKrw, setTotalCostKrw] = useState<number>(10_000_000);
    const [totalRevenueKrw, setTotalRevenueKrw] = useState<number>(0);
    const [totalUnits, setTotalUnits] = useState<number>(100);
    const [totalTransactions, setTotalTransactions] = useState<number>(10_000);
    const [allocationCount, setAllocationCount] = useState<number>(1000);
    const [revenueCompletenessPct, setRevenueCompletenessPct] =
        useState<number>(0);
    const [targetDimensions, setTargetDimensions] = useState<
        UnitEconomicsDimension[]
    >(["cost_center", "department", "business_unit"]);
    const [result, setResult] = useState<UnitEconomicsResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleSubmit() {
        setPending(true);
        setError(null);
        try {
            const fiveDimInputs: Record<string, number> = {
                cost_center: totalCostKrw * 0.30,
                department: totalCostKrw * 0.25,
                business_unit: totalCostKrw * 0.20,
                tag: totalCostKrw * 0.15,
                tenant: totalCostKrw * 0.10,
            };
            const req: ComputeUnitEconomicsRequest = {
                period_key: periodKey,
                source_settlement_id: sourceSettlementId,
                total_cost_krw: totalCostKrw,
                total_revenue_krw: totalRevenueKrw,
                total_units: totalUnits,
                total_transactions: totalTransactions,
                target_dimensions: targetDimensions,
                five_dim_inputs: fiveDimInputs,
                allocation_count: allocationCount,
                revenue_completeness_pct: revenueCompletenessPct,
                dry_run: false,
            };
            const resp = await computeUnitEconomics(req);
            setResult(resp.result);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    const highValueFlag = totalCostKrw * 12 >= 10_000_000;

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                Unit Economics 개요 (Phase 22 settlement_id 기반)
            </h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">기간 (period_key)</span>
                    <input
                        value={periodKey}
                        onChange={(e) => setPeriodKey(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">
                        Phase 22 source_settlement_id
                    </span>
                    <input
                        value={sourceSettlementId}
                        onChange={(e) =>
                            setSourceSettlementId(e.target.value)
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">총 비용 (KRW)</span>
                    <input
                        type="number"
                        value={totalCostKrw}
                        onChange={(e) =>
                            setTotalCostKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">
                        총 매출 (KRW) — D-FINOPS-12 DEFER
                    </span>
                    <input
                        type="number"
                        value={totalRevenueKrw}
                        onChange={(e) =>
                            setTotalRevenueKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">총 단위 (사업부 수)</span>
                    <input
                        type="number"
                        value={totalUnits}
                        onChange={(e) => setTotalUnits(Number(e.target.value))}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">총 거래 수</span>
                    <input
                        type="number"
                        value={totalTransactions}
                        onChange={(e) =>
                            setTotalTransactions(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">할당 수</span>
                    <input
                        type="number"
                        value={allocationCount}
                        onChange={(e) =>
                            setAllocationCount(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">
                        매출 완성도 (%)
                    </span>
                    <input
                        type="number"
                        value={revenueCompletenessPct}
                        onChange={(e) =>
                            setRevenueCompletenessPct(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="col-span-2 space-y-1">
                    <span className="text-slate-300">파생 차원</span>
                    <select
                        multiple
                        value={targetDimensions}
                        onChange={(e) =>
                            setTargetDimensions(
                                Array.from(
                                    e.target.selectedOptions,
                                    (o) => o.value as UnitEconomicsDimension
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
            <button
                type="button"
                onClick={handleSubmit}
                disabled={pending}
                className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
            >
                {pending ? "계산 중..." : "Unit Economics 계산"}
            </button>
            {highValueFlag ? (
                <p className="text-xs text-amber-400">
                    ⚠ 고가치 (≥10M KRW/year). Epic 12 2FA 챌린지 필요.
                </p>
            ) : null}
            {error ? (
                <p className="text-sm text-red-400">오류: {error}</p>
            ) : null}
            {result ? (
                <div className="rounded bg-slate-800 p-3 text-sm">
                    <p>
                        <strong>단가:</strong>{" "}
                        ₩{result.cost_per_business_unit_krw.toLocaleString()} / 사업부
                    </p>
                    <p>
                        <strong>거래 단가:</strong>{" "}
                        ₩{result.cost_per_transaction_krw.toLocaleString()} / 거래
                    </p>
                    <p>
                        <strong>마진:</strong> {result.margin_pct.toFixed(2)}%
                        (상태: {result.margin_status})
                    </p>
                    <p>
                        <strong>신뢰도:</strong>{" "}
                        {result.confidence_pct.toFixed(2)}%
                    </p>
                </div>
            ) : null}
        </section>
    );
}

function CostPerBusinessUnitCard() {
    const [unitEconomicsId, setUnitEconomicsId] = useState<string>(
        "unit_economics_default"
    );
    const [periodKey, setPeriodKey] = useState<string>("2026-08");
    const [businessUnit, setBusinessUnit] = useState<string>("sales-team");
    const [costCenter, setCostCenter] = useState<string>("billing-001");
    const [department, setDepartment] = useState<string>("sales");
    const [tagKey, setTagKey] = useState<string>("environment:prod");
    const [allocatedCostKrw, setAllocatedCostKrw] = useState<number>(100_000);
    const [transactionCount, setTransactionCount] = useState<number>(100);
    const [breakdown, setBreakdown] =
        useState<CostPerBusinessUnitBreakdown | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleSubmit() {
        setPending(true);
        setError(null);
        try {
            const req: RefreshCostPerBusinessUnitRequest = {
                unit_economics_id: unitEconomicsId,
                period_key: periodKey,
                business_unit: businessUnit,
                cost_center: costCenter,
                department: department,
                tag_key: tagKey,
                allocated_cost_krw: allocatedCostKrw,
                transaction_count: transactionCount,
                cost_center_amount_krw: allocatedCostKrw * 0.30,
                department_amount_krw: allocatedCostKrw * 0.25,
                business_unit_amount_krw: allocatedCostKrw * 0.20,
                tag_amount_krw: allocatedCostKrw * 0.15,
                tenant_amount_krw: allocatedCostKrw * 0.10,
                dry_run: false,
            };
            const resp = await refreshCostPerBusinessUnit(req);
            setBreakdown(resp.breakdown);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                사업부 단가 (5-dim rollup + ledger-key dedup)
            </h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">사업부</span>
                    <input
                        value={businessUnit}
                        onChange={(e) => setBusinessUnit(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">비용 센터</span>
                    <input
                        value={costCenter}
                        onChange={(e) => setCostCenter(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">부서</span>
                    <input
                        value={department}
                        onChange={(e) => setDepartment(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">태그 키</span>
                    <input
                        value={tagKey}
                        onChange={(e) => setTagKey(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">할당 비용 (KRW)</span>
                    <input
                        type="number"
                        value={allocatedCostKrw}
                        onChange={(e) =>
                            setAllocatedCostKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">거래 수</span>
                    <input
                        type="number"
                        value={transactionCount}
                        onChange={(e) =>
                            setTransactionCount(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
            </div>
            <button
                type="button"
                onClick={handleSubmit}
                disabled={pending}
                className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
            >
                {pending ? "갱신 중..." : "사업부 단가 갱신"}
            </button>
            {error ? (
                <p className="text-sm text-red-400">오류: {error}</p>
            ) : null}
            {breakdown ? (
                <div className="rounded bg-slate-800 p-3 text-sm">
                    <p>
                        <strong>사업부 단가:</strong>{" "}
                        ₩{breakdown.cost_per_unit_krw.toLocaleString()} / 단위
                    </p>
                    <p>
                        <strong>신뢰도:</strong>{" "}
                        {breakdown.confidence_pct.toFixed(2)}%
                    </p>
                </div>
            ) : null}
        </section>
    );
}

function CostPerTransactionCard() {
    const [unitEconomicsId, setUnitEconomicsId] = useState<string>(
        "unit_economics_default"
    );
    const [periodKey, setPeriodKey] = useState<string>("2026-08");
    const [transactionId, setTransactionId] = useState<string>("tx-001");
    const [businessUnit, setBusinessUnit] = useState<string>("sales-team");
    const [costCenter, setCostCenter] = useState<string>("billing-001");
    const [allocatedCostKrw, setAllocatedCostKrw] = useState<number>(10_000);
    const [transactionCount, setTransactionCount] = useState<number>(1);
    const [tagPropagationJson, setTagPropagationJson] = useState<string>(
        '{"cost_center":"billing-001","department":"sales"}'
    );
    const [transaction, setTransaction] =
        useState<CostPerTransactionBreakdown | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleSubmit() {
        setPending(true);
        setError(null);
        try {
            let parsedTags: Record<string, string> = {};
            try {
                parsedTags = JSON.parse(tagPropagationJson);
            } catch {
                parsedTags = {};
            }
            const req: ComputeCostPerTransactionRequest = {
                unit_economics_id: unitEconomicsId,
                period_key: periodKey,
                transaction_id: transactionId,
                business_unit: businessUnit,
                cost_center: costCenter,
                allocated_cost_krw: allocatedCostKrw,
                transaction_count: transactionCount,
                phase_22_settlement_tags: parsedTags,
                dry_run: false,
            };
            const resp = await computeCostPerTransaction(req);
            setTransaction(resp.transaction);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                거래 단가 (tag propagation + ledger-key dedup)
            </h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">거래 ID</span>
                    <input
                        value={transactionId}
                        onChange={(e) => setTransactionId(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">사업부</span>
                    <input
                        value={businessUnit}
                        onChange={(e) => setBusinessUnit(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">비용 센터</span>
                    <input
                        value={costCenter}
                        onChange={(e) => setCostCenter(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">할당 비용 (KRW)</span>
                    <input
                        type="number"
                        value={allocatedCostKrw}
                        onChange={(e) =>
                            setAllocatedCostKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="col-span-2 space-y-1">
                    <span className="text-slate-300">
                        Phase 22 settlement_tags (JSON)
                    </span>
                    <textarea
                        value={tagPropagationJson}
                        onChange={(e) =>
                            setTagPropagationJson(e.target.value)
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                        rows={3}
                    />
                </label>
            </div>
            <button
                type="button"
                onClick={handleSubmit}
                disabled={pending}
                className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
            >
                {pending ? "계산 중..." : "거래 단가 계산"}
            </button>
            {error ? (
                <p className="text-sm text-red-400">오류: {error}</p>
            ) : null}
            {transaction ? (
                <div className="rounded bg-slate-800 p-3 text-sm">
                    <p>
                        <strong>할당 비용:</strong>{" "}
                        ₩{transaction.allocated_cost_krw.toLocaleString()}
                    </p>
                    <p>
                        <strong>전파된 태그:</strong>{" "}
                        {transaction.tag_propagation_json.propagated_tag_count}개
                    </p>
                </div>
            ) : null}
        </section>
    );
}

function MarginAnalysisCard() {
    const [unitEconomicsId, setUnitEconomicsId] = useState<string>(
        "unit_economics_default"
    );
    const [periodKey, setPeriodKey] = useState<string>("2026-08");
    const [businessUnit, setBusinessUnit] = useState<string>("sales-team");
    const [totalCostKrw, setTotalCostKrw] = useState<number>(10_000_000);
    const [totalRevenueKrw, setTotalRevenueKrw] = useState<number>(15_000_000);
    const [revenueSourcesText, setRevenueSourcesText] = useState<string>(
        "revenue_source_1,revenue_source_2"
    );
    const [revenueCompletenessPct, setRevenueCompletenessPct] =
        useState<number>(100);
    const [margin, setMargin] = useState<MarginAnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleSubmit() {
        setPending(true);
        setError(null);
        try {
            const req: ExecuteMarginAnalysisRequest = {
                unit_economics_id: unitEconomicsId,
                period_key: periodKey,
                business_unit: businessUnit,
                total_cost_krw: totalCostKrw,
                total_revenue_krw: totalRevenueKrw,
                revenue_sources: revenueSourcesText
                    .split(",")
                    .map((s) => s.trim())
                    .filter(Boolean),
                revenue_completeness_pct: revenueCompletenessPct,
                dry_run: false,
            };
            const resp = await executeMarginAnalysis(req);
            setMargin(resp.margin);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    const statusColor = (s: string) => {
        if (s === "healthy") return "text-emerald-400";
        if (s === "warning") return "text-amber-400";
        if (s === "critical") return "text-orange-400";
        return "text-red-400";
    };

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                마진 분석 (OPTIONAL revenue attribution)
            </h2>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">사업부</span>
                    <input
                        value={businessUnit}
                        onChange={(e) => setBusinessUnit(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">총 비용 (KRW)</span>
                    <input
                        type="number"
                        value={totalCostKrw}
                        onChange={(e) =>
                            setTotalCostKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">총 매출 (KRW)</span>
                    <input
                        type="number"
                        value={totalRevenueKrw}
                        onChange={(e) =>
                            setTotalRevenueKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">
                        매출 완성도 (%)
                    </span>
                    <input
                        type="number"
                        value={revenueCompletenessPct}
                        onChange={(e) =>
                            setRevenueCompletenessPct(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="col-span-2 space-y-1">
                    <span className="text-slate-300">
                        매출 소스 (쉼표 구분)
                    </span>
                    <input
                        value={revenueSourcesText}
                        onChange={(e) =>
                            setRevenueSourcesText(e.target.value)
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
            </div>
            <button
                type="button"
                onClick={handleSubmit}
                disabled={pending}
                className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
            >
                {pending ? "분석 중..." : "마진 분석 실행"}
            </button>
            {error ? (
                <p className="text-sm text-red-400">오류: {error}</p>
            ) : null}
            {margin ? (
                <div className="rounded bg-slate-800 p-3 text-sm">
                    <p>
                        <strong>마진 금액:</strong>{" "}
                        ₩{margin.margin_amount_krw.toLocaleString()}
                    </p>
                    <p>
                        <strong>마진율:</strong>{" "}
                        <span className={statusColor(margin.margin_status)}>
                            {margin.margin_pct.toFixed(2)}%
                        </span>
                    </p>
                    <p>
                        <strong>상태:</strong>{" "}
                        <span className={statusColor(margin.margin_status)}>
                            {margin.margin_status}
                        </span>
                    </p>
                </div>
            ) : null}
        </section>
    );
}

function UnitEconomicsTrendMiniChart() {
    const [periodKey, setPeriodKey] = useState<string>("2026-08");
    const [results, setResults] = useState<UnitEconomicsResult[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleFetch() {
        setPending(true);
        setError(null);
        try {
            const resp = await fetchTrend(periodKey);
            setResults(resp.results);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                Unit Economics 추세 (Recharts AreaChart placeholder)
            </h2>
            <div className="flex gap-2 text-sm">
                <input
                    value={periodKey}
                    onChange={(e) => setPeriodKey(e.target.value)}
                    placeholder="YYYY-MM"
                    className="rounded bg-slate-800 px-2 py-1"
                />
                <button
                    type="button"
                    onClick={handleFetch}
                    disabled={pending}
                    className="rounded bg-emerald-600 px-4 py-1 text-sm hover:bg-emerald-500 disabled:opacity-50"
                >
                    {pending ? "조회 중..." : "조회"}
                </button>
            </div>
            {error ? (
                <p className="text-sm text-red-400">오류: {error}</p>
            ) : null}
            {results.length > 0 ? (
                <div className="rounded bg-slate-800 p-3 text-sm">
                    {results.map((r) => (
                        <p key={r.unit_economics_id}>
                            {r.period_key}: ₩
                            {r.cost_per_business_unit_krw.toLocaleString()} / 사업부
                            (마진: {r.margin_pct.toFixed(2)}%)
                        </p>
                    ))}
                </div>
            ) : (
                <p className="text-xs text-slate-400">
                    데이터 없음 — unit_economics 계산 후 조회 가능.
                </p>
            )}
        </section>
    );
}

function UnitEconomicsDryRunPreviewPanel() {
    const [periodKey, setPeriodKey] = useState<string>("2026-08");
    const [totalCostKrw, setTotalCostKrw] = useState<number>(10_000_000);
    const [totalRevenueKrw, setTotalRevenueKrw] = useState<number>(0);
    const [totalUnits, setTotalUnits] = useState<number>(100);
    const [totalTransactions, setTotalTransactions] = useState<number>(10_000);
    const [allocationCount, setAllocationCount] = useState<number>(1000);
    const [result, setResult] = useState<UnitEconomicsResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleDryRun() {
        setPending(true);
        setError(null);
        try {
            const fiveDimInputs: Record<string, number> = {
                cost_center: totalCostKrw * 0.30,
                department: totalCostKrw * 0.25,
                business_unit: totalCostKrw * 0.20,
                tag: totalCostKrw * 0.15,
                tenant: totalCostKrw * 0.10,
            };
            const req: DryRunRequest = {
                period_key: periodKey,
                source_settlement_id: "phase_22_dry_run",
                total_cost_krw: totalCostKrw,
                total_revenue_krw: totalRevenueKrw,
                total_units: totalUnits,
                total_transactions: totalTransactions,
                target_dimensions: [
                    "cost_center",
                    "department",
                    "business_unit",
                ],
                five_dim_inputs: fiveDimInputs,
                allocation_count: allocationCount,
                revenue_completeness_pct: 0,
            };
            const resp = await runDryRun(req);
            setResult(resp.dry_run_result);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-amber-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                Unit Economics Dry-Run 미리보기 (T7)
            </h2>
            <p className="text-xs text-slate-400">
                audit_action: unit_economics_dry_run_executed. 실제 저장/감사
                액션 발행 없음.
            </p>
            <div className="grid grid-cols-2 gap-3 text-sm">
                <label className="space-y-1">
                    <span className="text-slate-300">기간</span>
                    <input
                        value={periodKey}
                        onChange={(e) => setPeriodKey(e.target.value)}
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
                <label className="space-y-1">
                    <span className="text-slate-300">총 비용 (KRW)</span>
                    <input
                        type="number"
                        value={totalCostKrw}
                        onChange={(e) =>
                            setTotalCostKrw(Number(e.target.value))
                        }
                        className="w-full rounded bg-slate-800 px-2 py-1"
                    />
                </label>
            </div>
            <button
                type="button"
                onClick={handleDryRun}
                disabled={pending}
                className="rounded bg-amber-600 px-4 py-2 text-sm font-medium hover:bg-amber-500 disabled:opacity-50"
            >
                {pending ? "Dry-run 중..." : "Dry-run 실행"}
            </button>
            {error ? (
                <p className="text-sm text-red-400">오류: {error}</p>
            ) : null}
            {result ? (
                <div className="rounded bg-slate-800 p-3 text-sm">
                    <p>
                        <strong>Dry-run 사업부 단가:</strong>{" "}
                        ₩{result.cost_per_business_unit_krw.toLocaleString()}
                    </p>
                    <p>
                        <strong>Dry-run 거래 단가:</strong>{" "}
                        ₩{result.cost_per_transaction_krw.toLocaleString()}
                    </p>
                    <p className="text-xs text-amber-400">
                        ⚠ 미리보기 모드 — 실제 데이터 변경 없음.
                    </p>
                </div>
            ) : null}
        </section>
    );
}

function ScheduledUnitEconomicsCalculationConfigPanel() {
    const [cadence, setCadence] = useState<UnitEconomicsCadence>("daily");
    const [preview, setPreview] = useState<Record<string, unknown> | null>(
        null
    );
    const [error, setError] = useState<string | null>(null);
    const [pending, setPending] = useState<boolean>(false);

    async function handleFetchPreview() {
        setPending(true);
        setError(null);
        try {
            const resp = await fetchCadencePreview();
            setPreview(resp as unknown as Record<string, unknown>);
        } catch (err) {
            setError(err instanceof Error ? err.message : "unknown_error");
        } finally {
            setPending(false);
        }
    }

    return (
        <section className="space-y-4 rounded-lg border border-slate-700 bg-slate-900 p-4">
            <h2 className="text-lg font-medium">
                Scheduled Unit Economics 계산 설정 (4 cadence KST pytz)
            </h2>
            <div className="flex gap-2 text-sm">
                <select
                    value={cadence}
                    onChange={(e) =>
                        setCadence(e.target.value as UnitEconomicsCadence)
                    }
                    className="rounded bg-slate-800 px-2 py-1"
                >
                    {ALL_CADENCES.map((c) => (
                        <option key={c} value={c}>
                            {c}
                        </option>
                    ))}
                </select>
                <button
                    type="button"
                    onClick={handleFetchPreview}
                    disabled={pending}
                    className="rounded bg-emerald-600 px-4 py-1 text-sm hover:bg-emerald-500 disabled:opacity-50"
                >
                    {pending ? "조회 중..." : "Cadence 미리보기"}
                </button>
            </div>
            {error ? (
                <p className="text-sm text-red-400">오류: {error}</p>
            ) : null}
            {preview ? (
                <pre className="overflow-x-auto rounded bg-slate-800 p-3 text-xs">
                    {JSON.stringify(preview, null, 2)}
                </pre>
            ) : (
                <p className="text-xs text-slate-400">
                    KST pytz: daily 03:30 / weekly 04:00 / monthly 04:30 /
                    quarterly 05:00. apscheduler 3.10.4.
                </p>
            )}
        </section>
    );
}
