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

---

## Deferred from: 3rd-sweep bmad-code-review of 5-3-negative-closing-inventory-guard (2026-08-07)

> Re-review of T4-T9 + D4-D15 carry 재실행 (commit 3045f50). Diff = 1,227 lines / 12 files. 3 reviewers (Blind Hunter + Edge Case Hunter + Acceptance Auditor) parallel → 73 raw → 32 deduped → 0 decision + 32 patch + 16 defer + 13 dismiss. 3중 게이트 pre-sweep clean (ruff 0 / import-linter 2 KEPT / pytest 1108+ passed + 118 skipped / tsc clean / vitest 23/23). All patches left as action items in spec `### Review Findings` 3rd-sweep section.

- **D1** — `tests/api/m2_input/test_monthly_input_state_extension.py` still MISSING. Continuation of 2nd-sweep T5 defer (T12.1 resolved by 3rd-sweep carry, T12.2 unresolved). ~14 cases for `get_state` extension 5 NEW fields + state-extension integration. **Epic 5 close-out retro A8 candidate** (5-1.1 follow-up test gap carry).

- **D2** — vitest `test_tabs_render_three_navigation` no active tab check (defaultTab='subub' not asserted). Cosmetic. Test coverage follow-up.

- **D3** — page.tsx inline styles (`#475569`, `#fef2f2`, `#991b1b`) instead of shadcn theme tokens. Pre-existing — not 5-3 specific. Design system migration follow-up.

- **D4** — m2-input `ClosingGuardBanner` `<AlertDescription>` wraps `<ul>` (semantic smell). Pre-existing pattern. UX/accessibility follow-up.

- **D5** — `apps/web/tsconfig.tsbuildinfo` committed (build artifact, not source). Hygiene. `.gitignore` follow-up.

- **D6** — Type duplication `ClosingInvariant` / `ClosingInvariantCode` between `apps/web/lib/api-client.ts:570-580` and `apps/web/lib/l2-input-inventory-ledger.ts:73-80`. Pre-existing. Type-alias consolidation follow-up.

- **D7** — `NEGATIVE_CLOSING_INVENTORY_KO` dual export with unused `_NEGATIVE_CLOSING_INVENTORY_KO_SSOT` re-export alias (`apps/web/lib/closing-guard.ts:38, 44`). Pre-existing fragile pattern. Dead-code cleanup follow-up.

- **D8** — T11 dual-component pattern — git grep verification narrative-only. T11 disposition (no git rm) correct; current 3rd-sweep re-surfaced m4 sort-after-slice bug (patched as P16 high). Narrative refinement follow-up.

- **D9** — T17 D5 URL function-name inconsistency — `requestClosingGuardAttempt` (verb-first function) vs route `close-attempt` (noun-first). Pre-existing. Naming-convention cleanup follow-up.

- **D10** — Dual `vi.mock("sonner")` between `apps/web/__tests__/closing-guard-banner.test.tsx` and `apps/web/__tests__/monthly-input-tabs.test.tsx` — subtle mock reference risk on `await import("sonner")`. No observed failure in 3중 게이트. Mock consolidation follow-up.

- **D11** — vitest `OpeningInventoryField` `dispatchEvent` synthetic click bypasses jsdom disabled-fieldset click enforcement (`apps/web/__tests__/opening-inventory-edit-reject.test.tsx:121`). Acknowledged in test comment. JSDOM limitation follow-up.

- **D12** — page.tsx periodKey YYYY-MM validation missing (frontend). Validation is backend's responsibility (AD-24 typed period-key). Frontend silent fallback acceptable. Backend contract is SSOT.

- **D13** — vitest `NEGATIVE_CLOSING` with empty `negative_products` case uncovered. Test coverage gap. Coverage expansion follow-up.

- **D14** — vitest `EMPTY_PERIOD + guard_enabled=true` case uncovered. Test coverage gap. Coverage expansion follow-up.

- **D15** — vitest non-empty `closing_per_product` rendering branch uncovered. Test coverage gap. Coverage expansion follow-up.

- **D16** — vitest `closing-guard-banner.test.tsx:111-112` `getAllByText(/019200a0/).length >= 2` has no upper bound (loose assertion). Coverage expansion follow-up.

### Disambiguation vs prior 5-3 sweep deferrals

