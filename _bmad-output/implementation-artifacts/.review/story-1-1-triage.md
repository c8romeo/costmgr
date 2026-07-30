# Story 1.1 — Code Review Triage

**Story**: `1-1-industry-selector-menu-auto-toggle`
**Review mode**: full
**Date**: 2026-07-29
**Reviewers**: Blind Hunter · Edge Case Hunter · Acceptance Auditor
**Diff**: `_bmad-output/implementation-artifacts/.review/story-1-1.diff` (4040 lines, 28 files)

---

## Raw vs Final

| Layer | Raw findings | After dedup |
|---|---|---|
| Blind Hunter | 20 | merged |
| Edge Case Hunter | 18 | merged |
| Acceptance Auditor | 16 | merged (3 false-positives dismissed) |
| **Total raw** | **54** | **28 unique** |

3 dismissals: AA-2, AA-3, AA-8 (Acceptance Auditor claimed files were missing; verification shows they exist).

---

## Summary by severity

| Severity | Count |
|---|---|
| high | 14 |
| medium | 13 |
| low | 9 |
| **Total actionable** | **36** |

## Summary by route

| Bucket | Count |
|---|---|
| patch | 32 |
| decision_needed | 3 |
| defer | 1 |
| dismiss | 3 (false positives dropped) |

---

## Findings (most severe first)

### HIGH — patch

- **F-1** *(BH-1)* `apps/web/app/[locale]/(dashboard)/layout.tsx:22-30`
  - **RSC boundary violation — Server Component passes function prop to Client Components**
  - `getAccessToken` (function) is defined in a Server Component and passed as a prop to `<Sidebar>` and `<MenuProvider>` (both Client Components). Next.js cannot serialize function references across the RSC boundary. The dashboard route will fail to render.
  - **Fix**: Lift token reading into the Client Components (e.g., `document.cookie`) or wire auth through a server-side route handler that sets the Authorization header.

- **F-2** *(AA-1 + BH-12 + EC-3)* `apps/api/modules/m0_onboarding/services/settings_service.py:193, 207`
  - **SettingsService unconditionally writes `is_initial=False` — violates AC #1**
  - Line 193: `new_onboarding["is_initial"] = False` runs on every write. Line 207 returns `False, # post-write is_initial is always False`. AC #1 requires the first POST to persist `is_initial: true`. This breaks AC #4's "if is_initial == true" branch (dead code at runtime) and causes the audit action ternary (`industry_change_initial` vs `industry_selected`) to collapse to the wrong action on the second POST.
  - **Fix**: Only set `is_initial: False` when `is_change` is True; preserve `True` on the very first write. This also re-activates AC #4's `industry_change_initial` audit action.

- **F-3** *(AA-7 + BH-3)* `apps/web/app/[locale]/(auth)/layout.tsx` (MISSING)
  - **`(auth)` route group has no layout file**
  - File listing under `apps/web/app/[locale]/(auth)/` shows only `onboarding/industry/page.tsx`. Spec File List (§482) and Source Tree (§333) both list this as a NEW file. Without it, Next.js cannot render the auth route group consistently, and any future login/signup/forgot-password pages in the same group inherit the gap.
  - **Fix**: Create the `(auth)/layout.tsx` Server Component (minimal `{children}` shell at minimum).

