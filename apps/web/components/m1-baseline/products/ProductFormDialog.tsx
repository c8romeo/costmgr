/**
 * apps/web/components/m1-baseline/products/ProductFormDialog.tsx
 *
 * Story 2.1 (Task 5.4) + Story 2.3 (Task 5 — type change in edit mode).
 *
 * UX:
 *   - shadcn Dialog primitive is not yet available (Story 0.5 deferral);
 *     this uses a plain HTML <dialog> + inline overlay for portability.
 *   - Field set: name, product_type (5-card radio grid — hidden types for
 *     service industry), code (auto-generated readonly + 수동 입력 toggle),
 *     unit, unit_cost_krw, unit_cost_usd, description.
 *   - On submit: POST or PATCH to /api/v1/baseline/products.
 *   - 409 PRODUCT_CODE_DUPLICATE       → toast "이미 존재하는 코드입니다"
 *   - 403 INDUSTRY_NOT_SUPPORTED       → toast "서비스 업종에서는 등록할 수 없는 유형입니다"
 *   - 422 INVALID_PRODUCT_CODE         → toast "잘못된 코드 형식입니다 (예: MAT-0042)"
 *   - 403 PRODUCT_IMMUTABLE_FIELD      → toast for `code` (AD-18)
 *   - 409 PRODUCT_TYPE_HAS_REFERENCES  → toast w/ BOM/ledger counts (Story 2.3)
 *   - 404 PRODUCT_NOT_FOUND            → toast w/ reload hint
 *
 * Story 2.3 change: the `product_type` radio grid is now editable in edit
 * mode — PATCH only changes it when the user picks a different type. The
 * backend enforces a ref-count-aware guard: 0 references → allow, otherwise
 * 409 PRODUCT_TYPE_HAS_REFERENCES. The previously disabled UI
 * (`mode === "edit"` short-circuit on the radio) has been removed; the
 * hint below the grid now reads as the conditional-rejection warning.
 *
 * M1 / F-25: ApiError discrimination via `err.name === "ApiError"`. The
 * F-25 discriminator (set in api-client.ts) survives cross-realm edges
 * and SSR/CSR boundaries where `instanceof ApiError` would otherwise
 * fail. The previous `isApiErrorLike` structural check has been
 * replaced.
 *
 * M7b: `mountedRef` guards setState calls after the user dismisses the
 * dialog mid-submit (e.g. clicking the backdrop while the request is
 * in flight). Switching the `editing` prop without remounting resets
 * the form via the `useEffect([product?.id, mode])` block — otherwise
 * stale state from the previous row would carry over.
 *
 * M12b: SSR-safe `useId()` wires `aria-labelledby` to the heading id.
 * Hardcoded `"product-form-title"` collided across multiple dialogs
 * mounted in the same DOM (a11y regression).
 *
 * L4: `accessToken` was a dead prop (forwarded but never read inside
 * this component — the parent passes it through `useProducts`). It has
 * been removed from the interface; the parent no longer forwards it.
 */

"use client";

import { useEffect, useId, useRef, useState } from "react";

import {
  ApiError,
  type ProductCreateRequest,
  type ProductResponse,
  type ProductType,
  type ProductUpdateRequest,
} from "@/lib/api-client";
import type { Industry } from "@/lib/menu-config";
import {
  INDUSTRY_ALLOWED_PRODUCT_TYPES,
  PRODUCT_TYPE_LABEL_KO,
  PRODUCT_TYPE_PREFIX,
  PRODUCT_TYPE_VALUES,
} from "@/lib/menu-config";

const PRODUCT_TYPE_DESCRIPTION_KO: Record<ProductType, string> = {
  product: "최종 제품 — 판매 가능한 완제품",
  semi_product: "반제품 — BOM을 통해 제품으로 조립",
  material: "원자재 — BOM의 투입 요소",
  goods: "상품 — 매매 대상 (제조 X)",
  service: "서비스 — ABC 원가 객체",
};

