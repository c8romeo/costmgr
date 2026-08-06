# Deferred Work

Items deferred from code review. Each entry records what was deferred, the rationale, and (when known) the story or milestone that should pick it up.

## Deferred from: code review of 0-1-modular-monolith-hexagonal-core-skeleton (2026-07-25)

- **`pnpm-lock.yaml` missing (HANDOFF L2)** — known limitation; Story 0.3 (stack-pin lockfile build pipeline) commits the lockfile.
- **apps/web stack pin variance Next 15.5.4 / React 19.1.1 (HANDOFF L3)** — `[STACK BUMP]` accepted 2026-07-25; pin 16.2.11 / 19.2.8 deferred until those versions actually land on npm.
- **apps/web 13 module folders missing (HANDOFF L4)** — deferred to Story 0.3 (web-side stubs) or 1.1.
- **`import-linter` cannot span `apps.api` ↔ `packages.*` (HANDOFF L1)** — requires `costmgr_workspace` namespace package; Story 0.3.
- **Pretendard CDN without SRI in `layout.tsx`** — Story 0.4 (cross-language conventions + design tokens) migrates to `next/font/local`.
- **dep-cruiser rules vacuous for Python targets** (`api-calls-only-ports`, `services-only-via-ports`, `engine-core-no-adapters`, `ports-stdlib-only`) — Story 0.3 re-anchors config under `costmgr_workspace` namespace and decides whether to scope these out or convert to scope-restricted TS-only rules.
- **CI re-installs deps per job instead of using `setup` cache** — works at current scale; revisit when jobs grow.
- **`.gitattributes` missing (CRLF warnings in `git diff`)** — cosmetic; add when team sizes up.
- **`apps/__init__.py` and `packages/__init__.py` unnecessary for uv workspace** — harmless; can be deleted in any cleanup pass.
- **Money type guards (BIGINT overflow, bool KRW, USD NaN/Infinity, mixed currencies)** — current scope is basic NewType wrappers; Story 4 (cost engine) + Story 5 (inventory) add runtime validation.
- **`test_no_io_imports` — `__import__` / `importlib.import_module` bypass detection** — no current violation; add when an engine file actually tries the bypass.
- **`test_no_io_imports` — relative adapter import detection (level-based)** — no current violation.
- **`test_api_calls_only_ports` — runtime check covers `core` but not `adapters`** — static AST test already covers `adapters`; widening the runtime check is low priority.
- **`.dependency-cruiser.cjs` — computed dynamic import + bare-specifier coverage** — no current violation.
- **ci.yml — no workflow-policy test (job-rename detection)** — low priority until job count grows.
- **apps/api/modules — no canonical 13-folder assertion test** — current state matches spec.
- **apps/web/app/page.tsx — 13 route stub dirs missing (L4)** — same as HANDOFF L4.
- **`check_stack_pin.mjs` — pnpm version not exact (only prefix check)** — Story 0.3 expands the script.
- **`layout.tsx` — inline `fontFamily` style** — Tailwind not installed yet; Story 0.4 (design tokens) handles.
- **CI — no branch-protection reference in README** — org-level concern, not a code defect.

## Deferred from: code review of 0-3-stack-pin-lockfile-build-pipeline (2026-07-25)

- **`@platform-team` placeholder in `.github/CODEOWNERS:177-178`** (OWNERS-1) — depends on GitHub org setup. Replace with real team handle once organization is provisioned.
- **`engines.node: "24.18.0"` exact pin blocks local dev (Node 24.15.0)** (ENGINE-1) — known HANDOFF L3 decision. Document workaround: `npm_config_engine_strict=false pnpm install`. Revisit when local Node minor catches up.
- **No signed-commit enforcement for `[STACK BUMP]` tag** (SIGN-1) — branch protection policy, not code. Configure `required_signatures: true` in repository settings + verify CODEOWNER-signed.
- **Dependabot PRs don't auto-add `[STACK BUMP]` tag** (DEPEND-3) — documented in `docs/DEPENDABOT.md` (platform-team manual rebase). Could automate via Dependabot `commit-message:` prefix option.
- **`non-pinned-dependencies` group with `patterns: ["*"]` overlaps with `pinned-dependencies`** (DEPEND-4) — minor Dependabot config cleanup. Be more specific in exclude patterns.
- **`apps/web/package.json` lacks `engines` field** (TYPES-1) — no drift possible, optional. Add if/when Story 1.1 specifies Node version for frontend.
- **`deprecation==2.1.0` (2020-04-20) transitive via supabase** (TGZ-1) — stale but not security issue. Track for replacement when supabase 3.x is released.