- **F-4** *(BH-2)* `apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx:42`
  - **IndustrySelector rendered without `getAccessToken` → POST hits API unauthenticated → 401**
  - Line 42: `<IndustrySelector />` (no `getAccessToken` prop). IndustrySelector calls `getAccessToken?.()` which is `undefined`. api-client.ts only sets the `Authorization` header when an accessToken is provided (line 65). Result: every POST to `/api/v1/tenant-settings/onboarding/industry` arrives at the backend without `Authorization`. `get_tenant_context()` raises AuthError → 401. The frontend falls into the generic catch-all "업종 저장에 실패했습니다" branch. AC #1 is functionally unreachable end-to-end.
  - **Fix**: Either pass a token getter to `<IndustrySelector>` from the Server Component (after fixing F-1's function-prop issue), or have the Server Component POST server-side and return the result to the client.

- **F-5** *(AA-6 + BH-11)* `apps/api/modules/m0_onboarding/services/settings_service.py` (lines 800–916)
  - **Anti-pattern violation: industry change after first calculation is NOT blocked**
  - `update_industry()` reads only `tenant_settings.onboarding`. No `last_calc_date` lookup exists anywhere in the function. Spec anti-pattern rule (line 373) and `docs/onboarding-flow.md` §3.3 require "grace 만료 전 last_calc_date 채워지면 즉시 잠금". The corresponding test (`test_change_industry_after_calculation_blocked`) is a `pytest.skip` stub. A tenant who runs a calc on day 2 can still change industry within the 7-day grace. AC #4's "after first calculation" branch is unimplemented.
  - **Fix**: Add a `last_calc_date` read in `SettingsService.update_industry` and short-circuit with `IndustryLockedError(reason="locked_after_calc")`. Or document the deferral in the story and AC #4.

- **F-6** *(EC-9)* `apps/web/components/sidebar/Sidebar.tsx` (render loop)
  - **Menu hiding is presentation-only — direct navigation to incompatible routes is not blocked**
  - Sidebar filters which links render; the diff adds no middleware/guard for `/dashboard/bom`, `/dashboard/cost-pool`, etc. A service tenant can hand-type `/dashboard/bom` and reach the manufacturing screen. Per Story 0.5 follow-up note, this is structurally important for capability enforcement.
  - **Fix**: Add industry-aware route guards in (dashboard)/layout.tsx or in each route's middleware. Backend endpoints (e.g., `/api/v1/bom/*`) should also reject mismatched-industry writes.

- **F-7** *(EC-2)* `packages/services/m0_onboarding/industry_menu.py:250`
  - **`is_initial=True` permits changes indefinitely — no expiration check**
  - Decision rule: `if is_initial or days_since_selection < GRACE_PERIOD_DAYS`. If `is_initial` is `True`, the grace window is unbounded. A bug elsewhere that re-flips `is_initial=True` (or a data import that sets it) silently re-grants unlimited changes. Per code comment lines 222-225, the intent is that `is_initial` flips to `False` on the first write — but the implementation never enforces that invariant.
  - **Fix**: Either (a) require `days_since_selection < GRACE_PERIOD_DAYS` regardless of `is_initial`, or (b) document explicitly that `is_initial` is a transient flag set by `SettingsService` and add an invariant test.

- **F-8** *(EC-4 + BH-4)* `apps/api/modules/m0_onboarding/services/settings_service.py:189-196`
  - **Idempotent same-industry POST resets the 7-day grace clock by overwriting `selected_at`**
  - When `current_industry == target_industry`, `decision.allowed = True`. Step 4 unconditionally sets `new_onboarding["selected_at"] = now_iso` and bumps `settings_version`. A frontend retry on day 6 silently extends grace to day 13, and an attacker polling POSTs every <7 days can extend grace indefinitely.
  - **Fix**: Return early for same-industry POSTs. Skip the UPDATE, audit, and version bump. Preserve the existing `selected_at` and `settings_version`.

- **F-9** *(EC-5 + BH-5)* `apps/api/modules/m0_onboarding/services/settings_service.py:166-186`
  - **Idempotent same-industry POST still emits an `audit_logs` row, polluting the audit trail**
  - `emit_audit` is called for every successful `decision.allowed=True` path, including the `no_change` same-industry case. Combined with F-8, retries produce duplicate `industry_selected` rows.
  - **Fix**: Skip `emit_audit` for the `no_change` branch (couples with F-8).

- **F-10** *(EC-6)* `apps/api/modules/m0_onboarding/services/settings_service.py:135, 151`; `apps/api/modules/m0_onboarding/handlers.py:151`
  - **Unknown persisted industry values crash `Industry(...)` constructor in both GET and POST paths**
  - `Industry(current_industry_raw)` is called without `try/except ValueError`. A legacy or future DB value (e.g., `"consulting"` from a schema migration or external write) raises ValueError → 500. The migration default path (line 151 in handlers.py, GET handler) has the same gap.
  - **Fix**: Catch `ValueError` defensively. Either return a typed "inconsistent_settings" error to the client (so an admin can repair) or fall back to `None` with an audit trail entry.

- **F-11** *(EC-10 + BH-2 implication)* `apps/web/lib/api-client.ts:65-72`
  - **Cookie-authenticated flow is not implemented by the API client**
  - `request()` only attaches `Authorization: Bearer <token>` when `accessToken` is provided. If the cookie session exists but the wrapper receives no token (the common case for `getAccessToken?.()` returning `undefined`), the fetch goes out with NO auth header. The backend expects `Authorization: Bearer` (handlers.py:27).
  - **Fix**: Either explicitly include `credentials: "same-origin"` and have the backend accept cookie JWTs (full cookie session story), or always supply a bearer token. Decide on one auth contract.

- **F-12** *(EC-11)* `apps/api/core/tenant_context.py:138-149`
  - **`clear_tenant_local` defined but never wired to request lifecycle**
  - The function exists but is not called from any FastAPI middleware, dependency, or finally block. A pooled execution context that handles tenant A then starts a transaction without setting a fresh tenant could carry tenant A's tenant_id. (`attach_tenant_listener` is correctly called at startup in `apps/api/main.py:62`.)
  - **Fix**: Wire `clear_tenant_local` into a yield-based FastAPI dependency (`try/finally`) or a request-finally middleware.

- **F-13** *(EC-17 + EC-18 + BH-8 + AA-10)* `tests/api/test_industry_selector.py:2705,2719`; `tests/api/test_industry_isolation.py:2812,2825`
  - **4 DB-backed tests are `pytest.skip()` stubs that never execute even in CI**
  - `test_select_industry_creates_tenant_settings`, `test_change_industry_after_calculation_blocked`, `test_tenant_a_cannot_read_tenant_b_industry`, `test_tenant_a_cannot_change_tenant_b_industry` all unconditionally skip after an `if not rls_enabled: pytest.skip(...)` early-out. The Completion Notes claim "54 passed / 4 CI-skipped" but the 4 tests skip under ALL environments (CI=true or not). AC #1's database-level guarantees (audit INSERT actually persists, SELECT FOR UPDATE serializes, settings_version increment observable, RLS prevents cross-tenant writes) are NOT exercised.
  - **Fix**: Either wire the `rls_db` and `tenant_pair` fixtures from `tests/rls/conftest.py` so these tests run with `CI=true`/`RLS_RUN_LOCAL=1`, or mark the tests as `xfail` with a clear reason and update the Completion Notes count.

- **F-14** *(BH-9)* `apps/api/modules/m0_onboarding/services/settings_service.py:116`
  - **Role gate compares raw string (`role != "owner"`) — case/whitespace bypass risk**
  - No normalization, no enum, no allowlist. If a JWT issuer ever emits `role='Owner'`, `'OWNER'`, or `' owner '` (Supabase Auth has been seen to do case-mismatched `app_metadata`), a non-owner slips through. Brittle.
  - **Fix**: Normalize (`role = role.strip().lower()`), define `RoleEnum`, compare against `RoleEnum.OWNER.value`, and add a test for `'Owner'` / `' OWNER '`.

### MEDIUM — patch

- **F-15** *(EC-1 + BH-16)* `apps/api/modules/m0_onboarding/services/settings_service.py:138-146`
  - **Missing or unparseable `selected_at` falls back to `datetime.now(UTC)` — silently resets grace clock**
  - A future data import or migration that stores `selected_at` as a Unix timestamp or with a different timezone marker would reset grace on every settings read. The user sees the grace clock advance without explanation.
  - **Fix**: Raise a typed error so the caller can surface it (or persist the raw value to a structured error log). Do not silently mutate the timestamp on parse failure.

- **F-16** *(EC-7)* `apps/api/modules/m0_onboarding/services/settings_service.py:236`
  - **Future `selected_at` values are normalized to day zero via `max(0, delta.days)`**
  - If clock skew stores `selected_at = tomorrow` with `is_initial=false`, `days_since = 0` and the change is treated as within grace. Wrong-state writes should be rejected.
  - **Fix**: Reject timestamps materially later than server time rather than clamping negative durations to zero.

- **F-17** *(EC-8)* `apps/api/modules/m0_onboarding/services/settings_service.py:196`
  - **`settings_version` int4 overflow handling absent**
  - Both audit payload and ORM state use `settings_version + 1` without a maximum guard. PostgreSQL int4 max (~2.1B) is unreachable for real tenants, but the migration column type should be `bigint` for forward-compat.
  - **Fix**: Use `bigint` for `settings_version` (migration) and rotate/reject before the int4 maximum with a typed conflict.

- **F-18** *(EC-12)* `apps/web/lib/api-client.ts:74, 77`
  - **Non-JSON error and empty success responses bypass typed handling**
  - `await res.json()` unconditionally. Proxy returning HTML 502, backend returning empty 204, or any other non-JSON response throws a `SyntaxError` that the caller's `catch` (likely not typed for this) mis-handles.
  - **Fix**: Check content-type and body presence, then synthesize a typed fallback `ApiError` when JSON decoding fails.

- **F-19** *(EC-13)* `apps/web/components/onboarding/IndustrySelector.tsx:76`
  - **`err instanceof ApiError` check skips typed branches for serialized/cross-realm errors**
  - Handling depends on `err instanceof ApiError` rather than validating the error payload shape. A serialized ApiError (across realms, in test mocks, or post-IPC) carries `INDUSTRY_LOCKED` but the frontend displays only the generic failure toast.
  - **Fix**: Use a structural type guard based on `status` and `payload.code` instead of `instanceof` alone.

- **F-20** *(EC-14 + BH-6)* `apps/web/components/onboarding/IndustrySelector.tsx:162`
  - **Lock-screen message hardcodes "현재 업종: 제조업" regardless of actual industry**
  - The 409 response includes `details.current_industry` (e.g., `"service"`), but the frontend ignores it and renders `{INDUSTRY_LABEL_KO.MANUFACTURING}` directly. A service tenant sees false information about being a manufacturing tenant.
  - **Fix**: `<strong>{INDUSTRY_LABEL_KO[err.payload.details.current_industry]}</strong>`.

- **F-21** *(EC-15 + BH-7)* `apps/web/components/onboarding/IndustrySelector.tsx:73`
  - **`router.push("/dashboard")` drops the locale segment**
  - The site uses `[locale]` dynamic segment. The parent route lives at `/${params.locale}/onboarding/industry`. The push goes to `/dashboard` (no locale).
  - **Fix**: Read locale from `useParams()` (or accept as a prop) and `router.push(\`/${locale}/dashboard\`)`.

- **F-22** *(EC-16)* `apps/api/modules/m0_onboarding/handlers.py:142-161` (GET handler)
  - **GET handler does not map `TenantSettingsNotFoundError` to a typed response**
  - `SettingsService.get_tenant_settings()` raises `TenantSettingsNotFoundError`, but the GET handler has no `try/except`. A partial-signup tenant without a `tenant_settings` row returns 500.
  - **Fix**: Catch `TenantSettingsNotFoundError` in GET and return the same typed 404 contract used by POST (`TENANT_SETTINGS_NOT_FOUND`).

- **F-23** *(AA-5 + AA-4)* `apps/api/modules/m0_onboarding/services/settings_service.py:202`
  - **`X-Onboarding-Warning` header branch is internally inconsistent with spec text**
  - Currently fires only for `decision.reason == "within_grace"`. Spec ties the header to `is_initial == true`. Per the code's own comment ("Decision §1"), the header should fire for BOTH `is_initial=true` AND `within_grace` cases (header logic: `decision.reason in ("initial", "within_grace")`). See F-39 (decision_needed) — the developer intent is not clear from the code.
  - **Fix**: Tied to F-39 decision.

- **F-24** *(AA-9)* `apps/web/messages/ko-KR.json` (MISSING)
  - **next-intl messages file is missing despite spec claim**
  - Spec File List (lines 346, 482) and Source Tree (line 347) list this file. Directory exists but is empty. IndustrySelector.tsx inlines ko-KR strings (code comment lines 15-17 defers this to Story 0.5).
  - **Fix**: Either create `ko-KR.json` with the keys used by IndustrySelector (`m0_onboarding.title`, `m0_onboarding.subtitle`, etc.), OR update the spec File List to defer to Story 0.5 explicitly.

- **F-25** *(BH-10)* `tests/integration/test_menu_config_consistency.py:2984-3001`
  - **Drift guard regex captures every quoted string in a menu block — comments included**
  - `_assert_industry_menu_parity` uses `re.findall(r'"([^"]+)"', m.group("body"))` without stripping `//` line comments or `/* */` block comments. A developer adding `// TODO: add '품목' to the manufacturing list` would flip drift-test outcomes.
  - **Fix**: Strip line and block comments before regex application, or use a TS parser (typescript package).

- **F-26** *(BH-13)* `apps/api/modules/m0_onboarding/services/settings_service.py:236`
  - **`_days_between` floor uses raw `timedelta.days` — boundary miscounts by up to 23h59m**
  - `delta = end - start; return max(0, delta.days)`. Two users at near-identical wall-clock times get different A7 lock outcomes.
  - **Fix**: Either compute in UTC calendar days (`date(end.date()) - date(start.date())`) and document hour-granularity is acceptable. Update spec text to match.

- **F-27** *(BH-14)* `apps/api/alembic/versions/0002_tenant_settings_onboarding_defaults.py:991-997`
  - **Migration default sets `is_initial=true`, but the write side flips it to `False` immediately**
  - Defense in depth issue: if a tenant row is created before the migration runs (Story 0.2 path), `onboarding.is_initial` is missing. The fallback `bool(onboarding.get("is_initial", current_industry is None))` silently re-enables the grace window for hand-edited rows.
  - **Fix**: Document the fallback explicitly in the migration docstring; add a test for the `no-is_initial-key` case.

### LOW — patch

- **F-28** *(AA-11)* Spec File List lines 497–505
  - **Spec lists 5 files as "modified" but they're all "new"** (initial commit `bd58c18` doesn't contain them). Content-wise the diff respects the modifications the spec describes. **Spec doc fix only.**

