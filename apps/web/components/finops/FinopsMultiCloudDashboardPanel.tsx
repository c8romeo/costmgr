"use client";

/**
 * FinopsMultiCloudDashboardPanel — Phase 20 FinOps Multi-Cloud Cost Unified
 * Reconciliation Client panel.
 *
 * Phase 20 (cj-style 144번째 wire) — FinOps Multi-Cloud Cost Unified
 * Reconciliation territory (PRD §F36.1-7). 5 sub-components:
 * 1. RateCardReconciliationAggregator — 4 scope_type (tenant/department/
 *    cost_center/product_line) + 5-cloud-provider breakdown +
 *    5-tier rate card source priority chain (negotiation/contract/
 *    rate_card_api/manual/audit) + rate_card_variance_pct alert +
 *    negotiation_recommendation_count summary.
 * 2. CostReconciliationAggregator — cost_variance_pct > 3.0% alert +
 *    5-cloud-provider cost breakdown (AWS EDP + Azure EA + GCP CUD
 *    Pricing + Naver Cloud + KT Cloud) + 5-tier cost source priority
 *    chain + cost_growth_pct + cost_forecast_krw.
 * 3. NegotiationBotPanel — 3 status (auto_negotiate_ready/manual_review_
 *    required/low_confidence) + confidence_score + risk_score + 3 cloud
 *    provider (AWS EDP auto / Azure EA consumption commit / GCP CUD
 *    flexible+fixed tier break-even) + guard_check_passed indicator +
 *    auto_trigger_eligible toggle.
 * 4. BlendedUnblendedTrackerPanel — 3 cloud provider (AWS Cost Explorer /
 *    Azure Cost Management / GCP BigQuery billing export) +
 *    rate_diff_pct alert + drift_detected status + Naver/KT public
 *    pricing API stability verification (uptime ≥ 99.0% / P95 ≤ 2s /
 *    freshness ≤ 24h).
 * 5. MarketplaceSaaSPricingIntegratorPanel — 5 marketplace source
 *    (AWS Marketplace / Azure Marketplace / GCP Marketplace / Naver
 *    Marketplace / KT Marketplace) + 4-hour cron refresh + cheapest 3
 *    alternative suggestion within saas_category + integration_status
 *    badge (active/pending/failed/disabled) + freshness threshold.
 *
 * Plus ScheduledMultiCloudDispatchConfigPanel — 4 cron schedules
 * (weekly Mon 09:00 / monthly 1st-day 09:00 / quarterly 1st-day 09:00 /
 * annual Jan-1 09:00 KST pytz Asia/Seoul) + 4 recipient strategies
 * (owner_only/finops_team/exec_team/custom_recipients) + dry_run test
 * dispatch.
 *
 * Owner-only RBAC AD-22 verbatim + Epic 12 2FA 챌린지 보존.
 *
 * CR 11-4 D-003 RTL render discipline.
 * CR 12-5 D-PARITY-01 — TypeScript interfaces mirror Python TypedDict
 * via `lib/finops/multi-cloud-types.ts`.
 * AD-14 stack pin — Recharts 2.12.7.
 */

import { useState } from "react";

import {
  reconcileRateCards,
  reconcileCosts,
  runNegotiationBot,
  trackBlendedUnblended,
  integrateMarketplace,
  dispatchMultiCloudReport,
  type AggregateRateCardRequest,
  type AggregateCostRequest,
  type NegotiationRequest,
  type TrackBlendedUnblendedRequest,
  type IntegrateMarketplaceRequest,
  type DispatchMultiCloudRequest,
} from "@/lib/finops/multi-cloud-client";
import type {
  MultiCloudRateCardReconciliation,
  MultiCloudCostReconciliation,
  NegotiationRecommendation,
  BlendedUnblendedDiff,
  MarketplaceSaaSPricingRollup,
  ScheduledMultiCloudDispatch,
  MarketplaceSource,
} from "@/lib/finops/multi-cloud-types";