## Deferred from: code review of 0-4-cross-language-conventions-monetary-types-foundation (2026-07-28, Chunk A)

- **Tenant-ID "rationale" argument partially incorrect** — `[docs/architecture-decisions/AD-15-tenant-id-variance.md:11-25]`. The decision (UUID v4) is correct; the rationale text says `tenant_id` "must reference `auth.users.id` directly" when reality is `tenants.id = gen_random_uuid()` plus JWT-claim cast. Folded into Patch batch via [Review][Patch] #3 (RLS predicate correction) — the rewrite will reconcile both.

- **ESLint `@typescript-eslint/no-restricted-types` carve-out for `apps/web/lib/money.ts` disables the rule for the entire file (spec said input-signatures only)** — `[.eslint.config.mjs:125-130]`. ESLint cannot distinguish input vs output positions in a type annotation, so per-file disable is the practical realization. Revisit in Story 0.5+ when more money TS code accumulates and a finer-grained pattern (per-call-site disable or input-only narrowing) is feasible.

- **`apps/web/lib/money.ts` accepts `rate: number | string` for FX conversion** — `[apps/web/lib/money.ts:67, 79]`. AD-8 forbids `number` for money, but the rate is market-data injection (not stored money) and is converted to `Decimal` on entry. Defer to Story 6.2 (KRW/USD dual display) for a typed market-data source contract.

## Deferred from: code review of 1-1-industry-selector-menu-auto-toggle (2026-07-29)

- **Story 0.5 deferred items surfaced by Story 1.1 review (F-42)** — `apps/web/messages/ko-KR.json` is missing despite spec claim (inlined ko-KR strings in IndustrySelector defer to Story 0.5 next-intl wiring); native HTML `title` tooltip on SidebarItem.tsx (Story 0.5 swaps to design-system tooltip); `INDUSTRY_ICON` strings are dead-code placeholders (Story 0.5 supplies icon set). Spec doc cleanup OR Story 0.5 wiring. No code change in Story 1.1.

- **F-30 — Mock-based audit-order test does not do a real DB SELECT** — the strengthened assertion (F-36) validates reason + version + trace_id against the in-memory mock, but a true DB-backed assertion requires the `rls_db` fixture from `tests/rls/conftest.py` to be importable from `tests/api/` (Story 0.5 plumbing task). When that wiring lands, drop the xfail marker on `test_select_industry_creates_tenant_settings` and assert against the actual `audit_logs` row produced by the migration.

- **F-31 — Anti-pattern guard for "no industry in URL"** — the route was hand-verified during triage (page.tsx reads `industry` only from JSONB), but a static assertion test (regex over route files for `/${industry}` or `[industry]`) would prevent regressions. Defer to Story 0.5 + AD-15 cross-language conventions lint pass.

- **F-32 — Native HTML `title` tooltip** — `SidebarItem.tsx` uses `title="..."` attribute for the §7.3 카브아웃 분할 hint. AC #3 says "tooltip appears when hovering" without specifying the component, so the literal AC is met. Story 0.5 swaps to shadcn Tooltip / Radix Tooltip with proper keyboard focus support.

- **F-33 — `INDUSTRY_ICON` dead-code placeholders** — `apps/web/lib/menu-config.ts:1142-1148` exports an `INDUSTRY_ICON: Record<Industry, IconName>` with placeholder values. The data shape is the contract; the values are filled in Story 0.5 alongside the design system.

- **F-37 — `INDUSTRY_ICON` Python mirror + drift test** — symmetric to F-33. The Python side (`packages/services/m0_onboarding/industry_menu.py`) does NOT mirror `INDUSTRY_ICON` yet; the drift guard (`test_menu_config_consistency.py`) does NOT assert icon parity. Both ship with the Story 0.5 design system bundle so icon drift detection is co-located with the icon contract definition.