- **F-29** *(AA-12)* Spec Subtask 6.3
  - **Frontend unit test count claim is 4; actual file has 5 tests** (extra structural assertion). **Spec doc fix only.**

- **F-30** *(AA-13)* `tests/api/test_industry_selector.py:2486-2505`
  - **Mock-based audit-order test uses `session.add.call_args_list`** rather than a real DB SELECT. Acceptable for unit-test tier; spec wording implies a DB-backed assertion. **Either reword spec or move test to DB tier.**

- **F-31** *(AA-14)* anti-pattern:6 — Cannot verify "no industry in URL" because page.tsx is now confirmed present. **No action — pattern is consistent with e2e test usage.**

- **F-32** *(AA-15)* `apps/web/components/sidebar/SidebarItem.tsx` — Native HTML `title` attribute instead of a real tooltip. **Acceptable per AC literal text "appears when hovering". Story 0.5 swap.**

- **F-33** *(AA-16)* `apps/web/lib/menu-config.ts:1142-1148` — `INDUSTRY_ICON` is dead-code placeholders. **Acceptable; Story 0.5 supplies icon set.**

- **F-34** *(BH-15)* `apps/api/modules/m0_onboarding/handlers.py:91-99`
  - **`IndustryLockedError` details omit `decision_reason` and `days_since_selection`** — debugging an A7 lock requires a separate audit-log query. **Add to details.**

