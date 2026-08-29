/**
 * apps/web/components/m10-ai/AiCommentSection.tsx — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * Story 10.3 (AI Reference vs Auto Analysis Badge Separation) frontend mount.
 * Renders AI comments with appropriate badge based on source_kind.
 *
 * AD-7 verbatim: auto_analysis comments are IMMUTABLE — no edit/modify
 *   UI is rendered (F10.2-(c)). Only ai_reference comments MAY have
 *   user-driven re-confirmation flows.
 *
 * AD-11 layer rule: components/m10-ai/ ONLY mounts + display.
 *
 * CR 11-4 D-005 — Unknown state reject: unknown source_kind
 *   → 'unknown' tag + console.warn + 1-line ko-KR warning banner
 *   (F10.2-(d) strict reject surface).
 */

"use client";

import { useCallback, useEffect, useState } from "react";

import {
  type AICommentEntry,
  type AICommentEnvelope,
  fetchAIComments,
  isSourceKind,
} from "@/lib/ai-comments";
import { ApiError } from "@/lib/api-client";

import { AiReferenceBadge } from "./AiReferenceBadge";
import { AutoAnalysisBadge } from "./AutoAnalysisBadge";

interface AiCommentSectionProps {
  accessToken?: string;
  initialPeriodKey?: string;
  initialCalculationHash?: string;
  onCounterTotal?: (n: number) => void;
}

type LoadState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; comments: AICommentEntry[]; counterTotal: number }
  | { kind: "empty" }
  | { kind: "warning_source_kind"; unknownCount: number }
  | { kind: "error"; message_ko: string; errorCode: string };

export function AiCommentSection({
  accessToken,
  initialPeriodKey,
  initialCalculationHash,
  onCounterTotal,
}: AiCommentSectionProps): React.ReactElement {
  const [state, setState] = useState<LoadState>({ kind: "idle" });

  const load = useCallback(async (): Promise<void> => {
    if (!initialPeriodKey || !initialCalculationHash) {
      setState({ kind: "idle" });
      return;
    }
    setState({ kind: "loading" });
    try {
      const env: AICommentEnvelope = await fetchAIComments(
        {
          period_key: initialPeriodKey,
          calculation_result_hash: initialCalculationHash,
        },
        accessToken,
      );
      if ("status" in env && env.status === "success") {
        if (env.comments.length === 0) {
          setState({ kind: "empty" });
        } else {
          // Defense-in-depth: count unknown source_kind values (F10.2-(d))
          const unknownCount = env.comments.filter(
            (c) => !isSourceKind(c.source_kind),
          ).length;
          if (unknownCount > 0) {
            setState({ kind: "warning_source_kind", unknownCount });
          } else {
            setState({
              kind: "success",
              comments: env.comments,
              counterTotal: env.counter_total,
            });
            onCounterTotal?.(env.counter_total);
          }
        }
      } else {
        const err = env as unknown as { error_code: string; message_ko: string };
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
            err instanceof Error ? err.message : "의견 조회 실패",
          errorCode: "UNPARSEABLE_RESPONSE",
        });
      }
    }
  }, [accessToken, initialPeriodKey, initialCalculationHash, onCounterTotal]);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-4 p-4" data-testid="ai-comment-section">
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          AI 의견
        </h2>
      </div>

      <div data-testid="ai-comment-result-region">
        {state.kind === "idle" && (
          <p className="text-sm text-gray-500">
            기간과 계산 해시를 입력하면 의견이 표시됩니다.
          </p>
        )}
        {state.kind === "loading" && (
          <p className="text-sm text-gray-500">의견 로딩 중...</p>
        )}
        {state.kind === "empty" && (
          <p className="text-sm text-gray-500">
            이 기간에 표시할 AI 의견이 없습니다.
          </p>
        )}
        {state.kind === "warning_source_kind" && (
          <div
            role="alert"
            data-testid="ai-comment-warning"
            className="rounded bg-yellow-50 px-3 py-2 text-xs text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200"
          >
            ⚠ 분석 의견 출처가 불분명합니다 — strict reject 적용 (unknown
            source_kind {state.unknownCount}건)
          </div>
        )}
        {state.kind === "success" && (
          <div className="space-y-3" data-testid="ai-comment-entries">
            <div className="text-xs text-gray-500">
              총 거부 카운터 {state.counterTotal}
            </div>
            {state.comments.map((c) => (
              <div
                key={c.comment_id}
                className="rounded border border-gray-200 bg-white p-3 dark:border-gray-700 dark:bg-gray-900"
                data-testid="ai-comment-entry"
                data-source-kind={c.source_kind}
                data-comment-kind={c.comment_kind}
              >
                <div className="mb-2 flex items-center gap-2">
                  {c.source_kind === "auto_analysis" ? (
                    <AutoAnalysisBadge sourceKind={c.source_kind} />
                  ) : (
                    <AiReferenceBadge sourceKind={c.source_kind} />
                  )}
                </div>
                <p className="text-sm text-gray-800 dark:text-gray-200">
                  {c.body_text}
                </p>
                {c.evidence_ref && (
                  <div className="mt-2 text-xs text-gray-500">
                    출처: {c.evidence_ref}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
        {state.kind === "error" && (
          <div
            role="alert"
            data-testid="ai-comment-error"
            className="rounded bg-red-50 px-3 py-2 text-xs text-red-800 dark:bg-red-950 dark:text-red-200"
          >
            {state.message_ko} ({state.errorCode})
          </div>
        )}
      </div>
    </div>
  );
}
