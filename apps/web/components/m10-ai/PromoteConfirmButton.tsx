/**
 * apps/web/components/m10-ai/PromoteConfirmButton.tsx — Sprint 10.5 T4 wire (D-10-4-DEFER-4 해소)
 *
 * Story 10.4 (AI Promotion Port Idempotency) frontend mount.
 * Triggers `POST /api/v1/ai/promote` — the AD-17 verbatim promotion port.
 *
 * AD-17 verbatim bind: 3-layer defense stack:
 *   1st: PIPA gate (carried from 10-1/10-2/10-3 — D-10-3-DEFER-6 RESOLVED in 10-4 wire)
 *   2nd: M2-only capability gate (AI_INSIGHT + m2_service_role)
 *   3rd: AD-17 idempotency 3-tuple (tenant_id, period_key, source_draft_id)
 *
 * AD-7 verbatim: M10 NEVER writes confirmed_inputs/monthly_input_rows
 * except via this canonical promote port.
 *
 * AD-15 parity SSOT: this component uses `apps/web/lib/ai-promote.ts`
 * (wire-entered in Story 10.4 sprint) for backend handshake.
 */

"use client";

import { useCallback, useState } from "react";

import {
  type PromoteEnvelope,
  type PromoteRequestBody,
  promoteAiDraft,
} from "@/lib/ai-promote";
import { ApiError } from "@/lib/api-client";

interface PromoteConfirmButtonProps {
  accessToken?: string;
  tenantId: string;
  periodKey: string;
  sourceDraftId: string;
  confirmedValueHash?: string | null;
  actorId: string;
  onSuccess?: (result: Extract<PromoteEnvelope, { status: "success" }>) => void;
  onError?: (
    env: Extract<PromoteEnvelope, { status: Exclude<PromoteEnvelope["status"], "success"> }>,
  ) => void;
  disabled?: boolean;
}

type PromoteState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; env: Extract<PromoteEnvelope, { status: "success" }> }
  | {
      kind: "error";
      env: Extract<
        PromoteEnvelope,
        { status: Exclude<PromoteEnvelope["status"], "success"> }
      >;
      message_ko: string;
    };

export function PromoteConfirmButton({
  accessToken,
  tenantId,
  periodKey,
  sourceDraftId,
  confirmedValueHash = null,
  actorId,
  onSuccess,
  onError,
  disabled = false,
}: PromoteConfirmButtonProps): React.ReactElement {
  const [state, setState] = useState<PromoteState>({ kind: "idle" });

  const handleClick = useCallback(async (): Promise<void> => {
    setState({ kind: "loading" });
    const body: PromoteRequestBody = {
      tenant_id: tenantId,
      period_key: periodKey,
      source_draft_id: sourceDraftId,
      confirmed_value_hash: confirmedValueHash,
      actor_id: actorId,
    };
    try {
      const env = await promoteAiDraft(body, accessToken);
      if (env.status === "success") {
        setState({ kind: "success", env });
        onSuccess?.(env);
      } else {
        // env is the discriminated union's error branch
        const errEnv = env as Extract<
          PromoteEnvelope,
          { status: Exclude<PromoteEnvelope["status"], "success"> }
        >;
        setState({
          kind: "error",
          env: errEnv,
          message_ko: errEnv.message_ko,
        });
        onError?.(errEnv);
      }
    } catch (err) {
      let errEnv: Extract<
        PromoteEnvelope,
        { status: Exclude<PromoteEnvelope["status"], "success"> }
      >;
      if (err instanceof ApiError) {
        const p = err.payload;
        errEnv = {
          status: "draft_immutable",
          code: p.code as
            | "AI_PIPA_CONSENT_MISSING"
            | "PROMOTE_DRAFT_IMMUTABLE"
            | "PROMOTE_SOURCE_DRAFT_NOT_FOUND"
            | "PROMOTE_IDEMPOTENCY_MISMATCH"
            | "INPUT_PROMOTION_M2_ONLY"
            | "INPUT_PROMOTION_DENIED",
          message_ko: p.message_ko,
          details: p.details ?? {},
          trace_id: p.trace_id,
        };
      } else {
        errEnv = {
          status: "draft_immutable",
          code: "PROMOTE_DRAFT_IMMUTABLE",
          message_ko:
            err instanceof Error ? err.message : "승격 요청 실패",
          details: {},
          trace_id: "",
        };
      }
      setState({
        kind: "error",
        env: errEnv,
        message_ko: errEnv.message_ko,
      });
      onError?.(errEnv);
    }
  }, [
    accessToken,
    tenantId,
    periodKey,
    sourceDraftId,
    confirmedValueHash,
    actorId,
    onSuccess,
    onError,
  ]);

  const isLoading = state.kind === "loading";
  const label =
    state.kind === "loading" ? "승격 중..." : "초안 승격 (M2 전용)";

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={(): void => {
          void handleClick();
        }}
        disabled={disabled || isLoading}
        data-testid="promote-confirm-button"
        data-state={state.kind}
        aria-disabled={disabled || isLoading}
        className="rounded bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {label}
      </button>
      {state.kind === "error" && (
        <div
          role="alert"
          data-testid="promote-error-alert"
          data-error-code={state.env.code}
          className="rounded bg-red-50 px-3 py-2 text-xs text-red-800 dark:bg-red-950 dark:text-red-200"
        >
          {state.message_ko} ({state.env.code})
        </div>
      )}
    </div>
  );
}