- **F-35** *(BH-17)* `apps/api/modules/m0_onboarding/services/settings_service.py:243`
  - **`_next_fiscal_year_start` always returns Jan 1.** Korean fiscal years commonly start on other months. Story 1.2 wires configurability. **Document deferral.**

- **F-36** *(BH-18)* `tests/api/test_industry_selector.py` — **No test asserts audit payload includes `reason` or post-bump `version` or trace_id equality.** **Strengthen audit-order test.**

- **F-37** *(BH-19)* `apps/web/lib/menu-config.ts:1142-1148` — **`INDUSTRY_ICON` has no Python mirror or drift test.** **Mark frontend-only or add to drift guard.**

- **F-38** *(BH-20)* `apps/web/components/sidebar/MenuContext.tsx:75-82`
  - **`MenuProvider` refetches on every `getAccessToken` identity change** (each parent re-render). **Memoize after F-1 fix.**

### DECISION_NEEDED

- **F-39** `apps/api/modules/m0_onboarding/services/settings_service.py:202` + `apps/api/modules/m0_onboarding/handlers.py:117-120` + spec line 80-82
  - **Semantic of `X-Onboarding-Warning` header is ambiguous**
  - Spec ties the header to `is_initial == true` (AC #4). Code fires it for `within_grace` only. Three possible interpretations:
    1. Header fires for BOTH `initial` and `within_grace` (broader ux warning, aligns with code comment "Decision §1").
    2. Header fires ONLY for `is_initial=true` (literal spec reading; frontend surfaces grace expiry alert at the right moment).
    3. Header fires ONLY for `within_grace` (current code; spec drift).
  - **Requires PM input.** AA-5 marked this critical because AC #4 compliance depends on it.

- **F-40** AA-5 trace_id semantics — current `IndustryLockedError` (handlers.py:100) carries `trace_id` in payload. **IndustryUpdateResponse** (success path) does NOT carry trace_id. For audit correlation across success + failure paths, the success envelope should also include trace_id.
  - **Requires confirmation that success-path trace_id is needed.**

- **F-41** EC-9 routing guard — Menu hiding is presentation-only. Should the backend (BOM/CostPool/ABC endpoints) ALSO enforce industry capability, or is the rule "FE-only filter, no industry gating at API layer (Epic 2+ will gate)"?
  - **Requires PM input on the capability-enforcement boundary.**

### DEFER

- **F-42** *(EC-12 implication)* — Story 0.5 (Supabase SSR + i18n + design system) wires `next-intl`, real tooltip components, and the actual cookie session. Items F-24, F-32, F-33, F-37 explicitly defer to Story 0.5. **No code change in Story 1.1; spec doc fix or accept.**

### DISMISS

- **D-1** AA-2 *(verified false-positive)* — Acceptance Auditor claimed `apps/web/app/[locale]/(auth)/onboarding/industry/page.tsx` is missing. Verified present (45 lines, Server Component with cookie check + IndustrySelector render).
- **D-2** AA-3 *(verified false-positive)* — Claimed `apps/web/app/[locale]/(dashboard)/layout.tsx` is missing. Verified present (34 lines, Server Component with Sidebar + MenuProvider).
- **D-3** AA-8 *(verified false-positive)* — Claimed `apps/web/app/[locale]/(dashboard)/page.tsx` is missing. Verified present (29 lines, Client Component using `useMenuContext`).

---

## Failed layers

None — all three layers completed with structured findings.

## Recommendation

**Status**: ⚠️ Review findings indicate the implementation has at least 14 high-severity defects that prevent Story 1.1 from being promoted from `review` to `done`. Critical paths are broken end-to-end (F-1, F-2, F-4 alone block AC #1 from passing).

**Suggested next step**: Return to `in-progress`. Have dev address F-1, F-2, F-3, F-4, F-5, F-6 (the most severe six) plus the three `decision_needed` items. Then re-review.