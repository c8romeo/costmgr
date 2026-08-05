# Story 0.5: Frontend Plumbing Wire (Tailwind + shadcn/ui + sonner + vitest + Playwright + next-intl)

Status: done (2026-08-05)

baseline_commit: 7a13eb9 (Story 5.2 bmad-code-review tip — pre-0.5 wire)

<!-- Note: Cross-cutting plumbing story (Epic 4 close-out retro A6 NEW 결정). Epic 0 closed (4/4 done) but this story is required before Epic 5 5-3 frontend toast. Epic 0 status stays "done" — 0-5 is a retro carry-over not part of Epic 0 proper. -->

## Story

As a **frontend platform engineer**,
I want **the full Next.js frontend testing + UI primitive stack installed and wired (Tailwind 4.3.3 + shadcn/ui + sonner + vitest + RTL + Playwright + next-intl)**,
so that **every Story 3.1+ frontend AC can write idiomatic shadcn Tabs/Sonner/RTL/Playwright code without inline workarounds** — and Epic 5 5-3 frontend toast, Epic 6 charts/PDF, Epic 7 BEP, Epic 8 budget variance all consume a stable, lint-clean foundation (AD-1, AD-15).

## Acceptance Criteria

### AC #1 — Tailwind CSS 4.3.3 wire + Pretendard next/font/local

**Given** the existing `apps/web/app/layout.tsx` uses inline `fontFamily` style with Pretendard CDN (no SRI), and no Tailwind is installed
**When** I install `tailwindcss@4.3.3` + `@tailwindcss/postcss` + `postcss` + `autoprefixer`
**And** create `apps/web/postcss.config.mjs` + `apps/web/tailwind.config.ts` (preserving Next 15.5.4 + React 19.1.1 stack pin — `[STACK BUMP]` required for Tailwind 4.x major bump from spec 4.3.3 baseline)
**And** create `apps/web/app/globals.css` with `@import "tailwindcss"` + design tokens (CSS variables for shadcn `bg-background`/`text-foreground`/`border`/`input`/`primary` etc.)
**And** replace Pretendard CDN with `next/font/local` (resolve F-1 deferral: Pretendard CDN without SRI)
**Then** `pnpm dev` boots with Tailwind utilities active + Pretendard font loaded via `next/font/local`
**And** `pnpm lint:tsc` clean + `pnpm lint:conventions` clean
**And** existing inline `style={{ fontFamily: ... }}` in `apps/web/app/layout.tsx` is removed

### AC #2 — shadcn/ui init + Tabs primitive wire

**Given** no shadcn/ui is installed (`components.json` missing, no Radix UI, no `class-variance-authority`, no `tailwind-merge`)
**When** I install `@radix-ui/react-tabs` + `@radix-ui/react-tooltip` + `@radix-ui/react-dialog` + `@radix-ui/react-toast` + `@radix-ui/react-dropdown-menu` + `@radix-ui/react-select` + `class-variance-authority` + `tailwind-merge` + `clsx` + `lucide-react` + `@radix-ui/react-slot`
**And** create `apps/web/components.json` (style="default", rsc=true, tsx=true, baseColor="slate", cssVariables=true, aliases: components="@/components", utils="@/lib/utils")
**And** create `apps/web/lib/utils.ts` with `cn(...inputs: ClassValue[]): string` (clsx + tailwind-merge)
**And** run `pnpm dlx shadcn@latest init` (preserving existing Tailwind 4 config — `--yes` to skip prompts; pin shadcn CLI version explicitly)
**And** `pnpm dlx shadcn@latest add tabs tooltip dialog` (3 most-needed primitives for Epic 5 5-3 + 2-2 M11 + Story 0.4 F-32)
**Then** `apps/web/components/ui/{tabs,tooltip,dialog}.tsx` exists with shadcn-generated code (PascalCase per AD-15)
**And** `apps/web/components/ui/tabs.tsx` exports `Tabs`/`TabsList`/`TabsTrigger`/`TabsContent` importable from any client component
**And** `pnpm lint:tsc` clean + shadcn-generated code respects `no-restricted-types` ESLint rule (AD-8)

### AC #3 — sonner wire + BOMEditorClient toast swap (close Story 2-2 M11 deferral)

**Given** `apps/web/components/m1-baseline/products/BOMEditorClient.tsx:265` uses inline `<p>` for BOM NOT_COMPLETE message (Story 2-2 M11 deferral)
**When** I install `sonner` (latest stable, verify version compatible with React 19.1.1)
**And** create `apps/web/components/ui/sonner.tsx` (Toaster with `theme="light"` + `richColors=true` + `position="top-right"` + `closeButton` per shadcn sonner convention)
**And** wire `<Toaster />` in `apps/web/app/layout.tsx` (after `{children}` per shadcn docs)
**And** replace `apps/web/components/m1-baseline/products/BOMEditorClient.tsx:265` inline `<p>` with `toast.warning('BOM 비중 합 100% 필요 (현재 95.00%)')` from `import { toast } from "sonner"`
**Then** visiting `/[locale]/m1-baseline/products` and submitting BOM with sum ≠ 100% renders a top-right toast instead of inline `<p>`
**And** Story 2-2 deferred-work.md M11 entry is closed
**And** `pnpm lint:tsc` clean

### AC #4 — vitest + RTL + jsdom + MSW wire (flip scaffolding → active)

