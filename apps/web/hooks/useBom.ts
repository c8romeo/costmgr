/**
 * apps/web/hooks/useBom.ts — BOM fetch + bulk-replace hook.
 *
 * Story 2.2 — Task 5.7. Mirrors `useProducts` (Story 2.1) pattern:
 *   - Polls GET /api/v1/baseline/products/{id}/bom on mount + on focus
 *   - Exposes setBom + clearBom mutations
 *   - Returns `{ bom, isLoading, error, refetch, setBom, clearBom }`
 *
 * F-20: server-side initial fetch — `initialBom` is provided by the
 * RSC page (`app/[locale]/(dashboard)/m1-baseline/products/[productId]/page.tsx`).
 *
 * CR 2.1 lesson (100% invariant atomic): setBom is the ONLY mutation
 * path. Per-row add/remove would let the BOM dip below 100% temporarily.
 * The backend validates and returns 422 BOM_INVALID_RATIO /
 * BOM_DUPLICATE_CHILD / etc. typed errors.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  type BOMResponse,
  type BOMSetRequest,
  clearBom as apiClearBom,
  fetchBom as apiFetchBom,
  setBom as apiSetBom,
} from "@/lib/api-client";

export interface UseBomResult {
  bom: BOMResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
  setBom: (body: BOMSetRequest) => Promise<BOMResponse>;
  clearBom: () => Promise<void>;
}

const POLL_MS = 30_000;

export function useBom(
  productId: string,
  accessToken?: string,
  initial?: BOMResponse | null,
): UseBomResult {
  const [bom, setBomState] = useState<BOMResponse | null>(initial ?? null);
  const [isLoading, setIsLoading] = useState<boolean>(initial == null);
  const [error, setError] = useState<string | null>(null);
  const cancelledRef = useRef<boolean>(false);
  const accessTokenRef = useRef(accessToken);
  accessTokenRef.current = accessToken;
  const initialSeedRef = useRef<boolean>(initial != null);
  initialSeedRef.current = initial != null;
  // eslint-disable-next-line @typescript-eslint/no-restricted-types
  const reqIdRef = useRef<number>(0);

  const refetch = useCallback(() => {
    cancelledRef.current = false;
    const isFirstLoad = initialSeedRef.current === false && bom == null;
    if (isFirstLoad) setIsLoading(true);
    const reqId = ++reqIdRef.current;
    apiFetchBom(productId, accessTokenRef.current)
      .then((data) => {
        if (cancelledRef.current || reqId !== reqIdRef.current) return;
        setBomState(data);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelledRef.current || reqId !== reqIdRef.current) return;
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
        setBomState(null);
      })
      .finally(() => {
        if (!cancelledRef.current && reqId === reqIdRef.current && isFirstLoad) {
          setIsLoading(false);
        }
      });
  }, [productId]);

  const setBom = useCallback(
    async (body: BOMSetRequest): Promise<BOMResponse> => {
      const updated = await apiSetBom(productId, body, accessTokenRef.current);
      setBomState(updated);
      return updated;
    },
    [productId],
  );

  const clearBom = useCallback(async (): Promise<void> => {
    await apiClearBom(productId, accessTokenRef.current);
    // Refetch to get the cleared state (empty BOM).
    refetch();
  }, [productId, refetch]);

  useEffect(() => {
    refetch();
    const onFocus = () => {
      refetch();
    };
    const onVisibility = () => {
      if (document.visibilityState === "visible") refetch();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    const interval = setInterval(refetch, POLL_MS);
    return () => {
      clearInterval(interval);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
      cancelledRef.current = true;
    };
  }, [refetch]);

  return { bom, isLoading, error, refetch, setBom, clearBom };
}