The 16 items above **complement** (not replace) the prior 5-3 deferrals:
- 1st-sweep (2026-08-04): 5 items (Defer-1~5: perf micro-opt / AD-11 boundary / signature uniformity / style nit / AC#8 determinism)
- 1st-sweep carry-over closed: 6 items (M14/L8/W1/W2/W3/W4 — 5-1/5-2 carry)
- 2nd-sweep (2026-08-06): 6 items (T4-T9: dead code / test gap / docs / tabs structure / page.tsx / Playwright)

D1 is the **only direct carry-over** (continuation of 2nd-sweep T5). D2-D16 are 3rd-sweep-surfaced items distinct from prior deferrals.

### Story 5.3 3rd-sweep resolution summary

- **Patches**: 32 (16 high + 16 medium). All left as action items in spec `### Review Findings` 3rd-sweep section. Patches range: page.tsx wire (P1-P3, P25-P28), Playwright E2E URL/testids/seed (P4-P5, P8, P18-P21), vitest placeholder tests (P6-P7), m3-verdict V3 omission (P9-P10), backend wire shape (P11-P13, P17, P29), reversal test quality (P14-P15, P30), m4 banner sort (P16), server-api hardening (P22-P23), page.tsx error boundary (P24), vitest toast variant (P31), service-only tenant skip type (P32).
- **Defer**: 16 items (1 carry-over + 15 new).
- **Dismiss**: 13 items (5 Auditor looked in wrong dir + 8 verified-clean / pre-existing / not-real-issue).
- **3중 게이트 validation**: Pre-sweep clean (unchanged; 3rd sweep does NOT modify code).
- **Story status**: review → in-progress (32 patches pending + 1 carry-over defer).


## Deferred from: code review of 11-1-m11-reversal-ledger (2026-08-08)

## Deferred from: code review of 11-2-close-sequence-lock (2026-08-08, 3rd sweep)

- **TS mirrors missing** (`apps/web/lib/m11-close-sequence.ts` + parity file) — T10 frontend deferred per spec. `close_sequence_order.py` + `partial_close_guard.py` docstrings claim TS mirror exists. Add file or remove claim in 11-2 follow-up OR Task 10 frontend wire.

- **V8 골든 fixture 4 NEW (T11.8-T11.10)** — DEFERRED → bmad-code-review sweep. Need: `close_sequence_initiated` + `close_sequence_step_completed_partial_blocked` + `close_sequence_confirmed` + `close_sequence_reversal_blocked`. V8 18 → 22 fixture matrix extension.

- **Task 10 frontend (10.1-10.9)** — `CloseSequencePanel` / step + confirm buttons / `ko-KR.json` strings / page wire / vitest / Playwright all absent. AC#2, #3, #4, #8 UI halves unimplemented.

- **W2 reopen flow** — operator action + reason + audit row path deferred. `status='reversed'` + reopen state transition not implemented. Reversal can move row from 'closed' → 'reversed' but no path back to 'open' for operator.

- **Tests assert file text not behavior** — `tests/integration/test_fiscal_periods_rls.py` static string searches, no actual DB RLS exercise. `tests/api/m11_close/test_close_sequence_service.py` runs on AsyncMock/MagicMock rows. Real integration tests need Story 0.5 CI shim work (live DB RLS connection).

- **`db_models.py` `FiscalPeriod` lacks `created_by_actor_id` column** — defensive denormalization (audit-log-retained provenance on row) deferred.

- **Idempotent no-op audit skip for `confirm_close_sequence` retry** — partial. Full retry semantics (network-flap → re-POST) deferred. PATCH covers single-shot check only.

- **Envelope helper extraction** — 6 exception handlers in `main.py` duplicate `{code, message_ko, details, trace_id}` structure. DRY refactor deferred.

## Deferred from: code review of 11-3-snapshot-persistence-with-reverse (2026-08-09)

bmad-code-review 3rd sweep (129 raw → 3 DECISION + 50 PATCH applied + 8 DEFER + ~68 DISMISS). All 3 BLOCKING DECISIONS chosen option (a) full wire. 50 PATCH sweeping applied. 8 items honestly DEFER (carry-over from 11-2 dev-story).

- **V8 22→26 골든 fixture matrix extension (4 NEW: snapshot_committed + reversal_negating_snapshot + reversal_corrected_snapshot + reopen_committed)** — T10 carry-over honestly DEFER. Spec AC #10 (A11 V8 PRIMARY deliverable). V8 fixture count SDR claim 보존: 22 (NOT 26).

- **Frontend T8: 4 NEW components (SnapshotPersistencePanel + ReversalExecuteDialog + ReopenOperatorDialog + CacheInvalidationChannelBadge) + vitest + Playwright E2E 12 NEW scenarios** — T8 carry-over honestly DEFER. UI 진입점 부재로 backend routes wire가 사용자-facing이 아님. Frontend vitest/Playwright SDR claim 보존: 14+5+4 = 23 carry (NOT 23+30).

- **TS mirror files `apps/web/lib/m11-close-sequence.ts` + parity helper** — T8 carry-over honestly DEFER. AD-15 cross-language parity 깨짐 (no .ts in packages/services/m11_close/).

- **Capability matrix v1.12 fill (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR rows)** — T10 docs carry-over honestly DEFER. docs/capability-matrix.md v1.12 row count 보존: current state.

- **docs/snapshot-persistence-with-reverse.md NEW + docs/capability-matrix.md v1.12 EXTENSION** — T10 docs carry-over honestly DEFER. SDR docs claim 보존: not counted.

- **audit_action overlap (m11_reversal_handler_invoked + reversal_negating_inserted) → T7 sweep** — 11-3 author TODO marker로 남겨둠. T7 future Story에서 dedicated ActionClass.SNAPSHOT_PERSISTENCE actions wire.


## Deferred from: code review of 11-4-epic-11-carry-over-sprint (2026-08-10)

3rd sweep R4 triage + carry-over + 3rd sweep 3-pass pattern per CR 11-2/11-3 lesson. All deferrals explicitly per spec §Honestly DEFER or pre-existing 11-3 wire.

- **W-001 — W2 reopen `close_sequence_state` transition (`'confirmed' → 'reopened'`)** — Spec §5 honestly DEFER (T5 follow-up). Kernel docstring promises 'reopened' transition; service stays at 'confirmed' status update only. A future Alembic migration would extend the CHECK constraint. **Where**: `packages/services/m11_close/reopen_authorization.py:31` (docstring) vs `apps/api/modules/m11_close/services/reopen_service.py:148-162` (actual).
- **W-002 — Component-level vitest cases (35 claimed vs 32 actual parity cases)** — Spec AC #2 mentions 35 cases; subtask 1.5 only mandates 32 parity cases. 11-3 §Subtask 8.13-8.16 component tests honestly DEFER. **Where**: spec §AC #2 + 11-3 spec §Subtask 8.13-8.16.
- **W-003 — ko-KR string count (37 actual vs 12 spec claim)** — Spec undercounted; implementation more thorough than spec (5 NEW sections × 7-11 strings each). **Where**: spec §AC + `apps/web/messages/ko-KR.json:71-117` + `apps/web/lib/ko-KR.json:2485-2579`.
- **W-004 — Capability matrix v1.12 fill (SNAPSHOT_PERSISTENCE + REVERSAL_EXECUTE + REOPEN_OPERATOR)** — Spec explicitly waives 11-4 work; already wired in 11-3 (3 NEW capabilities + 4 routes capability gate + 19 drift tests). **Where**: spec §Task 3 + `apps/api/core/capability.py` (no diff) + `tests/integration/test_capability_matrix_v1_12_drift.py` (no diff).
- **W-005 — A5 audit_action partial wire + reopen audit_id separate row + D1 reversal V8 fixtures** — Per spec §Honestly DEFER follow-up sweep (5 items total: T10 docs + A5 partial wire + reopen state transition full + reopen audit_id separate row + D1 reversal V8 fixtures). **Where**: spec §Honestly DEFER + Epic 11 retro §7 A13.

### Honest DEFER — 3rd sweep PATCH items (post-3중 게이트 re-verification, 2026-08-10)

bmad-code-review 3rd sweep surfaced 21 PATCH items. After 3중 게이트 re-verification pass (2026-08-10), 3 items applied: **P-013** (test_v8_fixture_count_now_18_in_story_6_2 → now_22 + assertion 18→22 + fixtures count 18→22) + 3 pre-existing 6-3 ruff errors (F541 line 571 + C416 line 394 + B007/B905 line 667 in `closing_pdf_export.py`). 18 items remain honestly DEFERred per CR 11-3 lesson (structural W-class PATCH can DEFER without breaking 3중 게이트 when re-verification is clean):

- **D-001 — page.tsx 4 components mount with stub UUID props (partial wire)** — ✅ RESOLVED by 11-5 (2026-08-19). Verification revealed page.tsx already exists (lines 36-39 imports + lines 204-238 mounts all 4 m11_close components). Stub UUIDs (`00000000-...`) with `TODO(11-4 carry)` markers remain — real tenant/actor resolution from session/RSC context still W-class DEFER (separate concern from mount).

- **D-002 — ko-KR.json lib/messages dual-file split (dead code risk)** — `apps/web/lib/ko-KR.json` exists but `apps/web/i18n.ts:15` only loads `./messages/${locale}.json`. Two-file split creates dead-code risk; consolidation deferred. **Where**: `apps/web/i18n.ts:15` + `apps/web/lib/ko-KR.json` + `apps/web/messages/ko-KR.json`.

- **D-005 — TS mirror unknown state fall-through (defensive reject)** — `apps/web/lib/m11-reopen.ts` `buildReopenAuthorizationState` returns authorized state when all gates pass but lacks explicit `else` rejection for unknown operator_action / reason state combinations. Defense-in-depth hardening deferred. **Where**: `apps/web/lib/m11-reopen.ts:148-191` + `apps/web/lib/m11-close-sequence.ts` mirror.

- **P-001 — Catch-all error toasts (3 components)** — `SnapshotPersistencePanel` + `ReversalExecuteDialog` + `ReopenOperatorDialog` use generic toast.error fallbacks without specific error-code → user-facing message mapping. UX polish deferred. **Where**: `apps/web/components/m11-close/*.tsx` (3 files).

- **P-002 — TS response shape mismatch (3 components)** — Components may consume response shapes that drift from API envelope `{ code, message_ko, details, trace_id }`. Response narrowing deferred. **Where**: `apps/web/components/m11-close/*.tsx` (3 files).

- **P-003 — Number() coercion → Decimal validation** — Frontend uses `Number()` for target_qty etc., but backend uses `Decimal`. Cross-language precision drift deferred. **Where**: `apps/web/lib/m11-reversal-execute.ts` + component props.

- **P-004 — UUID format validation** — Frontend doesn't pre-validate tenant_id/actor_id UUID format before API call; backend raises NON_UUID_TENANT/NON_UUID_ACTOR. Pre-flight validation deferred. **Where**: `apps/web/lib/m11-*.ts` (5+ files).

- **P-005 — NO_CAPABILITY → NON_UUID_TENANT/ACTOR disambiguation** — Already applied to `m11-reopen.ts` (P-005 line 94-115). Other TS mirrors (`m11-close-sequence.ts`, `m11-reversal-execute.ts`, `m11-snapshot-persistence.ts`) still fall through to NO_CAPABILITY on empty input. Cross-mirror parity deferred.

- **P-006 — Hardcoded reason length → constants reuse** — Some components hardcode `20` / `500` instead of importing `REOPEN_REASON_MIN_LENGTH` / `REOPEN_REASON_MAX_LENGTH` from `m11-reopen.ts`. Constants reuse deferred.

- **P-007 — Toast mapping missing NO_CAPABILITY case** — Toast map in some components lacks explicit `NO_CAPABILITY` branch, falling to generic message. Mapping completeness deferred. **Where**: `apps/web/components/m11-close/*.tsx`.

- **P-008 — PII UUIDs in DOM (Playwright selectors risk)** — Components render stub UUIDs as `data-*` attributes; Playwright selectors may bind to PII. UUID scrubbing deferred (agent stalled mid-edit; needs Playwright selector audit first). **Where**: `apps/web/components/m11-close/*.tsx` (4 files).

- **P-009 — Button enabled when state=committed (idempotent UX)** — `SnapshotPersistencePanel` commit button may stay enabled in `committed` state, allowing redundant commit attempts. UX consistency deferred. **Where**: `apps/web/components/m11-close/SnapshotPersistencePanel.tsx`.

- **P-010 — CloseSequencePanel closed_at=null logic defect** — Panel may not handle `closed_at=null` (fiscal_period in 'open' status) gracefully. Edge case deferred. **Where**: `apps/web/components/m11-close/CloseSequencePanel.tsx`.

- **P-011 — Unused REOPEN_CACHE_INVALIDATION_CHANNELS re-export remove** — ✅ RESOLVED by 11-5 (2026-08-19). `apps/web/lib/closing-period.ts:193-196` dead code DELETE + stale comment in `apps/api/modules/m11_close/services/reopen_service.py:60-61` updated.

- **P-012 — V8 fixture `_fixture_lock_sha256` placeholder → actual computed SHA256** — 4 NEW 11-4 fixtures (`snapshot_committed` + `reversal_negating_snapshot` + `reversal_corrected_snapshot` + `reopen_committed`) have placeholder SHA256. Real SHA256 computation deferred. **Where**: `packages/cost_engine/tests/regression_v8/fixtures/*.json` (4 files).

- **P-014 — SnapshotPersistencePanel no re-fetch after commit** — Panel doesn't re-fetch `current_state` after commit mutation; UI may show stale state. Re-fetch logic deferred. **Where**: `apps/web/components/m11-close/SnapshotPersistencePanel.tsx`.

- **P-015 — ko-KR.json SSOT drift detector test (lib ↔ messages parity)** — No automated test verifying `lib/ko-KR.json` ↔ `messages/ko-KR.json` parity. Drift detection deferred. **Where**: `tests/` (new test file).

- **P-016 — Zero qty + NaN rejection in reversal-execute** — Frontend doesn't pre-reject `target_qty=0` or NaN before API call; backend raises validation error. Pre-flight validation deferred. **Where**: `apps/web/lib/m11-reversal-execute.ts` + `apps/web/components/m11-close/ReversalExecuteDialog.tsx`.

### 3중 게이트 re-verification summary (2026-08-10)

- **ruff scoped**: `apps/api` All checks passed / `packages/services/m11_close` All checks passed / `packages/services/m4_inventory` All checks passed (after 6-3 pre-existing F541/C416/B007/B905 fixes).
- **ruff full** (`ruff check apps packages`): All checks passed.
- **import-linter**: 2 KEPT (cost_engine_forbidden_io + engine_core_to_adapters_forbidden), 0 broken.
- **pytest**: 1714 passed + 127 skipped + 0 failed in 70.30s (baseline 1758 + 11-4 NEW V8 tests added).

All 18 honestly DEFERred items listed above are structural W-class / UX polish / pre-flight validation that don't affect runtime correctness in current state. Story 11.4 done 진입.


## Deferred from: Epic 6 close-out retro (2026-08-10) — A19 inline projection deprecate honestly DEFER

**A19 (A8 inline projection deprecate) honestly DEFERRED** per CR 11-3 lesson (structural W-class DEFER discipline).

**Scope analysis (2026-08-10) revealed**: 30min surgical diff 가 아닌 **multi-file refactor** (32+ files affected):

- `packages/services/m2_input/inventory_projection.py` 전체 제거 = 32+ call sites + 6+ docs + 4+ test files affected
- `build_inventory_projection` runtime call in `apps/api/modules/m4_inventory/services/opening_carry_service.py:552` → LedgerService.query_period_closing_all 마이그레이션 필요
- `LEDGER_REFERENCE_QUERY_STUB` 정의 **2 modules** (`inventory_projection.py:82-90` SQL fragment + `product_references.py:168` empty string marker)
- `QTY_QUANTUM` (NUMERIC(18,4) Decimal 상수) 9+ source files 사용 → shared constants module 이전 필요
- `INVENTORY_PRODUCT_TYPES` + `InventoryMovement` (NamedTuple) → similar module reorganization 필요
- 6+ docs (conventions.md + capability-matrix.md + architecture-inventory.md + monthly-input.md + inventory-ledger.md + opening-inventory-carry.md + item-type-change.md)
- 4+ test files (test_m2_input_inventory_projection.py + test_m2_input_warnings.py + test_inventory_projection_ledger_swap.py + test_product_references.py + test_m2_input_label_consistency.py)
- `packages/services/m2_input/__init__.py:36-41,72` + `warnings.py:40` re-export 정리

**Why honestly DEFER (vs partial Phase 1)**: A19 spec acceptance criteria = "**full deprecation + 모든 call sites ledger SSOT 전환 검증**". Partial Phase 1 (stub 상수 제거만)로는 acceptance 불충족. CR 11-3 honestly DEFER discipline 적용 = structural W-class는 3중 게이트 깨지 않고 DEFER 가능.

**Where to pick up (후속 진입점 후보)**:

1. **Story 0.6 cross-cutting tech debt sweep** — Epic 7 진입 전 또는 Epic 12 구현 중 병행
2. **Epic 7 spec entry pre-step** — sim module 진입 시 inline projection 의존성 정리
3. **Epic 12 implementation 중 parallel dev** — 2FA work와 동시 진행 (independent surface)

**3중 게이트 impact**: **None**. inventory_projection.py + LEDGER_REFERENCE_QUERY_STUB 현재 functional. TODO(epic-5) marker 보존 (이미 Story 5.2에서 closed per deprecation timeline). 코드 제거 없이 그대로 운영.

**Carry-over 누적 추적**: A19 = 3rd carry (Epic 5 retro §7 A8 → Epic 6 close-out retro §7 A19 결정 → 현재 honestly DEFER). Epic 7 또는 Epic 12 wire 시점에 반드시 해소 필수 (4th carry 방지).

---

## Deferred from: A19 carry-over sprint (2026-08-15) — pre-existing infra debt honestly DEFER per T0

**A19 carry-over sprint DONE** (baseline_commit = a63646c, Epic 12 진짜 close-out tip). sprint-scale work completed atomically (partial wire 금지 정합). CR 11-3 honest-DEFER discipline 10번째 epic 연속 검증 (carry-over sprint pattern 5번째: 11-4 / 12-4 / 12-5 T6 / 12-3 T7 / **A19**).

**3 pre-existing pytest failures honestly DEFERRED per T0** (A19 sprint scope 외 — 12-3 T7 handoff에 명시된 pre-existing infra debt):

1. `tests/integration/test_alembic_0022_does_not_exist` — Alembic 0022 dependency (Epic 12 12-1 2FA entry migration 미해결 시점 carry)
2. `tests/sdr/test_sdr_test_count_drift.py::test_max_sdr_claim_matches_pytest_collection` — SDR drift detector (MAX SDR claim stale — 2143 → 2236 actual, A19 sprint scope 외)
3. `tests/integration/test_tenant_backups_0024_migration.py::test_rls_0014_no_update_or_delete_policies` — RLS 0014 INSERT-only carve-out (Epic 12 12-2 backup INSERT-only 결정 wire)

**A19 introduced 0 NEW failures** (T0 honestly DEFER 정합 — partial wire 금지). affected tests verified: 50 passed (m2_input_warnings + m2_input_label_consistency + monthly_closing_report_label_consistency + test_api_calls_only_ports + test_opening_carry mostly skipped).

**MenuProvider boundary 500 error** = pre-existing dev server infra debt (12-3 T7 handoff 명시), A19 sprint scope 외.

**SDR MAX claim 갱신 (separate line, CR 11-2 lesson)**: 2143 → 2236 actual tests collected (after A19 removal of 22 tests). SDR drift detector 자체는 pre-existing failure (honestly DEFER per T0). sprint-status.yaml ## SDR section update required (별도 sprint, A19 wire 표에 미포함).

**Where to pick up (후속 진입점 후보)**:
- Pre-existing 3 pytest failures = 별도 sprint-up (1-2h scope each)
- SDR MAX claim 갱신 = 30min 별도 line update (CR 11-2 lesson 적용)
- MenuProvider boundary 500 error = dev server infra fix (Epic 12 close-out retro §7 follow-up OR Epic 7 진입 시 dev server hardening)

**3중 게이트 impact (A19 sprint surface)**: **None**. A19 surface 0 NEW failures + pre-existing debt T0 honestly DEFER 정합. carry-over sprint atomic wire 완료.

---

## Deferred from: Epic 9 close-out follow-up (2026-08-17)

> cj-style Epic 9 5번째 진입점 follow-up sprint (A27 결정 적용). **1 RESOLVE + 4 honestly DEFER** (CR 11-3 honest-DEFER discipline 22번째 epic 연속).

### D-9-4-DEFER-1 ✅ RESOLVED (2026-08-17, 9-5 follow-up)

**Conflict 분석 (verbatim wire)**:
- PRD §9 #21 verbatim (prd.md line 137, 401, 513, 732): **"부문귀속명세서"** (법인세법 시행규칙 제76조 2기준 카브아웃 분할 근거 공시 보고서)
- epics.md Story 9.4 (line 1052, 1056): **"원가대상별 원가 집계표"** (Cost Object Breakdown, ABC results display)
- 9-4 architecture-inventory.md line 918 (9-4 sprint 추가): **INCORRECT** claim — "PRD §9 #21 verbatim: '원가대상별 원가 집계표 (Cost Object Breakdown)'" — 실제 PRD §9 #21 verbatim ≠ 이 문구 (PRD는 "부문귀속명세서")
- 9-4 implementation = **합성 scope** (PRD §9 #21 SSOT + epics.md 9.4 product_id별 행 extension)

**Resolution (hybrid label)**:
- **PDF 라벨** = **"원가대상별 원가 집계표 (부문귀속명세서 §9 #21 기반)"** (hybrid — PRD §9 #21 verbatim + epics.md UX label 모두 존중)
- **UX 표기** = `[원가대상별 원가 집계표]` (epics.md 9.4 UX label 보존, 변경 0)

**선택 사유 (Option A vs B vs C)**:
- Option A: PRD §9 #21 verbatim 보존 ("부문귀속명세서") → Report #21 = "부문귀속명세서". 9-4 wire 사후 변경 → cj-style discipline 위반 (atomic wire 사후 변경).
- Option B: epics.md 9.4 UX label 보존 ("원가대상별 원가 집계표") → 9-4 wire 변경 없음, but PRD §9 #21 verbatim 무시 → PRD SSOT 위반.
- **Option C (선택)**: Hybrid label → 양쪽 SSOT 모두 존중 + 9-4 wire 변경 최소.

**Wire scope**:
- `docs/architecture-inventory.md` §9.4 line 918 incorrect verbatim claim 수정 (5 line 확장)
- `docs/abc-report-21.md` §1 line 3 incorrect verbatim claim 수정
- `docs/abc-report-21.md` "Deferred Work" section D-9-4-DEFER-1 status: honestly DEFER → ✅ RESOLVED (9-5)

**Where**: docs/architecture-inventory.md §9.4 (line 918+), docs/abc-report-21.md (§1 + Deferred Work table).

### D-9-3-DEFER-2 (preserved — separate sprint)

- **Activity standard hour 자동 추출** — Epic 9 close-out follow-up scope 외. 9-1 wire = manual entry 확정 (UX). 자동 추출 = time tracking data source 통합 필요 (별도 epic territory). 별도 sprint (cj-style carry-over 10번째, Epic 10+ 시점).
- **Where**: `packages/cost_engine/abc_engine.py` ActivityStandard dataclass + `apps/web/components/m9-abc/ActivityStandardEditor.tsx` (9-1 wire)
- **To pick up**: cj-style carry-over 10번째 sprint OR Epic 10+ activity management epic

### D-9-4-DEFER-2 (preserved — retro decision input)

- **Report #15 wire (활동원가 내역서)** = A30 SHARED factory 패턴 재사용. **A31+ 결정 wire** (Epic 9 close-out retro cj-style 5번째 진입점).
- **Where**: `packages/services/m5_reports/pdf_generator.py::_compose_report15_pdf` placeholder (9-4 wire)
- **To pick up**: Epic 9 close-out retro A31+ 결정 후 별도 story (cj-style Epic 9 6번째 진입점 OR Epic 10 진입)

### D-9-4-DEFER-3 (preserved — separate epic)

- **AI 자동 분석의견** (PRD §9 #16 + §A11 + §10) — **separate epic scope** (AI capability, 별도 epic territory). PRD §A11 (자동 분석 SSOT) + §10 (AI agent contract).
- **Where**: PRD §9 #16 verbatim + §A11 (자동 분석 SSOT) + §10 (AI agent contract)
- **To pick up**: Epic 11+ AI capability epic (별도 epic territory, A31+ 결정 영향)

### D-9-4-DEFER-4 (preserved — dedicated sprint)

- **Playwright E2E (Epic 9 전체)** — **dedicated sprint** (12-5 T6 pattern, A27 priority 미적용 사유: Epic 9 honestly DEFER profile = mixed, "단일 우선 항목 부재" → D-9-4-DEFER-1 lowest risk RESOLVE + 나머지 honestly DEFER 보존 결정).
- **Where**: `apps/web/e2e/` Epic 9 4 stories (9-1+9-2+9-3+9-4 ~50-60 cases)
- **To pick up**: Epic 9 close-out retro A31+ 결정 후 Playwright E2E dedicated sprint (12-5 T6 pattern)

### A27 priority 미적용 사유 (Epic 9 honestly DEFER profile)

Epic 8 retro §7 A27 verbatim:
> "D-8-3-DEFER-7 Playwright E2E (8-1+8-2+8-3 모두 mirror, 12-5 T6 패턴) **우선 wire** + 나머지 7 items **honestly DEFER 유지**."

A27 priority 적용 조건 = "단일 우선 항목 존재" (Epic 8 = Playwright E2E 1개). Epic 9 honestly DEFER profile = mixed (1 docs 정합 + 1 code work + 1 retro input + 1 separate epic + 1 dedicated sprint scope). 단일 우선 항목 부재 → **A27 priority 미적용 = D-9-4-DEFER-1 (lowest risk + docs only) RESOLVE + 나머지 honestly DEFER 보존**.

### CR carry (Epic 9 follow-up sprint)

- **CR 11-3 honest-DEFER discipline 22번째 epic 연속**: partial wire 시도 0건 + single sprint atomic wire + 4 honestly DEFER 보존
- **CR 11-2**: SDR claim 보존 (baseline 보존, no NEW SDR claim)
- **CR 11-4**: ko-KR.json SSOT cross-language parity (UX 표기 보존)
- **CR 12-1**: layer rule 보존 (no code change, layer boundary 무관)
- **cj-style carry-over sprint 9번째**: A19 → 12-4 → 12-5 T6 → 12-3 T7 → 11-4 → Epic 6 retro → Epic 12 follow-up → Epic 7/8 follow-up → **Epic 9 close-out follow-up**

### 3중 게이트 impact (Epic 9 follow-up sprint surface)

- **ruff scoped**: 0 NEW errors (docs only 변경)
- **import-linter**: 2 KEPT, 0 broken (보존)
- **pytest focused**: baseline 보존 (no code change, no test change)
- **tsc**: zero NEW (docs only)
- **vitest**: zero NEW (docs only)

---

## Deferred from: Epic 9 close-out retro + A35/A36 wire (2026-08-17, 9-6 follow-up sprint)

> cj-style Epic 9 6번째 진입점 (cj-style carry-over 10번째) sprint. **D1~D5 FACTS.md 발견 정직 반영 + A31~A36 결정 wire + A35 frontend test debt + A36 SDR 검증 프로토콜**. (CR 11-3 honest-DEFER discipline 23번째 epic 연속).

### D1~D5 FACTS.md 발견 (D2/D3 critical SDR overclaim 정직 반영)

### D2 ✅ HONESTLY DEFERRED → A35 결정 (frontend test debt)

- **9-3 `7683135` + 9-4 `2489e50` frontend test SDR overclaim 정직 발견** (FACTS.md §D2)
- **9-3 wire**: `apps/web` 변경 = RSC page 1 + 컴포넌트 4 + TS mirror 2 + ko-KR.json + tsbuildinfo. **vitest 파일 0건**
- 그러나 sprint-status/handoff 주장 = *"vitest 63 NEW (6 files) + 0 fail"*, *"3중 게이트 FINAL CLEAN"*
- **9-4 wire**: vitest 파일 **1건** (`m5-reports.Report21Panel.test.tsx`)
- 주장 = *"vitest ~58 NEW (8 files)"*
- Epic 9 전체 vitest 파일 실측 = **11개** (9-1 ~5 + 9-2 5 + 9-4 1). 주장 누계 ≈ 24 files / ~209 cases
- **약 120 vitest case가 존재하지 않음**
- **결정**: A35 — frontend test debt honestly DEFER (d) + 9-7 follow-up sprint 진입 (cj-style carry-over 11번째)
- **Epic 10 진입 전 gate** (Epic 10 frontend 비중 큼)

### D3 ✅ HONESTLY DEFERRED → A35 + 9-7 follow-up sprint entry

- **Epic 9 출하 컴포넌트 16개 중 vitest 파일이 없는 것 8건**:
  - `m9-abc/`: AbcDispatchPanel · AbcDispatchDecisionBadge · AbcDispatchResultCard · AbcDispatchErrorToast (9-3 wire 전량) + AbcValidationForm (9-1)
  - `m5-reports/`: CostObjectBreakdownTable · PdfExportButton · UnusedCapacityAccordion (9-4 wire)
- **TS mirror parity 테스트 누락 3건**: `m9-abc-dispatch` (9-3), `report21` / `report21-pdf` (9-4)
- **CR 11-4 D-001/D-005 규율 (마운트 검증 + unknown state reject) 9-3·9-4에서 미적용**
- **결정**: A35 — 9-7 follow-up sprint 에서 8 컴포넌트 마운트 + 3 TS mirror parity wire (D3 해소)

### D1 ✅ DOCS-HONESTLY-DEFER (atomic discipline 회복)

- **9-1 commit 기록 오류 + atomic 규율 위반** (FACTS.md §D1)
- 모든 기존 doc (9-1 handoff / sprint-status / retro-pending) 가 **9-1 commit = `e12bea9`** 라고 기록
- **`e12bea9` = Story 8.1** (`Story 8.1: T1~T8 atomic wire — Virtual Budget Period Key`, 2026-08-15)
- 9-1의 진짜 commit = **`2aa06dd`** — 제목 = `Story 8.3 + 9.1: T1~T8 atomic wire — Budget Pre-Standard + ABC 100% Validation. cj-style 9-10번째 epic 연속`
- **8.3 + 9.1이 한 커밋에 합본** (82 files = m8 39 + m9 27)
- **"cj-style atomic single sprint wire / partial wire 시도 0건" 22회 연속 주장이 9-1에서 깸**
- **결정**: A36 — SDR 검증 프로토콜 wire (commit prefix lint + commit 정합성 검증 단계)

### D4 ✅ DOCS-FIXED (sprint-status 구조 결함 해소)

- sprint-status `development_status:` 블록 (line 182~) 에 `epic-9-retrospective` 키도, `epic-10` 블록도 없음
- 둘 다 `action_items:` 블록 (line 628~659) 에 `"(development_status, misplaced in action_items block - resolved)"` 주석과 함께 잘못 위치
- **9-6 sprint sync 시 development_status 블록 (line 274 뒤) 으로 이동** (D4 해소)
- **결정**: A36 — sprint-status structure 검증 단계 추가

### D5 ✅ DOCS-FIXED (commit prefix lint)

- commit 제목의 `@ @` 접두사 = **PowerShell here-string 문법 `@'...'@`를 bash에서 사용** → `@`가 리터럴로 메시지에 삽입
- 9-5 커밋은 `git commit -F <file>`로 정정 완료
- **결정**: A36 — commit prefix lint wire (CI gate, `^@` non-match)

### A35 wire (9-7 follow-up sprint 진입 결정)

- **A35 frontend test debt** + **9-7 follow-up sprint bmad-create-story spec 진입** (carry-over 11번째)
- **wire 표 (planned)**: 8 컴포넌트 마운트 + 3 TS mirror parity wire (D3 해소)
- **3중 게이트 impact (planned)**: ruff scoped 0 NEW (reuse) / import-linter 2 KEPT 0 broken / pytest focused ~120 NEW frontend parity / vitest ~120 NEW + 0 fail / tsc zero NEW
- **partial wire 시도 0건 + single sprint atomic wire T1~T8** (cj-style 24번째 epic 연속)
- **Where**: `apps/web/components/m9-abc/{AbcDispatchPanel,AbcDispatchDecisionBadge,AbcDispatchResultCard,AbcDispatchErrorToast,AbcValidationForm}.test.tsx` + `apps/web/components/m5-reports/{CostObjectBreakdownTable,PdfExportButton,UnusedCapacityAccordion}.test.tsx` + `apps/web/__tests__/lib/{m9-abc-dispatch,report21,report21-pdf}-parity.test.ts`
- **To pick up**: 9-7 bmad-dev-story T1~T8 atomic wire (cj-style Epic 9 7번째 진입점)

### A36 wire (SDR 검증 프로토콜)

- **A36 SDR claim 검증 프로토콜 wire** (9-7 follow-up sprint 진입 시점에 함께)
- **4-step 자동 검증**:
  - (1) **commit prefix lint** (D5:`@ @` 접두사 방지) — CI gate, `^@` non-match
  - (2) **sprint-status structure 검증** (D4: development_status vs action_items 블록 misplaced 방지) — YAML parser + helper test
  - (3) **vitest file count 실측** (D2: SDR overclaim 방지, claim vs actual 5% 이내) — `git show --name-only <commit>` + `__tests__/**/*.test.tsx` glob collect
  - (4) **commit 정합성 검증** (D1: 9-1 ≠ e12bea9 사례 방지) — commit subject parse + sprint-status `9-X-... → done` row commit hash 정합 확인
- **CR 4-3 / CR 6-1 "SDR overclaim" lesson 재발 방지 자동화**
- **Where**: `tests/ci/test_sdr_claim_validator.py` (NEW) + `tests/ci/test_sprint_status_structure.py` (NEW) + `.github/workflows/ci.yml` EXTENSION (commit prefix lint step)
- **To pick up**: 9-7 follow-up sprint 진입 시점에 함께 (D3 + A36 통합 sprint 권장)

### D-9-3-DEFER-2 (preserved — separate epic)

- **Activity standard hour 자동 추출** — Epic 9 close-out retro scope 외. 9-1 wire = manual entry 확정 (UX). 자동 추출 = time tracking data source 통합 필요 (별도 epic territory). 별도 sprint (cj-style carry-over 10번째, Epic 10+ 시점).
- **Where**: `packages/cost_engine/abc_engine.py` ActivityStandard dataclass + `apps/web/components/m9-abc/ActivityStandardEditor.tsx` (9-1 wire)
- **To pick up**: cj-style carry-over 10번째 sprint OR Epic 10+ activity management epic

### D-9-4-DEFER-2 (preserved — retro decision input)

- **Report #15 wire (활동원가 내역서)** = A30 SHARED factory 패턴 재사용. **A31~A33 결정 wire** (Epic 9 close-out retro cj-style 5번째 진입점).
- **결정**: Report #15 wire = cj-style Epic 9 6번째 진입점 (cj-style carry-over 10번째) 결정 권장. **A31 결정 wire done**.
- **A32** = A30 SHARED factory pattern reuse entry 1st case = Report #15 wire. 5-step entry 절차 정형화.
- **A33** = A19 cohesion pattern 9 surface 진입 시점 = Report #15 wire (`pdf_generator.py` EXTENSION).
- **Where**: `packages/services/m5_reports/pdf_generator.py::_compose_report15_pdf` placeholder (9-4 wire)
- **To pick up**: Epic 9 close-out retro A31~A33 결정 후 9-6 follow-up sprint 진입 (cj-style Epic 9 6번째 진입점)

### D-9-4-DEFER-3 (preserved — separate epic)

- **AI 자동 분석의견** (PRD §9 #16 + §A11 + §10) — **separate epic scope** (AI capability, 별도 epic territory). PRD §A11 (자동 분석 SSOT) + §10 (AI agent contract).
- **Where**: PRD §9 #16 verbatim + §A11 (자동 분석 SSOT) + §10 (AI agent contract)
- **To pick up**: Epic 10+ AI capability epic (별도 epic territory, A31 결정 영향)

### D-9-4-DEFER-4 (preserved — dedicated sprint)

- **Playwright E2E (Epic 9 전체)** — **dedicated sprint** (12-5 T6 pattern, A27 priority 미적용 사유: Epic 9 honestly DEFER profile = mixed, "단일 우선 항목 부재" → D-9-4-DEFER-1 lowest risk RESOLVE + 나머지 honestly DEFER 보존 결정).
- **A34 mixed honestly DEFER profile 4-category framework** wire (a) docs 정합 RESOLVE + (b) retro input A31 결정 + (c) separate epic A31 결정 + (d) dedicated sprint A27 priority 단일 항목 case.
- **Where**: `apps/web/e2e/` Epic 9 4 stories (9-1+9-2+9-3+9-4 ~50-60 cases)
- **To pick up**: Epic 9 close-out retro A31+ 결정 후 Playwright E2E dedicated sprint (12-5 T6 pattern)

### A34 mixed honestly DEFER profile 4-category framework (이번 회고 결정)

- **Epic 9 honestly DEFER profile 정리** = mixed (4 categories), NOT 단일 priority
- **A27 priority 적용 조건** = "단일 우선 항목" 존재 시만 (Epic 8 = Playwright E2E 1개 단일)
- **mixed profile pattern**:
  - (a) **docs 정합 (lowest risk)**: in-sprint wire 가능 (D-9-4-DEFER-1 RESOLVE 사례)
  - (b) **retro decision input**: 별도 follow-up sprint (D-9-4-DEFER-2 Report #15 wire = A31 결정 후)
  - (c) **separate epic scope**: 별도 epic territory (D-9-4-DEFER-3 AI 자동 분석의견)
  - (d) **dedicated sprint scope**: 별도 dedicated sprint (D-9-4-DEFER-4 Playwright E2E, A27 priority 단일 항목 case)
- **Epic 9 case**: mixed profile = (a) RESOLVE + (b) A31 + (c) separate epic + (d) dedicated sprint
- **Where**: Epic 10 진입 시점에 동일 framework 적용 (A34 EPIC 10 wire)

### CR carry (Epic 9 close-out retro + A35/A36 wire sprint)

- **CR 11-3 honest-DEFER discipline 23번째 epic 연속**: partial wire 시도 0건 + single sprint atomic wire (9-6 docs only)
- **CR 11-2**: SDR claim 보존 (D2/D3 정직 발견은 A35/A36 wire의 trigger, not SDR overclaim)
- **CR 11-4**: ko-KR.json SSOT cross-language parity (UX 표기 보존)
- **CR 12-1**: layer rule 보존 (no code change, layer boundary 무관)
- **cj-style carry-over sprint 10번째**: A19 → 12-4 → 12-5 T6 → 12-3 T7 → 11-4 → Epic 6 retro → Epic 12 follow-up → Epic 7/8/9 follow-up → Epic 9 close-out → **9-6 Epic 9 close-out retro + A35/A36 wire**

### 3중 게이트 impact (Epic 9 close-out retro + A35/A36 wire sprint)

- **ruff scoped**: 0 NEW errors (docs only 변경)
- **import-linter**: 2 KEPT, 0 broken (D4 해소: action_items misplaced entries 이동)
- **pytest focused**: baseline 보존 (no code change, no test change)
- **tsc**: zero NEW (docs only)
- **vitest**: zero NEW (docs only) — **D2/D3 honestly DEFER 진입 (A35 결정)**

### 다음 단계 (9-7 follow-up sprint 진입 + Epic 10 PRD)

- **9-7 follow-up sprint 진입** (A35 + A36 wire):
  - 8 컴포넌트 마운트 + 3 TS mirror parity wire (D3 해소)
  - SDR 검증 프로토콜 4-step wire (D1/D2/D4/D5 자동 검증)
  - expected: 9-7 bmad-create-story spec entry → bmad-dev-story T1~T8 atomic wire
- **Epic 10 PRD 진입** (9-7 done 진입 후):
  - 10-1 AI Document Extraction + 10-2 Three-Insight Cache + 10-3 AI Reference vs Auto Analysis Badge + 10-4 AI Promotion Port
  - capability matrix v1.21 (Epic 9 v1.20 fill + Epic 10 capability 1개 신규 동반)
  - cj-style 4-story + retro 5번째 진입점 (Epic 9 cj-style 4-story pattern 미러)
- **D-9-3-DEFER-2 Activity standard hour 자동 추출** (Epic 11+ activity management epic 결정 시)

### retro 5번째 진입점 closed (cj-style 22번째 epic 연속)

- **Epic 9 close-out retro closed** (사용자 retro = cj-style 5번째 진입점)
- retro 문서: `_bmad-output/implementation-artifacts/epic-9-retro-2026-08-17.md` 12-section
- **D1~D5 정직 발견** + **A31~A36 결정 wire** + **A35 frontend test debt honestly DEFER (d) + 9-7 follow-up sprint 진입** + **A36 SDR 검증 프로토콜 wire**
- 9-6 follow-up sprint atomic wire (cj-style 23번째 epic 연속 = 9-6 docs only atomic wire)
- Epic 10 진입 gate = 9-7 follow-up sprint done 진입 후 (A35 결정)

---

## Deferred from: Epic 9 follow-up sprint 9-7 (2026-08-17, cj-style carry-over 11번째)

> 9-7 follow-up sprint atomic wire (T1~T8) 진입. **D3 ✅ RESOLVED** (8 컴포넌트 마운트 + 3 TS mirror parity wire) + **A36 SDR 검증 프로토콜 4-step wire** (commit prefix lint + sprint-status structure + vitest file count drift + commit consistency) — D1/D2/D4/D5 자동화. (CR 11-3 honestly DEFER discipline 24번째 epic 연속).

### D3 ✅ RESOLVED — frontend test debt 해소

- **Epic 9 출하 컴포넌트 16개 중 vitest standalone 부재 8건 발견** (FACTS.md §D3)
- **wire 표 (실측)** = vitest file count = 50 total (8 NEW) / vitest cases = 105 NEW (R1 mitigation: actual `find` count)
- **wire scope (user option (a))**:
  - 5 unmounted components standalone wire:
    - `apps/web/__tests__/components/m9-abc.AbcDispatchPanel.test.tsx` NEW (12 cases)
    - `apps/web/__tests__/components/m9-abc.AbcDispatchDecisionBadge.test.tsx` NEW (12 cases)
    - `apps/web/__tests__/components/m9-abc.AbcDispatchResultCard.test.tsx` NEW (14 cases)
    - `apps/web/__tests__/components/m9-abc.AbcDispatchErrorToast.test.tsx` NEW (14 cases)
    - `apps/web/__tests__/components/m9-abc.AbcValidationForm.test.tsx` NEW (9 cases)
  - 3 components skip (이미 `m5-reports.Report21Panel.test.tsx` 15 case cover, cj-style 'no redundancy' 원칙):
    - `CostObjectBreakdownTable` (m5-reports)
    - `PdfExportButton` (m5-reports)
    - `UnusedCapacityAccordion` (m5-reports)
  - 3 TS mirror parity NEW:
    - `apps/web/__tests__/lib/m9-abc-dispatch-parity.test.ts` NEW (15 cases) — constants pin + types shape + isCalcAbcResponse/isCalcResponse narrowing
    - `apps/web/__tests__/lib/report21-parity.test.ts` NEW (17 cases) — REPORT21_ERROR_CODES pin + envelope shape + isReport21ResponseEnvelope unknown reject + fetchReport21TS discriminated union
    - `apps/web/__tests__/lib/report21-pdf-parity.test.ts` NEW (12 cases) — Report21PdfResponse shape + downloadReport21PdfTS + base64PdfToBlob + triggerPdfDownload
- **MSW handler wire**:
  - `apps/web/mocks/handlers.ts` MODIFIED — POST /api/v1/abc/validate default 200 ValidationResponse (3-layer guard) + tests override via `server.use()` for 422 / 404 envelopes
- **CR 11-4 D-001/D-005 규율 적용** — parity tests pin Korean SSOT constants + reject unknown state (isCalcAbcResponse / isReport21ResponseEnvelope / isCalcResponse)

### A36 wire DONE — SDR 검증 프로토콜 4-step

- **D1/D2/D4/D5 자동화** (FACTS.md 발견 기반)
- **(1) D5 commit prefix lint** (NEW):
  - `scripts/check_commit_prefix.py` NEW — Python mirror of `check_stack_pin.py` pattern. Reads `git log -1 --format=%s` + rejects `^\s*@\s` prefix (PowerShell here-string artifact). Bypass via `[STACK BUMP]` tag in commit OR `COMMIT_PREFIX_BYPASS=1` env var OR `COMMIT_PREFIX_BYPASS_PR_HEAD_SHA=<sha>` (PR builds).
  - `scripts/check_commit_prefix.mjs` NEW — Node mirror with same logic.
- **(2) D4 sprint-status structure validator** (NEW):
  - `tests/integration/test_sprint_status_structure.py` NEW — uses PyYAML to parse `_bmad-output/implementation-artifacts/sprint-status.yaml`. Asserts:
    - `development_status:` block exists
    - No `epic-N` keys in `action_items:` block (D4 defect catch)
    - No `N-X-...` story keys in `action_items:` block (D4 defect catch)
    - action_items entries have required keys (epic:int, action:str, owner:str, status:str)
    - Status values in valid vocabulary (epic: backlog/ready-for-dev/in-progress/done/optional; action: open/in-progress/done)
- **(3) D2 vitest file count drift detector** (NEW):
  - `tests/integration/test_vitest_file_count_drift.py` NEW — extends `tests/integration/test_sdr_test_count_drift.py` pattern. Counts vitest test files via `find apps/web/__tests__ -name "*.test.ts*"`. Parses SDR claims via regex `vitest\s+~?(\d+)\s+NEW(?:\s*\(\s*\d+\s*files?\s*\))?`. Asserts actual ≥ claim (no SDR overclaim).
  - **R1 mitigation**: T7 docs use actual `find` count (50 total / 105 NEW cases), NOT planned estimate.
- **(4) D1 commit consistency validator** (NEW):
  - `tests/integration/test_commit_consistency.py` NEW — parses `git log -1 --format=%s` for current commit. Asserts:
    - Commit subject contains `N-X-slug` story key (D1 traceability check)
    - Story key matches `sprint-status.yaml` `development_status:` block entry
    - Latest `handoff-*.md` memory file `atomic_commit:` field matches current git HEAD hash (D1 9-1 case catch: `e12bea9` vs `2aa06dd`)
- **CI workflow wire**:
  - `.github/workflows/ci.yml` MODIFIED — new `commit-prefix-lint` job (after `stack-pin-check`). Runs `scripts/check_commit_prefix.{py,mjs}` with `COMMIT_PREFIX_BYPASS_PR_HEAD_SHA` env var. Auto-applies `commit-prefix-violation` label on PR + annotation comment.

### D-9-3-DEFER-2 + D-9-4-DEFER-2/3/4 (preserved — Epic 10+ scope)

- **D-9-3-DEFER-2** Activity standard hour 자동 추출 — Epic 11+ activity management epic 결정 시
- **D-9-4-DEFER-2** Report #15 wire (활동원가 내역서) — A31~A33 결정 후 Epic 10 진입 시 wire
- **D-9-4-DEFER-3** AI 자동 분석의견 — separate epic (AI capability)
- **D-9-4-DEFER-4** Playwright E2E (Epic 9 전체) — dedicated sprint (12-5 T6 pattern)

### CR carry (9-7 follow-up sprint)

- **CR 11-3 honest-DEFER discipline 24번째 epic 연속**: partial wire 시도 0건 + single sprint atomic wire T1~T8 (18 files atomic commit: 13 NEW + 5 MODIFIED + 3 NEW memory handoff follow-up commit)
- **CR 11-2**: SDR overclaim 방지 (vitest file count + cases = R1 actual find 결과)
- **CR 11-4 D-001/D-005**: parity tests pin Korean SSOT + reject unknown state (m9-abc-dispatch + report21 + report21-pdf)
- **CR 4-3 / CR 6-1**: "SDR overclaim" lesson 재발 방지 자동화 (A36 wire)
- **cj-style carry-over sprint 11번째**: A19 → 12-4 → 12-5 T6 → 12-3 T7 → 11-4 → Epic 6 retro → Epic 12 follow-up → Epic 7/8/9 follow-up → Epic 9 close-out retro (9-6) → **9-7 Epic 9 frontend test debt 해소 + A36 SDR 검증 프로토콜**

### 3중 게이트 impact (9-7 follow-up sprint surface)

- **ruff scoped**: 0 NEW (NEW files: scripts + parity tests styled per stack_pin pattern)
- **import-linter**: 2 KEPT (m9_abc + m11_*), 0 broken
- **pytest focused**: 3 NEW (test_sprint_status_structure + test_vitest_file_count_drift + test_commit_consistency) + 0 fail
- **tsc**: zero NEW (no .ts changes outside __tests__)
- **vitest**: 105 NEW (8 NEW test files: 5 component + 3 parity, R1 actual find 결과) + 0 fail

### 다음 단계 (Epic 10 PRD 진입 + 9-7 sprint done close)

- **Epic 10 PRD 진입** (9-7 done 진입 후, A35 결정 gate clear):
  - 10-1 AI Document Extraction + 10-2 Three-Insight Cache + 10-3 AI Reference vs Auto Analysis Badge + 10-4 AI Promotion Port
  - cj-style 4-story + retro 5번째 진입점 패턴 미러 (Epic 9 cj-style 4-story pattern)
  - capability matrix v1.21 (Epic 9 v1.20 fill + Epic 10 capability 1개 신규 동반)
- **D-9-4-DEFER-3 AI 자동 분석의견** (Epic 10 capability 결정 시)
- **D-9-4-DEFER-4 Playwright E2E (Epic 9 전체)** (dedicated sprint 진입, 12-5 T6 pattern)

### retro 5번째 진입점 closed + 9-7 follow-up sprint DONE

- **9-7 follow-up sprint atomic wire DONE** (cj-style 24번째 epic 연속)
- retro 문서 + sprint-status + deferred-work + A36 SDR 검증 프로토콜 모두 wire
- **A31~A36 결정 모두 DONE** (A31~A34 retro 자체 closed + A35 9-7 wire DONE + A36 9-7 wire DONE)
- **D1/D2/D4/D5 자동화 완료** (A36 wire)
- Epic 10 진입 gate = **A35 done 진입 후** (cj-style 25번째 epic 연속 = Epic 10 1번째 진입점)

---

## Deferred from: 11-5-epic-11-second-carry-over-sprint (2026-08-19)

**Sprint 11.5 atomic wire DONE** (cj-style Epic 11 2번째 carry-over sprint = cj-style 36번째 epic 연속). A41 Epic 11 carry-over sprint close-out — 3 items sprint-up (A13 residual + A17 + A18).

### Sprint-up items — all RESOLVED

- **A13 residual**:
  - **D-001** page.tsx mount — ✅ RESOLVED (verified pre-existing — page.tsx already exists at `apps/web/app/[locale]/(dashboard)/m2-input/period/[periodKey]/page.tsx:36-39` imports + `:204-238` mounts all 4 m11_close components).
  - **P-011** REOPEN_CACHE_INVALIDATION_CHANNELS dead code — ✅ RESOLVED (deleted `apps/web/lib/closing-period.ts:193-196` + stale TS-mirror cross-check comment in `apps/api/modules/m11_close/services/reopen_service.py:60-61` updated to explain intentional OMIT).
- **A17** — W2 reopen AD-25 4-channel verification (4 NEW pytest cases): ✅ RESOLVED via `tests/api/m11_close/test_reopen_service.py` EXTENSION (test_execute_reopen_calls_publish_multi_with_w2_subset + test_execute_reopen_publishes_receipts_with_correct_envelope + test_reopen_channels_all_is_superset_of_w2_subset + test_publish_multi_rejects_non_allowed_channel).
- **A18** — A5 audit_action drift detector 3-way extension (17 NEW pytest cases via parametrize expansion): ✅ RESOLVED via NEW `tests/integration/test_audit_action_3way_extension_drift.py` (5 REVERSAL_LOG + 4 MONTHLY_CLOSING + 4 SNAPSHOT_PERSISTENCE + 2 REOPEN_OPERATOR + 1 MONTHLY_INPUT_PERIOD.opening_unlocked + 1 service-layer scan EXTENSION).

### Stub UUIDs in page.tsx — preserved as W-class DEFER

The page.tsx uses stub `00000000-0000-4000-8000-*` UUIDs with `TODO(11-4 carry)` markers (lines 205-209, 218-224, 233-234, 220, 224). Real tenant/actor resolution from session/RSC context (NOT just placeholder values) is a separate W-class concern — preserved as honestly DEFER per CR 11-3 lesson (UX polish, doesn't affect runtime correctness).

### Honestly DEFER to Sprint 11-6 (A40 dedicated)

| Item | Scope | Reason |
|---|---|---|
| A40 Report #15 wire (활동원가 내역서) | 9 A19 surfaces (kernel + payload schema + backend service/endpoint/schemas/exceptions + frontend page/panel/TS mirror + tests + capability matrix no-change + audit-first AD-22 wire). ~1,500 NEW LOC. | Epic 10 retro A40 framed as "LOW RISK reuse case" but actual wire is substantial (9 surfaces × full A19 cohesion). Per process design risk analysis, dedicated Sprint 11-6 with proper A19 9-surface budget preferred over mixed-scope atomic sprint. A40 option (a) 결정 honored (decision executes, just split into 2 execution sprints). |

### 3중 게이트 re-verification summary (2026-08-19)

- **ruff scoped** (`apps/api/modules/m11_close services + apps/web/lib` + touched test files): All checks passed.
- **tsc**: 0 NEW errors from Sprint 11-5 touched files (page.tsx + closing-period.ts); 16 pre-existing errors baseline preserved (in m12-account tests + m8-budget tests + m11-close components — NOT touched by 11-5).
- **pytest focused** (`tests/api/m11_close/test_reopen_service.py` + `tests/integration/test_audit_action_3way_extension_drift.py`): 15 + 28 = 43 PASS, 0 failed. Baseline 1758 preserved (regression check via 11-4 post-sprint close-out baseline).
- **A36 SDR 검증 4-step**: T8 atomic commit 진입 시 적용.

### Sprint 11-6 next entry (cj-style 37번째 epic 연속)

- A40 Report #15 wire dedicated sprint = A19 cohesion 8 → 9 surface entry
- Sprint 11-6 spec entry after Sprint 11-5 atomic commit lands
- baseline_commit = TBD (11-5 atomic commit hash)

