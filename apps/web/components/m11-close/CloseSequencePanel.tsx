/**
 * apps/web/components/m11-close/CloseSequencePanel.tsx — Story 11.4 (A13 sprint-up)
 *
 * M11 4단계 마감 시퀀스 패널 (11-2 carry-over from sprint-up).
 *
 * Renders 4-step close sequence (divisions → manufacturing → abc →
 * common → confirmed) with per-step completion timestamps and a
 * [마감 확정] button. AD-6 close lock PRIMARY guard (PRD §F11.1).
 *
 * Korean SSOT: `lib/ko-KR.json::m11_close.close_sequence_*`.
 */

"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

import {
  CLOSE_SEQUENCE_STAGES,
  STEP_TIMESTAMP_ATTRS,
  computeCloseSequenceState,
  formatCloseSequenceStateKo,
  validateCloseSequenceOrder,
  type CloseSequenceStage,
} from "@/lib/m11-close-sequence";
import { CloseSequenceConfirmButton } from "./CloseSequenceConfirmButton";
import { CloseSequenceStepCompleteButton } from "./CloseSequenceStepCompleteButton";

export interface CloseSequencePanelProps {
  /** 4-stage completion timestamps (ISO-8601 UTC strings or null). */
  divisions_completed_at: string | null;
  manufacturing_completed_at: string | null;
  abc_completed_at: string | null;
  common_completed_at: string | null;
  /** Per-step click handler — receives the stage name. */
  onStepComplete?: (stage: "divisions" | "manufacturing" | "abc" | "common") => Promise<void>;
  /** Confirm click handler — fires when [마감 확정] is clicked. */
  onConfirm?: () => Promise<void>;
  /** Capability gate (CLOSE_SEQUENCE_CONFIRM). */
  capability_granted: boolean;
  /** Optional className override. */
  className?: string;
}

/**
 * CloseSequencePanel — 4-stage close sequence panel + step + confirm UI.
 *
 * Renders AD-6 close lock progress + 4 step-complete buttons + 1
 * confirm button. Toast feedback handled by individual button components.
 */
export function CloseSequencePanel({
  divisions_completed_at,
  manufacturing_completed_at,
  abc_completed_at,
  common_completed_at,
  onStepComplete,
  onConfirm,
  capability_granted,
  className,
}: CloseSequencePanelProps): React.ReactElement | null {
  const t = useTranslations("close_sequence_panel");

  if (!capability_granted) {
    return null;
  }

  // Compute sequence order result + state via TS mirror.
  const orderResult = validateCloseSequenceOrder({
    divisions_completed_at,
    manufacturing_completed_at,
    abc_completed_at,
    common_completed_at,
  });
  // P-010: Derive closed_at from the 4 stage timestamps — when all 4 stages
  // are complete (next_step === "confirmed"), use the common_completed_at
  // timestamp as the close-confirmation proxy so that
  // computeCloseSequenceState returns "confirmed" instead of "common".
  // TODO: Replace this heuristic with a parent-supplied closed_at prop
  // once the confirm action returns the actual server-confirmed timestamp.
  const allStagesCompleted = orderResult.next_step === "confirmed";
  const state: CloseSequenceStage = computeCloseSequenceState({
    divisions_completed_at,
    manufacturing_completed_at,
    abc_completed_at,
    common_completed_at,
    closed_at: allStagesCompleted ? common_completed_at : null,
  });

  const timestamps: Record<string, string | null> = {
    divisions: divisions_completed_at,
    manufacturing: manufacturing_completed_at,
    abc: abc_completed_at,
    common: common_completed_at,
  };

  const completedCount = STEP_TIMESTAMP_ATTRS.filter(
    (attr) => timestamps[attr.replace("_completed_at", "")] !== null,
  ).length;

  return (
    <section
      className={
        "rounded-md border border-slate-200 bg-white p-4 shadow-sm " +
        (className ?? "")
      }
      data-testid="close-sequence-panel"
      data-completed-count={completedCount}
      data-valid={orderResult.valid}
      data-next-step={orderResult.next_step ?? "confirmed"}
    >
      <h2 className="mb-2 text-lg font-semibold text-slate-900">
        {t("panel_title")}
      </h2>
      <p className="mb-2 text-sm text-slate-600">
        {t("panel_step_indicator")}
      </p>
      <p className="mb-4 text-sm font-mono text-slate-700">
        {t("progress_label", { completed: completedCount })}
        {" — "}
        {formatCloseSequenceStateKo(state)}
      </p>
      <ol className="mb-4 space-y-2">
        {CLOSE_SEQUENCE_STAGES.slice(0, 4).map((stage, idx) => {
          const completed = timestamps[stage] !== null;
          return (
            <li
              key={stage}
              data-testid={`close-sequence-step-${stage}`}
              data-completed={completed}
              className="flex items-center justify-between rounded border border-slate-200 bg-slate-50 px-3 py-2"
            >
              <span className="text-sm font-mono">
                {idx + 1}. {stage}
                {completed && (
                  <span className="ml-2 text-xs text-green-600">
                    ✓ {timestamps[stage]}
                  </span>
                )}
              </span>
              <CloseSequenceStepCompleteButton
                stage={stage as "divisions" | "manufacturing" | "abc" | "common"}
                disabled={
                  orderResult.next_step !== stage &&
                  orderResult.next_step !== "confirmed"
                }
                onClick={onStepComplete}
              />
            </li>
          );
        })}
      </ol>
      <CloseSequenceConfirmButton
        disabled={!orderResult.valid || orderResult.next_step !== "confirmed"}
        onClick={onConfirm}
      />
    </section>
  );
}