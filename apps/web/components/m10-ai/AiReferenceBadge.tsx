/**
 * apps/web/components/m10-ai/AiReferenceBadge.tsx — Sprint 10.5 T3 wire (D-10-3-DEFER-4 해소)
 *
 * Story 10.3 (AI Reference vs Auto Analysis Badge Separation) frontend mount.
 * Displays the 보라 (purple) badge '🤖 AI 참고(검증 필요)' for comments with
 * source_kind='ai_reference'.
 *
 * AD-7 verbatim (F10.2-(a)): source_kind='ai_reference' → 보라 배지 '🤖 AI 참고(검증 필요)'.
 * AD-22 ledger append-only: this badge is a frontend-only marker; the
 * backend service decides source_kind and the badge is read-only display.
 *
 * CR 11-4 D-005 — Unknown state reject: unknown source_kind literal
 * → `null` returned + console.warn (defensive guard). The frontend MUST
 * NOT silently coerce unknown source_kind values to 'auto_analysis' (audit
 * leakage risk).
 */

"use client";

import type { SourceKind } from "@/lib/ai-comments";

interface AiReferenceBadgeProps {
  sourceKind: SourceKind;
  locale?: "ko-KR" | "en-US";
}

export function AiReferenceBadge({
  sourceKind,
  locale = "ko-KR",
}: AiReferenceBadgeProps): React.ReactElement | null {
  if (sourceKind !== "ai_reference") {
    if (process.env.NODE_ENV === "development") {
      // eslint-disable-next-line no-console
      console.warn(
        `[AiReferenceBadge] sourceKind='${sourceKind}' is not 'ai_reference' — AiReferenceBadge MUST NOT render this. Use AutoAnalysisBadge instead.`,
      );
    }
    return null;
  }

  const label =
    locale === "ko-KR" ? "🤖 AI 참고(검증 필요)" : "🤖 AI Reference (verification required)";
  const tooltip = "AI는 비권위적입니다 — 확정 책임은 사용자에게";

  return (
    <span
      className="inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-950 dark:text-purple-200"
      data-testid="ai-reference-badge"
      data-source-kind="ai_reference"
      title={tooltip}
      aria-label={tooltip}
    >
      {label}
    </span>
  );
}
