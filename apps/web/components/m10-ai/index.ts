/**
 * apps/web/components/m10-ai/index.ts — Sprint 10.5 (A38) barrell export for m10-ai components.
 *
 * Sprint 10.5 (cj-style Epic 10 carry-over 14번째 진입점 = cj-style 38번째 epic 연속)
 * — A38 frontend test debt dedicated sprint T1~T5 wire (D-10-1-DEFER-3 + D-10-2-DEFER-4
 * + D-10-3-DEFER-4 + D-10-4-DEFER-4 모두 해소).
 *
 * Barrel export consolidation per 9-7 wire pattern (cj-style carry-over 11번째).
 *
 * AD-11 layer rule: ONLY mounts + display components live here (no business logic
 * or kernel-level computation). All Pydantic parity mirrors live in `apps/web/lib/`.
 */

export { AiDraftCard } from "./AiDraftCard";
export { ConfidenceBadge } from "./ConfidenceBadge";
export { AiExtractModal } from "./AiExtractModal";
export { InsightCachePanel } from "./InsightCachePanel";
export { AiReferenceBadge } from "./AiReferenceBadge";
export { AutoAnalysisBadge } from "./AutoAnalysisBadge";
export { AiCommentSection } from "./AiCommentSection";
export { PromoteConfirmButton } from "./PromoteConfirmButton";
export { PromoteResultToast } from "./PromoteResultToast";
