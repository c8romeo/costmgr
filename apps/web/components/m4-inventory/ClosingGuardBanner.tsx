/**
 * apps/web/components/m4-inventory/ClosingGuardBanner.tsx — Story 5.3 T9
 *
 * Korean red banner for the [수불부] tab + manual edit reject gate.
 *
 * PRD §F4.2 + §V3 + §A11:
 * - Closing inventory MUST be ≥ 0 for all inventory-tracked products
 * - Banner shown when invariant.code = NEGATIVE_CLOSING
 * - Manual edit on closing inventory blocked while banner is shown
 *
 * Props:
 * - code: 'CLOSING_OK' | 'NEGATIVE_CLOSING' | 'EMPTY_PERIOD' from backend
 * - banner_ko: Korean message from backend (AD-15 §11 SSOT)
 * - negativeProducts: list of {product_id, closing_qty} violating products
 *
 * UX (locked in UX v1.0):
 * - Red `bg-red-50 border-red-300` banner with NEGATIVE_CLOSING message
 * - Hidden when CLOSING_OK or EMPTY_PERIOD
 * - Manual edit gate: passes `disabled` state to children via slot pattern
 */

"use client";

import * as React from "react";

import { NEGATIVE_CLOSING_INVENTORY_KO } from "@/lib/closing-guard";
import { cn } from "@/lib/utils";

export interface ClosingGuardBannerProps {
  /** Invariant code from backend (CLOSING_OK | NEGATIVE_CLOSING | EMPTY_PERIOD). */
  code: string;
  /** Korean banner message from backend (mirrors `format_negative_closing_banner_ko`). */
  bannerKo: string;
  /** Optional negative product list (displayed in banner detail). */
  negativeProducts?: Array<{ product_id: string; closing_qty: string }>;
  /** Optional className override (defense-in-depth). */
  className?: string;
}

/**
 * ClosingGuardBanner — Renders the Korean red banner when invariant is violated.
 *
 * Hidden (returns null) when invariant is not violated (CLOSING_OK or
 * EMPTY_PERIOD). The visibility logic is AD-15 §11 parity — TS projection
 * mirrors `shouldShowClosingGuardBanner` Python kernel.
 */
export function ClosingGuardBanner({
  code,
  bannerKo,
  negativeProducts,
  className,
}: ClosingGuardBannerProps): React.ReactElement | null {
  if (code !== "NEGATIVE_CLOSING") {
    return null;
  }

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={cn(
        "rounded-md border border-red-300 bg-red-50 p-4 text-sm text-red-900",
        className,
      )}
      data-testid="closing-guard-banner"
    >
      <div className="font-semibold">{NEGATIVE_CLOSING_INVENTORY_KO}</div>
      {bannerKo && bannerKo !== NEGATIVE_CLOSING_INVENTORY_KO && (
        <div className="mt-1 text-red-800">{bannerKo}</div>
      )}
      {negativeProducts && negativeProducts.length > 0 && (
        <ul className="mt-2 list-disc pl-5 text-xs text-red-700">
          {negativeProducts.map((p) => (
            <li key={p.product_id}>
              {p.product_id.slice(0, 8)}: {p.closing_qty}개
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export interface ClosingGuardGateProps {
  /** Invariant code from backend. Manual edit disabled when NEGATIVE_CLOSING. */
  code: string;
  /** Children to gate. Renders as-is when allowed, wrapped in disabled state when blocked. */
  children: React.ReactNode;
  /** Optional fallback when blocked (overrides default '수정 차단' UI). */
  fallback?: React.ReactNode;
}

/**
 * ClosingGuardGate — Wraps children to disable manual edit while invariant violated.
 *
 * Manual edit is blocked when invariant.code = NEGATIVE_CLOSING.
 * The gate renders children inside a `pointer-events-none` wrapper with
 * `aria-disabled` so screen readers announce the disabled state.
 *
 * Use for: save buttons, form inputs, BOM editor, product create/edit
 * dialogs in the [수불부] tab when banner is visible.
 */
export function ClosingGuardGate({
  code,
  children,
  fallback,
}: ClosingGuardGateProps): React.ReactElement {
  const blocked = code === "NEGATIVE_CLOSING";

  if (!blocked) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  return (
    <div
      aria-disabled="true"
      data-testid="closing-guard-gate"
      className="pointer-events-none cursor-not-allowed opacity-50"
      title={NEGATIVE_CLOSING_INVENTORY_KO}
    >
      {children}
    </div>
  );
}