const ALL_MARKETPLACE_SOURCES: MarketplaceSource[] = [
  "aws_marketplace",
  "azure_marketplace",
  "gcp_marketplace",
  "naver_marketplace",
  "kt_marketplace",
];

// ── 1. RateCardReconciliationAggregator ──
function RateCardReconciliationAggregator({
  rollup,
  onRefresh,
}: {
  rollup: MultiCloudRateCardReconciliation | null;
  onRefresh: () => void;
}) {
  return (
    <div
      className="multi-cloud-rate-card-aggregator mb-6 rounded bg-slate-900 p-4"
      aria-label="multi_cloud_rate_card_aggregator"
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">
          다중 클라우드 요금 카드 통합 (5-cloud-provider)
        </h2>
        <button
          type="button"
          className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
          onClick={onRefresh}
        >
          새로 고침
        </button>
      </div>
      {rollup ? (
        <>
          <p className="text-sm text-slate-300">
            effective_rate_krw_per_hour:{" "}
            <span className="font-mono">
              {rollup.effective_rate_krw_per_hour.toFixed(2)}
            </span>
          </p>
          <p className="text-sm text-slate-300">
            rate_card_variance_pct:{" "}
            <span className="font-mono">
              {rollup.rate_card_variance_pct.toFixed(2)}%
            </span>
          </p>
          <p className="text-sm text-slate-300">
            source_count:{" "}
            <span className="font-mono">{rollup.rate_card_source_count}</span>
            {" | "}
            primary_source:{" "}
            <span className="font-mono">
              {rollup.primary_rate_card_source}
            </span>
          </p>
          <p className="text-sm text-slate-300">
            negotiation_recommendation_count:{" "}
            <span className="font-mono">
              {rollup.negotiation_recommendation_count}
            </span>
            {" | "}
            savings_krw_per_year:{" "}
            <span className="font-mono">
              {rollup.rate_card_savings_krw_per_year.toFixed(0)}
            </span>
          </p>
        </>
      ) : (
        <p className="text-sm text-slate-400">데이터 없음 — 새로 고침 누름</p>
      )}
    </div>
  );
}

// ── 2. CostReconciliationAggregator ──
function CostReconciliationAggregator({
  rollup,
  onRefresh,
}: {
  rollup: MultiCloudCostReconciliation | null;
  onRefresh: () => void;
}) {
  return (
    <div
      className="multi-cloud-cost-aggregator mb-6 rounded bg-slate-900 p-4"
      aria-label="multi_cloud_cost_aggregator"
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">
          다중 클라우드 비용 통합 (5-cloud-provider)
        </h2>
        <button
          type="button"
          className="rounded bg-blue-600 px-3 py-1 text-sm text-white hover:bg-blue-700"
          onClick={onRefresh}
        >
          새로 고침
        </button>
      </div>
      {rollup ? (
        <>
          <p className="text-sm text-slate-300">
            cloud_provider:{" "}
            <span className="font-mono">{rollup.cloud_provider}</span>
            {" | "}
            service:{" "}
            <span className="font-mono">{rollup.service_code}</span>
            {" | "}
            region:{" "}
            <span className="font-mono">{rollup.region}</span>
          </p>
          <p className="text-sm text-slate-300">
            blended_cost_krw:{" "}
            <span className="font-mono">
              {rollup.blended_cost_krw.toFixed(0)}
            </span>
            {" | "}
            cost_variance_pct:{" "}
            <span className="font-mono">
              {rollup.cost_variance_pct.toFixed(2)}%
            </span>
            {" (alert &gt; 3.0%)"}
          </p>
          <p className="text-sm text-slate-300">
            cost_growth_pct:{" "}
            <span className="font-mono">
              {rollup.cost_growth_pct.toFixed(2)}%
            </span>
            {" | "}
            forecast_krw:{" "}
            <span className="font-mono">
              {rollup.cost_forecast_krw.toFixed(0)}
            </span>
          </p>
        </>
      ) : (
        <p className="text-sm text-slate-400">데이터 없음</p>
      )}
    </div>
  );
}

