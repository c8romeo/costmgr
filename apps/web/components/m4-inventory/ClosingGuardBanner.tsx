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
 * - shadcn/ui Alert (variant=destructive) with AlertTriangle icon
 * - Hidden when CLOSING_OK or EMPTY_PERIOD
 * - Manual edit gate: <fieldset disabled> wraps form fields so keyboard
 *   Tab + Enter + programmatic submit all bypass correctly (P22 patch)
 *
 * Patches applied (Story 5.3 bmad-code-review):
 * - P20: Migrate raw `<div bg-red-50...>` to shadcn Alert primitive
 * - P21: Top-N offenders slice (top 5) sorted by severity ASC (qty ASC)
 * - P22: Migrate `pointer-events-none` + `aria-disabled` to `<fieldset disabled>`
 */

"use client";

import { Decimal } from "decimal.js";
import { AlertTriangle } from "lucide-react";
import * as React from "react";

import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
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

  // P21: Top-N offenders slice (top 5) sorted by severity ASC (qty ASC).
  // Use Decimal.js for severity sort (P28 — precision loss + NaN risk on Number).
  // P3-3rd-sweep: sort BEFORE slice — when negativeProducts is unsorted, slicing
  // first would drop the most severe entries (-100, -50). AD-15 §11 parity
  // with m2-input variant (line 59-62 of m2-input/ClosingGuardBanner.tsx).
  const topOffenders = (negativeProducts ?? [])
    .sort((a, b) => new Decimal(a.closing_qty).minus(b.closing_qty).toNumber())
    .slice(0, 5);

  return (
    <Alert
      variant="destructive"
      role="alert"
      aria-live="assertive"
      className={className}
      data-testid="closing-guard-banner"
    >
      <AlertTriangle className="h-4 w-4" aria-hidden="true" />
      <AlertTitle>{NEGATIVE_CLOSING_INVENTORY_KO}</AlertTitle>
      {bannerKo && bannerKo !== NEGATIVE_CLOSING_INVENTORY_KO && (
        <AlertDescription>{bannerKo}</AlertDescription>
      )}
      {topOffenders.length > 0 && (
        <AlertDescription>
          <ul className="mt-2 list-disc pl-5 text-xs">
            {topOffenders.map((p) => (
              <li key={p.product_id}>
                {p.product_id.slice(0, 8)}: {p.closing_qty}개
              </li>
            ))}
          </ul>
        </AlertDescription>
      )}
    </Alert>
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
 *
 * P22 (patch): Migrate `pointer-events-none` + `aria-disabled` to
 * `<fieldset disabled={is_blocked}>`. This ensures keyboard Tab + Enter +
 * programmatic submit all bypass correctly (the HTML disabled attribute
 * blocks form submission, while pointer-events-none only blocks mouse).
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
    <fieldset
      disabled
      data-testid="closing-guard-gate"
      className={cn("cursor-not-allowed", "border-0 p-0 m-0 min-w-0")}
      title={NEGATIVE_CLOSING_INVENTORY_KO}
    >
      {children}
    </fieldset>
  );
}