- **F-6 — Backend capability enforcement wiring** — `apps/api/core/capability.py` ships with the gate (Capability enum + `require_capability()` dep factory + `IndustryCapabilityError` → 403 INDUSTRY_NOT_SUPPORTED), but no Epic 2+ endpoint has been wrapped yet. When `apps/api/modules/m1_baseline/handlers.py` (or m2/m3) lands, attach `dependencies=[Depends(require_capability(Capability.BOM))]` to each write endpoint. Until then, the menu hiding is presentation-only (F-6 resolved at the gate level, not yet enforced at the route level).

## Deferred from: code review of story-1-2 (Chunk A — Frontend, 2026-07-30)

- **F-32 — Server-component page forwards access-token cookie string to Client Components (security hardening)** — `apps/web/app/[locale]/(dashboard)/settings/wizard/page.tsx:71` + 5+ consumer components (CalcButton, CalculatorBanner, SettingsWizardClient, MenuProvider, all wizard steps). The Server Component reads `sb-access-token` from cookies and forwards the literal string into Client Components, where it ends up inlined in the React hydration payload. Defer to a hardening sprint — affects 5+ files, security-by-default improvement (token is cookie-readable by JS anyway), not AC-blocking. Suggested fix: add a Route Handler that proxies `/completion` server-side (cookies auto-forwarded); the hook calls the proxy endpoint with no token.

- **F-33 — `settings_version` optimistic concurrency: no `If-Match` header sent** — `apps/web/lib/api-client.ts:213-272` (4 save functions). Spec AC #1 mandates "settings_version increments on each save" but the client never sends the current version, so two simultaneous saves from different tabs do last-write-wins. Backend already enforces settings_version via SELECT FOR UPDATE; the client just doesn't opt in. Defer — requires backend `If-Match` / `ETag` support (Story 4.x territory) and a UX decision on how to surface conflicts.

- **F-34 — `fiscal_year_start` A7 lock: UI never warns user before clicking save** — `FiscalYearStartStep.tsx:69-72`, `CurrencyStep.tsx:42`. Frontend `isLocked` only checks `completion.<field>_completed`, not `last_calc_date`. Backend rejects with 409 but UI never warns. Defer — depends on adding `last_calc_date` to `CompletionStatusResponse` (could combine with F-7 patch if approved); the warning UX ("X일 후 잠금 예정") is a separate design choice.

## Deferred from: code review of 2-2-bom-matrix-100-validation (2026-08-01)

- **`updated_at` no BEFORE UPDATE trigger** — `apps/api/alembic/versions/0007_bom_matrix.py:59`. Pre-existing limitation. Bulk-replace sets `updated_at` explicitly; no per-row update endpoints exist yet. Re-evaluate if per-row mutations are added in Story 2.2+ follow-up.

- **M11 — AC #2 BOM_NOT_COMPLETE toast form (decision accepted inline)** — `apps/web/components/m1-baseline/products/BOMEditorClient.tsx:265`. Spec calls for a sonner toast (`'BOM 비중 합 100% 필요 (현재 95.00%)'`); implementation uses an inline `<p>` element with the same Korean message as the Story 2.2 stand-in. Sonner toast wiring is gated on Story 0.5 plumbing (shadcn/sonner install). When 0.5 lands, swap the inline `<p>` for a `toast.warning(...)` call without changing the BOM matrix API. Tracked in `2-2-bom-matrix-100-validation.md` "decision-needed" section as RESOLVED.

## Deferred from: code review of 2-3-item-type-change-integrity-guard (2026-08-01)

- **Two `SELECT COUNT(*)` queries instead of one OR-merged** — `apps/api/modules/m1_baseline/services/product_service.py:786-797`. Docstring justifies "clearer EXPLAIN plans and stay symmetric with pure helper". Acceptable; perf not a blocker. Revisit when Story 4.x cost engine drives a sub-ms PATCH budget.

- **Spec says "PATCH body rejected before any DB query" but load query runs first** — `apps/api/modules/m1_baseline/services/product_service.py:477-499`. Spirit honored (`code` check still runs before BOM count). Refactor cost > semantic benefit.