// ── 3. NegotiationBotPanel ──
function NegotiationBotPanel({
  recommendation,
  onRun,
}: {
  recommendation: NegotiationRecommendation | null;
  onRun: () => void;
}) {
  return (
    <div
      className="multi-cloud-negotiation-bot mb-6 rounded bg-slate-900 p-4"
      aria-label="multi_cloud_negotiation_bot"
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">
          협상 봇 (AWS EDP + Azure EA + GCP CUD)
        </h2>
        <button
          type="button"
          className="rounded bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-700"
          onClick={onRun}
        >
          실행
        </button>
      </div>
      {recommendation ? (
        <>
          <p className="text-sm text-slate-300">
            cloud_provider:{" "}
            <span className="font-mono">{recommendation.cloud_provider}</span>
            {" | "}
            term:{" "}
            <span className="font-mono">
              {recommendation.commitment_term}
            </span>
            {" | "}
            status:{" "}
            <span className="font-mono">
              {recommendation.recommendation_status}
            </span>
          </p>
          <p className="text-sm text-slate-300">
            savings_pct:{" "}
            <span className="font-mono">
              {recommendation.savings_pct.toFixed(2)}%
            </span>
            {" | "}
            confidence:{" "}
            <span className="font-mono">
              {recommendation.confidence_score.toFixed(2)}
            </span>
            {" | "}
            risk:{" "}
            <span className="font-mono">
              {recommendation.risk_score.toFixed(2)}
            </span>
          </p>
          <p className="text-sm text-slate-300">
            auto_trigger_eligible:{" "}
            <span className="font-mono">
              {String(recommendation.auto_trigger_eligible)}
            </span>
            {" | "}
            guard_check_passed:{" "}
            <span className="font-mono">
              {String(recommendation.guard_check_passed)}
            </span>
          </p>
        </>
      ) : (
        <p className="text-sm text-slate-400">실행하여 추천 받기</p>
      )}
    </div>
  );
}

// ── 4. BlendedUnblendedTrackerPanel ──
function BlendedUnblendedTrackerPanel({
  diff,
  onTrack,
}: {
  diff: BlendedUnblendedDiff | null;
  onTrack: () => void;
}) {
  return (
    <div
      className="multi-cloud-blended-unblended-tracker mb-6 rounded bg-slate-900 p-4"
      aria-label="multi_cloud_blended_unblended_tracker"
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">
          블렌디드/언블렌디드 추적 (3-cloud-provider)
        </h2>
        <button
          type="button"
          className="rounded bg-purple-600 px-3 py-1 text-sm text-white hover:bg-purple-700"
          onClick={onTrack}
        >
          추적
        </button>
      </div>
      {diff ? (
        <>
          <p className="text-sm text-slate-300">
            cloud_provider:{" "}
            <span className="font-mono">{diff.cloud_provider}</span>
            {" | "}
            tracking_status:{" "}
            <span className="font-mono">{diff.tracking_status}</span>
          </p>
          <p className="text-sm text-slate-300">
            blended_krw/hour:{" "}
            <span className="font-mono">
              {diff.blended_rate_krw_per_hour.toFixed(2)}
            </span>
            {" | "}
            unblended_krw/hour:{" "}
            <span className="font-mono">
              {diff.unblended_rate_krw_per_hour.toFixed(2)}
            </span>
            {" | "}
            diff_pct:{" "}
            <span className="font-mono">
              {diff.rate_diff_pct.toFixed(2)}%
            </span>
          </p>
          <p className="text-xs text-slate-500">
            Naver/KT API 안정성 검증: uptime ≥ 99.0% / P95 ≤ 2s /
            freshness ≤ 24h / accuracy ≥ 95% (4-week rolling sample)
          </p>
        </>
      ) : (
        <p className="text-sm text-slate-400">추적 누름</p>
      )}
    </div>
  );
}

