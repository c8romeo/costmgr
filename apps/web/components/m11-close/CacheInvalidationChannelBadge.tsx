/**
 * apps/web/components/m11-close/CacheInvalidationChannelBadge.tsx — Story 11.4 (A13 sprint-up)
 *
 * M11 AD-25 cache invalidation 4-channel publisher badge.
 *
 * Renders 4 channel chips (ai_cache / cost_engine_cache /
 * fiscal_period_cache / closing_snapshot_cache) with optional
 * "active subset" highlight for W2 reopen (2 channels subset of 4).
 *
 * Korean SSOT: `lib/ko-KR.json::m11_close.cache_invalidation_channel_*`.
 * AD-15 §11 parity invariant preserved between Python ko-KR + TS messages mirror.
 */

"use client";

import { useTranslations } from "next-intl";
import * as React from "react";

import {
  CACHE_INVALIDATION_CHANNELS,
  type CacheInvalidationChannel,
} from "@/lib/closing-period";

export interface CacheInvalidationChannelBadgeProps {
  /** Subset of channels to highlight (e.g. W2 reopen uses 2 channels). */
  active_subset?: readonly CacheInvalidationChannel[];
  /** Optional className override. */
  className?: string;
}

/**
 * CacheInvalidationChannelBadge — AD-25 4-channel publisher UI.
 *
 * Renders all 4 channels as chips with optional highlight for the
 * active subset. Used in reversal execute + reopen confirmation
 * receipts to surface which caches were invalidated.
 */
export function CacheInvalidationChannelBadge({
  active_subset,
  className,
}: CacheInvalidationChannelBadgeProps): React.ReactElement {
  const t = useTranslations("cache_invalidation_channel_badge");
  const subset = active_subset ?? CACHE_INVALIDATION_CHANNELS;

  return (
    <section
      className={
        "rounded-md border border-slate-200 bg-white p-3 shadow-sm " +
        (className ?? "")
      }
      data-testid="cache-invalidation-channel-badge"
      data-active-subset={subset.join(",")}
    >
      <h3 className="mb-2 text-sm font-semibold text-slate-900">
        {t("badge_label")}{" "}
        <span className="font-mono text-xs text-slate-500">
          ({t("channel_4_set")})
        </span>
      </h3>
      <div className="flex flex-wrap gap-2">
        {CACHE_INVALIDATION_CHANNELS.map((channel) => {
          const isActive = subset.includes(channel);
          return (
            <span
              key={channel}
              data-testid={`cache-channel-${channel}`}
              data-active={isActive}
              className={
                "inline-flex items-center rounded-full border px-3 py-1 text-xs font-mono " +
                (isActive
                  ? "border-blue-500 bg-blue-50 text-blue-700"
                  : "border-slate-200 bg-slate-50 text-slate-500")
              }
            >
              {labelForChannel(channel, t)}
            </span>
          );
        })}
      </div>
    </section>
  );
}

function labelForChannel(
  channel: CacheInvalidationChannel,
  t: (key: string) => string,
): string {
  switch (channel) {
    case "ai_cache":
      return t("channel_ai_cache");
    case "cost_engine_cache":
      return t("channel_cost_engine_cache");
    case "fiscal_period_cache":
      return t("channel_fiscal_period_cache");
    case "closing_snapshot_cache":
      return t("channel_closing_snapshot_cache");
    default: {
      // Exhaustiveness check.
      const _exhaustive: never = channel;
      return _exhaustive;
    }
  }
}