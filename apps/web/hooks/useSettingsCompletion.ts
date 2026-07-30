/**
 * apps/web/hooks/useSettingsCompletion.ts — completion status polling hook.
 *
 * Story 1.2 — Task 5.6. React state-based hook (the project does not yet pull
 * in TanStack Query per Story 0.5 deferral; polling uses a lightweight timer
 * driven by `useEffect` + `useState`). The hook:
 *   - Calls `GET /api/v1/tenant-settings/completion` on mount + on focus
 *   - Returns `{ status, refetch }` for the [계산] button + tooltip
 *   - 5-second stale window to avoid hammering the API while typing
 *
 * Cross-language: the wire shape mirrors
 * `apps/api/modules/m0_onboarding/schemas.py::CompletionStatusResponse`
 * and `packages/services/m0_onboarding/settings_completion.py::CompletionStatus`.
 * Drift is caught by `tests/integration/test_completion_consistency.py` (Story 1.2 T7.5).
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  type CompletionStatus,
  fetchCompletionStatus,
} from "@/lib/api-client";

export interface UseSettingsCompletionResult {
  status: CompletionStatus | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
}

const POLL_MS = 30_000; // background poll cadence while a wizard step is mounted

export function useSettingsCompletion(
  accessToken?: string,
  initial?: CompletionStatus | null,
): UseSettingsCompletionResult {
  // F-20: server-side initial fetch — `initial` is provided by the RSC
  // when the wizard page renders server-side. Seed from it so the very
  // first render already shows the correct completion state (no race
  // between render and the first poll).
  const [status, setStatus] = useState<CompletionStatus | null>(initial ?? null);
  const [isLoading, setIsLoading] = useState<boolean>(initial == null);
  const [error, setError] = useState<string | null>(null);
  // F-4: cancellation guard. Replaces the broken "return cleanup"
  // pattern (callers never invoked the returned closure, so pending
  // fetches could clobber newer state).
  const cancelledRef = useRef<boolean>(false);
  const accessTokenRef = useRef(accessToken);
  accessTokenRef.current = accessToken;
  // F-20: track whether the RSC already supplied initial state so we can
  // skip the on-mount refetch.
  const initialSeedRef = useRef<boolean>(initial != null);
  initialSeedRef.current = initial != null;
  // F-27: `isLoading` is only true during the FIRST fetch (no data yet).
  // Background refetches leave it alone so the [계산] button does not
  // flicker disabled → enabled during polling. `statusRef` lets the
  // callback read the current `status` without rebuilding the callback
  // on every status change.
  const statusRef = useRef<CompletionStatus | null>(initial ?? null);

  const refetch = useCallback(() => {
    cancelledRef.current = false;
    const isFirstLoad = statusRef.current === null;
    if (isFirstLoad) setIsLoading(true);
    fetchCompletionStatus(accessTokenRef.current)
      .then((data) => {
        if (cancelledRef.current) return;
        statusRef.current = data;
        setStatus(data);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelledRef.current) return;
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
        // F-30: clear cached status on error so the UI flips back to a
        // defensive disabled state until the next successful poll.
        statusRef.current = null;
        setStatus(null);
      })
      .finally(() => {
        if (!cancelledRef.current && isFirstLoad) setIsLoading(false);
      });
  }, []);

  // Keep statusRef in sync so refetch() always sees the latest.
  useEffect(() => {
    statusRef.current = status;
  }, [status]);

  useEffect(() => {
    // F-20: skip the on-mount refetch when the RSC already supplied
    // initial state — that data is fresh enough.
    if (!initialSeedRef.current) {
      refetch();
    }
    // F-10: refetch on window focus (spec T5.6 mandate). Without this the
    // wizard stays stale for up to POLL_MS after the user returns to a
    // tab where another tab made a save.
    const onFocus = () => {
      refetch();
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") refetch();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    const interval = setInterval(refetch, POLL_MS); // F-28: dropped the dead STALE_MS gate.
    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
      cancelledRef.current = true; // F-4: cancel in-flight on unmount.
    };
  }, [refetch]);

  return { status, isLoading, error, refetch };
}