// ── 5. MarketplaceSaaSPricingIntegratorPanel ──
function MarketplaceSaaSPricingIntegratorPanel({
  pricing,
  onIntegrate,
  selectedSource,
  onSelectSource,
}: {
  pricing: MarketplaceSaaSPricingRollup | null;
  onIntegrate: () => void;
  selectedSource: MarketplaceSource;
  onSelectSource: (s: MarketplaceSource) => void;
}) {
  return (
    <div
      className="multi-cloud-marketplace-saas-pricing mb-6 rounded bg-slate-900 p-4"
      aria-label="multi_cloud_marketplace_saas_pricing"
    >
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-100">
          마켓플레이스 SaaS 가격 통합 (5-source)
        </h2>
        <button
          type="button"
          className="rounded bg-amber-600 px-3 py-1 text-sm text-white hover:bg-amber-700"
          onClick={onIntegrate}
        >
          통합
        </button>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        {ALL_MARKETPLACE_SOURCES.map((s) => (
          <button
            key={s}
            type="button"
            className={`rounded px-2 py-1 text-xs ${
              selectedSource === s
                ? "bg-amber-500 text-slate-900"
                : "bg-slate-700 text-slate-200"
            }`}
            onClick={() => onSelectSource(s)}
          >
            {s}
          </button>
        ))}
      </div>
      {pricing ? (
        <>
          <p className="text-sm text-slate-300">
            vendor:{" "}
            <span className="font-mono">{pricing.vendor_name}</span>
            {" / "}
            product:{" "}
            <span className="font-mono">{pricing.product_name}</span>
            {" / "}
            sku: <span className="font-mono">{pricing.sku}</span>
          </p>
          <p className="text-sm text-slate-300">
            effective_price_krw_per_unit:{" "}
            <span className="font-mono">
              {pricing.effective_price_krw_per_unit.toFixed(0)}
            </span>
            {" | "}
            category:{" "}
            <span className="font-mono">{pricing.saas_category}</span>
            {" | "}
            integration_status:{" "}
            <span className="font-mono">{pricing.integration_status}</span>
          </p>
          <p className="text-xs text-slate-500">
            4-hour cron refresh + cheapest 3 alternative suggestion +
            freshness threshold 24h
          </p>
        </>
      ) : (
        <p className="text-sm text-slate-400">소스 선택 후 통합 누름</p>
      )}
    </div>
  );
}

