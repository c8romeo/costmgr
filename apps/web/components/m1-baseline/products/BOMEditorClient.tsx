/**
 * apps/web/components/m1-baseline/products/BOMEditorClient.tsx — BOM matrix editor.
 *
 * Story 2.2 — Task 5.2.
 *
 * Client Component for the BOM matrix UI. Renders:
 *   - Header: parent product metadata (code, name, is_active badge)
 *   - Progress bar (목표 100%) + 합계 + 부족 %
 *   - BOM matrix table (자식코드 / 자식이름 / 비중(%) / 비고 / 액션)
 *   - "추가" button → opens BOMRowAddDialog
 *   - "저장" button → bulk-replace PUT
 *   - Inactive children show "(비활성)" overlay (AC #9)
 *   - Disabled state when is_complete=false: prominent "비중 합 X% 부족"
 *
 * CR 2.1 lesson: this component is PURELY a bulk-replace UI. There is
 * NO per-row add/remove button that talks to the API — local state is
 * the only mutable layer until "저장" fires the PUT. Per-row mutations
 * would let the BOM dip below 100% temporarily (between two PATCH calls).
 *
 * Story 0.5 plumbing gaps (shadcn/ui, sonner): the original spec
 * requested a shadcn Dialog + sonner toast for errors. Per the 2.1
 * close-out these are deferred to Story 0.5. We use plain HTML <dialog>
 * + an inline error banner as the Story 0.5-pragmatic equivalents.
 */

"use client";

import Decimal from "decimal.js";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";

import { ProductTypeBadge } from "@/components/m1-baseline/products/ProductTypeBadge";
import { useBom } from "@/hooks/useBom";
import {
  type BOMLineResponse,
  type BOMResponse,
  type BOMRowInput,
  ApiError,
  fetchProducts,
} from "@/lib/api-client";
import {
  TARGET_TOTAL,
  isCompleteBom,
  missingToComplete,
  quantizeRatio,
} from "@/lib/bom-validation";

export interface BOMEditorClientProps {
  productId: string;
  accessToken?: string;
  /**
   * Server-side pre-fetched BOM (Story 2.2 F-20 — race-free hydration).
   * Passed through to `useBom` as the initial state so the first paint
   * shows the matrix without a loading spinner.
   */
  initialBom?: BOMResponse | null;
}

