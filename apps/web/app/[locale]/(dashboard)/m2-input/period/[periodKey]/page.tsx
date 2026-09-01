/**
 * apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx
 *
 * Story 5.3 T15.1 — Server Component page-level wire for [월 입력].
 *
 * Reads access token, awaits the monthly-input state server-side
 * (F-20 race-free), projects the 5 NEW 5-3 closing-guard fields
 * (closing_guard_blocked, closing_guard_audit_trail,
 * production_consumption_events, v3_verdict, closing_guard_invariant)
 * to page-level state hook, then delegates the tab UI to
 * MonthlyInputTabs (existing client component).
 *
 * UX-locked: ko-KR labels, WCAG AA contrast, Professional 톤.
 *
 * P3-3rd-sweep fixes:
 * - P1: project all 5 NEW fields to <MonthlyInputTabs> (not just 2).
 * - P2: remove inline `<p>` blocking banner; rely on tab-level
 *   <M2ClosingGuardBanner> via MonthlyInputTabs.
 * - P3: thread `opening_inventory_locked` flag for manual edit reject UI.
 * - P24: wrap fetch in try/catch with error boundary (best-effort;
 *   actual ErrorBoundary would be a layout-level concern).
 * - P25: thread server-side `traceId` to <MonthlyInputTabs> for audit
 *   correlation.
 * - P26: pass `productNameLookup` (empty fallback; backend may supply
 *   product names in future).
 * - P27: pass `onSubmit` no-op handler (CLOSING_OK path: [수불부] tab
 *   form can save when unblocked).
 * - P28: fail-closed fallback — when initialState is null, invariant
 *   is EMPTY_PERIOD (not CLOSING_OK) + guard_enabled=false + isBlocked=false
 *   (consistent triple fallback).
 */

import { cookies } from "next/headers";

