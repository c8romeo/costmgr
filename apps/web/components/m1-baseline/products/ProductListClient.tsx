/**
 * apps/web/components/m1-baseline/products/ProductListClient.tsx
 *
 * Story 2.1 — Task 5.2. Product list client (table + filters + form dialog).
 *
 * Composition:
 *   - useProducts hook for list + mutations
 *   - ProductTypeBadge for type column
 *   - ProductFormDialog for create/edit
 *   - Inline filter chips + active toggle
 *
 * Industry-conditional rendering (AC #6): if the tenant is `service`
 * industry, hide the filter chips for `material` + `semi_product` (those
 * rows cannot exist for a service tenant — the backend rejects the POST
 * with 403 INDUSTRY_NOT_SUPPORTED, so the UI surfaces only what the
 * backend will accept).
 *
 * F-1: accessToken forwarded as a string prop from the RSC.
 */

"use client";

import { useState } from "react";

import {
  type ProductCreateRequest,
  type ProductListResponse,
  type ProductResponse,
  type ProductUpdateRequest,
} from "@/lib/api-client";
import type { Industry } from "@/lib/menu-config";
import {
  INDUSTRY_ALLOWED_PRODUCT_TYPES,
  PRODUCT_TYPE_LABEL_KO,
  PRODUCT_TYPE_VALUES,
} from "@/lib/menu-config";
import { useProducts } from "@/hooks/useProducts";
// M2: AD-8 money formatters — locale-aware display so the table renders
// `1,000,000원` / `$1,000.00` instead of raw `1000000` / `1000.00` strings.
import { formatKRW, formatUSD, toKRW, toUSD } from "@/lib/money";

import { ProductFormDialog } from "./ProductFormDialog";
import { ProductTypeBadge } from "./ProductTypeBadge";

export interface ProductListClientProps {
  /** Access token (string) forwarded from the RSC. F-1: not a function. */
  accessToken?: string;
  /** Tenant industry (read from cookie / context / server-side settings
   *  fetch). When omitted, the UI shows all 5 types in the filter chips
   *  but the backend still rejects disallowed types with 403
   *  INDUSTRY_NOT_SUPPORTED. */
  industry?: Industry | null;
  initialProducts?: ProductListResponse | null;
}

const TYPE_FILTER_ALL: "all" = "all";