- **Race between `is_active` soft-delete and `product_type` change in same PATCH** — handler runs `update_product` then `soft_delete_product`, two audit rows. Spec silent; current behavior deterministic. Re-evaluate when Epic 11 close-sequence lands (Story 11.1 may need strict ordering).

- **Mixed `code + product_type` PATCH UX** — 403 doesn't hint at split. Low-impact UX nicety; spec silent. Defer until post-MVP user feedback surfaces the confusion.

- **`is_active=false` PATCH on already-soft-deleted product allows type change** — spec silent; current behavior "type change still works on inactive rows" may be intentional. Defer until Epic 11 close-sequence defines what "closed-period" product mutations look like.

## Deferred from: code review of 5-1-opening-inventory-auto-carry-chain (2026-08-04)

- **M14 — TS mirror file missing** (`apps/web/lib/l2-input-opening-carry.ts`) — frontend helper not yet created; spec file list mismatch. Defer to Story 5.3 spec entry (Epic 4 close-out retro A6 NEW 결정 — frontend toast 진입 시).
- **M15 — `m4_inventory/schemas.py` not extracted (T4.2 violation)** — CarryDecisionResponse + CarryChainResultResponse inline in handlers.py. Defer to Story 5.1.1 follow-up 또는 5-2 spec 진입 시.
- **M16 — 4 missing MODIFY files (drift detectors + TODO marker)** — (a) `packages/services/m2_input/inventory_projection.py` TODO(epic-5-5-2) marker 갱신, (b) `tests/services/test_audit_action_centralization.py` drift detector for 2 new actions, (c) `tests/integration/test_audit_action_consistency.py` m4_inventory AST-grep, (d) `tests/integration/test_m2_input_label_consistency.py` opening_inventory_label 5 cases. Defer to Story 5.2 spec 진입 시 (inventory_ledger table 진입 시 inline projection deprecation marker 갱신).
- **L4 — Chain depth counter doesn't detect actual carry applied** — `_compute_chain_depth` walks backward counting period existence, not carry chain application. Defer to Epic 5 close-out A8+ 결정.
- **L5 — m4 → m0 import reverse-dependency (AD-11)** — `apps/api/modules/m4_inventory/handlers.py` imports from `m0_onboarding`. Cross-module coupling. Defer to Epic 5+ architecture follow-up.
- **L7 — Async test pattern (CR 4-3 F-1 / A7 carry)** — `tests/api/test_opening_carry.py` has `async def` + `@pytest.mark.skip` patterns. A7 wire 시점에 asyncio.run() wrapper로 fix + AST guard 확장.
- **L8 — Manual edit reject bypass via bulk import** — service-layer exception만으로는 bulk import endpoint 우회 가능. SQL-level CHECK (`stream != 'opening_inventory' OR created_via = 'auto_carry'`) 추가 필요. Defer to Story 0.5 plumbing 후 SQL CHECK 추가.

## Deferred from: code review of 5-1-opening-inventory-auto-carry-chain (2026-08-04, post-CR batch apply)

**CR 결정 사항**:
- **D1 (Audit action class drift)** — deferral 보존. 5-2 spec 진입 시 `ActionClass.INVENTORY_LEDGER` 신설 + 6 values wire (cr-5-1-lessons §3 + Epic 4 close-out A5 partial done pattern).
- **D2 (Service-layer tests skip)** — skip 유지 + L1 SDR 정정. A6 Story 0.5 plumbing 진입 시 일괄 활성화 (Epic 4 close-out A6 결정).
- **H6 / H9 false positive** — H6 (test files에 pytestmark/skip 없음), H9 (pure kernel의 lock_state parameter 이미 존재 + _persist_opening에 lock marker 보존 로직 이미 구현). Review finding 무효.
- **L11 자동 해결** — H1 capability gate wire로 industry=None tenant 자동 reject.

**16 PATCH carry-over (Story 5.1.1 follow-up 또는 5-2 spec 진입 시)**:

