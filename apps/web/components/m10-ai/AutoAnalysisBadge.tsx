/**
 * apps/web/components/m10-ai/AutoAnalysisBadge.tsx — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * Story 10.3 (AI Reference vs Auto Analysis Badge Separation) frontend mount.
 * Displays the 파란 (blue) badge '📊 자동 분석' for comments with
 * source_kind='auto_analysis'.
 *
 * AD-7 verbatim (F10.2-(a)): source_kind='auto_analysis' → 파란 배지 '📊 자동 분석'.
 *
 * CR 11-4 D-005 — Unknown state reject: unknown source_kind literal
 * → `null` returned + console.warn (defensive guard).
 */

"use client";

import type { SourceKind } from "@/lib/ai-comments";

interface AutoAnalysisBadgeProps {
  sourceKind: SourceKind;
  locale?: "ko-KR" | "en-US";
}

export function AutoAnalysisBadge({
  sourceKind,
  locale = "ko-KR",
}: AutoAnalysisBadgeProps): React.ReactElement | null {
  if (sourceKind !== "auto_analysis") {
    if (process.env.NODE_ENV === "development") {
       
      console.warn(
        `[AutoAnalysisBadge] sourceKind='${sourceKind}' is not 'auto_analysis' — AutoAnalysisBadge MUST NOT render this. Use AiReferenceBadge instead.`,
      );
    }
    return null;
  }

  const label = locale === "ko-KR" ? "📊 자동 분석" : "📊 Auto Analysis";
  const tooltip = "AI는 비권위적입니다 — 확정 책임은 사용자에게";

  return (
    <span
      className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-200"
      data-testid="auto-analysis-badge"
      data-source-kind="auto_analysis"
      title={tooltip}
      aria-label={tooltip}
    >
      {label}
    </span>
  );
}
