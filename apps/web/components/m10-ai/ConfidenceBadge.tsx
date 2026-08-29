/**
 * apps/web/components/m10-ai/ConfidenceBadge.tsx — Sprint 10.5 T1 wire (D-10-1-DEFER-3 해소)
 *
 * Story 10.1 (AI Document Extraction) confidence indicator badge.
 *
 * AD-7 verbatim bind: extraction_confidence threshold per master PRD
 * §8.1 M0-c 70% 임계값.
 *
 * Thresholds:
 *   - confidence >= 0.85 → GREEN (높음 — 자동 확인 가능)
 *   - 0.70 <= confidence < 0.85 → YELLOW (중간 — 사용자 확인 권장)
 *   - confidence < 0.70 → RED (낮음 — 사용자 확인 필수)
 *
 * AD-15 parity SSOT: threshold constants mirror `MonthlyDraftResponse.
 * confidence` Decimal field (Python) and the `extraction_confidence <
 * 0.70 → RED` invariant in `apps/api/modules/m10_ai/service.py`.
 */

"use client";

import { MONTHLY_EXTRACT_CONFIDENCE_THRESHOLD } from "@/lib/ai-extract";

interface ConfidenceBadgeProps {
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  confidence: number;
  locale?: "ko-KR" | "en-US";
}

const HIGH_CONFIDENCE_THRESHOLD = 0.85;

function classifyConfidence(
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  confidence: number,
): "high" | "medium" | "low" {
  if (confidence >= HIGH_CONFIDENCE_THRESHOLD) return "high";
  if (confidence >= MONTHLY_EXTRACT_CONFIDENCE_THRESHOLD) return "medium";
  return "low";
}

const BADGE_STYLES: Readonly<
  Record<
    "high" | "medium" | "low",
    { label: string; className: string; ariaLabel: string }
  >
> = {
  high: {
    label: "높음",
    className:
      "bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-200",
    ariaLabel: "높은 신뢰도",
  },
  medium: {
    label: "중간",
    className:
      "bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-200",
    ariaLabel: "중간 신뢰도",
  },
  low: {
    label: "낮음",
    className:
      "bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-200",
    ariaLabel: "낮은 신뢰도 — 사용자 확인 필수",
  },
} as const;

export function ConfidenceBadge({
  confidence,
  locale = "ko-KR",
}: ConfidenceBadgeProps): React.ReactElement {
  // Clamp invalid values defensively (AD-15 parity SSOT never-reject boundary)
  const safe =
    Number.isFinite(confidence) && confidence >= 0 && confidence <= 1
      ? confidence
      : 0;

  const tier = classifyConfidence(safe);
  const style = BADGE_STYLES[tier];
  const displayLabel = locale === "ko-KR" ? style.label : tier;

  return (
    <span
      className={`inline-flex items-center gap-1 rounded px-2 py-0.5 text-xs font-medium ${style.className}`}
      data-testid="confidence-badge"
      data-confidence-tier={tier}
      data-confidence-value={safe.toFixed(2)}
      aria-label={style.ariaLabel}
      title={`confidence ${safe.toFixed(2)}`}
    >
      {displayLabel} ({safe.toFixed(2)})
    </span>
  );
}