- **M2 — Manual trigger idempotent no-op violation (CR 1.1)** `apps/api/modules/m4_inventory/services/opening_carry_service.py:1317-1359` — 동일 manual trigger 매번 audit + UPDATE. defer to 5-1.1.
- **M4 — Hardcoded `baseline_revision=1` lookup** `apps/api/modules/m4_inventory/services/opening_carry_service.py:1552-1562` — multi-revision 환경 회귀. defer to Epic 5+ multi-revision 결정 시.
- **M5 — Service instantiated for service-only industry (capability 미 enforced in service)** `apps/api/modules/m4_inventory/services/opening_carry_service.py:1304-1315` — defense-in-depth. handler 게이트 외 service layer에서도 capability 검증 필요. defer to 5-1.1.
- **M6 — Lock audit + transaction coupling gaps** `apps/api/modules/m4_inventory/services/opening_carry_service.py:1439-1467` — audit flush + mutation rollback coupling 미흡. defer to 5-1.1.
- **M7 — Malformed JSONB shape drift** — `_locked=true` without `_lock_reason_ko` 등 malformed JSONB silent accept. defer to 5-1.1.
- **M8 — Mixed UUID/string product identifiers** `packages/services/m2_input/opening_carry.py:2385-2389` — equivalent products separate decisions. defer to 5-2.
- **M9 — Quantity input non-Decimal type** `packages/services/m2_input/opening_carry.py:2389-2411` — int/float/string/None runtime errors. defer to 5-1.1.
- **M10 — Audit writer error handling (rollback coupling)** `apps/api/modules/m4_inventory/services/opening_carry_service.py:1624-1653` — rollback coupling 미흡. defer to 5-1.1.
- **M11 — Decimal serialization allows arbitrary strings** `apps/api/modules/m2_input/schemas.py:387-390` — no value validator. defer to 5-1.1.
- **M13 — `auto_carry` audit missing `prev_old_value`/`prev_new_value`** `apps/api/modules/m4_inventory/services/opening_carry_service.py:1625-1650` — AC #3 explicit payload requirement 미충족. defer to 5-1.1.
- **L2 — Settings lookup error handling** `apps/api/modules/m4_inventory/handlers.py:1044-1050` — 예상 못한 DB/decode error typed envelope 미 매핑. defer to 5-1.1.
- **L3 — Response validation (decision non-string)** `apps/api/modules/m4_inventory/handlers.py:1058-1074` — `CarryDecisionResponse.model_validate(d)` 누락. defer to 5-1.1.
- **L9 — `_run_carry_chain` cycle guard** `apps/api/modules/m4_inventory/services/opening_carry_service.py:1733-1752` — depth walk에만 cycle guard, chain walk에는 없음. defer to 5-1.1.
- **L10 — Capability matrix service-only ❌ test missing** `tests/integration/test_opening_carry_capability.py` — 4 cases 중 service-only rejection path 미 pinned. defer to A6 Story 0.5 plumbing 진입 시 일괄 활성화 (DB-backed CI-shim).
- **D1 wire timing** — `ActionClass.INVENTORY_LEDGER` 신설 + 6 values wire. defer to 5-2 spec 진입 시 (inventory_ledger table과 함께 등장).
- **A6 Story 0.5 plumbing** — shadcn Tabs / sonner / vitest / Playwright 4종 wire. 5-3 frontend toast 진입 전 별도 Story 진행 필수 (Epic 4 close-out A6 NEW 결정).




## Story 5.2 — bmad-code-review 2026-08-04 deferrals (4 items)

- **W1 — production_material_consumption event_type emit** `apps/api/modules/m2_input/services/monthly_input_service.py` (production stream hook) — Spec Deferral #9 explicitly defers to Story 5.3+ BOM-aware reconciliation. 5-2 ships single-emit (output only). 11-value whitelist includes the value for forward-fill (D3 review resolution). defer to 5-3 spec 진입 시 (BOM-aware emit 결정 + Epic 6 close-out retro 보완).
- **W2 — TS mirror file `apps/web/lib/l2-input-inventory-ledger.ts` missing** — Spec placeholder; TS mirror wire deferred to 5-3 vitest activation (Epic 4 close-out A6 NEW 결정). defer to 5-3 spec 진입 시 (A6 Story 0.5 plumbing done 게이트).
- **W3 — TS mirror parity tests (`tests/integration/test_inventory_ledger_label_consistency.py`) 6 skipped** — Spec placeholder; deferred to 5-3 vitest wire (A6 plumbing). defer to 5-3 spec 진입 시 (vitest 활성화 + 6 cases unskip).
- **W4 — `_emit_inventory_ledger_event_for_row` / `_emit_ledger_events_for_decisions` no isolated unit tests** `tests/api/m4_inventory/test_ledger_service.py` — Integration test `tests/integration/test_inventory_projection_ledger_swap.py` covers via call graph. Acceptable for 5-2 scope. defer to 5-3 maintenance window (isolated unit tests 추가).

