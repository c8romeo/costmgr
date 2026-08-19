/**
 * apps/web/lib/m10-ai-types.ts — Sprint 10.5 T5 wire (A38 AC #5)
 *
 * Shared TypeScript type aliases for m10-ai module — consolidates the
 * Discriminated union type aliases used across AiDraftCard, AiExtractModal,
 * InsightCachePanel, AiReferenceBadge, AutoAnalysisBadge, AiCommentSection,
 * PromoteConfirmButton, PromoteResultToast.
 *
 * AD-15 cross-language parity SSOT: types mirror Python Literal Values
 * in apps/api/modules/m10_ai/schemas.py and packages/services/m10_ai/*_kernel.py.
 *
 * CR 11-4 D-005 — Unknown state reject: exhaustive type guards with
 * `never` return type ensure compiler-time exhaustiveness checks on
 * Discriminated union `status` discriminators.
 */

import type { PromoteEnvelope, PromoteStatus } from "./ai-promote";
import type { InsightKind, SourceKind } from "./insight-cache";
import type { AICommentKind } from "./ai-comments";

// Re-export common union types (single source of truth for components)
export type { SourceKind, InsightKind, AICommentKind, PromoteStatus };

// Shared helper: exhaustive switch guard (TS compiler-enforced)
export function assertExhaustive(x: never): never {
  throw new Error(
    `Unexpected value '${JSON.stringify(x)}' — must handle every case (CR 11-4 D-005)`,
  );
}

// 8 endpoint URL constants — used by mocks + tests (T5 AC #5)
export const M10_AI_ENDPOINT_PATHS = {
  EXTRACT_MONTHLY: "/api/v1/ai/extract-monthly",
  INSIGHTS: "/api/v1/ai/insights",
  COMMENTS: "/api/v1/ai/comments",
  PROMOTE: "/api/v1/ai/promote",
} as const;

export type M10AiEndpointPath =
  (typeof M10_AI_ENDPOINT_PATHS)[keyof typeof M10_AI_ENDPOINT_PATHS];

// PromoteEnvelope re-export w/ type guard (re-exported for convenience)
export type { PromoteEnvelope };
