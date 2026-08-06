/**
 * apps/web/components/m2-input/MonthlyInputTabs.tsx — Story 5.3 T9 + P19
 *
 * shadcn/ui Tabs container for the [기초재고] / [수불부] / [마감] tab
 * navigation. Composes the closing-guard banner + form + gate so the
 * [마감] tab shows the red banner and locks while invariant is violated.
 *
 * Re-uses existing `apps/web/components/ui/tabs.tsx` shadcn primitive.
 */

"use client";

import * as React from "react";

import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from "@/components/ui/tabs";
import {
  isCloseBlocked,
  type ClosingInvariant,
} from "@/lib/l2-input-inventory-ledger";
import { cn } from "@/lib/utils";

import { M2ClosingGuardBanner } from "./ClosingGuardBanner";
import { MonthlyInputRowForm } from "./MonthlyInputRowForm";

export type MonthlyInputTabId = "opening" | "subub" | "close";

export interface MonthlyInputTabsProps {
  /** Period key (e.g. "2026-07"). */
  period_key: string;
  /** Closing invariant — drives banner visibility + gate. */
  invariant: ClosingInvariant;
  /** Optional product id → human-readable name lookup. */
  productNameLookup?: Record<string, string>;
  /** Form submit handler passed to the [마감] tab form. */
  onSubmit?: (period_key: string) => Promise<void> | void;
  /** Initial active tab (defaults to "subub"). */
  defaultTab?: MonthlyInputTabId;
  /** Optional controlled active tab. */
  activeTab?: MonthlyInputTabId;
  /** Optional className override. */
  className?: string;
}

/**
 * MonthlyInputTabs — Tabbed container for [기초재고] / [수불부] / [마감].
 *
 * The [마감] tab wires the closing-guard banner + form + fieldset gate.
 * The banner is visible iff invariant.code = NEGATIVE_CLOSING, and the
 * form is blocked via <fieldset disabled> so keyboard + programmatic
 * submission bypass correctly (P22 patch).
 */
export function MonthlyInputTabs({
  period_key,
  invariant,
  productNameLookup,
  onSubmit,
  defaultTab = "subub",
  activeTab,
  className,
}: MonthlyInputTabsProps): React.ReactElement {
  const is_blocked = isCloseBlocked(invariant);

  return (
    <Tabs
      defaultValue={defaultTab}
      value={activeTab}
      className={cn("w-full", className)}
      data-testid="monthly-input-tabs"
      data-period-key={period_key}
    >
      <TabsList>
        <TabsTrigger value="opening" data-testid="tab-opening">
          기초재고
        </TabsTrigger>
        <TabsTrigger value="subub" data-testid="tab-subub">
          수불부
        </TabsTrigger>
        <TabsTrigger value="close" data-testid="tab-close">
          마감
        </TabsTrigger>
      </TabsList>
      <TabsContent value="opening">
        <div className="text-sm text-muted-foreground">
          {period_key} 기초재고 입력 (Story 5.1 M14)
        </div>
      </TabsContent>
      <TabsContent value="subub">
        <div className="text-sm text-muted-foreground">
          {period_key} 수불부 입력
        </div>
      </TabsContent>
      <TabsContent value="close" data-testid="tab-close-content">
        <div className="flex flex-col gap-3">
          <M2ClosingGuardBanner
            invariant={invariant}
            productNameLookup={productNameLookup}
          />
          <MonthlyInputRowForm
            is_blocked={is_blocked}
            period_key={period_key}
            onSubmit={onSubmit}
          />
        </div>
      </TabsContent>
    </Tabs>
  );
}