export function ProductListClient({
  accessToken: _accessToken,
  industry,
  initialProducts,
}: ProductListClientProps) {
  const allowedTypes: readonly (typeof PRODUCT_TYPE_VALUES)[number][] = industry
    ? INDUSTRY_ALLOWED_PRODUCT_TYPES[industry]
    : (PRODUCT_TYPE_VALUES as readonly (typeof PRODUCT_TYPE_VALUES)[number][]);

  const [typeFilter, setTypeFilter] = useState<
    (typeof PRODUCT_TYPE_VALUES)[number] | typeof TYPE_FILTER_ALL
  >(TYPE_FILTER_ALL);
  const [includeInactive, setIncludeInactive] = useState<boolean>(false);
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [editing, setEditing] = useState<ProductResponse | null>(null);
  const [filterError, setFilterError] = useState<string | null>(null);

  const query = {
    ...(typeFilter !== TYPE_FILTER_ALL ? { product_type: typeFilter } : {}),
    is_active: includeInactive ? undefined : true,
    limit: 200,
  };
  const { products, total, isLoading, error, create, update } = useProducts(
    _accessToken,
    initialProducts,
    query,
  );

  // H7: soft-delete / reactivate per-row action. The backend routes a
  // PATCH body of `{is_active: bool}` (and only that key) to the
  // `soft_delete_product` audit path so the event is recorded as
  // `product_soft_deleted` / `product_reactivated` rather than a
  // generic `product_updated`.
  async function handleToggleActive(p: ProductResponse): Promise<void> {
    setFilterError(null);
    try {
      await update(p.id, { is_active: !p.is_active });
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setFilterError(`${p.name} 상태 변경 실패: ${msg}`);
    }
  }

  function openCreate() {
    setEditing(null);
    setDialogOpen(true);
  }

  function openEdit(p: ProductResponse) {
    setEditing(p);
    setDialogOpen(true);
  }

  function closeDialog() {
    setDialogOpen(false);
    setEditing(null);
  }

  async function handleSubmit(
    body: ProductCreateRequest | ProductUpdateRequest,
  ): Promise<ProductResponse> {
    if (editing) {
      // Update path.
      const result = await update(editing.id, body as ProductUpdateRequest);
      setFilterError(null);
      return result;
    }
    const created = await create(body as ProductCreateRequest);
    setFilterError(null);
    return created;
  }

  return (
    <div>
      {/* ── Toolbar ───────────────────────────────────────────── */}
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: "0.5rem",
          alignItems: "center",
          marginBottom: "1rem",
        }}
      >
        <button
          type="button"
          onClick={openCreate}
          style={{
            padding: "0.5rem 1rem",
            borderRadius: 6,
            border: "none",
            background: "#2563eb",
            color: "white",
            fontWeight: 600,
            fontSize: "0.875rem",
            cursor: "pointer",
          }}
        >
          + 추가
        </button>

        {/* type filter chips */}
        <div
          role="group"
          aria-label="유형 필터"
          style={{ display: "flex", gap: "0.375rem", flexWrap: "wrap" }}
        >
          <Chip
            active={typeFilter === TYPE_FILTER_ALL}
            onClick={() => setTypeFilter(TYPE_FILTER_ALL)}
            label="전체"
          />
          {PRODUCT_TYPE_VALUES.map((t) => {
            const isAllowed = allowedTypes.includes(t);
            return (
              <Chip
                key={t}
                active={typeFilter === t}
                onClick={() => isAllowed && setTypeFilter(t)}
                label={PRODUCT_TYPE_LABEL_KO[t]}
                disabled={!isAllowed}
                tooltip={
                  isAllowed
                    ? undefined
                    : `${PRODUCT_TYPE_LABEL_KO[t]} — 현재 업종(${industry ?? "(미선지)"})에서는 등록 불가`
                }
              />
            );
          })}
        </div>

        <label
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
            fontSize: "0.8125rem",
            color: "#475569",
            marginLeft: "auto",
          }}
        >
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
          />
          비활성 포함
        </label>
      </div>

      {/* ── List status ──────────────────────────────────────── */}
      {isLoading && <StatusMessage>불러오는 중…</StatusMessage>}
      {error && (
        <StatusMessage role="alert">
          목록을 불러올 수 없습니다: {error}
        </StatusMessage>
      )}
      {filterError && (
        <StatusMessage role="alert">{filterError}</StatusMessage>
      )}
      {!isLoading && !error && products.length === 0 && (
        <StatusMessage>
          {typeFilter === TYPE_FILTER_ALL
            ? "등록된 품목이 없습니다. 우측 상단 「+ 추가」 버튼으로 시작하세요."
            : `${PRODUCT_TYPE_LABEL_KO[typeFilter]} 유형의 품목이 없습니다.`}
        </StatusMessage>
      )}

      {/* ── Table ─────────────────────────────────────────────── */}
      {!isLoading && !error && products.length > 0 && (
        <div
          style={{
            overflowX: "auto",
            border: "1px solid #e5e7eb",
            borderRadius: 8,
          }}
        >
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "0.875rem",
            }}
          >
            <thead>
              <tr style={{ background: "#f8fafc", textAlign: "left" }}>
                <Th>유형</Th>
                <Th>코드</Th>
                <Th>이름</Th>
                <Th>단위</Th>
                <Th align="right">단가 (KRW)</Th>
                <Th align="right">단가 (USD)</Th>
                <Th>상태</Th>
                <Th align="right">액션</Th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => (
                <tr
                  key={p.id}
                  style={{ borderTop: "1px solid #f1f5f9" }}
                >
                  <Td>
                    <ProductTypeBadge
                      productType={p.product_type}
                      isActive={p.is_active}
                    />
                  </Td>
                  <Td>
                    <code
                      style={{
                        fontFamily: "ui-monospace, monospace",
                        fontSize: "0.8125rem",
                        color: "#0f172a",
                      }}
                    >
                      {p.code}
                    </code>
                  </Td>
                  <Td>{p.name}</Td>
                  <Td>{p.unit ?? "—"}</Td>
                  <Td align="right">
                    {p.unit_cost_krw != null
                      ? formatKRW(toKRW(p.unit_cost_krw))
                      : "—"}
                  </Td>
                  <Td align="right">
                    {p.unit_cost_usd != null
                      ? formatUSD(toUSD(p.unit_cost_usd))
                      : "—"}
                  </Td>
                  <Td>
                    {p.is_active ? (
                      <span style={{ color: "#15803d", fontWeight: 600 }}>활성</span>
                    ) : (
                      // M3: bumped from `#9ca3af` (3.0:1, fails AA) to
                      // `#4b5563` (gray-600, 8.6:1, passes AA Large + AA
                      // Normal) so the inactive state remains legible
                      // to users with low vision.
                      <span
                        style={{ color: "#4b5563", fontWeight: 500 }}
                        aria-label="비활성 품목 — 목록에서 기본 제외됨"
                      >
                        비활성
                      </span>
                    )}
                  </Td>
                  <Td align="right">
                    <div style={{ display: "inline-flex", gap: "0.375rem" }}>
                      <button
                        type="button"
                        onClick={() => openEdit(p)}
                        style={{
                          padding: "0.25rem 0.625rem",
                          borderRadius: 4,
                          border: "1px solid #d1d5db",
                          background: "white",
                          color: "#0f172a",
                          fontSize: "0.8125rem",
                          cursor: "pointer",
                        }}
                      >
                        수정
                      </button>
                      {/* H7: per-row soft-delete / reactivate toggle. */}
                      <button
                        type="button"
                        onClick={() => handleToggleActive(p)}
                        aria-label={
                          p.is_active
                            ? `${p.name} 비활성화`
                            : `${p.name} 재활성화`
                        }
                        style={{
                          padding: "0.25rem 0.625rem",
                          borderRadius: 4,
                          border: `1px solid ${p.is_active ? "#fecaca" : "#bbf7d0"}`,
                          background: "white",
                          color: p.is_active ? "#b91c1c" : "#15803d",
                          fontSize: "0.8125rem",
                          cursor: "pointer",
                        }}
                      >
                        {p.is_active ? "비활성화" : "재활성화"}
                      </button>
                    </div>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
          <p
            style={{
              padding: "0.5rem 0.75rem",
              fontSize: "0.75rem",
              color: "#64748b",
              borderTop: "1px solid #f1f5f9",
            }}
          >
            총 {total}건 (최대 {query.limit}건 표시)
          </p>
        </div>
      )}

      {dialogOpen && (
        <ProductFormDialog
          mode={editing ? "edit" : "create"}
          product={editing}
          industry={industry ?? null}
          onSubmit={handleSubmit}
          onClose={closeDialog}
        />
      )}
    </div>
  );
}