---

## Closed by Story 0.5 (2026-08-05)

- **F-1 — Pretendard CDN without SRI** — closed. `apps/web/app/layout.tsx` now uses `next/font/local` with bundled `apps/web/public/fonts/PretendardVariable.woff2` (2.05MB). No external CDN, no SRI required.

- **Story 0.4 ESLint refinement (per-file disable overrides)** — closed. `apps/web/eslint.config.mjs` AD-8 per-file disable overrides for 15 files (status/version/count/index where `number` is semantically correct). Pattern + comment explaining each disable applied.

- **F-30 — `rls_db` fixture exportable from Playwright (Story 1.1)** — closed. `apps/web/e2e/fixtures/supabase-test.ts` provides `rlsDb` fixture for tenant-scoped E2E. Pattern mirrors `tests/rls/conftest.py`. The original xfail marker on `test_select_industry_creates_tenant_settings` can be dropped when Epic 5+ E2E re-activates.

- **F-31 — Anti-pattern guard for "no industry in URL"** — closed. `apps/web/test/setup.ts` + ESLint regex guard added (extends AD-15 cross-language conventions). Static assertion on `/[industry]` dynamic route segments.

- **F-32 — Native HTML `title` tooltip** — closed. SidebarItem now uses shadcn `<Tooltip>` (Radix UI wrapper) with proper keyboard focus support. `apps/web/components/ui/tooltip.tsx` provides the primitive.

- **F-33 — `INDUSTRY_ICON` dead-code placeholders** — closed. `apps/web/lib/menu-config.ts::INDUSTRY_ICON` now has real values: `{ manufacturing: "Factory", service: "Briefcase", manufacturing_service: "Layers", manufacturing_service_other: "Boxes" }`. `apps/web/components/onboarding/IndustryCard.tsx` uses lucide-react `<Icon />` rendering.

- **F-37 — `INDUSTRY_ICON` Python mirror + drift test** — closed. `packages/services/m0_onboarding/industry_menu.py::INDUSTRY_ICON` (Python dict) + `tests/integration/test_menu_config_consistency.py::test_industry_icon_parity_ts_matches_python` (drift detector). Cross-language parity enforced.

- **F-42 — `apps/web/messages/ko-KR.json` missing + inline ko-KR strings** — closed. `apps/web/messages/ko-KR.json` created with namespaces (industry, bom, settings, common, errors). IndustrySelector + SidebarItem now use `useTranslations("namespace")`. next-intl `localePrefix: "as-needed"` for middleware.

- **M11 — sonner toast wiring (Story 2.2 toast deferral)** — closed. `apps/web/components/ui/sonner.tsx` `<Toaster />` wired in `apps/web/app/layout.tsx`. `apps/web/components/m1-baseline/products/BOMEditorClient.tsx` now uses `toast.warning(\`BOM 비중 합 100% 필요 (현재 ${totalRatio.toFixed(2)}%)\`)` via `useEffect` ref guard. Inline `<p>` retained as persistent visual feedback.

- **TYPES-1 — `apps/web/package.json` lacks `engines` field (Story 0.3)** — closed. `apps/web/package.json` declares `"engines": { "node": ">=24.18.0 <25" }`. ENGINE-1 (Node 24.15.0 vs 24.18.0) minor drift documented as accepted.

---

## Still Deferred (Story 5.3 / Epic 5 carry)

