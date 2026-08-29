/**
 * apps/web/components/m2-input/ClosingGuardBanner.tsx — Story 5.3 T9 + P19
 *
 * Korean red banner for the [기초재고] / [수불부] tab in the m2-input
 * closing-guard flow. P19 patch (review): split from m4-inventory so the
 * [기초재고] / m2 tab can compose the banner without pulling the full
 * m4-inventory subtree.
 *
 * Composition:
 * - Alert (shadcn destructive) + AlertTitle + AlertDescription + AlertTriangle
 * - Top-N offenders slice (top 5) sorted by severity ASC (qty ASC)
 * - Manual edit gate via <fieldset disabled>
 *
 * AD-15 §11 parity: Korean SSOT constant + Python `format_negative_closing_banner_ko`
 * via `formatNegativeClosingBannerKo` (apps/web/lib/l2-input-inventory-ledger.ts).
 */

"use client";

import { Decimal } from "decimal.js";
import { AlertTriangle } from "lucide-react";
import * as React from "react";

import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import {
  NEGATIVE_CLOSING_INVENTORY_KO,
  formatNegativeClosingBannerKo,
  type ClosingInvariant,
} from "@/lib/l2-input-inventory-ledger";
import { cn } from "@/lib/utils";

export interface M2ClosingGuardBannerProps {
  /** Closing invariant from `classifyClosingInvariant`. */
  invariant: ClosingInvariant;
  /** Optional product id → human-readable name lookup. */
  productNameLookup?: Record<string, string>;
  /** Optional className override (defense-in-depth). */
  className?: string;
}

/**
 * M2ClosingGuardBanner — Renders the Korean red banner when invariant is violated.
 *
 * Hidden (returns null) when invariant.code != NEGATIVE_CLOSING. Top-N
 * offenders slice (top 5) sorted by severity ASC (qty ASC) for the
 * detail list. Severity sort uses Decimal.js to avoid precision loss
 * + NaN risk on `Number()` coercion (P28).
 */
export function M2ClosingGuardBanner({
  invariant,
  productNameLookup,
  className,
}: M2ClosingGuardBannerProps): React.ReactElement | null {
  if (invariant.code !== "NEGATIVE_CLOSING") {
    return null;
  }

  // P21: Top-N offenders slice (top 5) sorted by severity ASC (qty ASC).
  const topOffenders = Object.entries(invariant.negative_products)
    // eslint-disable-next-line camelcase
    .map(([product_id, qty]) => ({ product_id, qty }))
    .sort((a, b) => new Decimal(a.qty).minus(new Decimal(b.qty)).toNumber())
    .slice(0, 5);

  const bannerKo = formatNegativeClosingBannerKo(
    invariant,
    productNameLookup ?? {},
  );

  return (
    <Alert
      variant="destructive"
      role="alert"
      aria-live="assertive"
      className={cn(className)}
      data-testid="m2-closing-guard-banner"
    >
      <AlertTriangle className="h-4 w-4" aria-hidden="true" />
      <AlertTitle>{NEGATIVE_CLOSING_INVENTORY_KO}</AlertTitle>
      {bannerKo && bannerKo !== NEGATIVE_CLOSING_INVENTORY_KO && (
        <AlertDescription>{bannerKo}</AlertDescription>
      )}
      {topOffenders.length > 0 && (
        <AlertDescription>
          <ul className="mt-2 list-disc pl-5 text-xs">
            {topOffenders.map((p) => {
              const name =
                productNameLookup?.[p.product_id] ?? p.product_id.slice(0, 8);
              return (
                <li key={p.product_id}>
                  {name}: {p.qty}개
                </li>
              );
            })}
          </ul>
        </AlertDescription>
      )}
    </Alert>
  );
}

export interface M2ClosingGuardGateProps {
  /** Whether the gate is currently blocked. */
  is_blocked: boolean;
  /** Children to gate. Renders as-is when allowed, wrapped in disabled state when blocked. */
  children: React.ReactNode;
  /** Optional fallback when blocked (overrides default '수정 차단' UI). */
  fallback?: React.ReactNode;
}

/**
 * M2ClosingGuardGate — Wraps children to disable manual edit while invariant violated.
 *
 * P22 (patch): Migrate `pointer-events-none` + `aria-disabled` to
 * `<fieldset disabled={is_blocked}>`. This ensures keyboard Tab + Enter +
 * programmatic submit all bypass correctly (the HTML disabled attribute
 * blocks form submission, while pointer-events-none only blocks mouse).
 */
export function M2ClosingGuardGate({
  // eslint-disable-next-line camelcase
  is_blocked,
  children,
  fallback,
}: M2ClosingGuardGateProps): React.ReactElement {
  // eslint-disable-next-line camelcase
  if (!is_blocked) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  return (
    <fieldset
      disabled
      data-testid="m2-closing-guard-gate"
      className={cn("cursor-not-allowed", "border-0 p-0 m-0 min-w-0")}
      title={NEGATIVE_CLOSING_INVENTORY_KO}
    >
      {children}
    </fieldset>
  );
}