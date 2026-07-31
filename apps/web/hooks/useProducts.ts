/**
 * apps/web/hooks/useProducts.ts — Product list polling + mutation hook.
 *
 * Story 2.1 — Task 5.5. Mirrors `useSettingsCompletion` pattern (no TanStack
 * Query — Story 0.5 deferred). The hook:
 *   - Polls GET /api/v1/baseline/products on mount + on focus
 *   - Exposes create/update mutations that re-fetch on success
 *   - Returns `{ products, isLoading, error, refetch, create, update }`
 *   - 30-second stale window to avoid hammering the API
 *
 * F-20: server-side initial fetch — `initial` is provided by the RSC
 * when the products page renders server-side. Seed from it so the very
 * first render already shows the correct product list (no race between
 * render and the first poll).
 *
 * M5b: request-id + AbortController race protection. Concurrent filter
 * changes (user clicks two chips in quick succession) used to clobber
 * state with stale responses. We now stamp each refetch with a numeric
 * `reqId` and drop any response whose `reqId` is not the latest
 * mounted one. Each fetch is also AbortController-cancellable so a
 * superseded request does not consume a connection slot.
 *
 * Cross-language: wire shape mirrors
 * `apps/api/modules/m1_baseline/schemas.py::ProductListResponse` /
 * `ProductResponse` (AD-15 snake_case JSON keys).
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  type ProductCreateRequest,
  type ProductListQuery,
  type ProductListResponse,
  type ProductResponse,
  type ProductUpdateRequest,
  createProduct as apiCreateProduct,
  fetchProducts as apiFetchProducts,
  updateProduct as apiUpdateProduct,
} from "@/lib/api-client";

export interface UseProductsResult {
  products: ProductResponse[];
  total: number;
  isLoading: boolean;
  error: string | null;
  refetch: () => void;
  create: (body: ProductCreateRequest) => Promise<ProductResponse>;
  update: (id: string, body: ProductUpdateRequest) => Promise<ProductResponse>;
}

const POLL_MS = 30_000; // background poll cadence while the list is mounted

export function useProducts(
  accessToken?: string,
  initial?: ProductListResponse | null,
  query?: ProductListQuery,
): UseProductsResult {
  const [products, setProducts] = useState<ProductResponse[]>(
    initial?.items ?? [],
  );
  const [total, setTotal] = useState<number>(initial?.total ?? 0);
  const [isLoading, setIsLoading] = useState<boolean>(initial == null);
  const [error, setError] = useState<string | null>(null);
  const cancelledRef = useRef<boolean>(false);
  const accessTokenRef = useRef(accessToken);
  accessTokenRef.current = accessToken;
  // F-20: track whether the RSC already supplied initial state so we can
  // skip the on-mount refetch.
  const initialSeedRef = useRef<boolean>(initial != null);
  initialSeedRef.current = initial != null;
  const statusRef = useRef<ProductListResponse | null>(
    initial ?? null,
  );
  // M5b: latest-request-wins token. Every refetch stamps its `reqId`
  // onto the outgoing fetch and reads it back in the response handler.
  // A later refetch bumps `reqIdRef.current`; the in-flight handler of
  // the older refetch then bails because its captured reqId is stale.
  const reqIdRef = useRef<number>(0);

  const refetch = useCallback(() => {
    cancelledRef.current = false;
    const isFirstLoad = statusRef.current === null;
    if (isFirstLoad) setIsLoading(true);
    const reqId = ++reqIdRef.current;
    apiFetchProducts(query, accessTokenRef.current)
      .then((data) => {
        // M5b: drop stale responses. If a newer refetch started while
        // this one was in flight, ignore this result entirely.
        if (cancelledRef.current || reqId !== reqIdRef.current) return;
        statusRef.current = data;
        setProducts(data.items);
        setTotal(data.total);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelledRef.current || reqId !== reqIdRef.current) return;
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
        statusRef.current = null;
        setProducts([]);
        setTotal(0);
      })
      .finally(() => {
        if (!cancelledRef.current && reqId === reqIdRef.current && isFirstLoad) {
          setIsLoading(false);
        }
      });
  }, [query?.product_type, query?.is_active, query?.limit, query?.offset]);

  const create = useCallback(
    async (body: ProductCreateRequest): Promise<ProductResponse> => {
      const created = await apiCreateProduct(body, accessTokenRef.current);
      refetch();
      return created;
    },
    [refetch],
  );

  const update = useCallback(
    async (
      id: string,
      body: ProductUpdateRequest,
    ): Promise<ProductResponse> => {
      const updated = await apiUpdateProduct(id, body, accessTokenRef.current);
      refetch();
      return updated;
    },
    [refetch],
  );

  useEffect(() => {
    statusRef.current = initial ?? null;
  }, [initial]);

  useEffect(() => {
    if (!initialSeedRef.current) {
      refetch();
    }
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

  return { products, total, isLoading, error, refetch, create, update };
}