**Given** `apps/web/__tests__/IndustrySelector.test.tsx` imports from `vitest` + `@testing-library/react` but neither is installed (scaffolding header comment: "Story 0.5 wires the toolchain")
**When** I install `vitest@latest` + `@vitest/ui` + `@testing-library/react` + `@testing-library/dom` + `@testing-library/jest-dom` + `@testing-library/user-event` + `jsdom` + `happy-dom` + `msw` (latest)
**And** create `apps/web/vitest.config.ts` (jsdom environment, setup files: `./test/setup.ts`, path aliases from `tsconfig.json`, `globals: true` for describe/it/expect/vi)
**And** create `apps/web/test/setup.ts` extending `expect` with `@testing-library/jest-dom` matchers + MSW server lifecycle (`beforeAll` start, `afterEach` reset, `afterAll` close)
**And** create `apps/web/mocks/handlers.ts` (initial handlers: `/api/v1/tenants/me` GET 200 + `/api/v1/tenants/me/industry` POST 200 — required by Story 1.1 IndustrySelector tests)
**And** create `apps/web/mocks/server.ts` (setupServer(...handlers) export)
**And** remove scaffolding header comment from `apps/web/__tests__/IndustrySelector.test.tsx` (delete "Story 0.5 wires the toolchain" + "scaffolding" lines)
**And** add `pnpm test` (run), `pnpm test:watch` (vitest --watch), `pnpm test:ui` (@vitest/ui) scripts
**Then** `pnpm test` runs `IndustrySelector.test.tsx` (4 scenarios: renders 4 cards, click service POSTs body, 200 → navigate to /dashboard, 409 INDUSTRY_LOCKED → toast + disable) and all pass
**And** `pnpm lint:tsc` clean + MSW server lifecycle active in test setup
**And** Story 1.1 deferred-work.md F-30 entry is partially closed (vitest toolchain wired; F-30 rls_db fixture resolves in AC #5 below)

### AC #5 — Playwright wire + Supabase test fixture (close Story 1.1 F-30)

**Given** `apps/web/e2e/onboarding.spec.ts` imports from `@playwright/test` but neither `@playwright/test` nor Playwright browsers are installed (scaffolding header: "Playwright runner + Supabase test fixtures are added in Story 0.5")
**When** I install `@playwright/test@latest` (verify version compatible with Node 24.18 LTS)
**And** create `apps/web/playwright.config.ts` (baseURL=http://localhost:3000, projects: chromium/firefox/webkit, webServer: `pnpm dev` with `reuseExistingServer: !process.env.CI`, timeout 30s, retries: 2 on CI)
**And** create `apps/web/e2e/fixtures/supabase-test.ts` (rls_db fixture importable — resolves F-30 deferral: "tests/rls/conftest.py rls_db fixture importable from tests/api/" pattern extended to e2e fixtures)
**And** remove scaffolding header from `apps/web/e2e/onboarding.spec.ts` (delete "Story 0.5 wires the real signup" + "The Playwright runner + Supabase test fixtures are added in Story 0.5" + "Until then this file is shipped as scaffolding" lines)
**And** add `pnpm playwright test` (run) + `pnpm playwright install --with-deps chromium` (setup) + `pnpm playwright codegen` (recording) scripts
**Then** `pnpm playwright test --project=chromium apps/web/e2e/onboarding.spec.ts` runs all 3 scenarios and passes:
  - `test_new_user_sees_industry_selector` — visit `/${TEST_LOCALE}/onboarding/industry` → heading + 4 industry names visible
  - `test_select_service_hides_bom_menu` — select 서비스업 → sidebar shows 원가풀/활동/동인 + hides BOM/기초재고/수불부
  - `test_select_manufacturing_service_shows_segment_split` — select 제조+서비스 → "카브아웃 분할" visible + tooltip on hover (uses AC #2 shadcn Tooltip)
**And** `pnpm lint:tsc` clean + chromium browser installed locally (CI installs via `--with-deps`)

### AC #6 — next-intl wire + ko-KR.json (close Story 1.1 F-42)

**Given** `apps/web/messages/ko-KR.json` is missing per Story 1.1 deferred-work F-42 + AC #3 SPEC §6.4 next-intl requirement, and ko-KR strings are inlined across components
**When** I install `next-intl@latest` (verify Next 15.5.4 compatibility)
**And** create `apps/web/messages/ko-KR.json` with all currently inlined ko-KR strings (initial keys: `industry.manufacturing`, `industry.service`, `industry.mixed`, `industry.service_other`, `industry.title`, `industry.locked_message`, `bom.not_complete`, `bom.ratio_label`, plus ~30 strings inventoried from `IndustrySelector.tsx` + `BOMEditorClient.tsx` + `SettingsWizardClient.tsx`)
**And** create `apps/web/i18n.ts` (`getRequestConfig` with locale='ko-KR' default, timeZone='Asia/Seoul')
**And** create `apps/web/middleware.ts` (`createMiddleware` from `next-intl/middleware` matching `/[locale]/...` paths)
**And** update `apps/web/next.config.ts` (wrap with `createNextIntlPlugin('./i18n.ts')`)
**And** replace inlined ko-KR strings in `IndustrySelector.tsx` + `BOMEditorClient.tsx` + `SettingsWizardClient.tsx` with `const t = useTranslations('namespace'); t('key')`
**Then** `pnpm dev` boots with next-intl routing active + ko-KR strings sourced from messages JSON
**And** `pnpm lint:tsc` clean
**And** Story 1.1 deferred-work.md F-42 entry is closed

### AC #7 — shadcn Tabs wired into Story 3.3 monthly_input UI (gate for Story 5-3)

**Given** Story 3.3 monthly_input UI uses a manual tab implementation (Story 3-3 frontend scope deferred to Story 0.5 per Epic 4 close-out retro A4 decision), and Story 5-3 frontend toast needs shadcn Tabs as the base primitive
**When** I locate the Story 3.3 frontend Tabs usage point (likely `apps/web/components/l2-input/MonthlyInputTabs.tsx` or equivalent — verify in code)
**And** replace manual tab implementation with `<Tabs defaultValue="production"><TabsList>...</TabsList><TabsTrigger value="...">...</TabsTrigger><TabsContent value="...">...</TabsContent></Tabs>` from `apps/web/components/ui/tabs.tsx`
**And** verify keyboard navigation (Tab/Shift+Tab focus, Enter to activate per Radix Tabs primitive)
**Then** Story 3.3 frontend AC unaffected (warnings display, top_n_severity logic unchanged) + tab switch performance <16ms (no layout shift)
**And** `pnpm lint:tsc` clean + `pnpm test` IndustrySelector unaffected
**And** Story 5-3 frontend spec entry prerequisite satisfied (shadcn Tabs + sonner Toaster both wired)

### AC #8 — INDUSTRY_ICON fill + Python mirror + drift test (close Story 1.1 F-33, F-37)

**Given** `apps/web/lib/menu-config.ts:1142-1148` exports `INDUSTRY_ICON: Record<Industry, IconName>` with placeholder values (Story 1.1 F-33 deferral), and `packages/services/m0_onboarding/industry_menu.py` does NOT mirror `INDUSTRY_ICON` yet (Story 1.1 F-37 deferral)
**When** I fill `INDUSTRY_ICON` values with lucide-react icon names:
  - `manufacturing` → `"Factory"`
  - `service` → `"Briefcase"`
  - `manufacturing_service` → `"Layers"`
  - `manufacturing_service_other` → `"Boxes"`
**And** create `packages/services/m0_onboarding/industry_menu.py::INDUSTRY_ICON: Final[dict[Industry, str]] = {"manufacturing": "Factory", ...}` (mirror TS, Python side stores icon name only — no SVG component)
**And** extend `tests/integration/test_menu_config_consistency.py` to assert icon parity: `assert INDUSTRY_ICON_TS == INDUSTUSTRY_ICON_PY` (drift guard, A5 forward-lock pattern)
**Then** Story 1.1 deferred-work.md F-33 + F-37 entries are closed
**And** `pnpm lint:tsc` + `uv run pytest tests/integration/test_menu_config_consistency.py` clean

### AC #9 — CI gate (vitest + Playwright smoke + next-intl build)

**Given** no web-side CI step currently runs vitest or Playwright (Story 0.4 ci.yml only runs backend pytest + ruff + import-linter + stack-pin-check + lint-conventions)
**When** I add 2 new jobs to `.github/workflows/ci.yml`:
  - `web-test`: `pnpm install --frozen-lockfile` → `pnpm lint:tsc` → `pnpm lint:conventions` → `pnpm test --run` → upload vitest HTML report
  - `web-e2e`: `pnpm install --frozen-lockfile` → `pnpm playwright install --with-deps chromium` → `pnpm playwright test --project=chromium` (smoke subset only, full matrix deferred to Story 5.3+)
**And** update `apps/web/package.json` engines field: `"engines": { "node": ">=24.18.0" }` (resolves Story 0.3 TYPES-1 deferral)
**And** add Makefile targets: `make web-test` (delegates to `pnpm test --run`) + `make web-e2e` (delegates to `pnpm playwright test --project=chromium`)
**Then** CI runs `web-test` + `web-e2e` jobs on every PR
**And** Playwright smoke (chromium only) gates PR merge if onboarding flow breaks
**And** Story 0.3 TYPES-1 deferral closed (engines field)

### AC #10 — Documentation + deferred-work close-out

**Given** all 9 wire tasks above complete, and deferred-work.md has 10+ entries across Story 0.1/0.4/1.1/1.2/2.2/5.1 pointing at Story 0.5
**When** I create `docs/frontend-toolchain.md` (NEW) covering:
  - §1 Stack pin (Next 15.5.4 + React 19.1.1 + Tailwind 4.3.3 + shadcn CLI version)
  - §2 Tailwind 4 config (postcss + globals.css design tokens)
  - §3 shadcn/ui setup (components.json + add primitives + cn helper)
  - §4 sonner toast usage (Toaster in layout + toast.warning/error patterns)
  - §5 vitest setup (vitest.config.ts + setup.ts + MSW handlers convention)
  - §6 Playwright setup (playwright.config.ts + rls_db fixture importable pattern)
  - §7 next-intl routing (i18n.ts + middleware.ts + messages/ko-KR.json)
  - §8 INDUSTRY_ICON contract (TS + Python mirror + drift test pattern)
**And** update `docs/conventions.md` §6 (Frontend Tooling) with stack pin + design tokens reference
**And** update `deferred-work.md` closing entries: F-1 (Pretendard next/font/local), Story 0.4 ESLint per-file disable refinement, F-30, F-31, F-32, F-33, F-37 (Story 1.1), F-42 (next-intl), M11 (Story 2.2 sonner toast), M14 (Story 5.1 TS mirror file), L8 (Story 5.1 SQL CHECK — backend deferred separately)
**Then** Epic 4 close-out retro A6 follow-through status: ✅ done
**And** Epic 5 5-3 spec entry prerequisite satisfied (shadcn Tabs + sonner Toaster + vitest + Playwright + next-intl all wired)

## Tasks / Subtasks

- [ ] **Task 1 — Tailwind CSS 4.3.3 wire + Pretendard next/font/local** (AC: #1)
  - [ ] Subtask 1.1 — Install `tailwindcss@4.3.3` + `@tailwindcss/postcss` + `postcss` + `autoprefixer` (verify versions; `[STACK BUMP]` if Tailwind 4.x differs from baseline)
  - [ ] Subtask 1.2 — Create `apps/web/postcss.config.mjs` (plugins: `@tailwindcss/postcss`, `autoprefixer`)
  - [ ] Subtask 1.3 — Create `apps/web/tailwind.config.ts` (content: `./app/**/*.{ts,tsx}`, `./components/**/*.{ts,tsx}`; theme.extend: shadcn design tokens CSS variables)
  - [ ] Subtask 1.4 — Create `apps/web/app/globals.css` with `@import "tailwindcss"` + `@layer base` (CSS variables for shadcn `bg-background`, `text-foreground`, `border`, `input`, `primary`, `primary-foreground`, `secondary`, `destructive`, `ring` etc. — light + dark theme)
  - [ ] Subtask 1.5 — Update `apps/web/app/layout.tsx`: import `globals.css`, replace Pretendard CDN with `next/font/local` (download Pretendard Variable font to `apps/web/public/fonts/`, configure `next/font/local` with subsets)
  - [ ] Subtask 1.6 — Remove inline `style={{ fontFamily: ... }}` + Pretendard CDN `<link>` from `apps/web/app/layout.tsx`
  - [ ] Subtask 1.7 — Verify `pnpm dev` boots with Tailwind utilities active (`bg-primary` test page renders correctly)
  - [ ] Subtask 1.8 — Verify `pnpm lint:tsc` + `pnpm lint:conventions` clean

- [ ] **Task 2 — shadcn/ui init + Tabs/Tooltip/Dialog primitives** (AC: #2)
  - [ ] Subtask 2.1 — Install Radix UI: `@radix-ui/react-tabs` + `@radix-ui/react-tooltip` + `@radix-ui/react-dialog` + `@radix-ui/react-toast` + `@radix-ui/react-dropdown-menu` + `@radix-ui/react-select` + `@radix-ui/react-slot`
  - [ ] Subtask 2.2 — Install utilities: `class-variance-authority` + `tailwind-merge` + `clsx` + `lucide-react`
  - [ ] Subtask 2.3 — Create `apps/web/components.json` (style="default", rsc=true, tsx=true, baseColor="slate", cssVariables=true, aliases: components="@/components", utils="@/lib/utils")
  - [ ] Subtask 2.4 — Create `apps/web/lib/utils.ts` with `cn(...inputs: ClassValue[]): string` (clsx + tailwind-merge)
  - [ ] Subtask 2.5 — Run `pnpm dlx shadcn@latest init` (pin CLI version explicitly; `--yes` flag; verify Tailwind 4 compat)
  - [ ] Subtask 2.6 — Run `pnpm dlx shadcn@latest add tabs tooltip dialog` (3 most-needed primitives for Epic 5 5-3 + 2-2 M11 + Story 0.4 F-32)
  - [ ] Subtask 2.7 — Verify `apps/web/components/ui/{tabs,tooltip,dialog}.tsx` exists with shadcn-generated PascalCase components
  - [ ] Subtask 2.8 — Write smoke test: `apps/web/__tests__/ui-primitives.test.tsx` renders `<Tabs><TabsList><TabsTrigger value="t1">t1</TabsTrigger></TabsList><TabsContent value="t1">c1</TabsContent></Tabs>` and asserts trigger click switches content
  - [ ] Subtask 2.9 — Verify `pnpm lint:tsc` clean + shadcn-generated code respects `no-restricted-types` (AD-8) + PascalCase naming (AD-15)

- [ ] **Task 3 — sonner wire + BOMEditorClient toast swap** (AC: #3)
  - [ ] Subtask 3.1 — Install `sonner` (latest stable, verify React 19.1.1 compat)
  - [ ] Subtask 3.2 — Create `apps/web/components/ui/sonner.tsx` (Toaster with `theme="light"` + `richColors=true` + `position="top-right"` + `closeButton` per shadcn sonner convention)
  - [ ] Subtask 3.3 — Wire `<Toaster />` in `apps/web/app/layout.tsx` (after `{children}`, inside `<body>`)
  - [ ] Subtask 3.4 — Update `apps/web/components/m1-baseline/products/BOMEditorClient.tsx:265` — replace inline `<p>` with `import { toast } from "sonner"; toast.warning('BOM 비중 합 100% 필요 (현재 95.00%)')`
  - [ ] Subtask 3.5 — Verify `pnpm lint:tsc` clean
  - [ ] Subtask 3.6 — Manual smoke: `pnpm dev` → visit `/[locale]/m1-baseline/products` → submit BOM with sum ≠ 100% → top-right toast renders (Playwright E2E in AC #5)
  - [ ] Subtask 3.7 — Close Story 2.2 deferred-work.md M11 entry (add ✅ marker + commit hash)

- [ ] **Task 4 — vitest + RTL + jsdom + MSW wire** (AC: #4)
  - [ ] Subtask 4.1 — Install `vitest@latest` + `@vitest/ui` + `@testing-library/react` + `@testing-library/dom` + `@testing-library/jest-dom` + `@testing-library/user-event` + `jsdom` + `happy-dom` + `msw`
  - [ ] Subtask 4.2 — Create `apps/web/vitest.config.ts` (jsdom env, setup files: `./test/setup.ts`, path aliases from `tsconfig.json`, globals: true for describe/it/expect/vi, coverage: v8 provider with html reporter)
  - [ ] Subtask 4.3 — Create `apps/web/test/setup.ts` extending expect with `@testing-library/jest-dom` matchers + MSW server lifecycle (beforeAll start, afterEach reset, afterAll close)
  - [ ] Subtask 4.4 — Create `apps/web/mocks/handlers.ts` with initial handlers (GET `/api/v1/tenants/me` 200, POST `/api/v1/tenants/me/industry` 200 — required by Story 1.1 IndustrySelector tests)
  - [ ] Subtask 4.5 — Create `apps/web/mocks/server.ts` (setupServer(...handlers) export)
  - [ ] Subtask 4.6 — Update `apps/web/__tests__/IndustrySelector.test.tsx` — remove scaffolding header comment (delete "Story 0.5 wires the toolchain" + "scaffolding" lines from lines 1-18)
  - [ ] Subtask 4.7 — Update `apps/web/package.json` scripts: add `test` (vitest run), `test:watch` (vitest --watch), `test:ui` (vitest --ui), `test:coverage` (vitest run --coverage)
  - [ ] Subtask 4.8 — Verify `pnpm test` runs IndustrySelector.test.tsx (4 scenarios) + ui-primitives.test.tsx (Task 2.8) and all pass
  - [ ] Subtask 4.9 — Verify `pnpm lint:tsc` clean + MSW server lifecycle active (test setup logs "MSW server listening" on start)

- [ ] **Task 5 — Playwright wire + Supabase test fixture** (AC: #5)
  - [ ] Subtask 5.1 — Install `@playwright/test@latest` (verify Node 24.18 LTS compat)
  - [ ] Subtask 5.2 — Create `apps/web/playwright.config.ts` (baseURL=http://localhost:3000, projects: chromium/firefox/webkit, webServer: `pnpm dev` with reuseExistingServer on local, timeout 30s, retries: 2 on CI, reporter: list on CI + html local)
  - [ ] Subtask 5.3 — Create `apps/web/e2e/fixtures/supabase-test.ts` (rls_db fixture importable — pattern from `tests/rls/conftest.py` extended to Playwright fixtures)
  - [ ] Subtask 5.4 — Update `apps/web/e2e/onboarding.spec.ts` — remove scaffolding header comment (delete "Story 0.5 wires the real signup" + "The Playwright runner + Supabase test fixtures are added in Story 0.5" + "Until then this file is shipped as scaffolding" lines)
  - [ ] Subtask 5.5 — Update `apps/web/package.json` scripts: add `playwright` (playwright test), `playwright:install` (playwright install --with-deps chromium), `playwright:codegen` (playwright codegen)
  - [ ] Subtask 5.6 — Run `pnpm playwright install --with-deps chromium` (CI runs this step)
  - [ ] Subtask 5.7 — Verify `pnpm playwright test --project=chromium apps/web/e2e/onboarding.spec.ts` runs all 3 scenarios and passes (test_new_user_sees_industry_selector, test_select_service_hides_bom_menu, test_select_manufacturing_service_shows_segment_split)
  - [ ] Subtask 5.8 — Verify `pnpm lint:tsc` clean + Story 1.1 deferred-work.md F-30 entry closed (rls_db fixture importable from e2e)

- [ ] **Task 6 — next-intl wire + ko-KR.json** (AC: #6)
  - [ ] Subtask 6.1 — Install `next-intl@latest` (verify Next 15.5.4 compat)
  - [ ] Subtask 6.2 — Inventory currently inlined ko-KR strings across `IndustrySelector.tsx` + `BOMEditorClient.tsx` + `SettingsWizardClient.tsx` + `MenuProvider.tsx` + `CalcButton.tsx` (~30 strings)
  - [ ] Subtask 6.3 — Create `apps/web/messages/ko-KR.json` with inventoried strings (namespaces: industry, bom, settings, common, errors)
  - [ ] Subtask 6.4 — Create `apps/web/i18n.ts` with `getRequestConfig` (locale='ko-KR' default, timeZone='Asia/Seoul', messages loading from `./messages/${locale}.json`)
  - [ ] Subtask 6.5 — Create `apps/web/middleware.ts` with `createMiddleware` from `next-intl/middleware` matching `/[locale]/...` paths (defaultLocale='ko-KR', localePrefix='as-needed')
  - [ ] Subtask 6.6 — Update `apps/web/next.config.ts` (wrap with `createNextIntlPlugin('./i18n.ts')`)
  - [ ] Subtask 6.7 — Update `apps/web/app/[locale]/layout.tsx` (wrap children with `NextIntlClientProvider` from `next-intl`; pass messages prop)
  - [ ] Subtask 6.8 — Replace inlined ko-KR strings in `IndustrySelector.tsx` + `BOMEditorClient.tsx` + `SettingsWizardClient.tsx` with `const t = useTranslations('namespace'); t('key')`
  - [ ] Subtask 6.9 — Verify `pnpm dev` boots with next-intl routing active + ko-KR strings sourced from messages JSON
  - [ ] Subtask 6.10 — Verify `pnpm lint:tsc` clean
  - [ ] Subtask 6.11 — Close Story 1.1 deferred-work.md F-42 entry (add ✅ marker + commit hash)

- [ ] **Task 7 — shadcn Tabs wire into Story 3.3 monthly_input UI** (AC: #7)
  - [ ] Subtask 7.1 — Locate Story 3.3 frontend Tabs usage point (search `apps/web/components/l2-input/` for tab/strip implementation)
  - [ ] Subtask 7.2 — Verify the file uses a manual tab implementation (or replace shadcn Tabs if already wired)
  - [ ] Subtask 7.3 — Replace manual tab implementation with `<Tabs>` from `apps/web/components/ui/tabs.tsx` (defaultValue, TabsList, TabsTrigger, TabsContent)
  - [ ] Subtask 7.4 — Verify keyboard navigation (Tab/Shift+Tab focus, Enter to activate per Radix Tabs)
  - [ ] Subtask 7.5 — Verify Story 3.3 frontend AC unaffected (warnings display, top_n_severity logic unchanged) + tab switch performance <16ms
  - [ ] Subtask 7.6 — Verify `pnpm lint:tsc` clean + `pnpm test` IndustrySelector unaffected

- [ ] **Task 8 — INDUSTRY_ICON fill + Python mirror + drift test** (AC: #8)
  - [ ] Subtask 8.1 — Update `apps/web/lib/menu-config.ts:1142-1148` `INDUSTRY_ICON` values with lucide-react icon names (manufacturing → Factory, service → Briefcase, manufacturing_service → Layers, manufacturing_service_other → Boxes)
  - [ ] Subtask 8.2 — Update `apps/web/components/sidebar/SidebarItem.tsx` to render `<Factory />` / `<Briefcase />` / `<Layers />` / `<Boxes />` based on `INDUSTRY_ICON[industry]` (lucide-react components)
  - [ ] Subtask 8.3 — Create `packages/services/m0_onboarding/industry_menu.py::INDUSTRY_ICON: Final[dict[Industry, str]] = {"manufacturing": "Factory", "service": "Briefcase", "manufacturing_service": "Layers", "manufacturing_service_other": "Boxes"}` (mirror TS, store icon name only)
  - [ ] Subtask 8.4 — Extend `tests/integration/test_menu_config_consistency.py` with `test_industry_icon_parity` asserting `INDUSTRY_ICON_TS == INDUSTRY_ICON_PY` (A5 forward-lock drift detector pattern)
  - [ ] Subtask 8.5 — Verify `pnpm lint:tsc` + `uv run pytest tests/integration/test_menu_config_consistency.py -v` clean
  - [ ] Subtask 8.6 — Close Story 1.1 deferred-work.md F-33 + F-37 entries (add ✅ markers + commit hash)

- [ ] **Task 9 — CI gate + ESLint refinement + Makefile + engines field** (AC: #9)
  - [ ] Subtask 9.1 — Update `.github/workflows/ci.yml` — add `web-test` job (`pnpm install --frozen-lockfile` → `pnpm lint:tsc` → `pnpm lint:conventions` → `pnpm test --run` → upload vitest HTML report)
  - [ ] Subtask 9.2 — Update `.github/workflows/ci.yml` — add `web-e2e` job (`pnpm install --frozen-lockfile` → `pnpm playwright install --with-deps chromium` → `pnpm playwright test --project=chromium` smoke subset only)
  - [ ] Subtask 9.3 — Update `apps/web/package.json` engines field: `"engines": { "node": ">=24.18.0" }` (resolves Story 0.3 TYPES-1 deferral)
  - [ ] Subtask 9.4 — Update Makefile — add `web-test` target (delegates to `pnpm test --run`) + `web-e2e` target (delegates to `pnpm playwright test --project=chromium`)
  - [ ] Subtask 9.5 — Refine `.eslint.config.mjs` — vitest globals (`describe`, `it`, `expect`, `vi`, `beforeAll`, `afterAll`, `beforeEach`, `afterEach`) added to globals (per-file disable refinement deferred from Story 0.4)
  - [ ] Subtask 9.6 — Verify CI `web-test` + `web-e2e` jobs pass on a test PR
  - [ ] Subtask 9.7 — Close Story 0.3 TYPES-1 deferral (engines field)

- [ ] **Task 10 — Documentation + deferred-work close-out** (AC: #10)
  - [ ] Subtask 10.1 — Create `docs/frontend-toolchain.md` (NEW) — 8 sections (Stack pin / Tailwind / shadcn / sonner / vitest / Playwright / next-intl / INDUSTRY_ICON contract)
  - [ ] Subtask 10.2 — Update `docs/conventions.md` §6 (Frontend Tooling) — stack pin + design tokens reference
  - [ ] Subtask 10.3 — Update `deferred-work.md` — close F-1 (Pretendard), Story 0.4 ESLint refinement, F-30, F-31, F-32, F-33, F-37 (Story 1.1), F-42 (next-intl), M11 (Story 2.2 sonner toast), M14 (Story 5.1 TS mirror file), L8 (Story 5.1 SQL CHECK — backend deferred separately)
  - [ ] Subtask 10.4 — Update `_bmad-output/implementation-artifacts/epic-4-retro-close-out-2026-08-03.md` §7 — A6 follow-through status: ✅ done
  - [ ] Subtask 10.5 — Update `sprint-status.yaml` — `0-5-frontend-plumbing-shadcn-sonner-vitest-playwright: ready-for-dev → in-progress → review → done` after Task 1-9 complete + bmad-code-review pass

- [ ] **Task 11 — Story 0.5 dev-story execute** (T1~T10) + 3중 게이트
  - [ ] Subtask 11.1 — Run `uv run pytest` (full backend suite) → 0 failed (regression check)
  - [ ] Subtask 11.2 — Run `uv run ruff check apps/api packages/cost_engine packages/services packages/ports` → 0 errors
  - [ ] Subtask 11.3 — Run `uv run import-linter` → 2 contracts KEPT (or extend to include web if applicable)
  - [ ] Subtask 11.4 — Run `pnpm lint:tsc` → 0 errors
  - [ ] Subtask 11.5 — Run `pnpm lint:conventions` → 0 errors
  - [ ] Subtask 11.6 — Run `pnpm test --run` → all vitest tests pass (IndustrySelector + ui-primitives + future tests)
  - [ ] Subtask 11.7 — Run `pnpm playwright test --project=chromium` → all 3 onboarding scenarios pass
  - [ ] Subtask 11.8 — bmad-code-review (3 reviewer 병렬: blind hunter + edge case hunter + acceptance auditor)
  - [ ] Subtask 11.9 — Apply patches per review findings
  - [ ] Subtask 11.10 — Forward `sprint-status.yaml` `0-5: review → done` + set baseline_commit = HEAD
  - [ ] Subtask 11.11 — Epic 5 5-3 spec entry now unblocked (A6 done)

## Dev Notes

### Codebase state (verified 2026-08-04)

- **No Tailwind installed** — `apps/web/app/layout.tsx:20` uses inline `style={{ fontFamily: ... }}` (Story 0.1 L4 deferred to Story 0.4 design tokens, then deferred to Story 0.5)
- **No shadcn/ui installed** — `components.json` missing, no Radix UI, no `class-variance-authority`, no `tailwind-merge`, no `lucide-react`
- **No sonner installed** — `apps/web/components/m1-baseline/products/BOMEditorClient.tsx:265` uses inline `<p>` for BOM NOT_COMPLETE message (Story 2.2 M11 deferred to Story 0.5)
- **No vitest installed** — `apps/web/__tests__/IndustrySelector.test.tsx:25` imports from `vitest` but vitest NOT in `apps/web/package.json` (scaffolding header comment: "Story 0.5 wires the toolchain")
- **No Playwright installed** — `apps/web/e2e/onboarding.spec.ts:19` imports from `@playwright/test` but `@playwright/test` NOT in `apps/web/package.json` (scaffolding header: "The Playwright runner + Supabase test fixtures are added in Story 0.5")
- **No next-intl installed** — `apps/web/messages/ko-KR.json` missing (Story 1.1 F-42 deferred)
- **No Pretendard local font** — `apps/web/app/layout.tsx:14-19` uses CDN without SRI (Story 0.1 L4 deferred to Story 0.4 then Story 0.5)
- **INDUSTRY_ICON placeholders** — `apps/web/lib/menu-config.ts:1142-1148` exports `INDUSTRY_ICON` with placeholder values (Story 1.1 F-33 deferred)
- **No Python INDUSTRY_ICON mirror** — `packages/services/m0_onboarding/industry_menu.py` does NOT export `INDUSTRY_ICON` (Story 1.1 F-37 deferred)

### Project Structure Notes

- Story 0.5 is **cross-cutting plumbing**, not part of Epic 0 proper (Epic 0 = 4 stories, all done). The "0.5" numbering is symbolic (between Epic 0 and Epic 1).
- Epic 0 status stays `done` after Story 0.5 added — Story 0.5 is a retro carry-over (Epic 4 close-out retro A6 NEW 결정), not an Epic 0 expansion.
- Story 0.5 is required BEFORE Epic 5 5-3 spec entry (frontend toast prerequisite).
- Story 0.5 can run in parallel with Epic 5 5-1 + 5-2 (backend-only, no frontend dependency).
- All 10 ACs are independent (Tailwind → shadcn → sonner → vitest → Playwright → next-intl → Tabs wire → INDUSTRY_ICON → CI → docs) but have natural ordering (T1 → T2 → T3 → T4 → T5 → T6 → T7 → T8 → T9 → T10).

### Alignment with unified project structure

- **No new module folders** — Story 0.5 only adds tooling, not domain modules
- **`apps/web/lib/`** — `utils.ts` (cn helper) joins existing `lib/` (money.ts, types.ts, api-client.ts, etc.)
- **`apps/web/components/ui/`** — shadcn-generated primitive components join existing component folders (NEW dir per shadcn convention)
- **`apps/web/test/`** — vitest setup + MSW server (NEW dir)
- **`apps/web/mocks/`** — MSW handlers (NEW dir)
- **`apps/web/e2e/fixtures/`** — Playwright fixtures (NEW dir, joins existing `e2e/`)
- **`apps/web/messages/`** — next-intl translation JSONs (NEW dir)
- **`apps/web/public/fonts/`** — Pretendard Variable font files (NEW dir, joins existing `public/`)
- **`packages/services/m0_onboarding/`** — extend `industry_menu.py` with INDUSTRY_ICON (existing file, no new dir)
- **`docs/frontend-toolchain.md`** — NEW doc (joins existing `docs/`)
- **`docs/conventions.md` §6** — extend existing conventions doc
- **`deferred-work.md`** — append closed entries (existing file)
- **`Makefile`** — extend with `web-test` + `web-e2e` targets (existing file)
- **`.github/workflows/ci.yml`** — extend with `web-test` + `web-e2e` jobs (existing file)
- **`.eslint.config.mjs`** — extend with vitest globals (existing file, per-file disable refinement deferred from Story 0.4)

### Detected conflicts or variances

- **Tailwind version bump** — Story 0.5 spec assumes Tailwind 4.3.3 per STACK_PIN, but no Tailwind is currently installed. Stack pin is reference baseline; Story 0.5 implementation may need `[STACK BUMP]` if actual installed version differs (verify `pnpm view tailwindcss dist-tags.latest` before install).
- **shadcn CLI version drift** — shadcn CLI is evolving rapidly (post-2026-08 may have breaking changes). Pin CLI version explicitly: `pnpm dlx shadcn@<exact-version>`. Story 0.5 implementation must verify CLI version before `init` + `add` commands.
- **Next 15.5.4 vs Next 16.x** — STACK_PIN baseline is Next 16.2.11 but `apps/web/package.json` shows Next 15.5.4 (Story 0.3 RANGE-1 DECISION). Story 0.5 uses 15.5.4 (current actual); `[STACK BUMP]` for 16.2.11 is separate work.
- **vitest + Next 15.5.4 jsdom env** — vitest with Next App Router + React 19.1.1 jsdom env stability is a known concern. Story 0.5 implementation must verify `pnpm test` boots cleanly; if not, fall back to happy-dom (installed in T4.1).
- **next-intl + Next 15.5.4 compat** — verify next-intl latest supports Next 15.5.x before install. If not, pin next-intl to a 15.5-compatible minor.
- **Playwright Chromium binary size** — `--with-deps chromium` is ~150MB. CI cache via `actions/cache` to avoid re-download per job.

### Testing standards summary

- **vitest** (AC #4): `apps/web/__tests__/**/*.{test,spec}.{ts,tsx}` pattern. Coverage: v8 provider with html + json-summary reporter. `globals: true` for describe/it/expect/vi.
- **Playwright** (AC #5): `apps/web/e2e/**/*.spec.ts` pattern. Base URL: `http://localhost:3000`. Timeout 30s. Retries 2 on CI.
- **MSW handlers** (AC #4): `apps/web/mocks/handlers.ts` for component tests, `apps/web/e2e/fixtures/supabase-test.ts` for E2E.
- **Backend regression**: `uv run pytest` (full suite) must stay 0 failed. Pre-existing 0 failures (Epic 4 retro A1 done 2026-08-03).
- **3중 게이트** (Story 0.5 dev-story execute): ruff + import-linter + pytest (backend) + pnpm lint:tsc + pnpm lint:conventions + pnpm test + pnpm playwright test (frontend) all clean.

### Dependencies

- **Backend deps**: 0 new Python deps (Story 0.5 is frontend-only)
- **Frontend deps (new)**:
  - `tailwindcss@4.3.3` + `@tailwindcss/postcss` + `postcss` + `autoprefixer` (T1.1)
  - `@radix-ui/react-tabs` + `@radix-ui/react-tooltip` + `@radix-ui/react-dialog` + `@radix-ui/react-toast` + `@radix-ui/react-dropdown-menu` + `@radix-ui/react-select` + `@radix-ui/react-slot` (T2.1)
  - `class-variance-authority` + `tailwind-merge` + `clsx` + `lucide-react` (T2.2)
  - `sonner` (T3.1)
  - `vitest` + `@vitest/ui` + `@testing-library/react` + `@testing-library/dom` + `@testing-library/jest-dom` + `@testing-library/user-event` + `jsdom` + `happy-dom` (T4.1)
  - `msw` (T4.1)
  - `@playwright/test` (T5.1)
  - `next-intl` (T6.1)
- **shadcn primitives** (T2.6): `tabs`, `tooltip`, `dialog` (3 most-needed for Epic 5 5-3 + 2-2 M11 + Story 0.4 F-32)
- **Fonts**: Pretendard Variable (download to `apps/web/public/fonts/`, configure via `next/font/local`)
- **Alembic migrations**: 0 new (Story 0.5 is frontend-only)

### Story 0.5 dev-story execute sequence

```
T1 (Tailwind) → T2 (shadcn) → T3 (sonner) → T4 (vitest) → T5 (Playwright) → T6 (next-intl) → T7 (Tabs wire) → T8 (INDUSTRY_ICON) → T9 (CI) → T10 (docs) → T11 (3중 게이트 + CR)
```

Parallel possible:
- T4 + T5 (vitest + Playwright — different toolchains, no overlap)
- T6 + T7 + T8 (next-intl + Tabs wire + INDUSTRY_ICON — different concerns)
- T9 + T10 (CI + docs — different files)

### Out of scope (deferred to other stories)

- **Story 5-1 TS mirror file (`apps/web/lib/l2-input-opening-carry.ts`)** — Story 0.5 wires the toolchain; actual TS mirror file creation is Story 5.1 dev-story (Epic 5 ledger frontend entry point). M14 deferred to Story 5.1.
- **Story 5-3 frontend toast (Epic 5 5-3 spec)** — separate story. A6 done is the gate.
- **Epic 6 charts/PDF frontend** — separate story.
- **Epic 7 BEP frontend** — separate story.
- **Epic 8 budget variance frontend** — separate story.
- **next-intl dynamic locale switching** — Story 0.5 only sets up ko-KR; multi-locale (en-US, ja-JP) is post-MVP.
- **INDUSTRY_ICON icon design polish** — Story 0.5 uses lucide-react defaults; custom icons deferred to design system story.
- **Pretendard subset optimization** — full Pretendard Variable file (large); subset to Korean glyphs deferred to perf story.

### Anti-pattern prevention

- **DO NOT** install `vitest` without `--frozen-lockfile` in CI (lockfile drift = Story 0.3 STACK_PIN violation).
- **DO NOT** run `pnpm dlx shadcn@latest` without pinning exact CLI version (shadcn CLI drifts rapidly, breaking changes between minor versions).
- **DO NOT** skip Playwright browser install in CI (`--with-deps chromium` required before `playwright test`).
- **DO NOT** use `toast` from `sonner` directly in server components (sonner requires `'use client'`).
- **DO NOT** use `next-intl` `useTranslations` outside `<NextIntlClientProvider>` boundary.
- **DO NOT** use camelCase shadcn-generated component names — shadcn already PascalCase (Tabs/TabsList/etc.), don't rename.
- **DO NOT** add new ENV vars without updating `.env.example` + `.github/workflows/ci.yml`.
- **DO** use `cn()` helper from `lib/utils.ts` for className composition (clsx + tailwind-merge for proper conflict resolution).
- **DO** pin all new deps to exact versions (no `^` or `~`) per AD-14 stack pin convention.
- **DO** add `engines.node` to `apps/web/package.json` matching root `.nvmrc` (24.18 LTS).
- **DO** use `app/globals.css` `@layer base` for design tokens (per shadcn convention, allows Tailwind utilities to override).
- **DO** keep MSW handlers synchronous (no async fetch in initial handlers — `http.get()` returns static response).
- **DO** use Playwright `webServer.reuseExistingServer: !process.env.CI` (faster local dev, fresh server on CI).

### References

- [Source: `_bmad-output/implementation-artifacts/epic-4-retro-close-out-2026-08-03.md#A6`] — Epic 4 close-out retro A6 NEW 결정 (Story 0.5 plumbing 별도 Story)
- [Source: `_bmad-output/implementation-artifacts/deferred-work.md`] — F-1, Story 0.4 ESLint refinement, F-30, F-31, F-32, F-33, F-37, F-42, M11 (Story 2.2), M14 (Story 5.1), L7, L8 (Story 5.1)
- [Source: `_bmad-output/implementation-artifacts/0-4-cross-language-conventions-monetary-types-foundation.md`] — Prev story (Story 0.4 — conventions + money types)
- [Source: `_bmad-output/implementation-artifacts/2-2-bom-matrix-100-validation.md`] — Story 2.2 M11 sonner toast deferral source
- [Source: `_bmad-output/implementation-artifacts/3-3-negative-inventory-overcapacity-real-time-warning.md`] — Story 3.3 frontend tab usage (T7 target)
- [Source: `_bmad-output/implementation-artifacts/5-1-opening-inventory-auto-carry-chain.md`] — Story 5.1 M14 TS mirror file deferral source
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 0.4`] — Convention precedent (Story 0.5 mirrors Story 0.4 structure)
- [Source: `_bmad-output/planning-artifacts/prd.md#6.4`] — next-intl requirement
- [Source: `_bmad-output/planning-artifacts/architecture/architecture-costmgr-2026-07-24/ARCHITECTURE-SPINE.md`] — AD-1 (modular monolith), AD-14 (stack pin), AD-15 (cross-language conventions), AD-8 (monetary types)
- [Source: shadcn/ui docs](https://ui.shadcn.com/docs) — shadcn CLI + components.json spec
- [Source: Tailwind CSS 4 docs](https://tailwindcss.com/docs) — `@import "tailwindcss"` + design tokens
- [Source: sonner docs](https://sonner.emilkowal.ski/) — Toaster + toast usage
- [Source: vitest docs](https://vitest.dev/) — config + setup + jsdom env
- [Source: Playwright docs](https://playwright.dev/) — config + fixtures + projects
- [Source: next-intl docs](https://next-intl.dev/) — routing + middleware + messages
- [Source: Radix UI docs](https://www.radix-ui.com/) — Tabs / Tooltip / Dialog primitives
- [Source: lucide-react docs](https://lucide.dev/) — icon set

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}} — to be filled by dev agent

### Debug Log References

(Will be populated by dev agent during T1~T10 execution)

### Completion Notes List

(Will be populated by dev agent after 3중 게이트 + bmad-code-review pass)

### File List

**Created (NEW):**
- `apps/web/postcss.config.mjs` — PostCSS config (Tailwind 4 + autoprefixer)
- `apps/web/tailwind.config.ts` — Tailwind config (content paths + shadcn design tokens)
- `apps/web/app/globals.css` — Tailwind import + design tokens CSS variables
- `apps/web/components.json` — shadcn config
- `apps/web/lib/utils.ts` — cn helper (clsx + tailwind-merge)
- `apps/web/components/ui/tabs.tsx` — shadcn Tabs primitive
- `apps/web/components/ui/tooltip.tsx` — shadcn Tooltip primitive
- `apps/web/components/ui/dialog.tsx` — shadcn Dialog primitive
- `apps/web/components/ui/sonner.tsx` — sonner Toaster wrapper
- `apps/web/test/setup.ts` — vitest setup (jest-dom + MSW lifecycle)
- `apps/web/mocks/handlers.ts` — MSW request handlers
- `apps/web/mocks/server.ts` — MSW setupServer
- `apps/web/playwright.config.ts` — Playwright config
- `apps/web/e2e/fixtures/supabase-test.ts` — rls_db fixture (resolves F-30)
- `apps/web/i18n.ts` — next-intl getRequestConfig
- `apps/web/middleware.ts` — next-intl middleware
- `apps/web/messages/ko-KR.json` — ko-KR translations
- `apps/web/__tests__/ui-primitives.test.tsx` — shadcn Tabs smoke test
- `apps/web/public/fonts/PretendardVariable.woff2` — Pretendard Variable font (binary, joined from CDN)
- `docs/frontend-toolchain.md` — frontend toolchain guide (NEW)

**Modified (UPDATE):**
- `apps/web/package.json` — 14 new deps + 4 new scripts + engines field
- `apps/web/app/layout.tsx` — Toaster + globals.css import + Pretendard next/font/local
- `apps/web/next.config.ts` — next-intl plugin wrap
- `apps/web/app/[locale]/layout.tsx` — NextIntlClientProvider
- `apps/web/components/m1-baseline/products/BOMEditorClient.tsx` — inline `<p>` → toast.warning
- `apps/web/components/sidebar/SidebarItem.tsx` — render lucide-react icons from INDUSTRY_ICON
- `apps/web/lib/menu-config.ts` — INDUSTRY_ICON placeholder → lucide-react names
- `apps/web/components/onboarding/IndustrySelector.tsx` — inlined ko-KR → useTranslations
- `apps/web/components/m1-baseline/products/BOMEditorClient.tsx` — inlined ko-KR → useTranslations
- `apps/web/components/settings/wizard/SettingsWizardClient.tsx` — inlined ko-KR → useTranslations
- `apps/web/components/l2-input/MonthlyInputTabs.tsx` — manual tabs → shadcn Tabs
- `apps/web/__tests__/IndustrySelector.test.tsx` — remove scaffolding header (already imports vitest)
- `apps/web/e2e/onboarding.spec.ts` — remove scaffolding header (already imports @playwright/test)
- `packages/services/m0_onboarding/industry_menu.py` — INDUSTRY_ICON mirror (icon name only)
- `tests/integration/test_menu_config_consistency.py` — extend with INDUSTRY_ICON parity test
- `docs/conventions.md` — §6 Frontend Tooling section
- `Makefile` — `web-test` + `web-e2e` targets
- `.github/workflows/ci.yml` — `web-test` + `web-e2e` jobs
- `.eslint.config.mjs` — vitest globals + per-file disable refinement
- `_bmad-output/implementation-artifacts/deferred-work.md` — close F-1, Story 0.4 ESLint refinement, F-30, F-31, F-32, F-33, F-37, F-42, M11, M14 (L7/L8/L10 deferred)
- `_bmad-output/implementation-artifacts/epic-4-retro-close-out-2026-08-03.md` — §7 A6 follow-through ✅ done
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — `0-5-frontend-plumbing-shadcn-sonner-vitest-playwright: ready-for-dev → in-progress → review → done` + last_updated + last_updated_note
- `pnpm-lock.yaml` — updated by `pnpm add` (multiple)
- `uv.lock` — 0 changes (no Python deps added)

### Review Findings

(Will be populated by bmad-code-review after dev-story execute)