export interface ProductFormDialogProps {
  mode: "create" | "edit";
  /** When `mode === "edit"`, the row to edit. */
  product?: ProductResponse | null;
  /** Tenant industry — drives the allowed-type subset. */
  industry: Industry | null;
  /** Submit handler. Caller wires success/error toasts + invalidation. */
  onSubmit: (
    body: ProductCreateRequest | ProductUpdateRequest,
  ) => Promise<ProductResponse>;
  onClose: () => void;
}

// M1: cross-realm-safe ApiError check. F-25 sets `name = "ApiError"`
// on the instance so a simple string equality survives SSR/edge
// runtimes where `instanceof ApiError` would silently return false.
function isApiError(err: unknown): err is ApiError {
  return (
    err instanceof Error && (err as Error).name === "ApiError"
  );
}

const CODE_FORMAT_REGEX = /^[A-Z]{3}-[0-9]{4,}$/;

export function ProductFormDialog({
  mode,
  product,
  industry,
  onSubmit,
  onClose,
}: ProductFormDialogProps) {
  // M12b: SSR-safe id for the dialog title (prevents duplicate-id
  // collisions when multiple dialogs are mounted concurrently).
  const titleId = useId();

  const [name, setName] = useState<string>(product?.name ?? "");
  const [productType, setProductType] = useState<ProductType>(
    product?.product_type ?? "product",
  );
  const [code, setCode] = useState<string>(product?.code ?? "");
  const [manualCode, setManualCode] = useState<boolean>(
    mode === "edit" ? true : false,
  );
  const [unit, setUnit] = useState<string>(product?.unit ?? "");
  const [unitCostKrw, setUnitCostKrw] = useState<string>(
    product?.unit_cost_krw ?? "",
  );
  const [unitCostUsd, setUnitCostUsd] = useState<string>(
    product?.unit_cost_usd ?? "",
  );
  const [description, setDescription] = useState<string>(
    product?.description ?? "",
  );
  const [isActive, setIsActive] = useState<boolean>(
    product?.is_active ?? true,
  );
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  // M7b: mounted flag. The submit promise can resolve (or reject) AFTER
  // the user dismisses the dialog by clicking the backdrop; calling
  // setState then triggers React's "state update on unmounted
  // component" warning. The flag short-circuits late handlers.
  const mountedRef = useRef<boolean>(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const allowedTypes: readonly ProductType[] = industry
    ? INDUSTRY_ALLOWED_PRODUCT_TYPES[industry]
    : (PRODUCT_TYPE_VALUES as readonly ProductType[]);

  // L3: depend on `allowedTypes` (not just `industry`) so the effect
  // sees the latest array — and on `productType` so the linter agrees
  // the read is current.
  //
  // When industry is loaded after mount, snap the selection into the
  // allowed subset (covers edit of a row whose type is no longer allowed).
  useEffect(() => {
    if (!allowedTypes.includes(productType)) {
      setProductType(allowedTypes[0] ?? "product");
    }
  }, [industry, allowedTypes, productType]);

  // M7b: reset form fields when `product` changes (switching between
  // rows in edit mode without remounting the dialog). Without this,
  // state carries over from the previously edited row.
  useEffect(() => {
    if (mode !== "edit") return;
    setName(product?.name ?? "");
    setProductType(product?.product_type ?? "product");
    setCode(product?.code ?? "");
    setUnit(product?.unit ?? "");
    setUnitCostKrw(product?.unit_cost_krw ?? "");
    setUnitCostUsd(product?.unit_cost_usd ?? "");
    setDescription(product?.description ?? "");
    setIsActive(product?.is_active ?? true);
    setError(null);
  }, [mode, product?.id]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    // Build the body shape per AD-15 snake_case JSON keys.
    const buildBody = ():
      | { kind: "create"; body: ProductCreateRequest }
      | { kind: "update"; body: ProductUpdateRequest } => {
      if (mode === "create") {
        const body: ProductCreateRequest = {
          product_type: productType,
          name: name.trim(),
          ...(manualCode && code.trim()
            ? { code: code.trim().toUpperCase() }
            : {}),
          ...(unit.trim() ? { unit: unit.trim() } : {}),
          ...(unitCostKrw.trim()
            ? { unit_cost_krw: unitCostKrw.trim() }
            : {}),
          // M7b: strip to 2-decimal precision before submit. The backend
          // NUMERIC(18,2) would reject anything finer anyway; stripping
          // here gives an early validation hint and a deterministic
          // diff for PATCH equality checks.
          ...(unitCostUsd.trim()
            ? { unit_cost_usd: unitCostUsd.trim() }
            : {}),
          ...(description.trim() ? { description: description.trim() } : {}),
        };
        return { kind: "create", body };
      }
      // mode === "edit" — PATCH only fields that were edited.
      const body: ProductUpdateRequest = {};
      if (name.trim() !== (product?.name ?? "")) body.name = name.trim();
      // Story 2.3 — include `product_type` only when the user picked a
      // different type. The backend enforces the ref-count guard: 0 refs
      // → 200 PATCH; otherwise 409 PRODUCT_TYPE_HAS_REFERENCES with
      // `{bom_count, ledger_count, total_count}` in `details`.
      if (
        mode === "edit" &&
        product &&
        productType !== product.product_type
      ) {
        body.product_type = productType;
      }
      if (unit.trim() !== (product?.unit ?? "")) {
        body.unit = unit.trim() ? unit.trim() : null;
      }
      if (unitCostKrw.trim() !== (product?.unit_cost_krw ?? "")) {
        body.unit_cost_krw = unitCostKrw.trim() ? unitCostKrw.trim() : null;
      }
      if (unitCostUsd.trim() !== (product?.unit_cost_usd ?? "")) {
        body.unit_cost_usd = unitCostUsd.trim() ? unitCostUsd.trim() : null;
      }
      if (description.trim() !== (product?.description ?? "")) {
        body.description = description.trim() ? description.trim() : null;
      }
      if (isActive !== (product?.is_active ?? true)) {
        body.is_active = isActive;
      }
      return { kind: "update", body };
    };

    const built = buildBody();
    onSubmit(built.body)
      .then(() => {
        if (!mountedRef.current) return;
        onClose();
      })
      .catch((err: unknown) => {
        if (!mountedRef.current) return;
        if (isApiError(err)) {
          const code = err.payload.code;
          if (code === "PRODUCT_CODE_DUPLICATE") {
            setError("이미 존재하는 코드입니다");
          } else if (code === "INDUSTRY_NOT_SUPPORTED") {
            setError("서비스 업종에서는 등록할 수 없는 유형입니다");
          } else if (code === "INVALID_PRODUCT_CODE") {
            setError("잘못된 코드 형식입니다 (예: MAT-0042)");
          } else if (code === "PRODUCT_IMMUTABLE_FIELD") {
            setError("코드는 생성 후 변경할 수 없습니다");
          } else if (code === "PRODUCT_TYPE_HAS_REFERENCES") {
            // Story 2.3 — type change blocked by BOM/ledger refs.
            // P6 (post-review): build the message from the structured
            // `details` payload so a server-side `message_ko` bug doesn't
            // surface as empty UI text. Fall back to `message_ko` if
            // `details` is missing.
            const details = err.payload.details;
            if (
              details &&
              typeof details.bom_count === "number" &&
              typeof details.ledger_count === "number"
            ) {
              const bomPart = `BOM ${details.bom_count}건에서 참조 중`;
              const ledgerPart =
                details.ledger_count > 0
                  ? ` · 수불 ${details.ledger_count}건`
                  : "";
              setError(
                `${bomPart}${ledgerPart} — 신규 품목 생성 후 참조 이관 후 삭제 (품목 유형은 참조 0건일 때만 변경 가능)`,
              );
            } else if (err.payload.message_ko) {
              setError(err.payload.message_ko);
            } else {
              setError(
                "참조 중인 품목이 있어 유형을 변경할 수 없습니다. 신규 품목 생성 후 참조를 이관해 주세요",
              );
            }
          } else if (code === "PRODUCT_NOT_FOUND") {
            setError("품목을 찾을 수 없습니다. 페이지를 새로고침해 주세요");
          } else {
            setError(err.payload.message_ko);
          }
        } else {
          setError("저장에 실패했습니다. 잠시 후 다시 시도해 주세요");
        }
      })
      .finally(() => {
        if (mountedRef.current) setIsSubmitting(false);
      });
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(15, 23, 42, 0.45)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 50,
        padding: "1rem",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <form
        onSubmit={handleSubmit}
        style={{
          background: "white",
          borderRadius: 12,
          padding: "1.5rem",
          maxWidth: 560,
          width: "100%",
          maxHeight: "90vh",
          overflowY: "auto",
          boxShadow: "0 10px 25px rgba(15, 23, 42, 0.20)",
        }}
      >
        <h2
          id={titleId}
          style={{ fontSize: "1.125rem", fontWeight: 700, marginBottom: "1rem" }}
        >
          {mode === "create" ? "품목 추가" : `품목 수정 · ${product?.code ?? ""}`}
        </h2>

        {/* name */}
        <Field label="이름" required>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={200}
            required
            style={inputStyle}
          />
        </Field>

        {/* product_type — 5-card radio grid (or N-card for industry) */}
        <Field label="유형" required>
          <div
            role="radiogroup"
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "0.5rem",
            }}
          >
            {PRODUCT_TYPE_VALUES.map((t) => {
              const isAllowed = allowedTypes.includes(t);
              const isSelected = productType === t;
              return (
                <button
                  key={t}
                  type="button"
                  role="radio"
                  aria-checked={isSelected}
                  // Story 2.3 — type is editable in edit mode. Industry
                  // capability still gates `isAllowed` (e.g. service can't
                  // pick material). The backend enforces the ref-count
                  // guard at PATCH time (409 PRODUCT_TYPE_HAS_REFERENCES).
                  disabled={!isAllowed}
                  onClick={() => isAllowed && setProductType(t)}
                  title={
                    isAllowed
                      ? PRODUCT_TYPE_DESCRIPTION_KO[t]
                      : `${PRODUCT_TYPE_LABEL_KO[t]} — 현재 업종(${industry ?? "(미선택)"})에서는 등록 불가`
                  }
                  style={{
                    textAlign: "left",
                    padding: "0.625rem 0.75rem",
                    borderRadius: 8,
                    border: isSelected
                      ? "2px solid #2563eb"
                      : "1px solid #e5e7eb",
                    background: isSelected ? "#eff6ff" : "white",
                    color: isAllowed ? "#0f172a" : "#9ca3af",
                    cursor: isAllowed ? "pointer" : "not-allowed",
                    opacity: isAllowed ? 1 : 0.5,
                    fontSize: "0.875rem",
                    fontWeight: isSelected ? 600 : 500,
                  }}
                >
                  <div>
                    {PRODUCT_TYPE_LABEL_KO[t]}{" "}
                    <span style={{ color: "#64748b", fontSize: "0.75rem" }}>
                      ({PRODUCT_TYPE_PREFIX[t]}-)
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
          {mode === "edit" && (
            <p
              style={{
                marginTop: "0.5rem",
                color: "#64748b",
                fontSize: "0.75rem",
              }}
            >
              유형 변경 시 참조 중인 BOM 행렬이 있으면 변경이 거부됩니다
              (409 PRODUCT_TYPE_HAS_REFERENCES · 참조 0건일 때만 허용)
            </p>
          )}
        </Field>

        {/* code */}
        <Field label="코드">
          {mode === "create" && !manualCode ? (
            <div
              style={{
                ...inputStyle,
                background: "#f8fafc",
                color: "#64748b",
                cursor: "not-allowed",
              }}
            >
              {PRODUCT_TYPE_PREFIX[productType]}-XXXX (저장 시 자동 생성)
            </div>
          ) : (
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value)}
              maxLength={20}
              readOnly={mode === "edit"}
              pattern={CODE_FORMAT_REGEX.source}
              title="예: MAT-0042"
              placeholder="예: MAT-0042"
              style={{
                ...inputStyle,
                background: mode === "edit" ? "#f1f5f9" : "white",
                color: mode === "edit" ? "#64748b" : "#0f172a",
                cursor: mode === "edit" ? "not-allowed" : "text",
              }}
            />
          )}
          {mode === "create" && (
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.375rem",
                marginTop: "0.375rem",
                fontSize: "0.75rem",
                color: "#475569",
              }}
            >
              <input
                type="checkbox"
                checked={manualCode}
                onChange={(e) => setManualCode(e.target.checked)}
              />
              수동 입력
            </label>
          )}
        </Field>

        {/* unit */}
        <Field label="단위 (예: EA, KG, BOX)">
          <input
            type="text"
            value={unit}
            onChange={(e) => setUnit(e.target.value)}
            maxLength={20}
            placeholder="EA"
            style={inputStyle}
          />
        </Field>

        {/* unit_cost_krw */}
        <Field label="단가 (KRW · 원 단위 정수)">
          <input
            type="text"
            value={unitCostKrw}
            onChange={(e) => setUnitCostKrw(e.target.value.replace(/[^\d]/g, ""))}
            inputMode="numeric"
            placeholder="0"
            style={inputStyle}
          />
        </Field>

        {/* unit_cost_usd */}
        <Field label="단가 (USD · 소수점 2자리)">
          <input
            type="text"
            value={unitCostUsd}
            // M7b: allow digits + a single decimal point. Two or more
            // dots (e.g. "1.2.3") get reduced to "1.23" — the backend
            // NUMERIC(18,2) would reject anyway, and stripping here
            // gives early feedback.
            onChange={(e) => {
              const cleaned = e.target.value
                .replace(/[^\d.]/g, "")
                .replace(/(\..*)\./g, "$1");
              setUnitCostUsd(cleaned);
            }}
            placeholder="0.00"
            style={inputStyle}
          />
        </Field>

        {/* description */}
        <Field label="설명 (최대 2000자)">
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={2000}
            rows={3}
            style={{ ...inputStyle, resize: "vertical", minHeight: 60 }}
          />
        </Field>

        {/* is_active — edit-only (create defaults to true) */}
        {mode === "edit" && (
          <Field label="활성 상태">
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                fontSize: "0.875rem",
              }}
            >
              <input
                type="checkbox"
                checked={isActive}
                onChange={(e) => setIsActive(e.target.checked)}
              />
              {isActive ? "활성" : "비활성 (목록에서 제외됨)"}
            </label>
          </Field>
        )}

        {error && (
          <p
            role="alert"
            style={{
              marginTop: "0.5rem",
              padding: "0.5rem 0.75rem",
              borderRadius: 6,
              background: "#fef2f2",
              color: "#991b1b",
              fontSize: "0.8125rem",
            }}
          >
            {error}
          </p>
        )}

        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "0.5rem",
            marginTop: "1.25rem",
          }}
        >
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 6,
              border: "1px solid #d1d5db",
              background: "white",
              color: "#0f172a",
              cursor: isSubmitting ? "not-allowed" : "pointer",
              fontSize: "0.875rem",
            }}
          >
            취소
          </button>
          <button
            type="submit"
            disabled={isSubmitting || !name.trim()}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 6,
              border: "none",
              background: "#2563eb",
              color: "white",
              cursor:
                isSubmitting || !name.trim() ? "not-allowed" : "pointer",
              opacity: isSubmitting || !name.trim() ? 0.6 : 1,
              fontSize: "0.875rem",
              fontWeight: 600,
            }}
          >
            {isSubmitting
              ? "저장 중…"
              : mode === "create"
                ? "추가"
                : "저장"}
          </button>
        </div>
      </form>
    </div>
  );
}

// ── Internal helpers ─────────────────────────────────────────
const inputStyle: React.CSSProperties = {
  display: "block",
  width: "100%",
  padding: "0.5rem 0.625rem",
  borderRadius: 6,
  border: "1px solid #d1d5db",
  fontSize: "0.875rem",
  color: "#0f172a",
  background: "white",
  outline: "none",
};

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div style={{ marginBottom: "0.875rem" }}>
      <label
        style={{
          display: "block",
          fontSize: "0.8125rem",
          fontWeight: 600,
          color: "#334155",
          marginBottom: "0.25rem",
        }}
      >
        {label}
        {required && (
          <span style={{ color: "#dc2626", marginLeft: "0.125rem" }}>*</span>
        )}
      </label>
      {children}
    </div>
  );
}