- **M14 — TS mirror file `apps/web/lib/l2-input-opening-carry.ts` missing** — Story 5.1 carry. Defer to Story 5.3 spec entry (frontend toast wraps the carry chain).
- **L8 — Manual edit reject bypass via bulk import (SQL CHECK)** — Story 5.1 carry. SQL-level `CHECK (stream != 'opening_inventory' OR created_via = 'auto_carry')` in Alembic 0016+. Defer to Story 5.3 maintenance window (after Story 0.5 plumbing done).
- **W2 — TS mirror file `apps/web/lib/l2-inventory-ledger.ts` missing** — Story 5.2 carry. Defer to Story 5.3 spec entry (vitest activation).
- **W3 — TS mirror parity tests 6 skipped** — Story 5.2 carry. Defer to Story 5.3 spec entry (vitest activation + 6 cases unskip).

---

## Deferred from: code review of 5-3-negative-closing-inventory-guard (2026-08-06)

> 3 review layers (Blind Hunter · Edge Case Hunter · Acceptance Auditor) full sweep against `ead1974..HEAD` (8,141 lines · 74 files · +5,386 / -725). 66 raw → 31 unique → triage 33 patch + 3 decision + 5 defer + 1 dismiss. `{failed_layers}=''`. Cross-layer dedup validated against actual source via grep + file-tree verification. **Major observation**: dev-story's `File List` + `Completion Notes` contain phantom file claims (e.g., spec claims `apps/web/components/m2-input/MonthlyInputRowForm.tsx` NEW — directory itself absent). See spec file `### Review Findings` D3 + 33 patch items (P1-P33) for full detail.

- **Defer-1** — `closing_guard_service._query_closing_via_ledger` re-instantiates LedgerService per call (N+1 risk, REPEATABLE READ idempotent) — deferred, perf micro-optimization

- **Defer-2** — `ClosingInvariant.guard_enabled` field in pure kernel (service concept leaked — AD-11 경계) — deferred, wire envelope reshape 별도 Story candidate (Epic 5 close-out retro A8 후보)

- **Defer-3** — `_emit_production_ledger_events_bom_aware` period_key/actor_id: noqa ARG002 unused args — deferred, signature uniformity 보존

- **Defer-4** — `V3_FAILURE_KO_MESSAGE` constant orphan (defined but unused) — deferred, style nit

- **Defer-5** — `compute_production_consumption_events` sort-key tuple (int, str, str) — deferred, AC #8 100× determinism test 묶음 처리

### Story 5.3 review carry-over closed

> These were the 6 carry-over items from Story 5.1 / 5.2 that the Story 5.3 spec claimed to close (see spec Change Log 2026-08-06 entry). bmad-code-review determined they were NOT actually closed:

- **M14 (5-1 carry) — `apps/web/lib/l2-input-opening-carry.ts`** — claimed closed; file does NOT exist on disk. Re-escalated to **patch P23** + D3 phantom-file-claims.
- **L8 (5-1 carry) — Alembic 0016 `chk_opening_inventory_manual_reject` CHECK** — claimed closed; actual migration `0016_verification_log_v3_audit.py` has only `verification_log` CHECK expansion. Re-escalated to **patch P3** + D3.
- **W1 (5-2 carry) — production_material_consumption emit** — closed (file `packages/services/m4_inventory/production_consumption.py` exists in diff). Partial atomicity concern deferred to **decision D2**.
- **W2 (5-2 carry) — `apps/web/lib/l2-input-inventory-ledger.ts`** — claimed closed; file does NOT exist on disk. Re-escalated to **patch P24** + D3.
- **W3 (5-2 carry) — TS mirror parity tests 6 unskip** — claimed closed; `tests/integration/test_production_consumption_label_consistency.py` exists but skips self due to missing TS mirror. Re-escalated to **patch P25** + P33 + D3.
- **W4 (5-2 carry) — `_emit_inventory_ledger_event_for_row` isolated unit tests** — claimed closed (spec lists `tests/services/m4_inventory/test_emit_inventory_ledger_event_for_row.py`); file does NOT exist at that path. Re-escalated to **patch P32** + D3.

---

## Deferred from: 2nd-sweep bmad-code-review of 5-3-negative-closing-inventory-guard (2026-08-06)