export function BOMEditorClient({ productId, accessToken, initialBom }: BOMEditorClientProps) {
  const { bom, isLoading, error, setBom } = useBom(productId, accessToken, initialBom);

  // Local mutable state for unsaved edits. The PUT fires only on "저장".
  // Initialize from `bom` once on first render.
  const initialLines = useMemo<BOMLineResponse[]>(
    () => bom?.lines ?? [],
    // We deliberately exclude `bom` from deps — local state is the source
    // of truth between PUTs. Reset on `bom` change is explicit via a
    // `useEffect` below.
    [bom],
  );
  const [lines, setLines] = useState<BOMRowInput[]>(() =>
    initialLines.map((l) => ({
      child_product_id: l.child_product_id,
      ratio: l.ratio,
    })),
  );
  const [childMeta, setChildMeta] = useState<
    Record<string, { code: string; name: string; is_active: boolean; product_type: string }>
  >(() => {
    const m: Record<string, { code: string; name: string; is_active: boolean; product_type: string }> =
      {};
    for (const l of initialLines) {
      m[l.child_product_id] = {
        code: l.child_code,
        name: l.child_name,
        is_active: l.child_is_active,
        product_type: l.child_product_type,
      };
    }
    return m;
  });
  const [isSaving, setIsSaving] = useState<boolean>(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isAddDialogOpen, setIsAddDialogOpen] = useState<boolean>(false);

  // Live totals — derived from local state via the TS mirror.
  const totalRatio = useMemo(
    () =>
      lines
        .reduce((acc, l) => acc.plus(new Decimal(l.ratio)), new Decimal(0))
        .toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN),
    [lines],
  );
  const isComplete = useMemo(() => totalRatio.equals(TARGET_TOTAL), [totalRatio]);
  const missing = useMemo(
    () => TARGET_TOTAL.minus(totalRatio).toDecimalPlaces(4, Decimal.ROUND_HALF_EVEN),
    [totalRatio],
  );

  // Story 0.5 T3.4 — close Story 2-2 M11 deferral.
  // Fire a sonner toast when the BOM sum drops below 100% (transient
  // notification; the inline <p> below remains as persistent visual
  // feedback). One-time fire per non-complete render via ref guard.
  const wasCompleteRef = useRef<boolean>(isComplete);
  useEffect(() => {
    if (wasCompleteRef.current && !isComplete && lines.length > 0) {
      toast.warning(`BOM 비중 합 100% 필요 (현재 ${totalRatio.toFixed(2)}%)`);
    }
    wasCompleteRef.current = isComplete;
  }, [isComplete, totalRatio, lines.length]);


  // Add a child row.
  const handleAdd = useCallback(
    (childId: string, ratio: string, meta: { code: string; name: string; is_active: boolean; product_type: string }) => {
      setLines((prev) => [
        ...prev,
        { child_product_id: childId, ratio },
      ]);
      setChildMeta((prev) => ({ ...prev, [childId]: meta }));
    },
    [],
  );

  // Remove a row from local state (no API call).
  const handleRemove = useCallback((childId: string) => {
    setLines((prev) => prev.filter((l) => l.child_product_id !== childId));
    setChildMeta((prev) => {
      // eslint-disable-next-line @typescript-eslint/naming-convention
      const { [childId]: _, ...rest } = prev;
      return rest;
    });
  }, []);

  // Edit a row's ratio.
  const handleRatioChange = useCallback((childId: string, ratio: string) => {
    setLines((prev) =>
      prev.map((l) =>
        l.child_product_id === childId ? { ...l, ratio } : l,
      ),
    );
  }, []);

  // Save = bulk-replace PUT.
  const handleSave = useCallback(async () => {
    setIsSaving(true);
    setSaveError(null);
    try {
      // Quantize each ratio via the TS mirror (defense-in-depth).
      const payload = {
        lines: lines.map((l) => ({
          child_product_id: l.child_product_id,
          ratio: quantizeRatio(new Decimal(l.ratio)).toFixed(4),
        })),
      };
      const updated = await setBom(payload);
      // H1 (Review): re-sync local state from the server response so the
      // matrix shows the canonical (server-quantized) ratios. Without
      // this, user-entered `33.33335` displayed `33.33335%` after save
      // even though the server persisted `33.3334` (ROUND_HALF_EVEN).
      setLines(
        updated.lines.map((l) => ({
          child_product_id: l.child_product_id,
          ratio: l.ratio,
        })),
      );
      setChildMeta((prev) => {
        const m = { ...prev };
        for (const l of updated.lines) {
          m[l.child_product_id] = {
            code: l.child_code,
            name: l.child_name,
            is_active: l.child_is_active,
            product_type: l.child_product_type,
          };
        }
        return m;
      });
    } catch (e: unknown) {
      const msg =
        e instanceof ApiError
          ? `${e.payload.code}: ${e.payload.message_ko}`
          : e instanceof Error
            ? e.message
            : "저장에 실패했습니다";
      setSaveError(msg);
    } finally {
      setIsSaving(false);
    }
  }, [lines, setBom]);

  if (isLoading) {
    return (
      <div className="p-4 text-sm text-gray-500" data-testid="bom-loading">
        BOM 정보를 불러오는 중입니다...
      </div>
    );
  }

  if (error) {
    return (
      <div
        className="p-4 text-sm text-red-700 bg-red-50 border border-red-200 rounded"
        data-testid="bom-error"
      >
        BOM 조회 실패: {error}
      </div>
    );
  }

  if (!bom) {
    return null;
  }

  // Parent type guard — material/goods/service show "BOM 사용 불가".
  // Service-layer enforces this too (422 BOM_INVALID_PARENT_TYPE), but
  // the UI gives a friendlier message.
  if (!["product", "semi_product"].includes(bom.parent_product_type)) {
    return (
      <div
        className="p-4 text-sm text-amber-800 bg-amber-50 border border-amber-200 rounded"
        data-testid="bom-not-supported"
      >
        BOM 사용 불가 — 모품목은 제품 또는 반제품만 가능합니다 (현재:{" "}
        {bom.parent_product_type})
      </div>
    );
  }

  return (
    <div className="space-y-4" data-testid="bom-editor">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">
            BOM — {bom.parent_code} {bom.parent_name}
          </h2>
          <p className="text-xs text-gray-500">
            PRD §6.1 — 자식 품목은 원자재 또는 반제품만 가능합니다.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="px-3 py-1 text-sm bg-white border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50"
            onClick={() => setIsAddDialogOpen(true)}
            disabled={isSaving}
            data-testid="bom-add-button"
          >
            추가
          </button>
          <button
            type="button"
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:bg-gray-400"
            onClick={handleSave}
            disabled={isSaving || lines.length === 0}
            data-testid="bom-save-button"
          >
            {isSaving ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>

      {/* Progress + summary */}
      <div className="space-y-1">
        <div className="flex justify-between text-sm">
          <span>
            비중 합계:{" "}
            <span
              className={isComplete ? "text-green-700 font-medium" : "text-red-700 font-medium"}
              data-testid="bom-total-ratio"
            >
              {totalRatio.toFixed(4)}%
            </span>
          </span>
          <span className="text-gray-500">
            목표: {TARGET_TOTAL.toFixed(4)}%
          </span>
        </div>
        {/* Progress bar — clamped at 100% for visual stability. */}
        <div className="h-2 bg-gray-200 rounded overflow-hidden">
          <div
            className={
              isComplete
                ? "h-full bg-green-500 transition-all"
                : "h-full bg-red-500 transition-all"
            }
            style={{
              width: `${Math.min(totalRatio.toNumber(), 100)}%`,
            }}
            data-testid="bom-progress-bar"
          />
        </div>
        {!isComplete ? (
          <p
            className="text-xs text-red-700"
            data-testid="bom-missing-message"
          >
            비중 합 {missing.toFixed(4)}% 부족 — [계산] 버튼이 잠깁니다.
          </p>
        ) : (
          <p className="text-xs text-green-700" data-testid="bom-complete-message">
            비중 합 100% 완료 — [계산] 버튼이 활성화됩니다.
          </p>
        )}
      </div>

      {/* Error banner */}
      {saveError && (
        <div
          className="p-3 text-sm text-red-700 bg-red-50 border border-red-200 rounded"
          data-testid="bom-save-error"
        >
          {saveError}
        </div>
      )}

      {/* Matrix table */}
      <div className="overflow-x-auto border border-gray-200 rounded">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left font-medium">자식 코드</th>
              <th className="px-3 py-2 text-left font-medium">자식 이름</th>
              <th className="px-3 py-2 text-right font-medium">비중 (%)</th>
              <th className="px-3 py-2 text-left font-medium">비고</th>
              <th className="px-3 py-2 text-right font-medium">액션</th>
            </tr>
          </thead>
          <tbody>
            {lines.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-3 py-4 text-center text-gray-400"
                >
                  BOM이 비어 있습니다. [추가] 버튼으로 자식 품목을 등록하세요.
                </td>
              </tr>
            ) : (
              lines.map((l) => {
                const meta = childMeta[l.child_product_id];
                return (
                  <tr
                    key={l.child_product_id}
                    className={
                      meta && !meta.is_active
                        ? "bg-gray-50 text-gray-500"
                        : ""
                    }
                    data-testid="bom-row"
                  >
                    <td className="px-3 py-2">
                      {meta ? (
                        <span className="inline-flex items-center gap-2">
                          <ProductTypeBadge
                            productType={meta.product_type as never}
                            isActive={meta.is_active}
                          />
                          <span className="font-mono text-xs">{meta.code}</span>
                        </span>
                      ) : (
                        l.child_product_id.slice(0, 8)
                      )}
                    </td>
                    <td className="px-3 py-2">
                      {meta?.name ?? "(이름 없음)"}
                      {meta && !meta.is_active && (
                        <span
                          className="ml-2 text-xs text-gray-400 line-through"
                          data-testid="bom-inactive-overlay"
                        >
                          (비활성)
                        </span>
                      )}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <input
                        type="number"
                        step="0.0001"
                        min="0.0001"
                        max="100"
                        className="w-24 px-2 py-1 text-right border border-gray-300 rounded"
                        value={l.ratio}
                        onChange={(e) =>
                          handleRatioChange(l.child_product_id, e.target.value)
                        }
                        disabled={isSaving}
                        data-testid="bom-ratio-input"
                      />
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500">
                      {meta && !meta.is_active ? "비활성 — 계산 시 제외됨" : ""}
                    </td>
                    <td className="px-3 py-2 text-right">
                      <button
                        type="button"
                        className="text-red-600 hover:text-red-800 text-xs"
                        onClick={() => handleRemove(l.child_product_id)}
                        disabled={isSaving}
                        data-testid="bom-remove-button"
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Add dialog (Story 0.5 stub: plain HTML <dialog>) */}
      {isAddDialogOpen && (
        <BOMRowAddDialogStub
          productId={productId}
          accessToken={accessToken}
          excludeIds={lines.map((l) => l.child_product_id)}
          onAdd={handleAdd}
          onClose={() => setIsAddDialogOpen(false)}
        />
      )}
    </div>
  );
}

// ── Add Dialog (Story 0.5 stub) ────────────────────────────────
//
// Original spec called for shadcn Dialog + Combobox. Story 0.5 plumbing
// gaps defer that — for now we use a plain HTML <dialog> + native
// <select>. The structure mirrors the eventual shadcn shape so the
// Story 0.5 swap is mechanical.
function BOMRowAddDialogStub({
  productId: _productId,
  accessToken,
  excludeIds,
  onAdd,
  onClose,
}: {
  productId: string;
  accessToken?: string;
  excludeIds: string[];
  onAdd: (
    childId: string,
    ratio: string,
    meta: { code: string; name: string; is_active: boolean; product_type: string },
  ) => void;
  onClose: () => void;
}) {
  const [selectedId, setSelectedId] = useState<string>("");
  const [ratio, setRatio] = useState<string>("10.0000");
  // M13 (CR 2.1 lesson): the eligible-children fetch is local — we
  // already have products in scope from the parent page. But the matrix
  // editor is opened standalone, so we fetch on demand. Caching is
  // deferred to Story 0.5.
  const [eligible, setEligible] = useState<
    Array<{ id: string; code: string; name: string; product_type: string; is_active: boolean }>
  >([]);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // M2 (Review): useEffect for the lazy fetch (was `useState(() => {...})`
  // which is for synchronous initial state and produces a confusing lint
  // warning). Fetches BOTH material + semi_product — L17 (Review) found
  // the old version only fetched `product_type=material`, which would
  // hide semi_product children in the dropdown.
  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const [materials, semis] = await Promise.all([
          fetchProducts({ product_type: "material", limit: 200 }, accessToken),
          fetchProducts({ product_type: "semi_product", limit: 200 }, accessToken),
        ]);
        if (cancelled) return;
        const items = [...materials.items, ...semis.items].filter(
          (p) => !excludeIds.includes(p.id),
        );
        setEligible(
          items.map((p) => ({
            id: p.id,
            code: p.code,
            name: p.name,
            product_type: p.product_type,
            is_active: p.is_active,
          })),
        );
      } catch (e: unknown) {
        if (cancelled) return;
        const msg =
          e instanceof ApiError
            ? `${e.payload.code}: ${e.payload.message_ko}`
            : e instanceof Error
              ? e.message
              : "자식 품목 목록을 불러오지 못했습니다";
        setFetchError(msg);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken, excludeIds]);

  // M3 (Review): Decimal-based validation, not `Number()`. The previous
  // `Number(ratio)` would silently accept `"12.345678"` (rounds to
  // 12.345678 in Number, then the PUT fails on the server with 422).
  // Decimal traps NaN / Infinity and surfaces the exact bound check.
  const handleConfirm = () => {
    const child = eligible.find((e) => e.id === selectedId);
    if (!child) return;
    let parsed: Decimal;
    try {
      parsed = new Decimal(ratio);
    } catch {
      setFetchError("비중을 숫자로 입력해 주세요.");
      return;
    }
    if (
      parsed.isNaN() ||
      !parsed.isFinite() ||
      parsed.lessThanOrEqualTo(0) ||
      parsed.greaterThan(100)
    ) {
      setFetchError("비중은 0보다 크고 100 이하이어야 합니다.");
      return;
    }
    onAdd(child.id, parsed.toFixed(4), {
      code: child.code,
      name: child.name,
      is_active: child.is_active,
      product_type: child.product_type,
    });
    onClose();
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      data-testid="bom-add-dialog"
    >
      <div className="bg-white p-6 rounded shadow-lg w-96">
        <h3 className="text-lg font-semibold mb-4">BOM 자식 추가</h3>
        {fetchError && (
          <div
            className="mb-3 p-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded"
            data-testid="bom-add-error"
          >
            {fetchError}
          </div>
        )}
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">자식 품목</label>
            <select
              className="w-full px-2 py-1 border border-gray-300 rounded"
              value={selectedId}
              onChange={(e) => setSelectedId(e.target.value)}
              data-testid="bom-add-child-select"
            >
              <option value="">-- 선택 --</option>
              {eligible.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.code} {e.name} {e.is_active ? "" : "(비활성)"}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">비중 (%)</label>
            <input
              type="number"
              step="0.0001"
              min="0.0001"
              max="100"
              className="w-full px-2 py-1 border border-gray-300 rounded text-right"
              value={ratio}
              onChange={(e) => setRatio(e.target.value)}
              data-testid="bom-add-ratio-input"
            />
          </div>
        </div>
        <div className="flex justify-end gap-2 mt-4">
          <button
            type="button"
            className="px-3 py-1 text-sm border border-gray-300 rounded"
            onClick={onClose}
          >
            취소
          </button>
          <button
            type="button"
            className="px-3 py-1 text-sm bg-blue-600 text-white rounded disabled:opacity-50"
            onClick={handleConfirm}
            disabled={!selectedId}
            data-testid="bom-add-confirm"
          >
            추가
          </button>
        </div>
      </div>
    </div>
  );
}