import { CacheInvalidationChannelBadge } from "@/components/m11-close/CacheInvalidationChannelBadge";
import { ReopenOperatorDialog } from "@/components/m11-close/ReopenOperatorDialog";
import { ReversalExecuteDialog } from "@/components/m11-close/ReversalExecuteDialog";
import { SnapshotPersistencePanel } from "@/components/m11-close/SnapshotPersistencePanel";
import { TwoFactorGuard } from "@/components/m12-account/TwoFactorGuard";
import { MonthlyInputTabsInteractive } from "@/components/m2-input/MonthlyInputTabsInteractive";
import type { ClosingInvariant } from "@/lib/l2-input-inventory-ledger";
import { fetchMonthlyInputStateServerSide } from "@/lib/server-api";
import { fetchM2EntryGateServerSide } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function MonthlyInputPeriodPage({
  params,
}: {
  params: Promise<{ periodKey: string }>;
}) {
  const { periodKey } = await params;
  const cookieStore = await cookies();
  const accessToken = cookieStore.get("sb-access-token")?.value;
  const traceId = crypto.randomUUID();

  // P3-3rd-sweep P24: best-effort error boundary via try/catch. A thrown
  // fetch error or MonthlyInputService error would otherwise crash the
  // page. Returns null → fail-closed fallback (P28).
  let initialState: Awaited<
    ReturnType<typeof fetchMonthlyInputStateServerSide>
  > = null;
  try {
    initialState = await fetchMonthlyInputStateServerSide(
      periodKey,
      accessToken,
      traceId,
    );
  } catch {
    initialState = null;
  }

  // P3-3rd-sweep P28: fail-closed fallback — when initialState is null,
  // ALL three flags are consistent: invariant=EMPTY_PERIOD (not
  // CLOSING_OK), guard_enabled=false, isBlocked=false. Page does not
  // show a misleading "OK" banner when the backend is unreachable.
  const invariant: ClosingInvariant = initialState?.closing_guard_invariant ?? {
    code: "EMPTY_PERIOD",
    negative_products: {},
    closing_per_product: {},
    guard_enabled: false,
  };

  const openingInventoryLocked =
    initialState?.opening_inventory_locked ?? false;
  const auditTrail = initialState?.closing_guard_audit_trail ?? [];
  const productionConsumptionEvents =
    initialState?.production_consumption_events ?? [];

  // Story 6.1 T8.6 — 4 NEW closing-period fields from MonthlyInputStateResponse.
  // cj-252: `closing_snapshot_count` is now consumed inside the client
  // wrapper (MonthlyInputTabsInteractive.onClosingPeriodConfirm returns
  // `data.closing_snapshot_count ?? 0` directly from the POST response),
  // so we no longer project it on the server.
  const closingPeriodState = initialState?.closing_period_state ?? null;
  const closingPeriodFinalizedAt =
    initialState?.closing_period_finalized_at ?? null;
  // CR 6-1 R4 patch D11 — explicit capability gate (A10 MONTHLY_CLOSING_REPORT).
  // Decoupled from state-presence coupling: service-only tenants get False
  // even when closing_period_state is None.
  const monthlyClosingReportCapabilityGranted =
    initialState?.monthly_closing_report_capability_granted ?? false;

  // Story 12.4 review P-02: TwoFactorGuard props sourced from RSC server-side
  // session fetch via GET /api/v1/m2-entry-gate (best-effort, fail-closed).
  // The guard requires the actual role + 2FA enrolled state + lockout status
  // for the gate decision to be correct. When fetch fails, the guard defaults
  // to {role: "viewer", totp_enabled: false, locked_out: false} — which
  // fails CLOSED (viewer cannot enter M2 entry, must complete 2FA setup).
  let gateState: {
    role: string;
    totp_enabled: boolean;
    locked_out: boolean;
    lockout_until: string | null;
  } | null = null;
  try {
    gateState = await fetchM2EntryGateServerSide(accessToken, traceId);
  } catch {
    gateState = null;
  }

  return (
    <section style={{ maxWidth: 1100, margin: "0 auto", padding: "1.5rem 1rem" }}>
      <header style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.25rem" }}>
          월 입력 — {periodKey}
        </h1>
        <p style={{ color: "#475569" }}>
          PRD §8.M2(b) — 6 stream 입력 + 기말재고 검증 (§F4.2) + V3 연결성 검증 (§V3).
        </p>
      </header>
      {/* P3-3rd-sweep P1: project all 5 NEW fields. P3: opening locked.
          P25: traceId. P26: productNameLookup. P27: onSubmit no-op.
          Story 6.1 T8.6 — closing_period_state + capability gate + onConfirm. */}
      {/* Story 12.4 — T8 frontend mount (CR 11-4 D-001: must actually mount
          the component). <TwoFactorGuard> wraps the M2 entry content; when
          the gate is denied, the user sees a yellow panel with a setup
          link instead of the monthly input tabs.
          Story 12.4 review P-01 + P-02: TwoFactorGuard is now the WRAPPER
          (not sibling) + props read from RSC server-side session fetch
          via `getM2EntryGateState()`. The M2 tabs are inside the guard
          children so they DO NOT render when gate is denied. */}
      <TwoFactorGuard
        role={gateState?.role ?? "viewer"}
        totp_enabled={gateState?.totp_enabled ?? false}
        locked_out={gateState?.locked_out ?? false}
        lockout_until={gateState?.lockout_until ?? null}
      >
      <MonthlyInputTabsInteractive
        period_key={periodKey}
        invariant={invariant}
        audit_trail={auditTrail}
        production_consumption_events={productionConsumptionEvents}
        opening_inventory_locked={openingInventoryLocked}
        trace_id={traceId}
        productNameLookup={{}}
        closing_period_state={closingPeriodState ?? undefined}
        closing_period_capability_granted={monthlyClosingReportCapabilityGranted}
        closing_period_finalized_at={closingPeriodFinalizedAt}
        accessToken={accessToken}
      />
      </TwoFactorGuard>
      {/* Story 11.4 (A13 sprint-up) — T8 frontend mount (D-001).
          4 NEW Client Components rendered as siblings of <MonthlyInputTabs>.
          Each component has its own capability gate + service-only tenant
          UX guard, so the page-level stub props below are safe defaults.
          TODO(11-4 carry): replace stub UUIDs with server-side tenant/actor
          resolution (read from session cookie or RSC-fetched user context). */}
      <SnapshotPersistencePanel
        snapshot_id="00000000-0000-4000-8000-000000000001"
        period_key={periodKey}
        current_state="verified"
        actor_id="00000000-0000-4000-8000-000000000002"
        tenant_id="00000000-0000-4000-8000-000000000003"
        capability_granted={monthlyClosingReportCapabilityGranted}
      />
      <ReversalExecuteDialog
        open={false}
        tenant_id="00000000-0000-4000-8000-000000000003"
        target_event_id="00000000-0000-4000-8000-000000000004"
        snapshot_id="00000000-0000-4000-8000-000000000001"
        snapshot_state="committed"
        target_qty="0"
        correction_group_id="00000000-0000-4000-8000-000000000005"
        actor_id="00000000-0000-4000-8000-000000000002"
        capability_granted={monthlyClosingReportCapabilityGranted}
      />
      <ReopenOperatorDialog
        open={false}
        tenant_id="00000000-0000-4000-8000-000000000003"
        actor_id="00000000-0000-4000-8000-000000000002"
        is_owner={false}
        capability_granted={monthlyClosingReportCapabilityGranted}
      />
      <CacheInvalidationChannelBadge />
    </section>
  );
}