// ── Internal helpers ─────────────────────────────────────────

function Th({
  children,
  align,
}: {
  children: React.ReactNode;
  align?: "left" | "right" | "center";
}) {
  return (
    <th
      style={{
        padding: "0.625rem 0.75rem",
        fontWeight: 600,
        fontSize: "0.75rem",
        color: "#475569",
        textAlign: align ?? "left",
        textTransform: "uppercase",
        letterSpacing: "0.025em",
      }}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  align,
}: {
  children: React.ReactNode;
  align?: "left" | "right" | "center";
}) {
  return (
    <td
      style={{
        padding: "0.625rem 0.75rem",
        textAlign: align ?? "left",
        color: "#0f172a",
        verticalAlign: "middle",
      }}
    >
      {children}
    </td>
  );
}

function Chip({
  active,
  onClick,
  label,
  disabled,
  tooltip,
}: {
  active: boolean;
  onClick: () => void;
  label: string;
  disabled?: boolean;
  tooltip?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      title={tooltip}
      style={{
        padding: "0.25rem 0.625rem",
        borderRadius: 9999,
        border: active ? "1px solid #2563eb" : "1px solid #d1d5db",
        background: active ? "#eff6ff" : "white",
        color: active ? "#1d4ed8" : disabled ? "#9ca3af" : "#334155",
        fontSize: "0.75rem",
        fontWeight: 600,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
      }}
    >
      {label}
    </button>
  );
}

function StatusMessage({
  children,
  role,
}: {
  children: React.ReactNode;
  role?: "alert" | "status";
}) {
  return (
    <p
      role={role ?? "status"}
      style={{
        padding: "0.75rem 1rem",
        borderRadius: 8,
        background: role === "alert" ? "#fef2f2" : "#f1f5f9",
        color: role === "alert" ? "#991b1b" : "#475569",
        fontSize: "0.875rem",
      }}
    >
      {children}
    </p>
  );
}
