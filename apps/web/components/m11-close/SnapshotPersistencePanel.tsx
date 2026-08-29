/**
 * apps/web/components/m11-close/SnapshotPersistencePanel.tsx — Story 11.4 (A13 sprint-up)
 *
 * M11 스냅샷 영구화 패널 — AD-20 verified → committed 전이 UI.
 *
 * Mounted in `MonthlyInputTabs` (closing period section). Renders a
 * panel with the current snapshot state, [스냅샷 영구화] button, and
 * toast feedback for 4 outcomes (OK / idempotent / draft-reject /
 * reversed-reject).
 *
 * Capability gate: `Capability.SNAPSHOT_PERSISTENCE` (manufacturing 3종 ✅ / service-only ❌).
 * When `capability_granted=false`, the panel is hidden (service-only tenant UX).
 *
 * Korean SSOT: `lib/ko-KR.json::m11_close` + `messages/ko-KR.json::snapshot_persistence_panel`.
 * AD-15 §11 parity invariant preserved between Python ko-KR + TS messages mirror.
 */

"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import * as React from "react";
import { toast } from "sonner";

import {
  SNAPSHOT_COMMIT_DRAFT_REJECT_KO,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  SNAPSHOT_COMMIT_IDEMPOTENT_KO,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  SNAPSHOT_COMMIT_OK_KO,
  SNAPSHOT_COMMIT_REVERSED_REJECT_KO,
  buildSnapshotPersistenceState,
  formatCommitResultKo,
  isCommitAllowed,
  type SnapshotPersistenceState,
} from "@/lib/m11-snapshot-persistence";

export interface SnapshotPersistencePanelProps {
  /** Snapshot id (UUID v4 wire format). */
  snapshot_id: string;
  /** Period key (AD-24 typed "YYYY-MM"). */
  period_key: string;
  /** Current snapshot state (draft | verified | committed | reversed). */
  current_state: "draft" | "verified" | "committed" | "reversed";
  /** Actor id (UUID v4 wire format). */
  actor_id: string;
  /** Tenant id (UUID v4 wire format). */
  tenant_id: string;
  /** Capability.SNAPSHOT_PERSISTENCE capability_granted mirror. */
  capability_granted: boolean;
  /** Click handler that triggers the POST. */
  onCommit?: (payload: {
    snapshot_id: string;
    period_key: string;
  }) => Promise<{
    snapshot_id: string;
    period_key: string;
    state: "draft" | "verified" | "committed" | "reversed";
    cache_invalidation_receipts?: Array<Record<string, string>>;
    trace_id: string;
  }>;
  /** Optional className override. */
  className?: string;
}

/**
 * SnapshotPersistencePanel — AD-20 verified → committed transition UI.
 *
 * Hidden when capability_granted=false (service-only tenant). Toast
 * feedback covers 4 outcomes: OK / idempotent / draft-reject /
 * reversed-reject. Idempotent no-op per CR 1.1.
 */
export function SnapshotPersistencePanel({
  snapshot_id,
  period_key,
  current_state,
  actor_id,
  tenant_id,
  capability_granted,
  onCommit,
  className,
}: SnapshotPersistencePanelProps): React.ReactElement | null {
  const t = useTranslations("snapshot_persistence_panel");
  const router = useRouter();
  const [submitting, setSubmitting] = React.useState(false);

  // P-009 — committed state is terminal (AD-20); 영구화 button is no-op.
  const isCommitted = current_state === "committed";

  // Capability gate: service-only tenant → panel hidden entirely.
  if (!capability_granted) {
    return null;
  }

  // Compute authorization state via TS mirror.
  const state: SnapshotPersistenceState = buildSnapshotPersistenceState({
    snapshot_id,
    period_key,
    current_state,
    actor_id,
    tenant_id,
  });

  const handleCommit = async (): Promise<void> => {
    if (submitting) return; // idempotent no-op (CR 1.1)
    if (isCommitted) {
      // P-009 — committed is terminal; render disabled + already_committed_label.
      toast(t("already_committed_label") ?? "이미 영구화 완료");
      return;
    }
    if (!isCommitAllowed(state)) {
      // Should never happen — button disabled when not allowed.
      toast.error(state.reject_reason_ko ?? SNAPSHOT_COMMIT_DRAFT_REJECT_KO);
      return;
    }
    setSubmitting(true);
    try {
      const response = await onCommit?.({ snapshot_id, period_key });
      if (response) {
        // P-002 — backend envelope uses `cache_invalidation_receipts` (AD-25
        // multi-channel publish receipt) + `state` (current state after
        // commit). Idempotent no-op is detected via `state='committed'` on
        // a re-commit call (CR 1.1 SSOT).
        if ((response.cache_invalidation_receipts?.length ?? 0) > 0) {
          toast.success(t("committed_toast"));
        } else {
          toast.success(t("idempotent_toast"));
        }
      }
      // P-014 — re-fetch RSC tree so the parent Server Component
      // re-reads monthly_input_periods.status + finalized_at + audit
      // trail on next render (CR 6-1 revalidatePath pattern).
      router.refresh();
    } catch (err) {
      // P-001 — distinguish network errors vs state errors vs 404.
      // Network error (fetch failed): connection issue, not a state problem.
      // 404: snapshot not found (rare race; period mismatch).
      // State error: backend returned non-OK (already in correct envelope).
      const msg = err instanceof Error ? err.message : "";
      if (err instanceof TypeError || msg.includes("fetch")) {
        toast.error(t("network_error_toast") ?? "네트워크 오류");
      } else if (msg.includes("404")) {
        toast.error(t("snapshot_not_found_toast") ?? "스냅샷을 찾을 수 없습니다");
      } else {
        toast.error(t("commit_failed_toast") ?? "영구화 실패");
      }
    } finally {
      setSubmitting(false);
    }
  };

  const allowed = isCommitAllowed(state);
  const buttonLabel = isCommitted
    ? t("already_committed_label") ?? "이미 영구화 완료"
    : allowed
      ? t("commit_button")
      : state.terminal_rejected
        ? SNAPSHOT_COMMIT_REVERSED_REJECT_KO
        : state.reject_reason_ko ?? SNAPSHOT_COMMIT_DRAFT_REJECT_KO;

  return (
    <section
      className={
        "rounded-md border border-slate-200 bg-white p-4 shadow-sm " +
        (className ?? "")
      }
      data-testid="snapshot-persistence-panel"
      data-current-state={current_state}
      data-capability-granted={capability_granted}
    >
      <h2 className="mb-2 text-lg font-semibold text-slate-900">
        {t("panel_title")}
      </h2>
      <p className="mb-4 text-sm text-slate-600">
        {t("panel_step_indicator")}
      </p>
      <div className="mb-4 text-sm text-slate-700">
        <span className="font-mono">state: {current_state}</span>
        <span className="ml-3 font-mono">
          result: {formatCommitResultKo(state)}
        </span>
      </div>
      <button
        type="button"
        onClick={handleCommit}
        disabled={isCommitted || submitting || !allowed}
        data-testid="snapshot-persistence-commit-button"
        data-current-state={current_state}
        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {buttonLabel}
      </button>
    </section>
  );
}