// ── 6. ScheduledMultiCloudDispatchConfigPanel ──
function ScheduledMultiCloudDispatchConfigPanel({
  dispatches,
  onSchedule,
}: {
  dispatches: ScheduledMultiCloudDispatch[];
  onSchedule: (
    req: DispatchMultiCloudRequest,
  ) => Promise<void> | void;
}) {
  const handleClick = (schedule: DispatchMultiCloudRequest["dispatch_schedule"]) => {
    void onSchedule({
      tenant_id: "current",
      dispatch_schedule: schedule,
      recipient_strategy: "owner_only",
      dry_run: true,
    });
  };
  return (
    <div
      className="multi-cloud-scheduled-dispatch mb-6 rounded bg-slate-900 p-4"
      aria-label="multi_cloud_scheduled_dispatch"
    >
      <h2 className="mb-3 text-lg font-semibold text-slate-100">
        정기 디스패치 (KST cron)
      </h2>
      <div className="mb-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
          onClick={() => handleClick("weekly")}
        >
          weekly Mon 09:00
        </button>
        <button
          type="button"
          className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
          onClick={() => handleClick("monthly")}
        >
          monthly 1st 09:00
        </button>
        <button
          type="button"
          className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
          onClick={() => handleClick("quarterly")}
        >
          quarterly 1st 09:00
        </button>
        <button
          type="button"
          className="rounded bg-slate-700 px-3 py-1 text-sm text-slate-100"
          onClick={() => handleClick("annual")}
        >
          annual Jan-1 09:00
        </button>
      </div>
      <p className="text-xs text-slate-500">KST timezone (pytz Asia/Seoul)</p>
      {dispatches.length > 0 && (
        <ul className="mt-3 text-xs text-slate-300">
          {dispatches.map((d) => (
            <li key={d.dispatch_id}>
              {d.dispatch_schedule} | {d.cron_expression} | {d.status}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function FinopsMultiCloudDashboardPanel() {
  const [rollup, setRollup] = useState<MultiCloudRateCardReconciliation | null>(
    null,
  );
  const [cost, setCost] = useState<MultiCloudCostReconciliation | null>(null);
  const [recommendation, setRecommendation] =
    useState<NegotiationRecommendation | null>(null);
  const [diff, setDiff] = useState<BlendedUnblendedDiff | null>(null);
  const [pricing, setPricing] = useState<MarketplaceSaaSPricingRollup | null>(
    null,
  );
  const [dispatches, setDispatches] = useState<ScheduledMultiCloudDispatch[]>(
    [],
  );
  const [selectedSource, setSelectedSource] =
    useState<MarketplaceSource>("aws_marketplace");
  const [error, setError] = useState<string | null>(null);

  const handleRefreshRateCard = async () => {
    try {
      const req: AggregateRateCardRequest = {
        tenant_id: "current",
        scope_type: "tenant",
        scope_id: "default",
        period_key: "2026-08",
        dry_run: true,
      };
      const result = await reconcileRateCards(req);
      setRollup(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleRefreshCost = async () => {
    try {
      const req: AggregateCostRequest = {
        tenant_id: "current",
        scope_type: "tenant",
        scope_id: "default",
        period_key: "2026-08",
        cloud_provider: "aws",
        cost_sources: {
          billing_api: 1000000.0,
          invoice_pdf: 990000.0,
          manual: 1010000.0,
          audit: 1000000.0,
        },
        dry_run: true,
      };
      const result = await reconcileCosts(req);
      setCost(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleRunNegotiation = async () => {
    try {
      const req: NegotiationRequest = {
        tenant_id: "current",
        cloud_provider: "aws",
        commitment_term: "3_year",
      };
      const result = await runNegotiationBot(req);
      setRecommendation(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleTrackBlendedUnblended = async () => {
    try {
      const req: TrackBlendedUnblendedRequest = {
        tenant_id: "current",
        scope_type: "tenant",
        scope_id: "default",
        period_key: "2026-08",
        cloud_provider: "aws",
      };
      const result = await trackBlendedUnblended(req);
      setDiff(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleIntegrateMarketplace = async () => {
    try {
      const req: IntegrateMarketplaceRequest = {
        tenant_id: "current",
        vendor_name: "demo-vendor",
        product_name: "demo-product",
        saas_category: "analytics",
        period_key: "2026-08",
      };
      const result = await integrateMarketplace(req);
      setPricing(result);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  const handleScheduleDispatch = async (
    req: DispatchMultiCloudRequest,
  ) => {
    try {
      const result = await dispatchMultiCloudReport(req);
      setDispatches((prev) => [...prev, result]);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    }
  };

  return (
    <div className="finops-multi-cloud-dashboard-panel">
      {error && (
        <div
          className="mb-4 rounded bg-red-900 p-3 text-sm text-red-100"
          aria-label="multi_cloud_dashboard_error"
        >
          {error}
        </div>
      )}
      <RateCardReconciliationAggregator
        rollup={rollup}
        onRefresh={handleRefreshRateCard}
      />
      <CostReconciliationAggregator
        rollup={cost}
        onRefresh={handleRefreshCost}
      />
      <NegotiationBotPanel
        recommendation={recommendation}
        onRun={handleRunNegotiation}
      />
      <BlendedUnblendedTrackerPanel
        diff={diff}
        onTrack={handleTrackBlendedUnblended}
      />
      <MarketplaceSaaSPricingIntegratorPanel
        pricing={pricing}
        onIntegrate={handleIntegrateMarketplace}
        selectedSource={selectedSource}
        onSelectSource={setSelectedSource}
      />
      <ScheduledMultiCloudDispatchConfigPanel
        dispatches={dispatches}
        onSchedule={handleScheduleDispatch}
      />
    </div>
  );
}
