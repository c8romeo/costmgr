# Story 1.2 — Code Review Triage (Chunk A — Frontend)

**Story**: `1-2-settings-wizard-calculation-block`
**Chunk**: A — Frontend (13 files, 1762 lines)
**Review mode**: full
**Date**: 2026-07-30
**Reviewers**: Blind Hunter · Edge Case Hunter · Acceptance Auditor
**Diff**: `_bmad-output/implementation-artifacts/.review/story-1-2-chunk-A.diff`

---

## Raw → Final

| Layer | Raw findings | After dedup |
|---|---|---|
| Blind Hunter | 20 | merged |
| Edge Case Hunter | 25 | merged |
| Acceptance Auditor | 14 | merged (1 dismissed — AA-9 was misread) |
| **Total raw** | **59** | **27 unique** |

Sources merged where multiple reviewers surfaced the same issue (deduped in favor of the most specific location — typically Edge Case Hunter's `file:line` JSON).

---

## Summary by severity

| Severity | Count |
|---|---|
| high | 7 |
| medium | 11 |
| low | 9 |
| **Total actionable** | **27** |

## Summary by route

| Bucket | Count |
|---|---|
| patch | 21 |
| decision_needed | 3 |
| defer | 3 |
| dismiss | 0 |

---

## Findings (most severe first)

### HIGH — patch

#### F-1 — AC #2 + AC #3 tooltip text format deviates from verbatim spec
- **Sources**: AA-1 + AA-2 + BH-1
- **Location**: `apps/web/components/calc/CalcButton.tsx:35-40`
- **Evidence** (read from source):
  ```ts
  function tooltipText(missing: string[], isComplete: boolean): string {
    if (isComplete) return "원가 계산을 실행합니다";
    if (missing.length === 0) return "설정 상태를 확인하는 중입니다…";
    const completed = 4 - missing.length;
    return `설정 ${completed}/4 완료 — 다음 항목을 완료하세요: ${missing.join(", ")}`;
  }
  ```
- **Reachability**: HIGH — `tooltipText()` is the only producer of the button's tooltip text. Spec AC #2 mandates the literal `"회계연도 시작월/통화/언어/배부기준 3종을 모두 완료해 주세요 (2/4 완료)"`; AC #3 mandates a dedicated `"배부기준 3종을 모두 완료해 주세요 (1/3 완료): 고정/변동 분류(0행), 동인 정의(0행)"` branch with per-row counts. The current implementation collapses both ACs into one reworded string and drops the per-row counts entirely.
- **Fix**: Branch `tooltipText()` into three states:
  - complete → `"원가 계산 실행"`
  - top-level fields missing → `"<missing fields>을(를) 모두 완료해 주세요 (N/4 완료)"`
  - allocation criteria incomplete → `"배부기준 3종을 모두 완료해 주세요 (N/3 완료): <criterion>(<count>행), …"` using `completion.direct_indirect_count` / `fixed_variable_count` / `drivers_count`.

#### F-2 — AC #2 + AC #3 missing per-field deep links / no tab pre-selection
- **Sources**: AA-3 + AA-4 + BH-2 + EC-20
- **Location**: `apps/web/components/calc/CalcButton.tsx:126-136` (link rendering); `apps/web/components/settings/wizard/AllocationCriteriaStep.tsx:75-76, 153-172` (no query-param-aware `active`)
- **Evidence** (read from source):
  ```tsx
  {!isComplete && missing.length > 0 && (
    <div ...>
      설정 마법사로 이동 →
      <Link href="/dashboard/settings/wizard" ...>여기를 클릭</Link>
    </div>
  )}
  ```
  The `AllocationCriteriaStep` reads no `?tab=` query param; `active` state is seeded once from `visibleTabs[0]`.
- **Reachability**: HIGH — AC #2 requires per-field links; AC #3 requires deep link to a specific sub-tab. Currently only ONE generic wizard link is emitted, and the wizard can't be deep-linked to a specific tab.
- **Fix**: (a) emit one `<Link>` per missing field with `href` mapping each `missing` item to `/dashboard/settings/wizard[?tab=…]`; (b) `AllocationCriteriaStep` reads `useSearchParams().get("tab")` and seeds `active` from it.

#### F-3 — AC #4 click destination omits the spec locale path AND contains spurious `/dashboard/` prefix
- **Sources**: AA-5
- **Location**: `apps/web/components/calc/CalcButton.tsx:83`
- **Evidence**:
  ```tsx
  <Link href="/dashboard/m3-calculate/period" aria-disabled="false" ...>
  ```
- **Reachability**: HIGH — spec AC #4 mandates `/[locale]/(dashboard)/m3-calculate/period`. The `(dashboard)` route group is invisible in the URL, so the visible path is `/m3-calculate/period`. The current `/dashboard/...` is doubly wrong: spurious `dashboard/` prefix + missing `[locale]` segment.
- **Fix**: Use the next-intl locale-aware `<Link>` (or `useLocale()` + locale-prefixed `href`) — target `/[locale]/m3-calculate/period` where the `m3-calculate/period` route is defined under `(dashboard)`.

#### F-4 — `useSettingsCompletion` cancellation pattern is broken (refetch returns cleanup but no caller invokes it)
- **Sources**: AA-7 + BH-11 + EC-2 + EC-3
- **Location**: `apps/web/hooks/useSettingsCompletion.ts:46-67`
- **Evidence**:
  ```ts
  const refetch = useCallback(() => {
    let cancelled = false;
    ...
    return () => { cancelled = true; };
  }, []);
  ```
  `refetch` is declared `() => void` (no return type documented), and the only caller (`SettingsWizardClient.handleSaved` and `useEffect`) discards the returned cleanup. Pending fetches can never be cancelled.
- **Reachability**: HIGH — every focus event, every poll, every save triggers `refetch()`; with focus-refetch + 30 s polling + save-refetch, stale responses can clobber newer state and leak setState into unmounted components.
- **Fix**: Use `useRef<boolean>(false)` for `cancelledRef`; guard `setStatus`/`setError`/`setIsLoading` with `if (!cancelledRef.current)`. Track per-fetch request IDs to ignore older responses. Update type signature to `() => Promise<void>` if needed.

#### F-5 — SettingsWizardClient uses `setState` during render (race + render storm risk)
- **Sources**: AA-8 + BH-4 + EC-13 + EC-14
- **Location**: `apps/web/components/settings/wizard/SettingsWizardClient.tsx:39-43`
- **Evidence**:
  ```tsx
  if (status && completion && status.trace_id !== completion.trace_id) {
    setCompletion(status);
  } else if (status && !completion) {
    setCompletion(status);
  }
  ```
- **Reachability**: HIGH — server regenerates `trace_id` on every fetch, so the trace_id-equality gate is structurally always true after the first poll. `setState` during render causes a re-render that enters the same branch → React schedules another render, etc. With concurrent rendering this can produce render storms. Additionally, an older poll resolving after a fresh save clobbers the just-saved value (EC-13).
- **Fix**: Move into `useEffect` keyed on `status?.trace_id`. Or replace local `completion` with `status` directly and fold optimistic writes into the polled state via a versioned merge (compare `settings_version`).

#### F-6 — "완료로 표시" shortcuts the actual row registration (AC #3 spirit violation)
- **Sources**: AA-11 + BH-6 + EC-15
- **Location**: `apps/web/components/settings/wizard/AllocationCriteriaStep.tsx:90-116`
- **Evidence**:
  ```ts
  const targetCount = Math.max(currentCount, 1);
  const res = await saveAllocationCriterion(criterion, targetCount, accessToken);
  ```
- **Reachability**: HIGH — the user can mark **동인 정의** complete in `service` industry without ever registering a real driver row. Backend stores `count: 1` in `tenant_settings.onboarding.allocation_criteria`, satisfying the JSONB invariant but leaving `m9_abc.drivers` empty. When the user later runs calc, CCR divides by `practical_capacity_hours = 0` → silently wrong allocation per A11 (CCR = 부서 원가 / 실제적 조업능력).
- **Fix**: Remove the "완료로 표시" shortcut. Disable the button until the real CRUD has ≥1 row; surface a notice `"M1/M9 페이지에서 1행 이상 등록하면 자동으로 완료됩니다"`. The completion endpoint (backend) should derive counts from real tables, not accept user-stamped counts.

#### F-7 — Missing AC fields in `CompletionStatus` interface (fiscal_year_start / currency / industry actual values)
- **Sources**: BH-5 + EC-10
- **Location**: `apps/web/lib/api-client.ts:199-211`; consumer casts at `SettingsWizardClient.tsx:74-80, 87-94, 109-116`
- **Evidence**:
  ```ts
  export interface CompletionStatus {
    fiscal_year_start_completed: boolean;
    currency_completed: boolean;
    language_completed: boolean;
    allocation_criteria_completed: boolean;
    direct_indirect_count: number;
    fixed_variable_count: number;
    drivers_count: number;
    drivers_required: boolean;
    is_complete: boolean;
    missing: string[];
    trace_id: string;
  }
  // No `fiscal_year_start`, `currency`, `industry`
  ```
  Consumers reach for them via `(completion as unknown as Record<string, unknown>)["fiscal_year_start"]`.
- **Reachability**: HIGH — without `fiscal_year_start` value, the wizard cannot seed the year/month picker; the user's saved value is clobbered by `useState(parsed?.year ?? new Date().getFullYear())` defaulting to the current year on next visit. `industry` is needed to render the correct allocation tab set without an extra round-trip. Backend (per spec §8.M0(b)) should include them; `tests/integration/test_completion_consistency.py` should catch the drift.
- **Fix**: Add `fiscal_year_start: string | null`, `currency: "KRW" | "USD" | null`, `industry: Industry | null` to the interface; update backend `CompletionStatusResponse`; drop all `as unknown as Record<string, unknown>` casts.

---

### HIGH — decision_needed

#### F-8 — Wizard step components use `role="radio"` / `role="tab"` on `<button>` without keyboard arrow navigation
- **Sources**: BH-8
- **Location**: `FiscalYearStartStep.tsx:148-170` (`role="radio"`); `CurrencyStep.tsx:83-117` (`role="radio"`); `AllocationCriteriaStep.tsx:150-173` (`role="tab"`)
- **Evidence**: All three groups use `<button role="radio" aria-checked={selected}>` / `<button role="tab" aria-selected={selected}>` with **click-only** activation. ARIA APG requires arrow-key navigation, roving `tabindex`, and Home/End within a group.
- **Reachability**: HIGH for WCAG AA conformance (ux-locked-decisions: ko-KR + WCAG AA + Professional 톤). Tab-only users cannot move between options without leaving the group. **Decision needed**: replace with native `<input type="radio">` (form semantics + built-in arrow nav) vs implement roving tabindex manually. Native is simpler but the existing styling uses `<button>` to render cards; manual implementation keeps visual design but adds 30+ lines per group.
- **Fix options**: (a) shadcn/ui `RadioGroup` component (Story 0.3 added shadcn to cold-start stack pin); (b) native `<input type="radio">` + `<label>` + CSS; (c) roving tabindex + `onKeyDown` Arrow handlers. **Decision needed**: pick (a/b/c).

---

### MEDIUM — patch

#### F-9 — Hard-codes "4" denominator in calculator banner + CalcButton (manufacturing has only 3 effective criteria)
- **Sources**: BH-20
- **Location**: `apps/web/components/calc/CalculatorBanner.tsx:50`; `apps/web/components/calc/CalcButton.tsx:38`
- **Evidence**: `필수 항목 {4 - missing.length}/4` and `4 - missing.length`. For `manufacturing`, drivers are skipped → only 3 effective criteria. A manufacturing user who has done 2 of 3 criteria + fiscal + currency + language sees `3/4` even though they have nothing left to do.
- **Reachability**: MEDIUM — the spec anti-pattern (Story 1.2 line 340) explicitly states "DO NOT display `[계산]` button enabled when settings are incomplete" — but the corollary (don't show `3/4` when there are only 3 fields) is also a UX defect. Affects manufacturing tenants specifically.
- **Fix**: Derive the denominator from `completion.drivers_required`: `totalRequired = drivers_required ? 4 : 3`. Or expose `total_count` from the backend `CompletionStatusResponse`.

#### F-10 — `refetch` not invoked on window focus (spec T5.6 mandate)
- **Sources**: BH-3 + EC-1
- **Location**: `apps/web/hooks/useSettingsCompletion.ts:69-77`
- **Evidence**:
  ```ts
  useEffect(() => {
    refetch();
    const interval = setInterval(() => { ... }, POLL_MS);
    return () => clearInterval(interval);
  }, [refetch]);
  ```
  No `window.addEventListener("focus", refetch)`. Spec T5.6: "Stale time: 5 seconds, refetch on focus".
- **Reachability**: MEDIUM — if user opens wizard in tab A, makes a change in tab B, returns to tab A — the banner / button stay stale for up to 30 s. Spec-mandated behavior.
- **Fix**: Add `window.addEventListener("focus", refetch)` + `document.addEventListener("visibilitychange", ...)` inside `useEffect` with cleanup.

#### F-11 — `pathname.startsWith(href)` in sidebar produces false-positive active states
- **Sources**: BH-14
- **Location**: `apps/web/components/sidebar/Sidebar.tsx:72`
- **Evidence**: `const active = pathname.startsWith(href);`. When `href = "/dashboard"`, every dashboard route (`/dashboard/settings/wizard`, `/dashboard/m3-calculate/period`, …) highlights the "Dashboard" item as active.
- **Reachability**: MEDIUM — sidebar visual state; non-critical for AC but degrades navigation clarity. Spec anti-pattern rule (Story 1.2 line 338) wants correct UX.
- **Fix**: Use `useSelectedLayoutSegment('(dashboard)')` + segment compare, or check `pathname === href || pathname.startsWith(href + '/')`.

#### F-12 — Double-click on save fires two POSTs (audit log duplicates + settings_version double-increment)
- **Sources**: BH-19
- **Location**: `FiscalYearStartStep.tsx:74-90`, `CurrencyStep.tsx:44-60`, `LanguageStep.tsx:37-53`, `AllocationCriteriaStep.tsx:90-116`
- **Evidence**: `disabled={isSaving || isLocked}` only protects AFTER React commits `isSaving=true`. A user double-click fires two `handleSave` invocations; both reach the network. Audit log (AD-10) gets two rows for what should be one idempotent save.
- **Reachability**: MEDIUM — affects all 4 wizard steps. Audit trail integrity (AD-10).
- **Fix**: Capture `inFlightRef = useRef<boolean>(false)`; return early if `inFlightRef.current`; set/clear around the await.

#### F-13 — No 401 refresh / cookie fallback path in api-client
- **Sources**: EC-7
- **Location**: `apps/web/lib/api-client.ts:115-133` (error branch) + `request<T>()` wrapper
- **Evidence**: Error branch throws `ApiError` immediately on `!res.ok`; no 401 handling, no refresh-token call, no cookie-session retry.
- **Reachability**: MEDIUM — JWT expiry mid-session is normal. With `Authorization: Bearer <token>` and no refresh, the user gets stuck with a 401 forever. The cookie fallback (`credentials: "same-origin"`) covers the no-token case but not the case where a stale token IS sent.
- **Fix**: On 401, clear the in-memory bearer and retry once with `credentials: "same-origin"`. If that also 401s, surface an "세션 만료" UI.

#### F-14 — No fetch timeout (UI can hang forever on stalled network)
- **Sources**: EC-4
- **Location**: `apps/web/lib/api-client.ts:109-113`
- **Evidence**: `const res = await fetch(path, { ...init, headers, credentials });` — no `AbortSignal.timeout()`.
- **Reachability**: MEDIUM — a stalled backend leaves `isLoading=true` indefinitely; the wizard step save button stays disabled forever.
- **Fix**: Default `signal = AbortSignal.timeout(10_000)` (10 s) and pass via `init.signal`.

#### F-15 — Disabled calc button cannot receive focus → tooltip not exposed to keyboard users
- **Sources**: EC-18
- **Location**: `apps/web/components/calc/CalcButton.tsx:60-80` (the `disabled` branch)
- **Evidence**: `<button type="button" disabled ...>` removes the element from the tab order. Mouse hover still triggers `onMouseEnter`, but keyboard users have no way to focus the button → the tooltip cannot be discovered.
- **Reachability**: MEDIUM — WCAG AA + keyboard accessibility. Affects all users navigating with keyboards / screen readers.
- **Fix**: Use `aria-disabled="true"` without the HTML `disabled` attribute. Add `onClick` that returns early when disabled (no side effect). Use `aria-describedby` for the tooltip already wired (`tooltipId`) — works with focus.

#### F-16 — Optimistic save spreads `completion` and silently drops sibling fields
- **Sources**: BH-7
- **Location**: `CurrencyStep.tsx:48-53`, `FiscalYearStartStep.tsx:78-83`, `LanguageStep.tsx:41-46`, `AllocationCriteriaStep.tsx:100-109`
- **Evidence**: `{ ...(completion as CompletionStatus), <one_flag>, is_complete: res.is_complete, missing: res.missing }`. If `completion === null`, the spread is a no-op; the local cache loses `fiscal_year_start_completed` / `currency_completed` / etc. flags. With manufacturing industry, `allocation_criteria_completed` flag disappears after the first criterion save.
- **Reachability**: MEDIUM — affects all 4 steps. Causes the "전체 완료" banner downstream to compute against an incomplete shape.
- **Fix**: Replace the spread with the server's `OnboardingFieldSavedResponse` + polled `status` (server is truth). Or guard: skip the local merge when `completion === null`.

#### F-17 — Wizard step `isLocked` requires parsed value to match current state (regression on already-saved tenants)
- **Sources**: EC-23 + EC-24 (similar for FiscalYear)
- **Location**: `FiscalYearStartStep.tsx:69-72`; `CurrencyStep.tsx:42`; `LanguageStep.tsx:35`
- **Evidence**: `const isLocked = completion?.currency_completed === true && initial === currency;`. If the completion endpoint does NOT include the stored value (F-7), `initial === null` → `isLocked` is always false → the save button is always enabled → user can re-save → settings_version increments every click. After F-7 is fixed, this finding becomes dormant.
- **Reachability**: MEDIUM — currently dormant if F-7 is patched (CompletionStatus includes the value). Becomes relevant only if F-7 is deferred.
- **Fix**: Once F-7 is fixed, this becomes a non-issue. If F-7 is deferred, gate `isLocked` on `completion.<field>_completed === true` only (not the initial-value comparison).

#### F-18 — 7-day grace warning header not surfaced to UI
- **Sources**: EC-21
- **Location**: `apps/web/lib/api-client.ts:213-272` (4 save functions)
- **Evidence**: All 4 save functions discard `headers` (only `updateIndustry` reads `X-Onboarding-Warning` via `onWarningHeader` opt). Spec anti-pattern rule (Story 1.2 line 336): "DO NOT allow fiscal_year_start change after first calculation (A7). 7-day grace identical to industry." Without the warning surfacing, the user is told on the server side but the UI doesn't show it.
- **Reachability**: MEDIUM — A7 (전진법) graceful UX violation. The Story 1.2 T7.6 test mentions `test_fiscal_year_change_within_7_days_allowed` expects a `warning header`.
- **Fix**: Add `onWarningHeader` callback param to all 4 save functions (mirror `updateIndustry`); surface the warning in the wizard step UI.

#### F-19 — Touch user tapping the disabled calc control cannot see the tooltip
- **Sources**: EC-19
- **Location**: `apps/web/components/calc/CalcButton.tsx:55-58`
- **Evidence**: Tooltip visibility is wired to `onMouseEnter` / `onFocus` only — no `onPointerDown` / `onTouchStart` / `onClick` handler. Touch-only devices can never trigger the tooltip because focus doesn't fire on tap.
- **Reachability**: MEDIUM — affects all touch-only devices (phones, tablets).
- **Fix**: Add `onClick={() => setShowTooltip(v => !v)}` on the wrapper div (toggle on tap).

---

### MEDIUM — decision_needed

#### F-20 — Save succeeds before initial completion arrives → default month/currency overwrites existing tenant settings
- **Sources**: EC-9
- **Location**: `SettingsWizardClient.tsx:34-46`
- **Evidence**: `const { status, refetch } = useSettingsCompletion(accessToken); const [completion, setCompletion] = useState<CompletionStatus | null>(status);`. On first render, `status === null` and `completion === null`. If the user clicks save before the GET /completion returns, `initial === null` (per F-7), the step sends `formatStored(currentYear, 1)` as default, the backend saves it, and the original saved value is overwritten.
- **Reachability**: MEDIUM — race window is small (one round-trip), but it's a real silent data-loss path. Only triggers on slow network + fast user.
- **Fix options**: (a) Render a loading skeleton until first `status` arrives; disable all save buttons. (b) Fetch `tenant_settings.onboarding` server-side and pass as initial props (preferred — no race). **Decision needed**: confirm (a) vs (b). (b) is closer to the Story 1.1 RSC pattern.

---

### MEDIUM — patch (continued)

#### F-21 — Active tab goes stale when industry changes (manufacturing hides drivers)
- **Sources**: BH-13 + EC-17
- **Location**: `apps/web/components/settings/wizard/AllocationCriteriaStep.tsx:75-76`
- **Evidence**: `useState<TabKey>(initialActive as TabKey)` only seeds once. If `industry` switches from `service` → `manufacturing` (per §3.A7 grace window), `visibleTabs` filters out `drivers` but `active` still equals `"drivers"` → tabpanel renders nothing.
- **Reachability**: MEDIUM — affects industry-change users during the 7-day grace window.
- **Fix**: `useEffect(() => { if (!visibleTabs.some(t => t.key === active)) setActive(visibleTabs[0].key) }, [visibleTabs, active])`.

---

### LOW — patch

#### F-22 — `<a>` instead of `<Link>` for tab "추가 / 편집" causes hard reload
- **Sources**: BH-9
- **Location**: `apps/web/components/settings/wizard/AllocationCriteriaStep.tsx:192-204`
- **Evidence**: `<a href={tab.addHref} ...>추가 / 편집 (Epic {…})</a>` — full document navigation; blows away React state, polled `useSettingsCompletion` cache, and any unsaved wizard changes.
- **Fix**: `import Link from "next/link"`; replace `<a>` with `<Link>`.

#### F-23 — Tooltip nests interactive `<Link>` (ARIA violation)
- **Sources**: BH-10
- **Location**: `apps/web/components/calc/CalcButton.tsx:197-230`
- **Evidence**: An element with `role="tooltip"` should not contain interactive descendants per WAI-ARIA APG. Screen readers will announce both the tooltip text and the link's accessible name on every focus.
- **Fix**: Render the link as a sibling (positioned absolutely outside the tooltip span), or use `role="dialog"` with proper focus handling.

#### F-24 — No error boundary on the wizard route
- **Sources**: BH-17
- **Location**: `apps/web/app/[locale]/(dashboard)/settings/wizard/page.tsx:64-86`
- **Evidence**: `cookies()` can throw (`@supabase/ssr` redirect) and `SettingsWizardClient` can throw during render. No `error.tsx` in the route segment → Next.js's default error page, losing all wizard state.
- **Fix**: Add `apps/web/app/[locale]/(dashboard)/settings/wizard/error.tsx` with a "다시 시도" button.

#### F-25 — `ApiError.name` is `"Error"` not `"ApiError"` (breaks Sentry/stack-trace filters)
- **Sources**: BH-16
- **Location**: `apps/web/lib/api-client.ts:29-38`
- **Evidence**: `class ApiError extends Error { ... super(payload.message_ko); ... }` never sets `this.name = "ApiError"`.
- **Fix**: Add `this.name = "ApiError"` in the constructor.

#### F-26 — Industry name displayed in English on dashboard placeholder
- **Sources**: BH-18
- **Location**: `apps/web/app/[locale]/(dashboard)/page.tsx:30`
- **Evidence**: `<strong>{industry ?? "(미설정)"}</strong>` renders the raw enum (`manufacturing`, `service`, …). UX-locked-decisions mandates ko-KR.
- **Fix**: Use a `INDUSTRY_LABEL_KO` map or look up via `INDUSTRY_MENU_MAP`.

#### F-27 — Background refetch while cached status is complete → enabled button flickers disabled
- **Sources**: EC-5
- **Location**: `apps/web/hooks/useSettingsCompletion.ts:39` + `CalcButton.tsx:48`
- **Evidence**: `const disabled = isLoading || !status || !isComplete;`. When a poll starts, `setIsLoading(true)` → `disabled = true` → button flickers disabled even though `status` is still complete in the previous render.
- **Fix**: `const disabled = !status || (!isComplete && !isLoading)`. Or keep `status` displayed while refetching.

#### F-28 — `polling interval`'s `STALE_MS` gate is dead code (interval is 30 s, gate is 5 s)
- **Sources**: BH-12
- **Location**: `apps/web/hooks/useSettingsCompletion.ts:33-34, 71-75`
- **Evidence**: `POLL_MS = 30_000` and the gate `Date.now() - lastFetchedRef.current >= STALE_MS` where `STALE_MS = 5_000`. The interval fires every 30 s, so the gate is always true.
- **Fix**: Either shorten the interval (e.g. 5 s) and keep the gate, or drop the gate and rename the constant.

#### F-29 — `aria-disabled="false"` on enabled `<Link>` is mildly misleading for screen readers
- **Sources**: AA-12
- **Location**: `apps/web/components/calc/CalcButton.tsx:84`
- **Evidence**: ARIA recommends omitting `aria-disabled` when false. `<Link aria-disabled="false">` causes some screen readers to announce "disabled false" or skip the link entirely.
- **Fix**: Remove `aria-disabled` from the enabled `<Link>` branch.

#### F-30 — Refetch fails after previously complete → stale status can re-enable calculation
- **Sources**: EC-6
- **Location**: `apps/web/hooks/useSettingsCompletion.ts:56-60`
- **Evidence**: On refetch failure, `setError(msg)` is called but `status` is NOT cleared. A previous `is_complete: true` status remains, keeping the button enabled even though the current backend state is unknown.
- **Fix**: Either clear `status` to null on failure, or set `is_complete = false` defensively when fetch fails after a previous success.

---

### LOW — decision_needed

#### F-31 — Allocation count "0행" displayed even though user has not visited the M1/M9 page yet (semantic ambiguity)
- **Sources**: (spec deviation)
- **Location**: `apps/web/components/settings/wizard/AllocationCriteriaStep.tsx:183-189`
- **Evidence**: Shows "현재 등록: 0행 — 미완료". For a brand-new tenant, this is true but reads as if the user has explicitly not completed anything. Could be clearer: "아직 등록된 항목이 없습니다 — 추가 / 편집에서 시작하세요".
- **Reachability**: LOW — copy/UX. **Decision needed**: keep "0행 — 미완료" vs introduce a distinct "empty state" copy.

---

### LOW — defer

#### F-32 — Server-component page forwards access-token cookie string to Client Components (security hardening)
- **Sources**: BH-15
- **Location**: `apps/web/app/[locale]/(dashboard)/settings/wizard/page.tsx:71`, plus all client consumers
- **Evidence**: The Server Component reads `sb-access-token` from cookies and forwards the **literal string** through 5+ layers into deeply nested Client Components. The token ends up inlined in the server-rendered HTML and in the React hydration payload.
- **Reachability**: LOW for now (token is cookie-readable by JS anyway), but a hardening pass is warranted. Add a `Route Handler` that proxies `/completion` server-side (cookies auto-forwarded); the hook calls the proxy endpoint with no token.
- **Route**: defer to a hardening sprint — affects 5+ files and is security-by-default, not AC-blocking.

#### F-33 — `settings_version` optimistic concurrency: no `If-Match` header sent
- **Sources**: BH out-of-scope
- **Location**: All 4 save endpoints (`api-client.ts:213-272`)
- **Evidence**: Spec AC #1 says "settings_version increments on each save" — backend enforces it; client never sends the current version, so two simultaneous saves from different tabs do last-write-wins.
- **Reachability**: LOW for single-tab use; cross-tab is rare. Defensive but not AC-blocking.
- **Route**: defer — requires backend changes (Story 4.x territory).

#### F-34 — `fiscal_year_start` A7 lock: UI never warns the user before clicking save
- **Sources**: BH out-of-scope
- **Location**: `FiscalYearStartStep.tsx:69-72`, `CurrencyStep.tsx:42`
- **Evidence**: The frontend `isLocked` only checks `completion.<field>_completed`, not `last_calc_date`. The backend rejects with 409, but the UI never warns the user before they click save.
- **Reachability**: LOW — backend catches the violation; the UX is "click → error" instead of "locked before click".
- **Route**: defer — needs `last_calc_date` field on `CompletionStatus` (similar to F-7 fix); could be combined with F-7 if approved.

---

## Notes

- **Out-of-scope notes (dismissed, not counted)**: BH "out-of-scope" list items that are either already handled (`dynamic = "force-dynamic"` is intentional), style nitpicks (`MenuContext.refresh` async vs hook sync), or trivial (`parseStored` regex rejects year 9999 — not a real risk).
- **AA-9 dismissed**: AA-9 claimed "disabled button loses click handler entirely" — verified at `CalcButton.tsx:60-80`, this is the correct AC #2 behavior (no side effect when disabled). False positive.
- **AA-6 dismissed-LOW**: AC #1 endpoint path shape (`fiscal-year-start` kebab vs `fiscal_year_start` snake) — spec AC #1 uses `<field>` placeholder, so either interpretation is acceptable. Backend uses kebab; backend also accepts both. Low-priority consistency note, not blocking.
- **Frontend test deferral (AA-14)**: T7.3 (Vitest/RTL) + T7.4 (Playwright) are deferred to Story 0.5 per Completion Notes. Given the format deviations in F-1/F-2, automated tests would have caught the mismatch. **Recommend**: unblock Story 0.5 test-framework install OR write smoke-level Vitest tests for `tooltipText()` + `useSettingsCompletion()` race in this story.

---

## Triage outcome

- 27 actionable findings
- 21 patch (fixable in this story)
- 3 decision_needed (need kjw input before patch)
- 3 defer (out of scope or hardening)
- 0 dismiss (after AA-9 dedup)

### Decision_needed summary (need kjw input)

- **F-8**: Pick radio/tab pattern — shadcn RadioGroup (a) / native `<input type="radio">` (b) / roving tabindex manual (c)
- **F-20**: Loading skeleton (a) vs server-side initial fetch (b) for race between save and first completion load
- **F-31**: Keep "0행 — 미완료" copy vs introduce distinct "empty state" copy for new tenants