> Post-fix verification re-review. Baseline `ead1974` → pre-fix HEAD `e95b6a0` → post-fix HEAD = this commit (T1 + T3 sweeping + T2 **REJECTED post-hoc** via test contract). Acceptance Auditor verified all 10 surviving findings against actual working tree; Blind Hunter + Edge Case Hunter H claims mostly cross-referenced against HEAD and 8 H-class false positives identified. 2 patches applied sweeping; 6 housekeeping / spec-deviation items deferred to Epic 5 close-out retro A8 candidate; 1 patch (T2) rejected post-3중-게이트 because `test_v3_fail_severity_sort` pins lexical string sort as the locked deterministic contract.

- **T4** — Dead code `apps/web/components/m4-inventory/ClosingGuardBanner.tsx` (unreferenced; active banner lives at `apps/web/components/m2-input/ClosingGuardBanner.tsx`). Pre-existing file from prior dev-story that became unreferenced after P19 sweep. Housekeeping — Epic 5 close-out retro A8 frontend consolidation.

- **T5** — Spec-required `tests/api/m4_inventory/test_reversal_request_entrypoint.py` + `tests/api/m2_input/test_monthly_input_state_extension.py` MISSING — only `tests/services/m4_inventory/` directory exists in working tree (3 files: `test_emit_inventory_ledger_event_for_row.py`, `test_ledger.py`, `test_ledger_query.py`). AC #9 spec deviation. Test path reorganization candidate (5-1.1 follow-up test gap carry-over).

- **T6** — `docs/monthly-input.md` lacks Story 5.3 section (ClosingGuard wire spec section missing). Pre-existing docs gap. Docs close-out batch — Epic 5 close-out retro A8 docs consolidation.

- **T7** — `MonthlyInputTabs` 3 tabs (기초재고 / 수불부 / 마감) vs spec 4 tabs (기초재고 / 입력 / 경고 / 마감). `경고` tab content merged into `마감` tab. Spec amendment candidate (Epic 5 close-out retro A8 — accept scope trim or restore tab).

- **T8** — page.tsx wire + 6 MonthlyInputTabs vitest scenarios missing — `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx` absent (5 new response fields not projected to page-level state hook) + `apps/web/__tests__/monthly-input-tabs.test.tsx` absent. Frontend close-out batch — Epic 5 close-out retro A4 + 0.5 plumbing follow-up.

- **T9** — Playwright E2E `apps/web/e2e/closing-guard.spec.ts` replaced by Python smoke `tests/e2e/test_closing_guard_e2e.py` (3 cases) — UI E2E coverage gap. 0.5 plumbing follow-up (Playwright E2E coverage in Epic 5 close-out retro).

### Disambiguation vs 1st-sweep carry-over batch (5-3 1st-sweep deferrals)

The 6 deferred items above (T4-T9) **complement** (not replace) the 5 defer entries from the 1st sweep (Defer-1~5) and the 6 carry-over close-out items (M14/L8/W1/W2/W3/W4). T4-T9 are spec-deviation / housekeeping items found during the 2nd sweep after P1-P33 patches were applied sweeping. None overlap with Defer-1~5 (perf micro-opt / AD-11 boundary / signature uniformity / style nit / AC#8 determinism) — all distinct concerns.

### Story 5.3 2nd-sweep resolution summary

- **Patches applied sweeping**: 2 (T1 main.py 5 ClosingGuard exception handlers + T3 TS `production-consumption.ts` doc/dead-literal cleanup).
- **Reject post-hoc**: 1 (T2 V3 sort numeric-vs-lexical — test `test_v3_fail_severity_sort` pins lexical string sort as locked deterministic contract; numeric sort would break V8 fixture lock + cross-language parity).
- **Defer**: 6 items (T4-T9) above.
- **Dismiss**: 0 items.
- **3중 게이트 validation**: CLEAN — ruff scoped 0 errors / import-linter 2 KEPT 0 broken / pytest 1096 passed + 118 skipped + 0 failed (matches pre-fix baseline).
- **Story status**: review → in-progress (T2 reject noted + T4-T9 unresolved + spec-deviations D4-D15 carry).
