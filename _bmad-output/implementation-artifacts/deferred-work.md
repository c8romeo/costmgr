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
