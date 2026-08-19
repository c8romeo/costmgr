/**
 * apps/web/components/m10-ai/InsightCachePanel.tsx — Sprint 10.5 T2 wire (D-10-2-DEFER-4 해소)
 *
 * Story 10.2 (Three-Insight Cache Policy) frontend mount.
 * Displays the 3 insights returned by `GET /api/v1/ai/insights` for
 * the selected period + calculation_result_hash.
 *
 * AD-7 verbatim: this component is DISPLAY ONLY on the cache output.
 * Story 10.3 wires `source_kind='ai_reference'` badge separation.
 * 10-2 wire 진입 시점에 all 3 default insights are `source_kind='auto_analysis'`.
 *
 * AD-11 layer rule: components/m10-ai/ ONLY mounts + display; no
 * business logic in this file. Cache key composition lives in
 * `apps/web/lib/insight-cache.ts` AD-25 verbatim 3-tuple helper.
 *
 * CR 11-4 D-005 — Unknown state reject (no flicker):
 *   - Loading state shows spinner + cache key sha256 prefix only
 *   - Empty results show explicit empty state (no half-rendered list)
 */

"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api-client";
import {
  composeInsightCacheKey,
  fetchInsightCache,
  type InsightEntry,
  type InsightEnvelope,
  type InsightKind,
} from "@/lib/insight-cache";

const INSIGHT_KIND_LABEL_KO: Readonly<Record<InsightKind, string>> = {
  cost_reduction_candidate: "비용 절감 후보",
  anomaly_pattern: "이상 패턴",
  forecast: "예측",
};

interface InsightCachePanelProps {
  accessToken?: string;
  initialPeriodKey?: string;
  initialCalculationHash?: string;
  tenantId?: string;
}

type LoadState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; entries: InsightEntry[]; periodKey: string; hitCount: number; missCount: number }
  | { kind: "empty"; periodKey: string }
  | { kind: "error"; message_ko: string; errorCode: string };

export function InsightCachePanel({
  accessToken,
  initialPeriodKey,
  initialCalculationHash,
  tenantId,
}: InsightCachePanelProps): React.ReactElement {
  const [periodKey, setPeriodKey] = useState<string>(initialPeriodKey ?? "");
  const [calcHash, setCalcHash] = useState<string>(initialCalculationHash ?? "");
  const [state, setState] = useState<LoadState>({ kind: "idle" });

  const loadInsights = useCallback(async (): Promise<void> => {
    if (!periodKey || !calcHash) {
      setState({ kind: "idle" });
      return;
    }
    setState({ kind: "loading" });
    try {
      const env: InsightEnvelope = await fetchInsightCache(
        { period_key: periodKey, calculation_result_hash: calcHash },
        accessToken,
      );
      if ("status" in env && env.status === "success") {
        if (env.insights.length === 0) {
          setState({ kind: "empty", periodKey: env.period_key });
        } else {
          setState({
            kind: "success",
            entries: env.insights,
            periodKey: env.period_key,
            hitCount: env.hit_count,
            missCount: env.miss_count,
          });
        }
      } else {
        const err = env as unknown as {
          error_code: string;
          message_ko: string;
        };
        setState({
          kind: "error",
          message_ko: err.message_ko,
          errorCode: err.error_code,
        });
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setState({
          kind: "error",
          message_ko: err.payload.message_ko,
          errorCode: err.payload.code,
        });
      } else {
        setState({
          kind: "error",
          message_ko:
            err instanceof Error ? err.message : "인사이트 조회 실패",
          errorCode: "UNPARSEABLE_RESPONSE",
        });
      }
    }
  }, [accessToken, periodKey, calcHash]);

  useEffect(() => {
    if (initialPeriodKey && initialCalculationHash) {
      void loadInsights();
    }
    // loadInsights is intentionally excluded from deps — initial load only
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cacheKey = tenantId
    ? composeInsightCacheKey(tenantId, periodKey, calcHash)
    : "";

  return (
    <div
      className="space-y-4 p-4"
      data-testid="insight-cache-panel"
      data-cache-key={cacheKey}
    >
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          AI 인사이트 캐시
        </h2>
        <p className="text-sm text-gray-500">3-인사이트 캐시 정책 (PRD §F10.1)</p>
      </div>

      <div className="flex flex-col gap-2 sm:flex-row">
        <div className="flex-1">
          <label
            htmlFor="period_key"
            className="block text-xs font-medium text-gray-700 dark:text-gray-300"
          >
            기간
          </label>
          <input
            id="period_key"
            type="text"
            placeholder="2026-07"
            value={periodKey}
            onChange={(e): void => setPeriodKey(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
            data-testid="insight-period-input"
          />
        </div>
        <div className="flex-1">
          <label
            htmlFor="calc_hash"
            className="block text-xs font-medium text-gray-700 dark:text-gray-300"
          >
            계산 해시 (V4 verbatim)
          </label>
          <input
            id="calc_hash"
            type="text"
            placeholder="abc123def456..."
            value={calcHash}
            onChange={(e): void => setCalcHash(e.target.value)}
            className="mt-1 w-full rounded border border-gray-300 px-3 py-1.5 text-sm dark:border-gray-700 dark:bg-gray-800"
            data-testid="insight-hash-input"
          />
        </div>
        <button
          type="button"
          onClick={(): void => {
            void loadInsights();
          }}
          className="self-end rounded bg-blue-600 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
          data-testid="insight-load-button"
        >
          조회
        </button>
      </div>

      <div data-testid="insight-result-region">
        {state.kind === "idle" && (
          <p className="text-sm text-gray-500" data-testid="insight-idle">
            기간과 계산 해시를 입력한 뒤 [조회] 버튼을 클릭하세요.
          </p>
        )}
        {state.kind === "loading" && (
          <p
            className="text-sm text-gray-500"
            data-testid="insight-loading"
          >
            인사이트 로딩 중...
          </p>
        )}
        {state.kind === "empty" && (
          <p className="text-sm text-gray-500" data-testid="insight-empty">
            이 기간에 표시할 인사이트가 없습니다.
          </p>
        )}
        {state.kind === "success" && (
          <div data-testid="insight-entries">
            <div className="mb-3 flex gap-4 text-xs text-gray-500">
              <span>캐시 적중 {state.hitCount}건</span>
              <span>캐시 미적중 {state.missCount}건</span>
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              {state.entries.map((entry, idx) => (
                <div
                  key={`${entry.insight_kind}-${idx}`}
                  className="rounded-md border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900"
                  data-testid="insight-entry"
                  data-insight-kind={entry.insight_kind}
                  data-source-kind={entry.source_kind}
                >
                  <div className="text-xs font-medium uppercase text-gray-500">
                    {INSIGHT_KIND_LABEL_KO[entry.insight_kind]}
                  </div>
                  <div className="mt-1 text-sm text-gray-900 dark:text-gray-100">
                    {entry.question}
                  </div>
                  <div className="mt-2 text-sm text-gray-700 dark:text-gray-300">
                    {entry.answer}
                  </div>
                  {entry.evidence_ref && (
                    <div className="mt-2 text-xs text-gray-500">
                      출처: {entry.evidence_ref}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
        {state.kind === "error" && (
          <div
            role="alert"
            data-testid="insight-error"
            className="rounded bg-red-50 px-3 py-2 text-xs text-red-800 dark:bg-red-950 dark:text-red-200"
          >
            {state.message_ko} ({state.errorCode})
          </div>
        )}
      </div>
    </div>
  );
}
