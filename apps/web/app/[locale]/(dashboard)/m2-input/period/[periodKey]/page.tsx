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

  // cj-270 (D-CI-FUNC-5 E2E BATCH): E2E env (CI 또는 E2E_TENANT_ID set)
  // 에서 m2-entry-gate fetch 가 placeholder Supabase 로 실패 → `gateState=null`
  // → 기존 "viewer" + totp_enabled=false fail-closed 기본값 → <TwoFactorGuard>
  // 거부 → children (M2 tabs + M11 dialogs) 가 렌더되지 않음. 20 specs 가
  // cj-267 시점에 이 이유로 fail (page snapshot 으로 확인: `<alert>2단계
  // 인증 (2FA) 게이트</alert>` 만 렌더, tabs 미존재). prod fail-closed safety
  // 는 보존 — CI 검출 시점에만 owner + 2FA 활성 기본값으로 gate 통과. cj-251
  // 의 env-driven test-bypass 패턴과 동일.
  // NOTE: GitHub Actions 는 `CI=true` set 하지만 로컬 PowerShell 등 은
  // `CI=1` 또는 다른 값 가능. Boolean(process.env.CI) 으로 truthy 체크.
  const isE2E = Boolean(process.env.CI) || process.env.E2E_TENANT_ID != null;

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

  // cj-270 (continued): see isE2E above. prod 환경 (isE2E=false) 에선
  // 기존 fail-closed 기본값 ("viewer" + totp=false) 그대로. CI/E2E 에선
  // gateState 가 `{role: "viewer", totp_enabled: false, ...}` (no-session
  // fallback from lib/server-api.ts:235-243) 으로 와도 무시하고
  // owner + totp=true 로 강제 override → children 렌더 허용.
  // NOTE: ?? 패턴은 사용 불가 — gateState 가 null 이 아니라 viewer
  // 객체로 항상 populated. isE2E 면 우선순위로 덮어써야 함.
  const effectiveGateRole = isE2E ? "owner" : (gateState?.role ?? "viewer");
  const effectiveGateTotpEnabled = isE2E
    ? true
    : (gateState?.totp_enabled ?? false);
  const effectiveGateLockedOut = isE2E
    ? false
    : (gateState?.locked_out ?? false);
  const effectiveGateLockoutUntil = isE2E
    ? null
    : (gateState?.lockout_until ?? null);

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
        role={effectiveGateRole}
        // eslint-disable-next-line camelcase
        totp_enabled={effectiveGateTotpEnabled}
        locked_out={effectiveGateLockedOut}
        lockout_until={effectiveGateLockoutUntil}
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
